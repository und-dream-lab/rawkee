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
# Coordinate system helpers
# ---------------------------------------------------------------------------

# ROS/NavVis world frame: Z-up right-handed
# X3D / OBJ / glTF frame: Y-up right-handed
# Conversion: (x, y, z)_ros -> (x, z, -y)_x3d
_ROS_TO_X3D = np.array([[1., 0., 0.],
                         [0., 0., 1.],
                         [0.,-1., 0.]], dtype=np.float64)

# Quaternion (w,x,y,z) for the -90° rotation around X that maps ROS→X3D
_Q_ROS_TO_X3D = np.array([np.sqrt(2)/2, -np.sqrt(2)/2, 0.0, 0.0], dtype=np.float64)


def _quat_apply_basis(q_basis: np.ndarray, quats: np.ndarray) -> np.ndarray:
    """Left-multiply an (N,4) array of (w,x,y,z) quaternions by a single quaternion."""
    w1, x1, y1, z1 = q_basis
    w2, x2, y2, z2 = quats[:, 0], quats[:, 1], quats[:, 2], quats[:, 3]
    return np.stack([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
    ], axis=-1)


def _sh_wigner_d(R: np.ndarray, l_max: int) -> list:
    """Numerically compute Wigner D matrices for real SH rotation by R for degrees 0..l_max.
    Uses Fibonacci sphere sampling + least-squares; matches the gsplat real SH convention."""
    try:
        from scipy.special import sph_harm_y as _sph_harm_raw
        def _sph_harm(m, l, phi, theta):   # adapt new API (n, m, theta, phi) to old call style
            return _sph_harm_raw(l, m, theta, phi)
    except ImportError:
        from scipy.special import sph_harm as _sph_harm  # scipy < 1.15 old API
    N = max(500, 200 * (l_max + 1) ** 2)
    golden_angle = np.pi * (3.0 - np.sqrt(5.0))
    i = np.arange(N, dtype=float)
    y_fib = 1.0 - (2.0 * i + 1.0) / N
    r_fib = np.sqrt(np.maximum(1.0 - y_fib**2, 0.0))
    phi_fib = golden_angle * i
    dirs = np.column_stack([r_fib * np.cos(phi_fib), y_fib, r_fib * np.sin(phi_fib)])
    dirs_rt = dirs @ R  # R^T applied to each row direction

    def _rsh(l, d):
        th = np.arccos(np.clip(d[:, 2], -1.0, 1.0))
        ph = np.arctan2(d[:, 1], d[:, 0])
        Y = np.zeros((len(d), 2 * l + 1))
        for j, m in enumerate(range(-l, l + 1)):
            if m < 0:
                Y[:, j] = np.sqrt(2) * (-1)**m * np.imag(_sph_harm(abs(m), l, ph, th))
            elif m == 0:
                Y[:, j] = np.real(_sph_harm(0, l, ph, th))
            else:
                Y[:, j] = np.sqrt(2) * (-1)**m * np.real(_sph_harm(m, l, ph, th))
        return Y

    D_list = [np.eye(1)]
    for l in range(1, l_max + 1):
        B, Br = _rsh(l, dirs), _rsh(l, dirs_rt)
        # Br = B @ D^T  →  D = lstsq(B, Br)^T
        D, _, _, _ = np.linalg.lstsq(B, Br, rcond=None)
        D_list.append(np.ascontiguousarray(D))   # D[m',m] = D_{m'm}(R); c' = D @ c
    return D_list


def _rotate_sh_coeffs(sh_coeffs: np.ndarray, R: np.ndarray, sh_degree: int) -> np.ndarray:
    """Rotate SH coefficients (N, n_sh, 3) by 3x3 rotation matrix R using Wigner D-matrices."""
    if sh_degree == 0:
        return sh_coeffs
    D_list = _sh_wigner_d(R, sh_degree)
    result = sh_coeffs.copy()
    for l in range(1, sh_degree + 1):
        s, e = l * l, (l + 1) * (l + 1)
        result[:, s:e, :] = np.einsum('pm,nmc->npc', D_list[l], sh_coeffs[:, s:e, :])
    return result


def _linear_to_srgb(arr: np.ndarray) -> np.ndarray:
    """Convert linear float32 [0,1] to gamma-encoded sRGB uint8. PNG is always interpreted as sRGB."""
    a = np.clip(arr, 0.0, 1.0)
    srgb = np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1.0 / 2.4) - 0.055)
    return (np.clip(srgb, 0.0, 1.0) * 255).astype(np.uint8)


def _ros_verts_to_x3d(verts: np.ndarray) -> np.ndarray:
    return np.stack([verts[:, 0], verts[:, 2], -verts[:, 1]], axis=1)


def _ros_mesh_to_x3d(mesh):
    """Return a Y-up copy of an Open3D TriangleMesh whose vertices are in ROS Z-up."""
    import copy
    m = copy.deepcopy(mesh)
    import open3d as o3d
    v = np.asarray(m.vertices)
    m.vertices = o3d.utility.Vector3dVector(_ros_verts_to_x3d(v))
    if m.has_vertex_normals():
        n = np.asarray(m.vertex_normals)
        m.vertex_normals = o3d.utility.Vector3dVector(
            np.stack([n[:, 0], n[:, 2], -n[:, 1]], axis=1)
        )
    return m


def _viewpoint_orientation(R_ros: np.ndarray) -> tuple:
    """Axis-angle from X3D default look (0,0,-1) to device forward in Y-up frame."""
    fwd = _ROS_TO_X3D @ R_ros[0]           # device X-axis (forward) in X3D frame
    fwd /= max(float(np.linalg.norm(fwd)), 1e-9)
    default_look = np.array([0., 0., -1.])
    axis = np.cross(default_look, fwd)
    sin_a = float(np.linalg.norm(axis))
    cos_a = float(np.dot(default_look, fwd))
    if sin_a < 1e-6:
        return (0., 1., 0., math.pi if cos_a < 0 else 0.)
    axis /= sin_a
    return (float(axis[0]), float(axis[1]), float(axis[2]), math.atan2(sin_a, cos_a))


def _make_x3d_viewpoints(viewpoints: list, geo_origin, geo_system) -> list:
    raise RuntimeError('_make_x3d_viewpoints is retired; use processBasicNodeAddition instead')


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_mesh(
    mesh,
    cam_patches: list,
    spec_cubemap_paths: dict[str, Path],
    diff_cubemap_paths: dict[str, Path],
    output_dir: Path,
    stem: str,
    fmt: str = 'x3d',
    equirect_spec_path: Optional[Path] = None,
    equirect_diff_path: Optional[Path] = None,
    geo_origin: Optional[tuple] = None,
    viewpoints: Optional[list] = None,
) -> Path:
    """Export a textured polygon mesh in the requested format.

    Parameters
    ----------
    geo_origin:  (easting, northing, height, epsg) from ScanDataset.geo_origin(), or None.
    viewpoints:  list of (pos_ros, R_ros, description) from _collect_scan_viewpoints().
    """
    fmt = fmt.lower().lstrip('.')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if fmt in ('x3d', 'x3dv', 'x3dj'):
        return _export_mesh_x3d(
            mesh, cam_patches, spec_cubemap_paths, diff_cubemap_paths,
            equirect_spec_path, equirect_diff_path,
            output_dir, stem, fmt, geo_origin, viewpoints,
        )
    elif fmt == 'obj':
        return _export_mesh_obj(mesh, cam_patches, output_dir, stem)
    elif fmt == 'glb':
        return _export_mesh_glb(mesh, cam_patches, output_dir, stem)
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
    viewpoints: Optional[list] = None,
    apply_coord_transform: bool = True,
    sky_face_paths: Optional[dict] = None,
) -> Path:
    """Export trained Gaussian splat parameters in the requested format.

    Parameters
    ----------
    geo_origin: (easting, northing, height, epsg) from ScanDataset.geo_origin(), or None.
    decode_sh:  When True, PLY output stores pre-decoded linear RGB in f_dc_* fields
                instead of raw SH coefficients. Use when the consumer does not
                implement SH decoding.
    apply_coord_transform: Apply ROS Z-up → X3D Y-up rotation on X3D export.
                Set False for COLMAP/Metashape data already in Y-up space.
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
            viewpoints=viewpoints, decode_sh=decode_sh,
            apply_coord_transform=apply_coord_transform,
            sky_face_paths=sky_face_paths,
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
    mesh, cam_patches: list,
    spec_paths: dict[str, Path],
    diff_paths: dict[str, Path],
    equirect_spec: Optional[Path],
    equirect_diff: Optional[Path],
    output_dir: Path, stem: str, fmt: str,
    geo_origin: Optional[tuple] = None,
    viewpoints: Optional[list] = None,
) -> Path:
    try:
        import open3d as o3d
    except ImportError:
        raise RuntimeError('open3d required: pip install open3d')
    try:
        import imageio.v3 as iio
    except ImportError:
        raise RuntimeError('imageio required: pip install imageio')

    from rawkee.io.RKSceneTraversal import RKSceneTraversal

    # --- Save camera patch images ---
    for patch in cam_patches:
        img_path = output_dir / f'{stem}_{patch["label"]}.png'
        iio.imwrite(str(img_path), patch['image'])
        log.info('Patch image → %s', img_path)

    # --- Prepare KTX2 / HDR env maps ---
    spec_env_path = _make_env_ktx2(equirect_spec, spec_paths, output_dir, f'{stem}_envmap_spec')
    diff_env_path = _make_env_ktx2(equirect_diff, diff_paths, output_dir, f'{stem}_envmap_diff')

    # --- Mesh data ---
    verts_ros = np.asarray(mesh.vertices)          # (V, 3) ROS Z-up
    mesh_tris = np.asarray(mesh.triangles)         # (T, 3)
    vcolors   = np.asarray(mesh.vertex_colors) if mesh.has_vertex_colors() else None

    # --- Build X3D scene ---
    trv = RKSceneTraversal()
    trv.clearMemberLists()
    x3d_doc   = trv.getX3DObject()
    x3d_scene = trv.getSceneObject()
    x3d_doc.Scene = x3d_scene

    # Viewpoints
    if viewpoints:
        geo_sys = _epsg_to_geo_system(geo_origin[3]) if geo_origin else None
        for i, (pos_ros, R_ros, desc) in enumerate(viewpoints):
            ori = _viewpoint_orientation(R_ros)
            if geo_origin is not None:
                vp = trv.processBasicNodeAddition(x3d_scene, "children", "GeoViewpoint", f'VP{i}')
                if vp:
                    e0, n0, h0, _ = geo_origin
                    vp.geoCoords   = (e0 + pos_ros[0], n0 + pos_ros[1], h0 + pos_ros[2])
                    vp.geoSystem   = geo_sys or ['GD', 'WE']
                    vp.description = desc
                    vp.orientation = ori
                    vp.fieldOfView = 1.047
            else:
                vp = trv.processBasicNodeAddition(x3d_scene, "children", "Viewpoint", f'VP{i}')
                if vp:
                    vp.position    = tuple((_ROS_TO_X3D @ pos_ros).tolist())
                    vp.description = desc
                    vp.orientation = ori
                    vp.fieldOfView = 1.047

    # EnvironmentLight
    env_light = trv.processBasicNodeAddition(x3d_scene, "children", "EnvironmentLight", "EnvLight")
    if env_light:
        env_light.intensity = 1.0
        env_light.global_   = True
        if spec_env_path:
            spec_tex = trv.processBasicNodeAddition(env_light, "specularTexture", "ImageCubeMapTexture", "EnvSpec")
            if spec_tex:
                spec_tex.url = [str(spec_env_path.name)]
        if diff_env_path:
            diff_tex = trv.processBasicNodeAddition(env_light, "diffuseTexture", "ImageCubeMapTexture", "EnvDiff")
            if diff_tex:
                diff_tex.url = [str(diff_env_path.name)]

    # Shape parent (GeoLocation wrapper when georeferenced)
    if geo_origin is not None:
        e, n, h, epsg = geo_origin
        geo_node = trv.processBasicNodeAddition(x3d_scene, "children", "GeoLocation", "GeoScanLocation")
        if geo_node:
            geo_node.geoCoords = (e, n, h)
            geo_node.geoSystem = _epsg_to_geo_system(epsg)
        shape_parent, shape_field = geo_node, "children"
    else:
        shape_parent, shape_field = x3d_scene, "children"

    # --- One Shape per camera patch (triangles duplicated per corner for unique UVs) ---
    covered_tris = set()
    for patch in cam_patches:
        lbl   = patch['label']
        t_idx = patch['tri_indices']                        # (M,)
        uvs   = patch['uvs']                               # (M*3, 2)

        corners = mesh_tris[t_idx].ravel()                 # (M*3,) global vert indices
        vd      = _ros_verts_to_x3d(verts_ros[corners])   # (M*3, 3) Y-up
        idx_seq = list(range(len(vd)))

        img_path = output_dir / f'{stem}_{lbl}.png'
        shape = trv.processBasicNodeAddition(shape_parent, shape_field, "Shape", f'Shape_{lbl}')
        if shape:
            app = trv.processBasicNodeAddition(shape, "appearance", "Appearance", f'App_{lbl}')
            if app:
                mat = trv.processBasicNodeAddition(app, "material", "PhysicalMaterial", f'Mat_{lbl}')
                if mat:
                    mat.baseColor = (1.0, 1.0, 1.0)
                    mat.metallic  = 0.0
                    mat.roughness = 0.6
                    tex = trv.processBasicNodeAddition(mat, "baseTexture", "ImageTexture", f'Tex_{lbl}')
                    if tex:
                        tex.url = [img_path.name]
            geom = trv.processBasicNodeAddition(shape, "geometry", "IndexedTriangleSet", f'Geom_{lbl}')
            if geom:
                geom.index = idx_seq
                geom.solid = False
                co = trv.processBasicNodeAddition(geom, "coord", "Coordinate", f'Coord_{lbl}')
                if co:
                    co.point = [tuple(v) for v in vd.tolist()]
                tc = trv.processBasicNodeAddition(geom, "texCoord", "TextureCoordinate", f'UV_{lbl}')
                if tc:
                    tc.point = [tuple(uv) for uv in uvs.tolist()]
        covered_tris.update(t_idx.tolist())

    # Fallback shape for triangles not covered by any camera (vertex colors or gray)
    uncovered = sorted(set(range(len(mesh_tris))) - covered_tris)
    if uncovered:
        unc_arr = np.array(uncovered, dtype=np.int32)
        corners = mesh_tris[unc_arr].ravel()
        vd      = _ros_verts_to_x3d(verts_ros[corners])
        idx_seq = list(range(len(vd)))
        vc      = np.clip(vcolors[corners], 0, 1) if vcolors is not None and len(vcolors) > 0 \
                  else np.full((len(vd), 3), 0.5)
        shape = trv.processBasicNodeAddition(shape_parent, shape_field, "Shape", "ShapeFallback")
        if shape:
            app = trv.processBasicNodeAddition(shape, "appearance", "Appearance", "AppFallback")
            if app:
                mat = trv.processBasicNodeAddition(app, "material", "PhysicalMaterial", "MatFallback")
                if mat:
                    mat.metallic  = 0.0
                    mat.roughness = 0.8
            geom = trv.processBasicNodeAddition(shape, "geometry", "IndexedTriangleSet", "GeomFallback")
            if geom:
                geom.index = idx_seq
                geom.solid = False
                co = trv.processBasicNodeAddition(geom, "coord", "Coordinate", "CoordFallback")
                if co:
                    co.point = [tuple(v) for v in vd.tolist()]
                cn = trv.processBasicNodeAddition(geom, "color", "Color", "ColorFallback")
                if cn:
                    cn.color = [tuple(c) for c in vc.tolist()]
        log.info('Fallback shape: %d uncovered triangles', len(uncovered))

    trv.collectProfileFromScene(x3d_doc)

    out_path = output_dir / f'{stem}.{fmt}'
    trv.x3d2disk(x3d_doc, str(out_path), fmt)
    log.info('Mesh X3D → %s', out_path)
    return out_path


# ---------------------------------------------------------------------------
# Mesh — OBJ
# ---------------------------------------------------------------------------

def _export_mesh_obj(mesh, cam_patches: list, output_dir: Path, stem: str) -> Path:
    try:
        import open3d as o3d
    except ImportError:
        raise RuntimeError('open3d required')

    mesh = _ros_mesh_to_x3d(mesh)
    out_path = output_dir / f'{stem}.obj'
    o3d.io.write_triangle_mesh(
        str(out_path), mesh,
        write_ascii=True, write_vertex_normals=True, write_vertex_colors=True,
    )
    log.info('Mesh OBJ → %s', out_path)
    return out_path


# ---------------------------------------------------------------------------
# Mesh — GLB
# ---------------------------------------------------------------------------

def _export_mesh_glb(mesh, cam_patches: list, output_dir: Path, stem: str) -> Path:
    try:
        import open3d as o3d
    except ImportError:
        raise RuntimeError('open3d required')

    mesh = _ros_mesh_to_x3d(mesh)
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
    viewpoints: Optional[list] = None,
    decode_sh: bool = True,
    apply_coord_transform: bool = True,
    sky_face_paths: Optional[dict] = None,
) -> Path:
    from rawkee.io.RKSceneTraversal import RKSceneTraversal

    N = len(means)
    log.info('Building X3D GaussianSplats node  N=%d  sh_degree=%d  decode_sh=%s', N, sh_degree, decode_sh)

    if apply_coord_transform:
        # Convert ROS Z-up world frame → X3D Y-up frame
        means      = _ros_verts_to_x3d(means)
        quats_wxyz = _quat_apply_basis(_Q_ROS_TO_X3D, quats_wxyz)
        sh_coeffs  = _rotate_sh_coeffs(sh_coeffs, _ROS_TO_X3D, sh_degree)

    # Quaternion order: (w,x,y,z) → X3D spec (x,y,z,w)
    quats_xyzw = np.roll(quats_wxyz, -1, axis=1)

    # bulk numpy→Python conversion; arr.tolist() is a single C call, far faster than row iteration
    def _mf3(arr):
        return list(map(tuple, arr.tolist()))

    trv = RKSceneTraversal()
    trv.clearMemberLists()
    x3d_doc   = trv.getX3DObject()
    x3d_scene = trv.getSceneObject()
    x3d_doc.Scene = x3d_scene

    # Sky background: 6-face cube map → Background node
    # face order matches X3D Background field names
    _FACE_FIELDS = ('front', 'back', 'left', 'right', 'top', 'bottom')
    if sky_face_paths and any(f in sky_face_paths for f in _FACE_FIELDS):
        bg = trv.processBasicNodeAddition(x3d_scene, 'children', 'Background', 'SkyBackground')
        if bg:
            for face in _FACE_FIELDS:
                p = sky_face_paths.get(face)
                if p and Path(p).exists():
                    field = f'{face}Url'
                    mf = getattr(bg, field, None)
                    if isinstance(mf, list):
                        mf.append(Path(p).name)
                    else:
                        setattr(bg, field, [Path(p).name])
            log.info('Background node added with %d sky faces',
                     sum(1 for f in _FACE_FIELDS if sky_face_paths.get(f)))

    # Viewpoints (same pattern as mesh export)
    if viewpoints:
        geo_sys = _epsg_to_geo_system(geo_origin[3]) if geo_origin else None
        for i, (pos_ros, R_ros, desc) in enumerate(viewpoints):
            if apply_coord_transform:
                # NavVis: device X-axis is forward, convert ROS frame → X3D Y-up
                ori = _viewpoint_orientation(R_ros)
            else:
                # COLMAP/non-NavVis: camera -Z column is look dir, already in Y-up frame
                fwd = -np.asarray(R_ros)[:, 2]
                fwd = fwd / max(float(np.linalg.norm(fwd)), 1e-9)
                default_look = np.array([0., 0., -1.])
                ax = np.cross(default_look, fwd)
                sin_a = float(np.linalg.norm(ax))
                cos_a = float(np.dot(default_look, fwd))
                if sin_a < 1e-6:
                    ori = (0., 1., 0., math.pi if cos_a < 0 else 0.)
                else:
                    ax /= sin_a
                    ori = (float(ax[0]), float(ax[1]), float(ax[2]), math.atan2(sin_a, cos_a))
            if geo_origin is not None:
                vp = trv.processBasicNodeAddition(x3d_scene, 'children', 'GeoViewpoint', f'VP{i}')
                if vp:
                    e0, n0, h0, _ = geo_origin
                    vp.geoCoords   = (e0 + pos_ros[0], n0 + pos_ros[1], h0 + pos_ros[2])
                    vp.geoSystem   = geo_sys or ['GD', 'WE']
                    vp.description = desc
                    vp.orientation = ori
                    vp.fieldOfView = 1.047
            else:
                vp = trv.processBasicNodeAddition(x3d_scene, 'children', 'Viewpoint', f'VP{i}')
                if vp:
                    # Apply coord transform only when the scene itself is transformed
                    vp_pos = (_ROS_TO_X3D @ pos_ros) if apply_coord_transform else pos_ros
                    vp.position    = tuple(vp_pos.tolist())
                    vp.description = desc
                    vp.orientation = ori
                    vp.fieldOfView = 1.047

    # GeoTransform wrapper when georeferenced
    if geo_origin is not None:
        e, n, h, epsg = geo_origin
        geo_node = trv.processBasicNodeAddition(x3d_scene, 'children', 'GeoTransform', 'GeoSplatTransform')
        if geo_node:
            geo_node.geoCenter = (e, n, h)
            geo_node.geoSystem = _epsg_to_geo_system(epsg)
        gs_parent, gs_field = geo_node, 'children'
    else:
        gs_parent, gs_field = x3d_scene, 'children'

    gs = trv.processBasicNodeAddition(gs_parent, gs_field, 'GaussianSplats', 'ScanSplats')
    if gs:
        log.info('Converting arrays to X3D field lists  N=%d', N)
        gs.positions    = _mf3(means)
        gs.orientations = list(map(tuple, quats_xyzw.tolist()))
        gs.scales       = _mf3(scales)
        gs.opacities    = opacities.tolist()

        if decode_sh:
            # Pre-decode DC SH to view-independent linear RGB so viewers without SH get correct colors
            _C0 = 0.28209479177387814   # 1 / (2 * sqrt(pi))
            dc_rgb = np.clip(sh_coeffs[:, 0, :] * _C0 + 0.5, 0.0, 1.0)
            gs.sphericalHarmonicsDegree0Coef0 = _mf3(dc_rgb)
        else:
            gs.sphericalHarmonicsDegree0Coef0 = _sh_flat(sh_coeffs, sh_degree, 0)
            if sh_degree >= 1:
                gs.sphericalHarmonicsDegree1Coef0 = _sh_flat(sh_coeffs, sh_degree, 1)
                gs.sphericalHarmonicsDegree1Coef1 = _sh_flat(sh_coeffs, sh_degree, 2)
                gs.sphericalHarmonicsDegree1Coef2 = _sh_flat(sh_coeffs, sh_degree, 3)
            if sh_degree >= 2:
                gs.sphericalHarmonicsDegree2Coef0 = _sh_flat(sh_coeffs, sh_degree, 4)
                gs.sphericalHarmonicsDegree2Coef1 = _sh_flat(sh_coeffs, sh_degree, 5)
                gs.sphericalHarmonicsDegree2Coef2 = _sh_flat(sh_coeffs, sh_degree, 6)
                gs.sphericalHarmonicsDegree2Coef3 = _sh_flat(sh_coeffs, sh_degree, 7)
                gs.sphericalHarmonicsDegree2Coef4 = _sh_flat(sh_coeffs, sh_degree, 8)
            if sh_degree >= 3:
                gs.sphericalHarmonicsDegree3Coef0 = _sh_flat(sh_coeffs, sh_degree,  9)
                gs.sphericalHarmonicsDegree3Coef1 = _sh_flat(sh_coeffs, sh_degree, 10)
                gs.sphericalHarmonicsDegree3Coef2 = _sh_flat(sh_coeffs, sh_degree, 11)
                gs.sphericalHarmonicsDegree3Coef3 = _sh_flat(sh_coeffs, sh_degree, 12)
                gs.sphericalHarmonicsDegree3Coef4 = _sh_flat(sh_coeffs, sh_degree, 13)
                gs.sphericalHarmonicsDegree3Coef5 = _sh_flat(sh_coeffs, sh_degree, 14)
                gs.sphericalHarmonicsDegree3Coef6 = _sh_flat(sh_coeffs, sh_degree, 15)

    trv.collectProfileFromScene(x3d_doc)
    out_path = output_dir / f'{stem}.{fmt}'
    log.info('Writing Splat X3D → %s', out_path)
    trv.x3d2disk(x3d_doc, str(out_path), fmt)
    log.info('Splat X3D → %s', out_path)
    return out_path


def _export_splat_x3d_inline(
    glb_path: Path,
    output_dir: Path,
    stem: str,
    fmt: str,
    viewpoints: Optional[list] = None,
    geo_origin: Optional[tuple] = None,
    apply_coord_transform: bool = False,
) -> Path:
    """Create a lightweight X3D wrapper with viewpoints + an Inline node referencing a GLB."""
    from rawkee.io.RKSceneTraversal import RKSceneTraversal

    trv = RKSceneTraversal()
    trv.clearMemberLists()
    x3d_doc   = trv.getX3DObject()
    x3d_scene = trv.getSceneObject()
    x3d_doc.Scene = x3d_scene

    if viewpoints:
        geo_sys = _epsg_to_geo_system(geo_origin[3]) if geo_origin else None
        for i, (pos_ros, R_ros, desc) in enumerate(viewpoints):
            if apply_coord_transform:
                ori = _viewpoint_orientation(R_ros)
            else:
                fwd = -np.asarray(R_ros)[:, 2]
                fwd = fwd / max(float(np.linalg.norm(fwd)), 1e-9)
                default_look = np.array([0., 0., -1.])
                ax = np.cross(default_look, fwd)
                sin_a = float(np.linalg.norm(ax))
                cos_a = float(np.dot(default_look, fwd))
                if sin_a < 1e-6:
                    ori = (0., 1., 0., math.pi if cos_a < 0 else 0.)
                else:
                    ax /= sin_a
                    ori = (float(ax[0]), float(ax[1]), float(ax[2]), math.atan2(sin_a, cos_a))
            if geo_origin is not None:
                vp = trv.processBasicNodeAddition(x3d_scene, 'children', 'GeoViewpoint', f'VP{i}')
                if vp:
                    e0, n0, h0, _ = geo_origin
                    vp.geoCoords   = (e0 + pos_ros[0], n0 + pos_ros[1], h0 + pos_ros[2])
                    vp.geoSystem   = geo_sys or ['GD', 'WE']
                    vp.description = desc
                    vp.orientation = ori
                    vp.fieldOfView = 1.047
            else:
                vp = trv.processBasicNodeAddition(x3d_scene, 'children', 'Viewpoint', f'VP{i}')
                if vp:
                    vp_pos = (_ROS_TO_X3D @ pos_ros) if apply_coord_transform else pos_ros
                    vp.position    = tuple(vp_pos.tolist())
                    vp.description = desc
                    vp.orientation = ori
                    vp.fieldOfView = 1.047

    inline = trv.processBasicNodeAddition(x3d_scene, 'children', 'Inline', 'SplatInline')
    if inline:
        inline.url.append(glb_path.name)   # relative URL — GLB lives beside the X3D

    trv.collectProfileFromScene(x3d_doc)
    out_path = output_dir / f'{stem}.{fmt}'
    trv.x3d2disk(x3d_doc, str(out_path), fmt)
    log.info('Splat X3D Inline → %s', out_path)
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
    ros_tag: bool = True,
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
            + ('comment rawkee coordinate_system ros-zup\n' if ros_tag else '')
            + f'element vertex {N}\n'
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
