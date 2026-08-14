#!/usr/bin/env python3
"""
install_workstation_deps.py
============================
Run this script once on a workstation to install all Python packages required
to launch the rawkee scan GUI and run the mesh / Gaussian splat pipelines.

The script:
  1. Installs required and optional packages via pip.
  2. Auto-detects your CUDA driver and installs the matching PyTorch wheel.
  3. Reports any CUDA/PyTorch mismatches it cannot fix automatically.
  4. Verifies every install succeeded before reporting done.

Usage:
    python install_workstation_deps.py           # interactive
    python install_workstation_deps.py --yes     # non-interactive (skip prompts)
    python install_workstation_deps.py --dry-run # show what would be installed
"""

import argparse
import importlib
import importlib.metadata
import os
import re
import subprocess
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# Colour helpers (graceful fallback on Windows without ANSI support)
# ---------------------------------------------------------------------------

try:
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)
    _ANSI = True
except Exception:
    _ANSI = False

def _c(text: str, code: str) -> str:
    return f'\033[{code}m{text}\033[0m' if _ANSI else text

def green(t):  return _c(t, '32')
def yellow(t): return _c(t, '33')
def red(t):    return _c(t, '31')
def bold(t):   return _c(t, '1')
def cyan(t):   return _c(t, '36')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DRY_RUN = False
FAILURES: list[str] = []
WARNINGS: list[str] = []


def _run(cmd: list[str], capture: bool = True) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=capture, text=True, timeout=300,
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return -1, 'command not found'
    except Exception as e:
        return -1, str(e)


def _is_installed(pkg_import: str) -> bool:
    try:
        importlib.import_module(pkg_import)
        return True
    except ImportError:
        return False


def _installed_version(dist_name: str) -> Optional[str]:
    try:
        return importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def pip_install(packages: list[str], index_url: str = '', label: str = '') -> bool:
    """Install one or more packages; return True on success."""
    if DRY_RUN:
        print(f'  {cyan("[dry-run]")} pip install {" ".join(packages)}')
        return True

    cmd = [sys.executable, '-m', 'pip', 'install', '--quiet', '--upgrade'] + packages
    if index_url:
        cmd += ['--index-url', index_url]

    desc = label or ' '.join(packages)
    print(f'  Installing {bold(desc)} … ', end='', flush=True)
    rc, out = _run(cmd, capture=True)
    if rc == 0:
        print(green('OK'))
        return True
    else:
        print(red('FAILED'))
        FAILURES.append(f'{desc}: {out[:200]}')
        return False


def section(title: str):
    print(f'\n{bold(cyan(title))}')
    print('─' * 60)


# ---------------------------------------------------------------------------
# CUDA auto-detection
# ---------------------------------------------------------------------------

def _detect_cuda_driver_version() -> Optional[int]:
    """Return NVIDIA driver major version, or None if no GPU."""
    rc, out = _run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'])
    if rc != 0:
        return None
    first = out.strip().splitlines()[0].strip()
    m = re.match(r'^(\d+)', first)
    return int(m.group(1)) if m else None


def _cuda_wheel_for_driver(driver_major: int) -> tuple[str, str]:
    """Return (cuda_label, torch_index_url) appropriate for this driver."""
    if driver_major >= 570:
        return 'cu128', 'https://download.pytorch.org/whl/cu128'
    if driver_major >= 545:
        return 'cu124', 'https://download.pytorch.org/whl/cu124'
    if driver_major >= 528:
        return 'cu121', 'https://download.pytorch.org/whl/cu121'
    # Very old driver: CPU-only torch but warn
    return 'cpu', 'https://download.pytorch.org/whl/cpu'


def _check_torch_cuda_mismatch() -> list[str]:
    """Return list of mismatch messages after torch is installed."""
    issues = []
    try:
        import torch
        cuda_build = getattr(torch.version, 'cuda', None)
        if not cuda_build:
            issues.append(
                f'PyTorch {torch.__version__} was not compiled with CUDA support.\n'
                '  Gaussian splat training will be unavailable.\n'
                '  Fix: pip install torch --index-url https://download.pytorch.org/whl/cu124'
            )
            return issues

        if not torch.cuda.is_available():
            issues.append(
                f'PyTorch CUDA build ({cuda_build}) installed but torch.cuda.is_available() is False.\n'
                '  This usually means the NVIDIA driver is too old for the CUDA version.\n'
                '  Fix: update your NVIDIA driver or install PyTorch for a lower CUDA version.\n'
                f'  Your driver supports up to CUDA {_cuda_from_driver()} — reinstall with:\n'
                '    python install_workstation_deps.py --reinstall-torch'
            )
            return issues

        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            if p.major < 6:
                issues.append(
                    f'GPU {i} ({p.name}, sm_{p.major}{p.minor}) is below sm_60.\n'
                    '  Gaussian splat training requires Pascal (sm_60) or newer.'
                )
            elif p.major >= 10:
                if not (cuda_build or '').startswith('12.8'):
                    issues.append(
                        f'GPU {i} ({p.name}) is Blackwell (sm_{p.major}{p.minor}) and requires CUDA 12.8.\n'
                        f'  Detected PyTorch CUDA build: {cuda_build}.\n'
                        '  Fix: use the NGC container nvcr.io/nvidia/pytorch:26.05-py3'
                    )
    except ImportError:
        pass
    return issues


def _cuda_from_driver() -> str:
    drv = _detect_cuda_driver_version()
    if drv is None:
        return 'unknown'
    label, _ = _cuda_wheel_for_driver(drv)
    return label.replace('cu', '').replace('cpu', 'none')


# ---------------------------------------------------------------------------
# Installation steps
# ---------------------------------------------------------------------------

def step_cxx_compiler():
    section('0 / 7  C++ compiler check (required for gsplat CUDA compilation)')
    import platform
    if platform.system() == 'Windows':
        import shutil as _shutil
        cl_path = _shutil.which('cl')
        if cl_path:
            print(f'  {green("[+]")} cl.exe (MSVC) found: {cl_path}')
        else:
            # where failed — check known VS install locations so we can give a better message
            import glob as _glob
            _cl_candidates = _glob.glob(
                r'C:\Program Files (x86)\Microsoft Visual Studio\**\cl.exe', recursive=True
            ) + _glob.glob(
                r'C:\Program Files\Microsoft Visual Studio\**\cl.exe', recursive=True
            )
            # Filter to host/x64 compiler only (skip cross-compilers)
            _cl_candidates = [p for p in _cl_candidates if r'\Hostx64\x64' in p or r'\x64\cl.exe' in p.lower()]
            if not _cl_candidates:
                _cl_candidates = _glob.glob(
                    r'C:\Program Files (x86)\Microsoft Visual Studio\**\cl.exe', recursive=True
                ) + _glob.glob(
                    r'C:\Program Files\Microsoft Visual Studio\**\cl.exe', recursive=True
                )
            if _cl_candidates:
                print(f'  {yellow("[!]")} cl.exe found on disk but NOT on PATH:')
                print(f'       {_cl_candidates[0]}')
                print( '       You must launch from a Developer PowerShell so PATH is configured.')
                print( '       Start menu -> "Developer PowerShell for VS 2022"')
                print( '       Then re-run:  python -m rawkee.tools.lidar.install_workstation_deps')
                WARNINGS.append('MSVC cl.exe not found. Install VS Build Tools and rerun from Developer PowerShell.')
            else:
                print(f'  {yellow("[!]")} cl.exe (MSVC) NOT found on PATH or on disk.')
                print( '       gsplat CUDA JIT compilation will fail at runtime.')
                print( '       Fix:')
                print( '         1. Install Visual Studio Build Tools 2022 (free):')
                print( '            https://visualstudio.microsoft.com/visual-cpp-build-tools/')
                print( '            Select "Desktop development with C++"')
                print( '         2. Relaunch from Developer PowerShell for VS 2022')
                print( '            (Start menu -> "Developer PowerShell for VS 2022")')
                WARNINGS.append('MSVC cl.exe not found. Install VS Build Tools and rerun from Developer PowerShell.')
    else:
        rc, out = _run(['gcc', '--version'])
        if rc == 0:
            ver = out.splitlines()[0] if out else 'unknown'
            print(f'  {green("[+]")} gcc found: {ver.strip()}')
        else:
            print(f'  {yellow("[!]")} gcc NOT found.')
            print( '       gsplat CUDA JIT compilation will fail at runtime.')
            print( '       Fix (choose one):')
            print( '         Ubuntu/Debian:  sudo apt install build-essential python3-dev')
            print( '         RHEL/CentOS:    sudo yum groupinstall "Development Tools" && sudo yum install python3-devel')
            print( '         HPC module:     module load gcc')
            WARNINGS.append('gcc not found. Install build-essential / "Development Tools" before running the splat pipeline.')
            return
        rc2, _ = _run(['python3-config', '--includes'])
        if rc2 != 0:
            print(f'  {yellow("[!]")} python3-dev headers not found.')
            print( '       C extension builds (gsplat) may fail.')
            print( '       Fix: sudo apt install python3-dev   # or yum install python3-devel')
            WARNINGS.append('python3-dev headers missing. Install python3-dev/python3-devel.')
        else:
            print(f'  {green("[+]")} python3-dev headers found')


def step_pip_upgrade():
    section('1 / 7  Upgrading pip')
    pip_install(['pip'], label='pip (upgrade)')


def step_core_gui():
    section('2 / 7  Core GUI and numeric packages')
    pkgs = [
        ('numpy>=1.24',         'numpy',    'numpy'),
        ('Pillow',              'PIL',      'Pillow'),
        ('scipy',               'scipy',    'scipy'),
        ('PySide6',             'PySide6',  'PySide6'),
    ]
    for dist, imp, label in pkgs:
        if _is_installed(imp):
            ver = _installed_version(dist.split('>=')[0].split('[')[0])
            print(f'  {green("[+]")} {label} already installed  [{ver}]')
        else:
            pip_install([dist], label=label)


def step_imageio():
    section('3 / 7  imageio (HDR export)')
    imp = 'imageio'
    if not _is_installed(imp):
        pip_install(['imageio[freeimage]'], label='imageio + FreeImage')
    else:
        # Verify FreeImage actually works by writing/reading a small HDR file
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
            ver = _installed_version('imageio')
            print(f'  {green("[+]")} imageio already installed [{ver}] with FreeImage')
        else:
            ver = _installed_version('imageio')
            print(f'  {yellow("[!]")} imageio [{ver}] present but FreeImage binary missing — reinstalling')
            pip_install(['imageio[freeimage]'], label='imageio[freeimage] (FreeImage binary)')


def step_torch():
    section('4 / 7  PyTorch (GPU-accelerated pipelines)')
    existing = _installed_version('torch')

    if existing:
        print(f'  {green("[+]")} PyTorch {existing} already installed — checking CUDA compatibility …')
        issues = _check_torch_cuda_mismatch()
        for issue in issues:
            print(f'\n  {yellow("[!]")} {issue}\n')
            WARNINGS.append(issue)
        if not issues:
            import torch
            cuda_avail = torch.cuda.is_available()
            print(f'  {green("[+]")} CUDA available: {cuda_avail}  '
                  f'({torch.cuda.device_count()} GPU(s))')
        return

    drv = _detect_cuda_driver_version()
    if drv is None:
        print(f'  {yellow("[!]")} No NVIDIA GPU detected — installing CPU-only PyTorch.')
        print( '       GPU-based pipelines (splat training) will be unavailable.')
        WARNINGS.append(
            'No NVIDIA GPU found. Installing CPU-only PyTorch.\n'
            '  Gaussian splat training requires a CUDA GPU.'
        )
        pip_install(['torch'], index_url='https://download.pytorch.org/whl/cpu',
                    label='torch (CPU-only)')
        return

    label, index_url = _cuda_wheel_for_driver(drv)
    print(f'  Detected driver v{drv} → installing PyTorch for {label} …')
    if label == 'cpu':
        WARNINGS.append(
            f'NVIDIA driver v{drv} is too old for CUDA 12.x.\n'
            '  Installed CPU-only PyTorch. Update driver to ≥ 528 for GPU support.'
        )
    ok = pip_install(['torch'], index_url=index_url, label=f'torch ({label})')
    if ok:
        issues = _check_torch_cuda_mismatch()
        for issue in issues:
            print(f'\n  {yellow("[!]")} {issue}\n')
            WARNINGS.append(issue)


def step_open3d():
    section('5 / 7  open3d (mesh reconstruction + E57 fallback)')
    if _is_installed('open3d'):
        ver = _installed_version('open3d')
        print(f'  {green("[+]")} open3d already installed  [{ver}]')
    else:
        pip_install(['open3d'], label='open3d')


def step_pipeline_extras():
    section('6 / 7  Optional pipeline packages')
    optional = [
        ('rawpy',        'rawpy',        'rawpy  (DNG/RAW camera images)'),
        ('rosbags',      'rosbags',      'rosbags  (NavVis LiDAR bag reading)'),
        ('pye57',        'pye57',        'pye57  (E57 point cloud reading)'),
        ('pyproj',       'pyproj',       'pyproj  (precise UTM georeferencing)'),
    ]
    for dist, imp, label in optional:
        if _is_installed(imp):
            ver = _installed_version(dist)
            print(f'  {green("[+]")} {label}  already installed  [{ver}]')
        else:
            pip_install([dist], label=label)

    # ninja: small build tool required by PyTorch JIT / gsplat CUDA compilation
    if _is_installed('ninja'):
        ver = _installed_version('ninja')
        print(f'  {green("[+]")} ninja  already installed  [{ver}]')
    else:
        pip_install(['ninja'], label='ninja  (C++ build tool for gsplat CUDA JIT)')

    # gsplat: requires CUDA toolkit — attempt but don't fail hard
    if _is_installed('gsplat'):
        ver = _installed_version('gsplat')
        print(f'  {green("[+]")} gsplat already installed  [{ver}]')
    else:
        rc, _ = _run(['nvcc', '--version'])
        if rc == 0:
            if not DRY_RUN:
                print(f'  Installing {bold("gsplat")} (requires CUDA toolkit — may take several minutes) … ',
                      end='', flush=True)
                rc2, out2 = _run([sys.executable, '-m', 'pip', 'install', 'gsplat'])
                if rc2 == 0:
                    print(green('OK'))
                else:
                    print(red('FAILED'))
                    WARNINGS.append(
                        f'gsplat install failed. Gaussian splat training will be unavailable.\n'
                        '  Try manually: pip install gsplat\n'
                        f'  Detail: {out2[:300]}'
                    )
            else:
                print(f'  {cyan("[dry-run]")} pip install gsplat')
        else:
            WARNINGS.append(
                'gsplat not installed: nvcc (CUDA toolkit) not found.\n'
                '  Install the CUDA toolkit matching your driver, then: pip install gsplat'
            )
            print(f'  {yellow("[!]")} gsplat skipped — nvcc not found '
                  f'(CUDA toolkit required for compilation)')


def step_verify() -> bool:
    section('7 / 7  Verifying installs')
    if DRY_RUN:
        print(f'  {cyan("[dry-run]")} skipping verification (nothing was installed)')
        return True
    checks = [
        ('numpy',      'numpy',     True),
        ('PIL',        'Pillow',    True),
        ('scipy',      'scipy',     True),
        ('PySide6',    'PySide6',   True),
        ('imageio',    'imageio',   True),
        ('open3d',     'open3d',    True),
        ('torch',      'torch',     True),
        ('rawpy',      'rawpy',     False),
        ('rosbags',    'rosbags',   False),
        ('pye57',      'pye57',     False),
        ('pyproj',     'pyproj',    False),
        ('ninja',      'ninja',     False),
        ('gsplat',     'gsplat',    False),
    ]
    all_required_ok = True
    for imp, dist, required in checks:
        ok_flag = _is_installed(imp)
        ver = _installed_version(dist) or '—'
        tag = 'required' if required else 'optional'
        if ok_flag:
            print(f'  {green("[+]")} {imp:<20} [{ver}]')
        elif required:
            print(f'  {red("[X]")} {imp:<20} MISSING  ({tag})')
            all_required_ok = False
        else:
            print(f'  {yellow("[-]")} {imp:<20} not installed  ({tag})')
    return all_required_ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(
        description='rawkee workstation dependency installer'
    )
    parser.add_argument('--yes',            action='store_true',
                        help='Skip confirmation prompts')
    parser.add_argument('--dry-run',        action='store_true',
                        help='Show what would be installed without installing')
    parser.add_argument('--reinstall-torch', action='store_true',
                        help='Force reinstall PyTorch (useful after driver update)')
    args = parser.parse_args()
    DRY_RUN = args.dry_run

    print('=' * 60)
    print(bold('rawkee scan pipeline — workstation dependency installer'))
    print(f'Python: {sys.executable}  ({sys.version.split()[0]})')
    if DRY_RUN:
        print(yellow('DRY-RUN mode — nothing will be installed'))
    print('=' * 60)

    if sys.version_info < (3, 10):
        print(red(f'\n[X] Python {sys.version_info.major}.{sys.version_info.minor} is too old.'
                  ' rawkee requires Python >= 3.10.\n'))
        sys.exit(1)

    if not args.yes and not DRY_RUN:
        print('\nThis will install/upgrade packages into:')
        print(f'  {sys.executable}')
        env = os.environ.get('VIRTUAL_ENV') or os.environ.get('CONDA_DEFAULT_ENV') or '(system)'
        print(f'  Environment: {env}')
        answer = input('\nProceed? [Y/n] ').strip().lower()
        if answer and answer != 'y':
            print('Aborted.')
            sys.exit(0)

    if args.reinstall_torch and not DRY_RUN:
        print('\nRemoving existing torch installation …')
        _run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'torch'])

    step_cxx_compiler()
    step_pip_upgrade()
    step_core_gui()
    step_imageio()
    step_torch()
    step_open3d()
    step_pipeline_extras()
    all_ok = step_verify()

    # Summary
    print(f'\n{"=" * 60}')
    print(bold('Summary'))
    print('─' * 60)

    if FAILURES:
        print(f'\n{red("[X] Installation failures:")}')
        for f in FAILURES:
            print(f'    • {f}')

    if WARNINGS:
        print(f'\n{yellow("[!] Warnings:")}')
        for w in WARNINGS:
            for line in w.splitlines():
                print(f'    {line}')

    if not FAILURES and not WARNINGS and all_ok:
        print(green('\n[+] All packages installed successfully.'))
        print(    '    Launch the GUI with (from the rawkee root directory):')
        print(f'       python -m rawkee.tools.lidar.scan_gui')
    elif not FAILURES and all_ok:
        print(yellow('\n[!] Required packages OK; some optional packages have warnings.'))
        print(    '    The GUI will launch but some features may be limited.')
        print(f'    Launch with (from the rawkee root directory): python -m rawkee.tools.lidar.scan_gui')
    else:
        print(red('\n[X] Some required packages failed. Fix the errors above and re-run.'))
        print(    '    You can also run: python rawkee/tools/lidar/hpc_preflight_check.py')

    print('=' * 60)
    sys.exit(0 if (not FAILURES and all_ok) else 1)


if __name__ == '__main__':
    main()
