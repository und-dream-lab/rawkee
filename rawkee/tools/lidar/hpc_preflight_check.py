#!/usr/bin/env python3
"""
hpc_preflight_check.py
======================
Run this script on a compute node BEFORE submitting rawkee scan pipeline jobs.
It checks every required Python dependency, validates CUDA/PyTorch compatibility,
and prints fix commands for anything that is missing or mismatched.

Usage:
    python hpc_preflight_check.py
    python hpc_preflight_check.py --json   # machine-readable output
    python hpc_preflight_check.py --strict # exit 1 if any warning/error found
"""

import argparse
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name:     str
    status:   str           # OK | WARN | ERROR | SKIP
    version:  Optional[str] = None
    message:  str = ''
    fix:      str = ''


results: list[CheckResult] = []


def ok(name, version=None, msg=''):
    results.append(CheckResult(name, 'OK', version, msg))

def warn(name, msg, fix='', version=None):
    results.append(CheckResult(name, 'WARN', version, msg, fix))

def error(name, msg, fix='', version=None):
    results.append(CheckResult(name, 'ERROR', version, msg, fix))

def skip(name, msg=''):
    results.append(CheckResult(name, 'SKIP', message=msg))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _try_import(mod: str):
    try:
        return importlib.import_module(mod)
    except ImportError:
        return None

def _pkg_version(mod_name: str, attr: str = '__version__') -> Optional[str]:
    m = _try_import(mod_name)
    if m is None:
        return None
    return getattr(m, attr, 'unknown')

def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception:
        return -1, ''


# ---------------------------------------------------------------------------
# Check sections
# ---------------------------------------------------------------------------

def check_python():
    v = sys.version_info
    ver = f'{v.major}.{v.minor}.{v.micro}'
    if v < (3, 10):
        error('Python', f'Version {ver} is too old. rawkee requires Python â‰¥ 3.10.',
              fix='module load python/3.11  # or use a virtualenv with Python 3.11+',
              version=ver)
    else:
        ok('Python', version=ver)



def check_numpy():
    np = _try_import('numpy')
    if np is None:
        error('numpy', 'Not installed.',
              fix='pip install "numpy>=1.24"')
        return
    v = np.__version__
    major = int(v.split('.')[0])
    if major < 1 or (major == 1 and int(v.split('.')[1]) < 24):
        warn('numpy', f'Version {v} is old; recommend â‰¥ 1.24.',
             fix='pip install --upgrade "numpy>=1.24"', version=v)
    else:
        ok('numpy', version=v)


def check_torch():
    torch = _try_import('torch')
    if torch is None:
        error('torch (PyTorch)', 'Not installed.',
              fix=(
                  'pip install torch --index-url https://download.pytorch.org/whl/cu124\n'
                  '  For Grace/Hopper use cu124; for Blackwell/DGX Spark use NGC container:\n'
                  '  nvcr.io/nvidia/pytorch:26.05-py3'
              ))
        return

    tv = torch.__version__
    cuda_ver = getattr(torch.version, 'cuda', None) or 'not compiled with CUDA'
    ok('torch (PyTorch)', version=f'{tv}  (CUDA build: {cuda_ver})')

    # Check CUDA availability
    if not torch.cuda.is_available():
        error('CUDA', 'torch.cuda.is_available() returned False.',
              fix=(
                  '1. Check driver: nvidia-smi\n'
                  '  2. Match PyTorch CUDA build to driver:\n'
                  '     driver â‰¥ 525  â†’  pip install torch --index-url https://download.pytorch.org/whl/cu121\n'
                  '     driver â‰¥ 545  â†’  pip install torch --index-url https://download.pytorch.org/whl/cu124\n'
                  '     Blackwell     â†’  use NGC container nvcr.io/nvidia/pytorch:26.05-py3'
              ))
        return

    # GPU info
    n = torch.cuda.device_count()
    for i in range(n):
        p     = torch.cuda.get_device_properties(i)
        sm    = f'sm_{p.major}{p.minor}'
        vram  = p.total_memory >> 30
        label = f'GPU {i}: {p.name}  {vram} GB  {sm}'

        if p.major < 6:
            error(f'GPU {i}', f'{p.name} ({sm}) is below sm_60. Training will fail.',
                  fix='Upgrade to an NVIDIA GPU with compute capability â‰¥ 6.0 (Pascal or newer).',
                  version=sm)
        elif p.major < 7:
            warn(f'GPU {i}', f'{p.name} ({sm}) is Pascal-era. gsplat training may be slow.',
                 fix='Recommend Volta (sm_70) or newer for efficient training.',
                 version=sm)
        else:
            ok(f'GPU {i}', version=sm, msg=label)

        # Blackwell (sm_100) requires NGC container or nightly PyTorch
        if p.major >= 10:
            cuda_b = torch.version.cuda or ''
            if not cuda_b.startswith('12.8') and 'nightly' not in tv:
                warn(f'GPU {i} (Blackwell)', 
                     f'{p.name} requires CUDA â‰¥ 12.8 or NGC container; detected torch CUDA {cuda_b}.',
                     fix=(
                         'Use NVIDIA NGC container: nvcr.io/nvidia/pytorch:26.05-py3\n'
                         '  or: pip install torch --pre --index-url https://download.pytorch.org/whl/nightly/cu128'
                     ), version=sm)

    # NCCL for DDP
    try:
        nccl = torch.cuda.nccl.version()
        ok('NCCL', version='.'.join(str(x) for x in nccl))
    except Exception:
        warn('NCCL', 'NCCL version not detectable. DDP multi-node training may fail.',
             fix='Ensure torch was built with NCCL support (standard CUDA wheels include it).')


def check_gsplat():
    m = _try_import('gsplat')
    if m is None:
        error('gsplat', 'Not installed. Required for Gaussian splat training.',
              fix='pip install gsplat  # requires CUDA toolkit and a compiled wheel')
        return
    ok('gsplat', version=_pkg_version('gsplat'))


def check_open3d():
    m = _try_import('open3d')
    if m is None:
        error('open3d', 'Not installed. Required for Poisson mesh reconstruction and E57 fallback.',
              fix='pip install open3d')
        return
    ok('open3d', version=_pkg_version('open3d'))


def check_scipy():
    m = _try_import('scipy')
    if m is None:
        error('scipy', 'Not installed. Required for KDTree in texture baking and UTM projection.',
              fix='pip install scipy')
        return
    ok('scipy', version=_pkg_version('scipy'))


def check_imageio():
    m = _try_import('imageio')
    if m is None:
        error('imageio', 'Not installed. Required for HDR/PNG image saving.',
              fix='pip install "imageio[freeimage]"')
        return
    iio_ver = _pkg_version('imageio')
    # Verify FreeImage works by writing/reading a small HDR file
    fi_ok = False
    try:
        import imageio.v3 as _iio3, numpy as _np, tempfile as _tf, os as _os
        _tmp = _tf.mktemp(suffix='.hdr')
        _iio3.imwrite(_tmp, _np.ones((4, 4, 3), dtype=_np.float32))
        _iio3.imread(_tmp)
        _os.unlink(_tmp)
        fi_ok = True
    except Exception:
        pass
    if fi_ok:
        ok('imageio', version=iio_ver, msg='FreeImage binary confirmed')
    else:
        warn('imageio', 'FreeImage binary not loadable. HDR (.hdr) output will fail.',
             fix='pip install "imageio[freeimage]"',
             version=iio_ver)


def check_rawpy():
    m = _try_import('rawpy')
    if m is None:
        warn('rawpy', 'Not installed. DNG/RAW image loading will be unavailable (JPEG/TIFF still works).',
             fix='pip install rawpy')
        return
    ok('rawpy', version=_pkg_version('rawpy'))


def check_pil():
    m = _try_import('PIL')
    if m is None:
        error('Pillow (PIL)', 'Not installed. Required for image resizing in splat training.',
              fix='pip install Pillow')
        return
    try:
        version = importlib.metadata.version('Pillow')
    except importlib.metadata.PackageNotFoundError:
        version = getattr(m, '__version__', 'unknown')
    ok('Pillow (PIL)', version=version)


def check_rosbags():
    m = _try_import('rosbags')
    if m is None:
        warn('rosbags', 'Not installed. LiDAR extraction from NavVis ROS bags will be unavailable.',
             fix='pip install rosbags')
        return
    ok('rosbags', version=_pkg_version('rosbags'))


def check_pye57():
    m = _try_import('pye57')
    if m is None:
        warn('pye57', 'Not installed. E57 point cloud reading will fall back to open3d.',
             fix='pip install pye57')
        return
    ok('pye57', version=_pkg_version('pye57'))


def check_pyproj():
    m = _try_import('pyproj')
    if m is None:
        warn('pyproj', 'Not installed. Georeferencing will use built-in Helmert UTM formula (< 1 mm error within a zone).',
             fix='pip install pyproj')
        return
    ok('pyproj', version=_pkg_version('pyproj'))


def check_ninja():
    m = _try_import('ninja')
    if m is None:
        warn('ninja', 'Not installed. gsplat CUDA JIT compilation will fail at runtime.',
             fix='pip install ninja  # small C++ build tool, ~1 MB, not an LLM')
        return
    try:
        version = importlib.metadata.version('ninja')
    except importlib.metadata.PackageNotFoundError:
        version = 'unknown'
    ok('ninja', version=version)


def check_pyside6():
    m = _try_import('PySide6')
    if m is None:
        warn('PySide6', 'Not installed. The desktop GUI (scan_gui.py) will be unavailable.',
             fix='pip install PySide6  # not required for CLI / SLURM usage')
        return
    ok('PySide6', version=_pkg_version('PySide6'))


def check_rawkee():
    m = _try_import('rawkee.tools.lidar')
    if m is None:
        error('rawkee.tools.lidar', 'rawkee package is not on PYTHONPATH.',
              fix=(
                  'cd /path/to/rawkee\n'
                  '  pip install -e .   # editable install\n'
                  '  # or: export PYTHONPATH=/path/to/rawkee:$PYTHONPATH'
              ))
        return
    ok('rawkee.tools.lidar', msg='Package importable')


def check_nvidia_smi():
    rc, out = _run(['nvidia-smi', '--query-gpu=name,driver_version,memory.total',
                    '--format=csv,noheader'])
    if rc != 0:
        warn('nvidia-smi', 'nvidia-smi not available or no GPU detected.',
             fix='Ensure NVIDIA drivers are installed: module load cuda')
        return
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 3:
            name, drv, mem = parts[0], parts[1], parts[2]
            drv_major = int(drv.split('.')[0]) if drv.split('.')[0].isdigit() else 0
            msg = f'{name}  driver {drv}  {mem}'
            if drv_major < 525:
                warn('nvidia-smi', f'Driver {drv} is below 525; CUDA 12.x requires â‰¥ 525.',
                     fix='Update NVIDIA driver: contact your HPC sysadmin or use "module load cuda/12.x"',
                     version=drv)
            else:
                ok('nvidia-smi', version=drv, msg=msg)


def check_cuda_toolkit():
    rc, out = _run(['nvcc', '--version'])
    if rc != 0:
        warn('nvcc (CUDA toolkit)', 'nvcc not found. Compilation of custom CUDA extensions (gsplat) may fail.',
             fix='module load cuda/12.4   # or whichever version matches your PyTorch build')
        return
    import re
    m = re.search(r'release (\S+),', out)
    ver = m.group(1).rstrip(',') if m else 'unknown'
    ok('nvcc (CUDA toolkit)', version=ver)


def check_cxx_compiler():
    """Check for gcc needed by gsplat / PyTorch JIT."""
    import platform
    if platform.system() == 'Windows':
        skip('C++ compiler', 'Windows check skipped — run install_workstation_deps.py instead')
        return
    rc, out = _run(['gcc', '--version'])
        if rc != 0:
            error('gcc',
                  'GCC C++ compiler not found. gsplat CUDA JIT compilation will fail.',
                  fix=(
                      'Ubuntu/Debian: apt install build-essential python3-dev\n'
                      'RHEL/CentOS:   yum groupinstall "Development Tools" && yum install python3-devel\n'
                      'HPC module:    module load gcc'
                  ))
            return
        import re as _re
        m = _re.search(r'(\d+\.\d+\.\d+)', out.splitlines()[0])
        ver = m.group(1) if m else 'unknown'
        ok('gcc', version=ver)

        # Also check python dev headers (needed to build C extensions)
        rc2, _ = _run(['python3-config', '--includes'])
        if rc2 != 0:
            warn('python3-dev headers',
                 'python3-config not found. Building C extensions may fail.',
                 fix=(
                     'Ubuntu/Debian: apt install python3-dev\n'
                     'RHEL/CentOS:   yum install python3-devel'
                 ))
        else:
            ok('python3-dev headers', msg='python3-config found')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CHECKS = [
    check_python,
    check_numpy,
    check_torch,
    check_gsplat,
    check_open3d,
    check_scipy,
    check_imageio,
    check_rawpy,
    check_pil,
    check_rosbags,
    check_pye57,
    check_pyproj,
    check_ninja,
    check_pyside6,
    check_rawkee,
    check_nvidia_smi,
    check_cuda_toolkit,
    check_cxx_compiler,
]

STATUS_ICON  = {'OK': '[+]', 'WARN': '[!]', 'ERROR': '[X]', 'SKIP': '[-]'}
STATUS_LABEL = {'OK': 'OK   ', 'WARN': 'WARN ', 'ERROR': 'ERROR', 'SKIP': 'SKIP '}


def main():
    parser = argparse.ArgumentParser(description='rawkee HPC environment preflight check')
    parser.add_argument('--json',   action='store_true', help='Output machine-readable JSON')
    parser.add_argument('--strict', action='store_true', help='Exit 1 if any WARN or ERROR')
    args = parser.parse_args()

    print('=' * 70)
    print('rawkee scan pipeline â€” HPC environment preflight check')
    print(f'Host    : {platform.node()}')
    print(f'OS      : {platform.system()} {platform.release()}  {platform.machine()}')
    print(f'Python  : {sys.executable}')
    print(f'Env     : {os.environ.get("VIRTUAL_ENV") or os.environ.get("CONDA_DEFAULT_ENV") or "(none)"}')
    print('=' * 70)

    for check in CHECKS:
        check()

    errors  = [r for r in results if r.status == 'ERROR']
    warns   = [r for r in results if r.status == 'WARN']

    if args.json:
        print(json.dumps([vars(r) for r in results], indent=2))
        sys.exit(1 if (errors or (args.strict and warns)) else 0)

    # Pretty-print results
    print()
    for r in results:
        icon  = STATUS_ICON[r.status]
        label = STATUS_LABEL[r.status]
        ver   = f'  [{r.version}]' if r.version else ''
        msg   = f'  {r.message}' if r.message else ''
        print(f'  {icon} {label}  {r.name}{ver}{msg}')

    # Fix section
    fixable = [r for r in results if r.fix and r.status in ('ERROR', 'WARN')]
    if fixable:
        print()
        print('â”€' * 70)
        print('SUGGESTED FIXES')
        print('â”€' * 70)
        for r in fixable:
            tag = '[ ERROR ]' if r.status == 'ERROR' else '[ WARN  ]'
            print(f'\n{tag} {r.name}')
            for line in r.fix.splitlines():
                print(f'  {line}')

    # Summary
    print()
    print('â”€' * 70)
    n_ok   = sum(1 for r in results if r.status == 'OK')
    n_warn = len(warns)
    n_err  = len(errors)
    print(f'  {STATUS_ICON["OK"]} {n_ok} OK    '
          f'{STATUS_ICON["WARN"]} {n_warn} warnings    '
          f'{STATUS_ICON["ERROR"]} {n_err} errors')

    if n_err == 0 and n_warn == 0:
        print('\n  Environment is fully ready.')
    elif n_err == 0:
        print('\n  Environment is functional. Address warnings for full capability.')
    else:
        print('\n  Environment has critical issues. Fix errors before submitting jobs.')

    print('=' * 70)

    should_fail = bool(errors) or (args.strict and bool(warns))
    sys.exit(1 if should_fail else 0)


if __name__ == '__main__':
    main()

