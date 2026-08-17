"""Convert Gaussian splat files between all formats supported by the splat pipeline.

Supported formats
-----------------
*.ply   — 3DGS standard PLY (binary little-endian, gsplat/3DGS convention)
*.splat — packed 32-byte binary (Luma AI / web viewer)
*.glb   — GLB with KHR_gaussian_splatting extension
*.x3d   — X3D XML encoding
*.x3dv  — X3D Classic VRML encoding
*.x3dj  — X3D JSON encoding

Coordinate systems
------------------
PLY, .splat, and GLB produced by this pipeline are stored in the native
training frame (ROS/NavVis Z-up right-handed).  X3D files store splats in
the X3D Y-up right-handed frame after applying:

    (x, y, z)_native → (x, z, -y)_x3d

The internal representation used here is always the native training frame.
X3D sources are rotated back to native on load; X3D targets are rotated on
export by the existing _export_splat_x3d helper.

Internal dict layout
--------------------
{
  'means':         (N, 3) float64  positions in native space
  'scales':        (N, 3) float64  linear (exp) scales
  'log_scales':    (N, 3) float64  log scales   (needed for PLY round-trip)
  'quats_wxyz':    (N, 4) float64  quaternion (w, x, y, z)
  'sh_coeffs':     (N, C, 3) float64  SH coefficients; C = (sh_degree+1)^2
  'opacities':     (N,)  float64  post-sigmoid [0, 1]
  'raw_opacities': (N,)  float64  pre-sigmoid logit (needed for PLY round-trip)
  'sh_degree':     int
}
"""
from __future__ import annotations

import json as _json
import logging
import math
import struct as _s
from pathlib import Path
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Coordinate-system helpers
#
# Internal representation: Y-up right-handed (same as X3D and SuperSplat).
#
# COLMAP/3DGS PLY → Y-up: +180° around Z  — (x,y,z) → (-x,-y,z)
#   This is what SuperSplat/PlayCanvas applies at PLY load time.
#   The transform is self-inverse (applying it twice = identity).
#
# ROS Z-up → Y-up: -90° around X  — (x,y,z) → (x,z,-y)
#   Same as _ROS_TO_X3D in export.py.
# ---------------------------------------------------------------------------

# +180°Z: COLMAP/3DGS PLY → Y-up  (and inverse: Y-up → COLMAP, self-inverse)
_PLY_TO_YUP   = np.array([[-1., 0., 0.], [0., -1., 0.], [0.,  0., 1.]], dtype=np.float64)
_Q_PLY_TO_YUP = np.array([0., 0., 0., 1.], dtype=np.float64)  # 180°Z quaternion (w,x,y,z)

# -90°X: ROS Z-up → Y-up  (same as _ROS_TO_X3D in export.py)
_ROS_TO_YUP   = np.array([[1.,  0.,  0.], [0., 0., 1.], [0., -1., 0.]], dtype=np.float64)
_Q_ROS_TO_YUP = np.array([math.sqrt(2) / 2, -math.sqrt(2) / 2, 0., 0.], dtype=np.float64)

# Header comment written by our pipeline’s _export_splat_ply to identify ROS-frame PLYs
_ROS_PLY_TAG = 'rawkee coordinate_system ros-zup'

# Ordered list mapping X3D GaussianSplats SH field names → sh_coeffs column index
_SH_FIELD_ORDER = [
    'sphericalHarmonicsDegree0Coef0',   #  0 — DC
    'sphericalHarmonicsDegree1Coef0',   #  1
    'sphericalHarmonicsDegree1Coef1',   #  2
    'sphericalHarmonicsDegree1Coef2',   #  3
    'sphericalHarmonicsDegree2Coef0',   #  4
    'sphericalHarmonicsDegree2Coef1',   #  5
    'sphericalHarmonicsDegree2Coef2',   #  6
    'sphericalHarmonicsDegree2Coef3',   #  7
    'sphericalHarmonicsDegree2Coef4',   #  8
    'sphericalHarmonicsDegree3Coef0',   #  9
    'sphericalHarmonicsDegree3Coef1',   # 10
    'sphericalHarmonicsDegree3Coef2',   # 11
    'sphericalHarmonicsDegree3Coef3',   # 12
    'sphericalHarmonicsDegree3Coef4',   # 13
    'sphericalHarmonicsDegree3Coef5',   # 14
    'sphericalHarmonicsDegree3Coef6',   # 15
]

_SH0 = 0.28209479177387814   # 1 / (2*sqrt(pi))


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-7, 1.0 - 1e-7)
    return np.log(p / (1.0 - p))


def _quat_apply_basis(q_basis: np.ndarray, quats: np.ndarray) -> np.ndarray:
    """Left-multiply an (N,4) array of (w,x,y,z) quaternions by a single quaternion."""
    w1, x1, y1, z1 = q_basis
    w2 = quats[:, 0]; x2 = quats[:, 1]; y2 = quats[:, 2]; z2 = quats[:, 3]
    return np.stack([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
    ], axis=-1)


def _degree_from_n_sh(n_sh: int) -> int:
    if   n_sh >= 16: return 3
    elif n_sh >= 9:  return 2
    elif n_sh >= 4:  return 1
    return 0


def _pick(pi: dict, *candidates: str) -> str:
    """Return the first candidate key present in pi, or raise a clear error."""
    for name in candidates:
        if name in pi:
            return name
    raise KeyError(
        f'PLY file is missing expected property. Tried: {list(candidates)}. '
        f'Properties found: {list(pi.keys())}'
    )


# ---------------------------------------------------------------------------
# PLY loader — 3DGS standard binary little-endian format
# ---------------------------------------------------------------------------

def _to_yup(means, quats_wxyz, sh_coeffs, sh_degree, R, q_basis):
    """Rotate splat data from a source frame into Y-up using matrix R and quaternion q_basis."""
    means_out = means @ R.T
    quats_out = _quat_apply_basis(q_basis, quats_wxyz)
    quats_out /= np.linalg.norm(quats_out, axis=1, keepdims=True).clip(min=1e-8)
    if sh_degree > 0:
        from rawkee.tools.lidar.export import _rotate_sh_coeffs
        sh_out = _rotate_sh_coeffs(sh_coeffs, R, sh_degree)
    else:
        sh_out = sh_coeffs
    return means_out, quats_out, sh_out


def _load_ply(path: Path) -> dict:
    with open(path, 'rb') as f:
        props: list[str] = []
        comments: list[str] = []
        n_verts = 0
        in_vertex = False
        while True:
            line = f.readline().decode('ascii', errors='replace').strip()
            if line == 'end_header':
                break
            if line.startswith('comment '):
                comments.append(line[8:])
            elif line.startswith('element vertex'):
                n_verts = int(line.split()[-1])
                in_vertex = True
            elif line.startswith('element '):
                in_vertex = False
            elif in_vertex and line.startswith('property float '):
                props.append(line.split()[-1])

        n_props = len(props)
        raw = np.frombuffer(f.read(n_verts * n_props * 4), dtype='<f4')
        data = raw.reshape(n_verts, n_props).astype(np.float64)

    pi = {p: i for i, p in enumerate(props)}

    # Require at minimum the DC SH colour properties; plain point-cloud PLYs only have x/y/z/nx/ny/nz
    if 'f_dc_0' not in pi:
        raise ValueError(
            f'{path.name} does not appear to be a 3DGS splat PLY — '
            f'missing f_dc_* SH properties. Properties found: {list(pi.keys())}'
        )

    means = np.stack([data[:, pi['x']], data[:, pi['y']], data[:, pi['z']]], axis=1)

    # Scale: log-space in 3DGS convention; some exporters use dashes or sx/sy/sz
    s0 = _pick(pi, 'scale_0', 'scale-0', 'log_scale_0', 'sx')
    s1 = _pick(pi, 'scale_1', 'scale-1', 'log_scale_1', 'sy')
    s2 = _pick(pi, 'scale_2', 'scale-2', 'log_scale_2', 'sz')
    log_scales = np.stack([data[:, pi[s0]], data[:, pi[s1]], data[:, pi[s2]]], axis=1)
    # If the property name suggests linear scales, take the log; otherwise treat as log already
    if s0 in ('sx', 'sy', 'sz'):
        scales     = log_scales.copy()
        log_scales = np.log(np.clip(scales, 1e-8, None))
    else:
        scales = np.exp(log_scales)

    # Quaternion: 3DGS uses rot_0..3 (w,x,y,z); others use q_0..3 or qw/qx/qy/qz
    r0 = _pick(pi, 'rot_0', 'rot-0', 'q_0', 'qw', 'rotation_0')
    r1 = _pick(pi, 'rot_1', 'rot-1', 'q_1', 'qx', 'rotation_1')
    r2 = _pick(pi, 'rot_2', 'rot-2', 'q_2', 'qy', 'rotation_2')
    r3 = _pick(pi, 'rot_3', 'rot-3', 'q_3', 'qz', 'rotation_3')
    quats_wxyz = np.stack(
        [data[:, pi[r0]], data[:, pi[r1]], data[:, pi[r2]], data[:, pi[r3]]], axis=1
    )
    # If the file used qx/qy/qz/qw order, the first col is x — reorder to w,x,y,z
    if r0 in ('qx',):
        quats_wxyz = np.roll(quats_wxyz, 1, axis=1)
    quats_wxyz /= np.linalg.norm(quats_wxyz, axis=1, keepdims=True).clip(min=1e-8)

    op_name       = _pick(pi, 'opacity', 'alpha')
    raw_opacities = data[:, pi[op_name]]
    # If property is 'alpha' it is likely already in [0,1]; 'opacity' is pre-sigmoid logit
    if op_name == 'alpha':
        opacities     = np.clip(raw_opacities, 0.0, 1.0)
        raw_opacities = _logit(opacities)
    else:
        opacities = 1.0 / (1.0 + np.exp(-raw_opacities))

    dc = np.stack([data[:, pi['f_dc_0']], data[:, pi['f_dc_1']], data[:, pi['f_dc_2']]], axis=1)

    n_rest = sum(1 for p in props if p.startswith('f_rest_'))
    n_sh_extra = n_rest // 3   # number of SH bases beyond DC
    n_sh = n_sh_extra + 1
    sh_degree = _degree_from_n_sh(n_sh)
    # Clamp n_sh to the canonical count for the detected degree
    n_sh = (sh_degree + 1) ** 2

    sh_coeffs = np.zeros((n_verts, n_sh, 3), dtype=np.float64)
    sh_coeffs[:, 0, :] = dc
    if n_sh_extra > 0:
        rest_cols = n_sh_extra * 3
        rest = np.stack([data[:, pi[f'f_rest_{i}']] for i in range(rest_cols)], axis=1)
        # Layout: interleaved (coef_idx, channel) → reshape to (N, n_sh_extra, 3)
        sh_coeffs[:, 1:n_sh, :] = rest[:, :((n_sh - 1) * 3)].reshape(n_verts, n_sh - 1, 3)

    log.info('PLY loaded: %d splats, sh_degree=%d  (scale=%s rot=%s opacity=%s)',
             n_verts, sh_degree, s0, r0, op_name)

    # Auto-detect coordinate system from header comment; apply appropriate rotation to Y-up
    if any(_ROS_PLY_TAG in c for c in comments):
        log.info('PLY coord system: ros-zup (tagged by rawkee pipeline)')
        means, quats_wxyz, sh_coeffs = _to_yup(means, quats_wxyz, sh_coeffs, sh_degree,
                                                _ROS_TO_YUP, _Q_ROS_TO_YUP)
    else:
        log.info('PLY coord system: colmap/3dgs — applying +180°Z to reach Y-up')
        means, quats_wxyz, sh_coeffs = _to_yup(means, quats_wxyz, sh_coeffs, sh_degree,
                                                _PLY_TO_YUP, _Q_PLY_TO_YUP)

    return {
        'means':         means,
        'scales':        scales,
        'log_scales':    log_scales,
        'quats_wxyz':    quats_wxyz,
        'sh_coeffs':     sh_coeffs,
        'opacities':     opacities,
        'raw_opacities': raw_opacities,
        'sh_degree':     sh_degree,
    }


# ---------------------------------------------------------------------------
# binary .splat loader — packed 32-byte-per-splat web viewer format
# ---------------------------------------------------------------------------

def _load_splat_binary(path: Path) -> dict:
    raw  = path.read_bytes()
    N    = len(raw) // 32
    rec_dtype = np.dtype([
        ('pos',   '<f4', (3,)),
        ('scale', '<f4', (3,)),
        ('rgba',  'u1',  (4,)),
        ('rot',   'u1',  (4,)),
    ])
    rec = np.frombuffer(raw[:N * 32], dtype=rec_dtype)

    means      = rec['pos'].astype(np.float64)
    scales     = rec['scale'].astype(np.float64)
    log_scales = np.log(np.clip(scales, 1e-8, None))

    rgba       = rec['rgba'].astype(np.float64)
    rgb_lin    = rgba[:, :3] / 255.0
    opacities  = rgba[:, 3] / 255.0
    raw_opacities = _logit(opacities)

    # Quaternion bytes: [qx, qy, qz, qw] mapped from [-1,1] → [0,255]
    rot_f      = rec['rot'].astype(np.float64) / 255.0 * 2.0 - 1.0
    quats_wxyz = np.stack([rot_f[:, 3], rot_f[:, 0], rot_f[:, 1], rot_f[:, 2]], axis=1)
    quats_wxyz /= np.linalg.norm(quats_wxyz, axis=1, keepdims=True).clip(min=1e-8)

    # Back-calculate DC SH from decoded linear RGB:  rgb = dc*C0 + 0.5
    dc = (rgb_lin - 0.5) / _SH0
    sh_coeffs = dc[:, np.newaxis, :]  # (N, 1, 3)

    log.info('.splat loaded: %d splats (DC SH only — higher-order SH unavailable)', N)
    # .splat files are assumed COLMAP/3DGS convention; apply +180°Z to reach Y-up
    means, quats_wxyz, sh_coeffs = _to_yup(means, quats_wxyz, sh_coeffs, 0,
                                            _PLY_TO_YUP, _Q_PLY_TO_YUP)
    return {
        'means':         means,
        'scales':        scales,
        'log_scales':    log_scales,
        'quats_wxyz':    quats_wxyz,
        'sh_coeffs':     sh_coeffs,
        'opacities':     opacities,
        'raw_opacities': raw_opacities,
        'sh_degree':     0,
    }


# ---------------------------------------------------------------------------
# GLB loader — KHR_gaussian_splatting extension
# ---------------------------------------------------------------------------

def _load_glb(path: Path) -> dict:
    raw = path.read_bytes()
    magic, _ver, total_len = _s.unpack_from('<III', raw, 0)
    if magic != 0x46546C67:
        raise ValueError(f'Not a valid GLB file: {path}')

    offset    = 12
    json_bytes = b''
    bin_block  = b''
    while offset < total_len:
        chunk_len, chunk_type = _s.unpack_from('<II', raw, offset)
        offset += 8
        chunk = raw[offset: offset + chunk_len]
        offset += chunk_len
        if chunk_type == 0x4E4F534A:    # JSON
            json_bytes = chunk
        elif chunk_type == 0x004E4942:  # BIN
            bin_block = chunk

    gltf = _json.loads(json_bytes.decode('utf-8'))

    # Locate the KHR_gaussian_splatting primitive
    attrs: dict | None = None
    for mesh in gltf.get('meshes', []):
        for prim in mesh.get('primitives', []):
            if 'KHR_gaussian_splatting' in prim.get('extensions', {}):
                attrs = prim['attributes']
                break
        if attrs is not None:
            break
    if attrs is None:
        raise ValueError(f'No KHR_gaussian_splatting primitive in: {path}')

    accessors  = gltf['accessors']
    bv_list    = gltf['bufferViews']
    _COMP_SIZES = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

    def _read(attr_name: str) -> Optional[np.ndarray]:
        if attr_name not in attrs:
            return None
        acc    = accessors[attrs[attr_name]]
        bv     = bv_list[acc['bufferView']]
        off    = bv.get('byteOffset', 0)
        length = bv['byteLength']
        arr    = np.frombuffer(bin_block[off: off + length], dtype='<f4').astype(np.float64)
        n_comp = _COMP_SIZES[acc['type']]
        return arr.reshape(acc['count'], n_comp) if n_comp > 1 else arr.reshape(acc['count'])

    means    = _read('POSITION')    # (N, 3)
    rot_xyzw = _read('_ROTATION')  # (N, 4) x,y,z,w
    scales   = _read('_SCALE')     # (N, 3)
    opac     = _read('_OPACITY')   # (N,)
    color    = _read('_COLOR')     # (N, 3) linear RGB [0,1]

    if opac is not None and opac.ndim == 2:
        opac = opac[:, 0]

    # glTF quaternion (x,y,z,w) → internal (w,x,y,z)
    quats_wxyz = np.roll(rot_xyzw, 1, axis=1)
    quats_wxyz /= np.linalg.norm(quats_wxyz, axis=1, keepdims=True).clip(min=1e-8)

    log_scales    = np.log(np.clip(scales, 1e-8, None))
    N             = len(means)
    opacities     = np.clip(opac, 0.0, 1.0) if opac is not None else np.ones(N)
    raw_opacities = _logit(opacities)

    dc = (np.clip(color, 0.0, 1.0) - 0.5) / _SH0 if color is not None else np.zeros((N, 3))
    sh_coeffs = dc[:, np.newaxis, :]  # (N, 1, 3)

    log.info('GLB loaded: %d splats (DC SH only — KHR_gaussian_splatting stores RGB)', N)
    # GLB/glTF is Y-up — no coordinate transform needed
    return {
        'means':         means,
        'scales':        scales,
        'log_scales':    log_scales,
        'quats_wxyz':    quats_wxyz,
        'sh_coeffs':     sh_coeffs,
        'opacities':     opacities,
        'raw_opacities': raw_opacities,
        'sh_degree':     0,
    }


# ---------------------------------------------------------------------------
# X3D loader — walks rkx3d node tree, converts X3D Y-up → native
# ---------------------------------------------------------------------------

def _find_gs_node(node):
    """Recursively find the first GaussianSplats node in an rkx3d tree."""
    if type(node).__name__ == 'GaussianSplats':
        return node
    for val in vars(node).values():
        if isinstance(val, list):
            for item in val:
                if hasattr(item, 'NAME'):
                    found = _find_gs_node(item)
                    if found:
                        return found
        elif hasattr(val, 'NAME'):
            found = _find_gs_node(val)
            if found:
                return found
    return None


def _load_x3d(path: Path) -> dict:
    from rawkee.io.RKLoadSceneFromFile import RKLoadSceneFromFile

    loader  = RKLoadSceneFromFile()
    x3d_doc = loader.disk2x3d(str(path))
    if x3d_doc is None or x3d_doc.Scene is None:
        raise ValueError(f'Failed to load X3D file: {path}')

    gs = None
    for child in x3d_doc.Scene.children:
        gs = _find_gs_node(child)
        if gs:
            break
    if gs is None:
        raise ValueError(f'No GaussianSplats node found in: {path}')

    N = len(gs.positions)
    if N == 0:
        raise ValueError(f'GaussianSplats node has no positions in: {path}')

    def _to_array(field, stride):
        """Parse a GaussianSplats MF field regardless of whether it came back as
        tuples (correctly parsed) or space-separated strings (MFQuaternion bug)."""
        first = field[0]
        if isinstance(first, (tuple, list)):
            return np.array(field, dtype=np.float64).reshape(-1, stride)
        flat = []
        for item in field:
            if isinstance(item, str):
                flat.extend(float(x) for x in item.split())
            else:
                flat.append(float(item))
        return np.array(flat, dtype=np.float64).reshape(-1, stride)

    # X3D is Y-up — store positions and scales as-is (no coordinate transform)
    means  = _to_array(gs.positions, 3)
    scales = _to_array(gs.scales, 3)

    # X3D stores orientations as (x,y,z,w); reorder to internal (w,x,y,z)
    ori_xyzw   = _to_array(gs.orientations, 4)
    quats_wxyz = np.roll(ori_xyzw, 1, axis=1)   # (x,y,z,w) → (w,x,y,z)
    quats_wxyz /= np.linalg.norm(quats_wxyz, axis=1, keepdims=True).clip(min=1e-8)

    log_scales    = np.log(np.clip(scales, 1e-8, None))
    opacities     = np.array(gs.opacities, dtype=np.float64).reshape(N)
    raw_opacities = _logit(opacities)

    max_idx = -1
    for idx, fname in enumerate(_SH_FIELD_ORDER):
        vals = getattr(gs, fname, [])
        if vals and len(vals) == N:
            max_idx = idx

    sh_degree = _degree_from_n_sh(max_idx + 1) if max_idx >= 0 else 0
    n_sh      = (sh_degree + 1) ** 2

    sh_coeffs = np.zeros((N, n_sh, 3), dtype=np.float64)
    for idx, fname in enumerate(_SH_FIELD_ORDER):
        if idx >= n_sh:
            break
        vals = getattr(gs, fname, [])
        if vals and len(vals) == N:
            sh_coeffs[:, idx, :] = _to_array(vals, 3)

    log.info('X3D loaded: %d splats, sh_degree=%d from %s', N, sh_degree, path.name)
    return {
        'means':         means,
        'scales':        scales,
        'log_scales':    log_scales,
        'quats_wxyz':    quats_wxyz,
        'sh_coeffs':     sh_coeffs,
        'opacities':     opacities,
        'raw_opacities': raw_opacities,
        'sh_degree':     sh_degree,
    }


# ---------------------------------------------------------------------------
# Public load entry point
# ---------------------------------------------------------------------------

def load_splat(path) -> dict:
    """Load a Gaussian splat file in any supported format.

    Returns an internal-format dict with all arrays normalised to Y-up space.
    Supported extensions: .ply .splat .glb .x3d .x3dv .x3dj
    """
    path = Path(path)
    ext  = path.suffix.lower()
    if   ext == '.ply':                   return _load_ply(path)
    elif ext == '.splat':                 return _load_splat_binary(path)
    elif ext == '.glb':                   return _load_glb(path)
    elif ext in ('.x3d', '.x3dv', '.x3dj'): return _load_x3d(path)
    else:
        raise ValueError(f'Unsupported splat input format: {ext!r}')


# ---------------------------------------------------------------------------
# Export from internal dict using the existing private export helpers
# ---------------------------------------------------------------------------

def _export_from_dict(
    g: dict,
    output_dir: Path,
    stem: str,
    fmt: str,
    sh_degree: Optional[int]  = None,
    geo_origin: Optional[tuple] = None,
    decode_sh: bool           = False,
    viewpoints: Optional[list] = None,
    max_splats: Optional[int] = None,
) -> Path:
    import numpy as np
    from rawkee.tools.lidar.export import (
        _export_splat_x3d,
        _export_splat_ply,
        _export_splat_binary,
        _export_splat_glb,
    )

    fmt = fmt.lower().lstrip('.')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Subsample when N exceeds the cap (default 500K for X3D text formats)
    _cap = max_splats if max_splats is not None else (500_000 if fmt in ('x3d', 'x3dv', 'x3dj') else None)
    N = g['means'].shape[0]
    if _cap is not None and N > _cap:
        log.info('Subsampling %d → %d Gaussians (max_splats=%d)', N, _cap, _cap)
        idx = np.random.choice(N, _cap, replace=False)
        idx.sort()
        g = {k: (v[idx] if isinstance(v, np.ndarray) else v) for k, v in g.items()}

    deg = g['sh_degree'] if sh_degree is None else sh_degree

    if fmt in ('x3d', 'x3dv', 'x3dj'):
        # Internal dict is already Y-up; skip the ROS→X3D transform
        return _export_splat_x3d(
            g['means'], g['scales'], g['quats_wxyz'], g['sh_coeffs'], g['opacities'],
            output_dir, stem, fmt, deg,
            geo_origin=geo_origin, viewpoints=viewpoints, decode_sh=decode_sh,
            apply_coord_transform=False,
        )
    elif fmt in ('ply', 'splat'):
        # Rotate Y-up → COLMAP convention (+180°Z, self-inverse) before writing
        means, quats, sh = _to_yup(
            g['means'], g['quats_wxyz'], g['sh_coeffs'], deg,
            _PLY_TO_YUP, _Q_PLY_TO_YUP,
        )
        if fmt == 'ply':
            return _export_splat_ply(
                means, g['scales'], quats, sh,
                g['raw_opacities'], g['log_scales'],
                output_dir, stem, decode_sh=decode_sh, ros_tag=False,
            )
        else:
            return _export_splat_binary(
                means, g['scales'], quats, sh, g['opacities'],
                output_dir, stem,
            )
    elif fmt == 'glb':
        # GLB/glTF is Y-up — no coordinate transform
        return _export_splat_glb(
            g['means'], g['scales'], g['quats_wxyz'], g['sh_coeffs'], g['opacities'],
            output_dir, stem, deg,
        )
    else:
        raise ValueError(f'Unsupported splat output format: {fmt!r}')


# ---------------------------------------------------------------------------
# Public convert entry point
# ---------------------------------------------------------------------------

def convert_splat(
    input_path,
    output_dir,
    stem: str,
    fmt: str,
    sh_degree: Optional[int]   = None,
    geo_origin: Optional[tuple] = None,
    decode_sh: bool            = False,
    viewpoints: Optional[list]  = None,
    max_splats: Optional[int]   = None,
) -> Path:
    """Convert a Gaussian splat file to a different format.

    Conversion matrix (all pairs supported):

        Source ↓  / Target →  | ply | splat | glb | x3d | x3dv | x3dj
        ---------------------- |-----|-------|-----|-----|------|------
        ply                    |  ✓  |   ✓   |  ✓  |  ✓  |  ✓   |  ✓
        splat (DC SH only)     |  ✓  |   ✓   |  ✓  |  ✓  |  ✓   |  ✓
        glb   (DC SH only)     |  ✓  |   ✓   |  ✓  |  ✓  |  ✓   |  ✓
        x3d / x3dv / x3dj      |  ✓  |   ✓   |  ✓  |  ✓  |  ✓   |  ✓

    Note: .splat and .glb sources only carry DC SH (sh_degree=0); higher-order
    SH information is not recoverable from those formats.

    Parameters
    ----------
    input_path : str or Path
        Source file (.ply, .splat, .glb, .x3d, .x3dv, .x3dj).
    output_dir : str or Path
        Directory to write the converted file into.
    stem : str
        Output filename stem (without extension).
    fmt : str
        Target format: 'ply', 'splat', 'glb', 'x3d', 'x3dv', or 'x3dj'.
    sh_degree : int, optional
        SH degree to use in output. Defaults to the source file's degree.
    geo_origin : tuple, optional
        (easting, northing, height, epsg) for X3D GeoTransform wrapping.
    decode_sh : bool
        Pre-decode SH DC to RGB in PLY / X3D output so viewers without SH
        decoding still display correct colours.
    viewpoints : list, optional
        List of (pos_native, R_native, description) tuples to include as
        Viewpoints in X3D output.

    Returns
    -------
    Path
        Absolute path of the written output file.
    """
    gaussians = load_splat(input_path)
    out = _export_from_dict(
        gaussians, Path(output_dir), stem, fmt,
        sh_degree=sh_degree, geo_origin=geo_origin,
        decode_sh=decode_sh, viewpoints=viewpoints,
        max_splats=max_splats,
    )
    log.info('convert_splat: %s → %s', Path(input_path).name, out.name)
    return out
