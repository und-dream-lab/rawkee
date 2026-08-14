"""Export functions for scan mesh and Gaussian splat pipelines.

Mesh formats  : x3d (default) | x3dv | x3dj | obj | glb
Splat formats : x3d (default) | x3dv | x3dj | ply | splat | glb
"""
from __future__ import annotations
import json
import struct as _s
import logging
import math
from pathlib import Path
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_mesh(
    mesh,
    atlas: np.ndarray,
    spec_cubemap_paths: dict[str, Path],
    diff_cubemap_paths: dict[str, Path],
    output_dir: Path,
    stem: str,
    fmt: str = 'x3d',
    equirect_spec_path: Optional[Path] = None,
    equirect_diff_path: Optional[Path] = None,
    geo_origin: Optional[tuple] = None,
) -> Path:
    """Export a textured polygon mesh in the requested format.

    Parameters
    ----------
    geo_origin: (easting, northing, height, epsg) from ScanDataset.geo_origin(), or None.
    """
    fmt = fmt.lower().lstrip('.')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if fmt in ('x3d', 'x3dv', 'x3dj'):
        return _export_mesh_x3d(
            mesh, atlas, spec_cubemap_paths, diff_cubemap_paths,
            equirect_spec_path, equirect_diff_path,
            output_dir, stem, fmt, geo_origin,
        )
    elif fmt == 'obj':
        return _export_mesh_obj(mesh, atlas, output_dir, stem)
    elif fmt == 'glb':
        return _export_mesh_glb(mesh, atlas, output_dir, stem)
    else:
        raise ValueError(f'Unknown mesh export format: {fmt!r}')


def export_splat(
    gaussians: dict[str, 'torch.Tensor'],
    output_dir: Path,
    stem: str,
    fmt: str = 'x3d',
    sh_degree: int = 3,
    geo_origin: Optional[tuple] = None,
    decode_sh: bool = False,
) -> Path:
    """Export trained Gaussian splat parameters in the requested format.

    Parameters
    ----------
    geo_origin: (easting, northing, height, epsg) from ScanDataset.geo_origin(), or None.
    decode_sh:  When True, PLY output stores pre-decoded linear RGB in f_dc_* fields
                instead of raw SH coefficients. Use when the consumer does not
                implement SH decoding.
    """
    fmt = fmt.lower().lstrip('.')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert tensors to numpy once
    params = {k: v.cpu().numpy() for k, v in gaussians.items()}
    means      = params['means']                        # (N, 3)
    scales     = np.exp(params['log_scales'])           # (N, 3)
    quats_wxyz = params['quats']                        # (N, 4) w,x,y,z
    sh_coeffs  = params['sh_coeffs']                   # (N, n_sh, 3)
    opacities  = 1.0 / (1.0 + np.exp(-params['opacities']))  # (N,) sigmoid

    if fmt in ('x3d', 'x3dv', 'x3dj'):
        return _export_splat_x3d(
            means, scales, quats_wxyz, sh_coeffs, opacities,
            output_dir, stem, fmt, sh_degree, geo_origin,
        )
    elif fmt == 'ply':
        return _export_splat_ply(
            means, scales, quats_wxyz, sh_coeffs, params['opacities'],
            params['log_scales'], output_dir, stem, decode_sh=decode_sh,
        )
    elif fmt == 'splat':
        return _export_splat_binary(
            means, scales, quats_wxyz, sh_coeffs, opacities,
            output_dir, stem,
        )
    elif fmt == 'glb':
        return _export_splat_glb(
            means, scales, quats_wxyz, sh_coeffs, opacities,
            output_dir, stem, sh_degree,
        )
    else:
        raise ValueError(f'Unknown splat export format: {fmt!r}')


# ---------------------------------------------------------------------------
# Geospatial helpers
# ---------------------------------------------------------------------------

def _epsg_to_geo_system(epsg: int) -> list[str]:
    """Return X3D geoSystem MFString for a UTM EPSG code."""
    if 32601 <= epsg <= 32660:
        return ['UTM', f'Z{epsg - 32600}', 'N']
    if 32701 <= epsg <= 32760:
        return ['UTM', f'Z{epsg - 32700}', 'S']
    return ['GD', 'WE']   # fall back to geodetic for non-UTM EPSG


# ---------------------------------------------------------------------------
# Mesh — X3D / X3DV / X3DJ
# ---------------------------------------------------------------------------

def _make_env_ktx2(equirect_path: Optional[Path], face_paths: dict[str, Path],
                   out_dir: Path, label: str) -> Optional[Path]:
    """Convert equirectangular HDR to KTX2 for ImageCubeMapTexture.

    Falls back to listing the first face HDR path when conversion is unavailable.
    """
    ktx2_path = out_dir / f'{label}.ktx2'
    if ktx2_path.exists():
        return ktx2_path
    if equirect_path and equirect_path.exists():
        try:
            from rawkee.tools.RKTools import RKTools
            RKTools.hdri2ktx2(str(equirect_path), str(ktx2_path))
            log.info('KTX2 cubemap → %s', ktx2_path)
            return ktx2_path
        except Exception as exc:
            log.warning('KTX2 conversion failed (%s) — falling back to HDR', exc)
    # Fall back: return the px (positive-x) face; ImageCubeMapTexture will
    # only get one face but is still valid X3D.
    return face_paths.get('px') or next(iter(face_paths.values()), None)


def _export_mesh_x3d(
    mesh, atlas: np.ndarray,
    spec_paths: dict[str, Path],
    diff_paths: dict[str, Path],
    equirect_spec: Optional[Path],
    equirect_diff: Optional[Path],
    output_dir: Path, stem: str, fmt: str,
    geo_origin: Optional[tuple] = None,
) -> Path:
    try:
        import open3d as o3d
    except ImportError:
        raise RuntimeError('open3d required: pip install open3d')
    try:
        import imageio.v3 as iio
    except ImportError:
        raise RuntimeError('imageio required: pip install imageio')

    from rawkee.io.RKx3d import (
        X3D, Scene, Shape, Appearance, PhysicalMaterial,
        ImageTexture, IndexedTriangleSet, Coordinate, TextureCoordinate,
        EnvironmentLight, ImageCubeMapTexture, GeoLocation,
    )
    from rawkee.io.RKSceneTraversal import RKSceneTraversal

    # --- Save atlas PNG ---
    atlas_uint8 = (np.clip(atlas, 0, 1) * 255).astype(np.uint8)
    atlas_path = output_dir / f'{stem}_atlas.png'
    iio.imwrite(str(atlas_path), atlas_uint8)
    log.info('Atlas → %s', atlas_path)

    # --- Prepare KTX2 / HDR env maps ---
    spec_env_path = _make_env_ktx2(equirect_spec, spec_paths, output_dir, f'{stem}_envmap_spec')
    diff_env_path = _make_env_ktx2(equirect_diff, diff_paths, output_dir, f'{stem}_envmap_diff')

    # --- Mesh geometry ---
    verts = np.asarray(mesh.vertices)           # (V, 3)
    tris  = np.asarray(mesh.triangles)          # (T, 3) int

    # UVs from triangle_uvs if present, else planar
    if mesh.has_triangle_uvs():
        uvs = np.asarray(mesh.triangle_uvs)     # (T*3, 2)
    else:
        uvs = np.zeros((len(tris) * 3, 2), dtype=np.float32)

    # Flatten index list: each row of tris → 3 consecutive indices
    idx_flat = tris.ravel().tolist()

    # --- Build X3D scene ---
    trv = RKSceneTraversal()
    x3d_doc   = trv.getX3DObject()
    x3d_scene = trv.getSceneObject()
    x3d_doc.Scene = x3d_scene

    # EnvironmentLight
    spec_url = [str(spec_env_path.name)] if spec_env_path else []
    diff_url = [str(diff_env_path.name)] if diff_env_path else []
    env_light = EnvironmentLight(
        intensity=1.0,
        specularTexture=ImageCubeMapTexture(url=spec_url, DEF='EnvSpec') if spec_url else None,
        diffuseTexture =ImageCubeMapTexture(url=diff_url, DEF='EnvDiff') if diff_url else None,
        global_=True,
        DEF='EnvLight',
    )
    x3d_scene.children.append(env_light)

    # PhysicalMaterial with baked texture
    mat = PhysicalMaterial(
        baseColor=(1.0, 1.0, 1.0),
        metallic=0.0,
        roughness=0.6,
        baseTexture=ImageTexture(url=[str(atlas_path.name)], DEF='AtlasTex'),
        DEF='ScanMat',
    )
    appearance = Appearance(material=mat, DEF='ScanApp')

    # Geometry
    coord     = Coordinate(point=verts.tolist(), DEF='MeshCoord')
    tex_coord = TextureCoordinate(point=uvs.tolist(), DEF='MeshUV')
    geom = IndexedTriangleSet(
        index=idx_flat,
        coord=coord,
        texCoord=tex_coord,
        solid=False,
        DEF='MeshGeom',
    )

    shape = Shape(appearance=appearance, geometry=geom, DEF='ScanShape')

    # Wrap in GeoLocation when georeferenced anchor data is available
    if geo_origin is not None:
        e, n, h, epsg = geo_origin
        geo_node = GeoLocation(
            geoCoords=(e, n, h),
            geoSystem=_epsg_to_geo_system(epsg),
            children=[shape],
            DEF='GeoScanLocation',
        )
        x3d_scene.children.append(geo_node)
    else:
        x3d_scene.children.append(shape)

    # Write
    out_path = output_dir / f'{stem}.{fmt}'
    trv.x3d2disk(x3d_doc, str(out_path), fmt)
    log.info('Mesh X3D → %s', out_path)
    return out_path


# ---------------------------------------------------------------------------
# Mesh — OBJ
# ---------------------------------------------------------------------------

def _export_mesh_obj(mesh, atlas: np.ndarray, output_dir: Path, stem: str) -> Path:
    try:
        import open3d as o3d
        import imageio.v3 as iio
    except ImportError:
        raise RuntimeError('open3d and imageio required')

    atlas_uint8 = (np.clip(atlas, 0, 1) * 255).astype(np.uint8)
    atlas_path = output_dir / f'{stem}_atlas.png'
    iio.imwrite(str(atlas_path), atlas_uint8)

    # Write MTL
    mtl_path = output_dir / f'{stem}.mtl'
    mtl_path.write_text(
        f'newmtl ScanMaterial\n'
        f'map_Kd {atlas_path.name}\n'
        f'Ns 10.0\nKa 0.1 0.1 0.1\nKd 0.9 0.9 0.9\nKs 0.0 0.0 0.0\nd 1.0\n'
    )

    out_path = output_dir / f'{stem}.obj'
    o3d.io.write_triangle_mesh(
        str(out_path), mesh,
        write_ascii=True, write_vertex_normals=True, write_vertex_colors=False,
    )
    # Inject mtllib reference
    obj_text = out_path.read_text()
    if 'mtllib' not in obj_text:
        out_path.write_text(f'mtllib {mtl_path.name}\n' + obj_text)
    log.info('Mesh OBJ → %s', out_path)
    return out_path


# ---------------------------------------------------------------------------
# Mesh — GLB
# ---------------------------------------------------------------------------

def _export_mesh_glb(mesh, atlas: np.ndarray, output_dir: Path, stem: str) -> Path:
    try:
        import open3d as o3d
        import imageio.v3 as iio
    except ImportError:
        raise RuntimeError('open3d and imageio required')

    atlas_uint8 = (np.clip(atlas, 0, 1) * 255).astype(np.uint8)
    atlas_path = output_dir / f'{stem}_atlas.png'
    iio.imwrite(str(atlas_path), atlas_uint8)

    out_path = output_dir / f'{stem}.glb'
    o3d.io.write_triangle_mesh(str(out_path), mesh)
    log.info('Mesh GLB → %s', out_path)
    return out_path


# ---------------------------------------------------------------------------
# Splat — X3D / X3DV / X3DJ
# ---------------------------------------------------------------------------

def _sh_flat(sh_coeffs: np.ndarray, degree: int, coef_idx: int) -> list:
    """Extract one SH coefficient vector (N, 3) and return as flat list of (x,y,z)."""
    n_sh = (degree + 1) ** 2
    if coef_idx >= sh_coeffs.shape[1]:
        return []
    v = sh_coeffs[:, coef_idx, :]      # (N, 3)
    return [tuple(row.tolist()) for row in v]


def _export_splat_x3d(
    means: np.ndarray, scales: np.ndarray,
    quats_wxyz: np.ndarray, sh_coeffs: np.ndarray, opacities: np.ndarray,
    output_dir: Path, stem: str, fmt: str, sh_degree: int,
    geo_origin: Optional[tuple] = None,
) -> Path:
    from rawkee.io.RKx3d import X3D, Scene, GaussianSplats, GeoTransform
    from rawkee.io.RKSceneTraversal import RKSceneTraversal

    N = len(means)
    log.info('Building X3D GaussianSplats node  N=%d  sh_degree=%d', N, sh_degree)

    # Quaternion order: training stores (w,x,y,z); X3D spec says (x,y,z,w)
    quats_xyzw = np.roll(quats_wxyz, -1, axis=1)   # (N,4) x,y,z,w

    def _mf3(arr):
        return [tuple(r.tolist()) for r in arr]

    def _sh(ci):
        return _sh_flat(sh_coeffs, sh_degree, ci)

    gs_kwargs: dict = dict(
        positions   = _mf3(means),
        orientations= [tuple(r.tolist()) for r in quats_xyzw],
        scales      = _mf3(scales),
        opacities   = opacities.tolist(),
        sphericalHarmonicsDegree0Coef0 = _sh(0),
        DEF='ScanSplats',
    )
    if sh_degree >= 1:
        gs_kwargs.update(
            sphericalHarmonicsDegree1Coef0=_sh(1),
            sphericalHarmonicsDegree1Coef1=_sh(2),
            sphericalHarmonicsDegree1Coef2=_sh(3),
        )
    if sh_degree >= 2:
        gs_kwargs.update(
            sphericalHarmonicsDegree2Coef0=_sh(4),
            sphericalHarmonicsDegree2Coef1=_sh(5),
            sphericalHarmonicsDegree2Coef2=_sh(6),
            sphericalHarmonicsDegree2Coef3=_sh(7),
            sphericalHarmonicsDegree2Coef4=_sh(8),
        )
    if sh_degree >= 3:
        gs_kwargs.update(
            sphericalHarmonicsDegree3Coef0=_sh(9),
            sphericalHarmonicsDegree3Coef1=_sh(10),
            sphericalHarmonicsDegree3Coef2=_sh(11),
            sphericalHarmonicsDegree3Coef3=_sh(12),
            sphericalHarmonicsDegree3Coef4=_sh(13),
            sphericalHarmonicsDegree3Coef5=_sh(14),
            sphericalHarmonicsDegree3Coef6=_sh(15),
        )

    gs_node = GaussianSplats(**gs_kwargs)

    trv = RKSceneTraversal()
    x3d_doc   = trv.getX3DObject()
    x3d_scene = trv.getSceneObject()
    x3d_doc.Scene = x3d_scene

    # Wrap in GeoTransform when georeferenced anchor data is available
    if geo_origin is not None:
        e, n, h, epsg = geo_origin
        geo_node = GeoTransform(
            geoCenter=(e, n, h),
            geoSystem=_epsg_to_geo_system(epsg),
            children=[gs_node],
            DEF='GeoSplatTransform',
        )
        x3d_scene.children.append(geo_node)
    else:
        x3d_scene.children.append(gs_node)

    out_path = output_dir / f'{stem}.{fmt}'
    trv.x3d2disk(x3d_doc, str(out_path), fmt)
    log.info('Splat X3D → %s', out_path)
    return out_path


# ---------------------------------------------------------------------------
# Splat — PLY (3DGS standard format)
# ---------------------------------------------------------------------------

def _export_splat_ply(
    means: np.ndarray, scales: np.ndarray,
    quats_wxyz: np.ndarray, sh_coeffs: np.ndarray,
    raw_opacities: np.ndarray, log_scales: np.ndarray,
    output_dir: Path, stem: str,
    decode_sh: bool = False,
) -> Path:
    """Write a 3DGS-compatible PLY file with pre-activation (raw) parameter values."""
    N = len(means)
    n_sh = sh_coeffs.shape[1]     # number of SH coefficients per channel
    n_rest = max(0, n_sh - 1)     # DC is f_dc_*, rest are f_rest_*

    # Build per-vertex property arrays (pre-activation, matching 3DGS convention)
    sh0 = 0.28209479177387814  # 1 / (2 * sqrt(pi))
    if decode_sh:
        # Pre-decode DC so consumers that don't implement SH get correct RGB
        dc     = (sh_coeffs[:, 0, :] * sh0 + 0.5).clip(0.0, 1.0)  # (N, 3)
        rest   = np.zeros((N, 0), dtype=np.float32)                 # omit higher-order
        n_rest = 0
    else:
        dc    = sh_coeffs[:, 0, :]                                   # (N, 3)
        rest  = sh_coeffs[:, 1:, :].reshape(N, -1)                  # (N, n_rest*3)

    out_path = output_dir / f'{stem}.ply'
    with open(out_path, 'wb') as f:
        # --- PLY header ---
        props = (
            ['x', 'y', 'z', 'nx', 'ny', 'nz']
            + [f'f_dc_{i}'   for i in range(3)]
            + [f'f_rest_{i}' for i in range(n_rest * 3)]
            + ['opacity']
            + [f'scale_{i}'  for i in range(3)]
            + ['rot_0', 'rot_1', 'rot_2', 'rot_3']   # w,x,y,z
        )
        header = (
            'ply\nformat binary_little_endian 1.0\n'
            f'element vertex {N}\n'
        )
        for p in props:
            header += f'property float {p}\n'
        header += 'end_header\n'
        f.write(header.encode())

        # --- Vertex data (all float32) ---
        normals = np.zeros((N, 3), dtype=np.float32)
        row = np.concatenate([
            means.astype(np.float32),
            normals,
            dc.astype(np.float32),
            rest.astype(np.float32),
            raw_opacities.astype(np.float32).reshape(N, 1),
            log_scales.astype(np.float32),
            quats_wxyz.astype(np.float32),              # w,x,y,z per 3DGS convention
        ], axis=1)
        f.write(row.tobytes())

    log.info('Splat PLY → %s  (%d Gaussians, %d SH coeffs)', out_path, N, n_sh)
    return out_path


# ---------------------------------------------------------------------------
# Splat — binary .splat (Luma AI / web viewer format)
# ---------------------------------------------------------------------------

def _export_splat_binary(
    means: np.ndarray, scales: np.ndarray,
    quats_wxyz: np.ndarray, sh_coeffs: np.ndarray, opacities: np.ndarray,
    output_dir: Path, stem: str,
) -> Path:
    """Write the packed 32-byte-per-splat binary .splat format.

    Layout per splat:
      bytes  0–11 : x, y, z  (float32 × 3)
      bytes 12–23 : sx, sy, sz (float32 × 3, linear scale)
      bytes 24–27 : r, g, b, alpha (uint8; colour from DC SH, opacity → sigmoid)
      bytes 28–31 : qx, qy, qz, qw (uint8; normalised quaternion → [0,255])
    """
    N = len(means)

    # Colour from DC SH coefficient (SH DC → linear RGB via the standard SH basis)
    sh0 = 0.28209479177387814   # 1 / (2 * sqrt(pi))
    dc  = sh_coeffs[:, 0, :]                            # (N, 3)
    rgb_lin = (dc * sh0 + 0.5).clip(0.0, 1.0)          # (N, 3)
    r = (rgb_lin[:, 0] * 255).astype(np.uint8)
    g = (rgb_lin[:, 1] * 255).astype(np.uint8)
    b = (rgb_lin[:, 2] * 255).astype(np.uint8)
    a = (opacities * 255).astype(np.uint8)

    # Quaternion (w,x,y,z) → uint8 in range [0,255]
    # Normalise then map [-1,1] → [0,255]
    q = quats_wxyz.astype(np.float32)
    norms = np.linalg.norm(q, axis=1, keepdims=True).clip(min=1e-8)
    q /= norms
    # Pack as x,y,z,w
    qx = ((q[:, 1] * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)
    qy = ((q[:, 2] * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)
    qz = ((q[:, 3] * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)
    qw = ((q[:, 0] * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)

    # Sort by distance from scene centroid (improves web renderer alpha blending)
    centroid = means.mean(axis=0)
    order = np.argsort(-np.linalg.norm(means - centroid, axis=1))

    # Vectorized write using a numpy structured record array
    rec_dtype = np.dtype([
        ('pos',   '<f4', (3,)),
        ('scale', '<f4', (3,)),
        ('rgba',  'u1',  (4,)),
        ('rot',   'u1',  (4,)),
    ])
    records = np.empty(N, dtype=rec_dtype)
    records['pos']   = means[order].astype('<f4')
    records['scale'] = scales[order].astype('<f4')
    records['rgba']  = np.stack([r[order], g[order], b[order], a[order]], axis=1)
    records['rot']   = np.stack([qx[order], qy[order], qz[order], qw[order]], axis=1)

    out_path = output_dir / f'{stem}.splat'
    out_path.write_bytes(records.tobytes())

    log.info('Splat binary → %s  (%d Gaussians)', out_path, N)
    return out_path


# ---------------------------------------------------------------------------
# Splat — GLB (KHR_gaussian_splatting extension)
# ---------------------------------------------------------------------------

def _export_splat_glb(
    means: np.ndarray, scales: np.ndarray,
    quats_wxyz: np.ndarray, sh_coeffs: np.ndarray, opacities: np.ndarray,
    output_dir: Path, stem: str, sh_degree: int,
) -> Path:
    """Write a GLB using the KHR_gaussian_splatting glTF extension.

    The extension stores splats as a point-cloud mesh primitive with custom
    accessor attributes following the KHR_gaussian_splatting draft spec.
    """
    N = len(means)

    # --- Build binary buffer ---
    # POSITION (vec3 float32)
    pos_bytes  = means.astype('<f4').tobytes()
    # ROTATION (vec4 float32, x,y,z,w)
    rot_xyzw   = np.roll(quats_wxyz, -1, axis=1).astype('<f4')
    rot_bytes  = rot_xyzw.tobytes()
    # SCALE (vec3 float32)
    scale_bytes = scales.astype('<f4').tobytes()
    # OPACITY (scalar float32)
    op_bytes   = opacities.astype('<f4').tobytes()
    # COLOR (DC SH → linear RGB, vec3 float32)
    sh0        = 0.28209479177387814
    dc_rgb     = (sh_coeffs[:, 0, :] * sh0 + 0.5).clip(0, 1).astype('<f4')
    col_bytes  = dc_rgb.tobytes()

    buffer_data = pos_bytes + rot_bytes + scale_bytes + op_bytes + col_bytes
    buf_len  = len(buffer_data)

    def _bv(offset, length, target=None):
        bv = {'buffer': 0, 'byteOffset': offset, 'byteLength': length}
        if target is not None:
            bv['target'] = target
        return bv

    def _acc(bv_idx, count, comp_type, acc_type, min_v=None, max_v=None):
        a = {'bufferView': bv_idx, 'componentType': comp_type,
             'count': count, 'type': acc_type}
        if min_v is not None:
            a['min'] = min_v
            a['max'] = max_v
        return a

    FLOAT = 5126  # GL_FLOAT

    off = 0
    bvs, accs = [], []
    attr = {}

    for name, raw, atype in [
        ('POSITION',  pos_bytes,   'VEC3'),
        ('_ROTATION', rot_bytes,   'VEC4'),
        ('_SCALE',    scale_bytes, 'VEC3'),
        ('_OPACITY',  op_bytes,    'SCALAR'),
        ('_COLOR',    col_bytes,   'VEC3'),
    ]:
        bvs.append(_bv(off, len(raw)))
        mn, mx = None, None
        if name == 'POSITION':
            mn = means.min(axis=0).tolist()
            mx = means.max(axis=0).tolist()
        elif name == '_OPACITY':
            mn = [float(opacities.min())]
            mx = [float(opacities.max())]
        accs.append(_acc(len(bvs) - 1, N, FLOAT, atype, mn, mx))
        attr[name] = len(accs) - 1
        off += len(raw)

    gltf = {
        'asset': {'version': '2.0', 'generator': 'rawkee NavVis splat pipeline'},
        'extensionsUsed': ['KHR_gaussian_splatting'],
        'extensionsRequired': ['KHR_gaussian_splatting'],
        'scene': 0,
        'scenes': [{'nodes': [0]}],
        'nodes': [{'mesh': 0}],
        'meshes': [{
            'name': stem,
            'primitives': [{
                'attributes': attr,
                'mode': 0,   # POINTS
                'extensions': {'KHR_gaussian_splatting': {}},
            }],
        }],
        'accessors': accs,
        'bufferViews': bvs,
        'buffers': [{'byteLength': buf_len}],
    }

    json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    # Pad to 4-byte boundary
    if len(json_bytes) % 4:
        json_bytes += b' ' * (4 - len(json_bytes) % 4)
    if len(buffer_data) % 4:
        buffer_data += b'\x00' * (4 - len(buffer_data) % 4)

    glb_len = 12 + 8 + len(json_bytes) + 8 + len(buffer_data)
    out_path = output_dir / f'{stem}.glb'
    with open(out_path, 'wb') as f:
        f.write(_s.pack('<III', 0x46546C67, 2, glb_len))          # GLB header
        f.write(_s.pack('<II', len(json_bytes), 0x4E4F534A))       # JSON chunk header
        f.write(json_bytes)
        f.write(_s.pack('<II', len(buffer_data), 0x004E4942))      # BIN chunk header
        f.write(buffer_data)

    log.info('Splat GLB → %s  (%d Gaussians)', out_path, N)
    return out_path
