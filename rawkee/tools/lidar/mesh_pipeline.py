"""Textured polygon mesh pipeline for mobile LiDAR scan datasets.

Strategy
--------
1. Extract LiDAR point clouds from the SLAM ROS bag (PandarXTM laser_horiz +
   laser_vert).  Falls back to GPU depth estimation (Depth Anything V2) when
   the bag does not expose raw scan topics.
2. Colorize point cloud: reproject each LiDAR point into every camera frame
   that sees it, average colour using inverse-distance weighting.
3. Run Open3D Poisson surface reconstruction on the coloured cloud.
4. UV unwrap and bake a texture atlas.
5. Export via scan.export in the requested format.
"""
from __future__ import annotations
import logging
import math
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import torch
    import torch.nn.functional as F
    _TORCH = True
except ImportError:
    _TORCH = False

try:
    import open3d as o3d
    _O3D = True
except ImportError:
    _O3D = False

try:
    from rosbags.rosbag1 import Reader as Rosbag1Reader
    _ROSBAGS = True
except ImportError:
    _ROSBAGS = False

from .dataset import ScanDataset, _quat_to_rot

log = logging.getLogger(__name__)


def _warn_no_gpu(pipeline: str, require: bool = False) -> None:
    """Print actionable GPU diagnostic and optionally raise."""
    lines = ['', f'WARNING: No CUDA GPU is available for the {pipeline} pipeline.']
    if _TORCH:
        lines.append(f'  PyTorch version : {torch.__version__}')
        lines.append(f'  PyTorch CUDA    : {torch.version.cuda or "not compiled"}')
    else:
        lines.append('  PyTorch is not installed.')
    lines += [
        '  Suggested fixes:',
        '    1. Ensure your NVIDIA driver is installed (>=525 for CUDA 12.x).',
        '    2. Reinstall PyTorch for your CUDA version:',
        '         pip install torch --index-url https://download.pytorch.org/whl/cu124',
        '    3. For Grace/Hopper or DGX Spark use the NGC PyTorch container.',
        '    4. Quick check: python -c "import torch; print(torch.cuda.is_available())"',
    ]
    if require:
        lines.append('')
        print('\n'.join(lines), flush=True)
        raise RuntimeError(f'A CUDA GPU is required for the {pipeline} pipeline but none is available.')
    lines.append('  Continuing on CPU — performance will be significantly reduced.')
    lines.append('')
    print('\n'.join(lines), flush=True)


def _get_device() -> 'torch.device':
    if _TORCH and torch.cuda.is_available():
        p = torch.cuda.get_device_properties(0)
        log.info('Mesh pipeline GPU: %s  sm_%d%d', p.name, p.major, p.minor)
        if p.major >= 9:
            torch.cuda.set_per_process_memory_fraction(0.85)
        return torch.device('cuda')
    _warn_no_gpu('mesh', require=False)
    return torch.device('cpu')


# ---------------------------------------------------------------------------
# LiDAR extraction from ROS bag
# ---------------------------------------------------------------------------

# ROS sensor_msgs/PointField datatype codes → (numpy dtype, byte size)
_ROS_DTYPE: dict[int, tuple[type, int]] = {
    1: (np.int8,    1), 2: (np.uint8,   1),
    3: (np.int16,   2), 4: (np.uint16,  2),
    5: (np.int32,   4), 6: (np.uint32,  4),
    7: (np.float32, 4), 8: (np.float64, 8),
}


def _parse_pointcloud2(msg_data: bytes, fields_meta: list, point_step: int) -> Optional[np.ndarray]:
    """Parse a ROS sensor_msgs/PointCloud2 blob to (N,3) float32 xyz."""
    try:
        if point_step <= 0 or len(msg_data) == 0:
            return None
        n_pts = len(msg_data) // point_step
        if n_pts == 0:
            return None

        offsets = {f.name: (f.offset, f.datatype) for f in fields_meta}
        raw = np.frombuffer(msg_data[:n_pts * point_step], dtype=np.uint8).reshape(n_pts, point_step)

        def _extract(name: str, default_off: int) -> np.ndarray:
            off, dt = offsets.get(name, (default_off, 7))  # 7 = FLOAT32
            np_dtype, nbytes = _ROS_DTYPE.get(dt, (np.float32, 4))
            return np.frombuffer(raw[:, off:off + nbytes].tobytes(), dtype=np_dtype).astype(np.float32)

        x = _extract('x', 0)
        y = _extract('y', 4)
        z = _extract('z', 8)
        valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
        return np.stack([x[valid], y[valid], z[valid]], axis=-1).astype(np.float32)
    except Exception as exc:
        log.debug('PointCloud2 parse failed: %s', exc)
        return None


def _extract_e57_cloud(dataset: ScanDataset) -> tuple[np.ndarray, 'np.ndarray | None']:
    """Read (xyz, colors_or_None) from an E57 dataset and voxel-downsample."""
    xyz, colors = dataset.e57_point_cloud()
    if _O3D:
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(xyz.astype(np.float64))
        if colors is not None:
            pcd.colors = o3d.utility.Vector3dVector(np.clip(colors, 0, 1).astype(np.float64))
        pcd = pcd.voxel_down_sample(voxel_size=0.02)
        xyz    = np.asarray(pcd.points).astype(np.float32)
        colors = np.asarray(pcd.colors).astype(np.float32) if pcd.has_colors() else None
        log.info('E57 after voxel downsample: %d points', len(xyz))
    return xyz, colors


def _extract_lidar_from_bag(
    bag_path: Path,
    lidar_topics: tuple[str, ...] = ('/laser_horiz', '/laser_vert',
                                      '/velodyne_points', '/points_raw'),
    max_clouds: int = 500,
) -> Optional[np.ndarray]:
    """Return combined (N,3) float32 point cloud from a ROS1 bag, or None."""
    if not _ROSBAGS:
        log.warning('rosbags not installed — cannot read ROS bags: pip install rosbags')
        return None
    if not bag_path.exists():
        log.warning('Bag not found: %s', bag_path)
        return None

    clouds = []
    count = 0
    try:
        from rosbags.typesys import Stores, get_typestore
        ts = get_typestore(Stores.ROS1_NOETIC)
        with Rosbag1Reader(bag_path) as reader:
            topics_in_bag = {c.topic for c in reader.connections}
            active = [t for t in lidar_topics if t in topics_in_bag]
            if not active:
                log.warning('No LiDAR topics found in bag (have: %s)', topics_in_bag)
                return None
            log.info('Reading LiDAR from bag topics: %s', active)
            conns = [c for c in reader.connections if c.topic in active]
            for conn, ts_ns, raw in reader.messages(connections=conns):
                if count >= max_clouds:
                    break
                try:
                    msg = ts.deserialize_ros1(raw, conn.msgtype)
                    xyz = _parse_pointcloud2(bytes(msg.data), msg.fields, msg.point_step)
                    if xyz is not None and len(xyz) > 0:
                        clouds.append(xyz)
                        count += 1
                except Exception as exc:
                    log.debug('Skip cloud %d: %s', count, exc)
    except Exception as exc:
        log.warning('Bag read error: %s', exc)
        return None

    if not clouds:
        return None
    combined = np.concatenate(clouds, axis=0)
    log.info('Extracted %d LiDAR clouds → %d points total', count, len(combined))
    return combined


# ---------------------------------------------------------------------------
# Depth estimation fallback (Depth Anything V2 via transformers)
# ---------------------------------------------------------------------------

def _estimate_depth_gpu(
    dataset: ScanDataset,
    frame_indices: list[int],
    device: 'torch.device',
    stride: int = 5,
) -> np.ndarray:
    """Estimate depth for selected frames and return fused (N,3) world point cloud."""
    try:
        from transformers import pipeline as hf_pipeline
    except ImportError:
        raise RuntimeError(
            'transformers required for depth fallback: pip install transformers'
        )

    log.info('Depth estimation fallback using Depth Anything V2 …')
    depth_pipe = hf_pipeline(
        task='depth-estimation',
        model='depth-anything/Depth-Anything-V2-Large-hf',
        device=0 if device.type == 'cuda' else -1,
    )

    all_pts: list[np.ndarray] = []

    for fi in frame_indices[::stride]:
        head_pos, R_head = dataset.frame_transform(fi)
        for ci, cam in enumerate(dataset.cameras):
            dng = dataset.dng_path(fi, ci)
            if not dng.exists():
                continue
            try:
                from PIL import Image
                import rawpy
                with rawpy.imread(str(dng)) as raw:
                    rgb8 = raw.postprocess(output_bps=8, use_camera_wb=True)
                pil_img = Image.fromarray(rgb8)
                pil_img = pil_img.resize((512, 512))
                depth_out = depth_pipe(pil_img)
                depth = np.array(depth_out['depth'], dtype=np.float32)

                h, w = depth.shape
                col_g = np.arange(w, dtype=np.float32)
                row_g = np.arange(h, dtype=np.float32)
                cc, rr = np.meshgrid(col_g, row_g)
                cc = cc * (cam.ocam.width  / w)
                rr = rr * (cam.ocam.height / h)
                uv = np.stack([cc.ravel(), rr.ravel()], axis=-1)
                dirs_cam = cam.ocam.unproject(uv)
                pts_cam = dirs_cam * depth.ravel()[:, None]

                # Transform to world frame
                R_cam_to_head = cam.R                     # (3,3)
                pts_head = pts_cam @ R_cam_to_head.T + cam.position
                pts_world = pts_head @ R_head.T + head_pos

                all_pts.append(pts_world.astype(np.float32))
            except Exception as exc:
                log.debug('Depth estimation frame %d cam %d: %s', fi, ci, exc)

    if not all_pts:
        raise RuntimeError('Depth estimation produced no points')
    combined = np.concatenate(all_pts, axis=0)
    log.info('Depth fallback: %d world points from %d frames', len(combined), len(frame_indices[::stride]))
    return combined


# ---------------------------------------------------------------------------
# Colorisation
# ---------------------------------------------------------------------------

def _colorize_cloud(
    xyz: np.ndarray,
    dataset: ScanDataset,
    frame_indices: list[int],
    device: 'torch.device',
    stride: int = 10,
    max_dist: float = 20.0,
) -> np.ndarray:
    """Return (N,3) float32 RGB colours for each world-frame point in xyz."""
    from .hdri import _load_image_hdr

    N = len(xyz)
    colour_sum   = np.zeros((N, 3), dtype=np.float32)
    colour_count = np.zeros(N, dtype=np.float32)

    xyz_t = torch.from_numpy(xyz).to(device)

    # Pre-compute per-camera rotation and position tensors once
    cam_R_t   = [torch.tensor(c.R,        device=device, dtype=torch.float32) for c in dataset.cameras]
    cam_pos_t = [torch.tensor(c.position, device=device, dtype=torch.float32) for c in dataset.cameras]

    for fi in frame_indices[::stride]:
        head_pos, R_head = dataset.frame_transform(fi)
        head_pos_t = torch.tensor(head_pos, device=device, dtype=torch.float32)
        R_head_t   = torch.tensor(R_head,   device=device, dtype=torch.float32)

        for ci, cam in enumerate(dataset.cameras):
            dng = dataset.dng_path(fi, ci)
            if not dng.exists():
                continue
            try:
                img_np = _load_image_hdr(dng)
                img_t = torch.from_numpy(img_np).to(device).permute(2, 0, 1).unsqueeze(0)

                pts_head = (xyz_t - head_pos_t) @ R_head_t
                pts_cam  = (pts_head - cam_pos_t[ci]) @ cam_R_t[ci]

                uvs, mask = cam.ocam.project_gpu(pts_cam, device)

                # Additional distance filter
                dist = torch.norm(pts_cam, dim=-1)
                mask = mask & (dist < max_dist)

                if not mask.any():
                    continue

                # grid_sample expects (1, C, 1, N_valid)
                uvs_valid = uvs[mask].unsqueeze(0).unsqueeze(0)
                sampled = F.grid_sample(
                    img_t, uvs_valid, mode='bilinear',
                    padding_mode='border', align_corners=True,
                ).squeeze(0).squeeze(1).T   # (N_v, 3)

                w = (1.0 / dist[mask].clamp(min=0.1)).cpu().numpy()
                idx = mask.cpu().numpy().nonzero()[0]
                colour_sum[idx]   += sampled.cpu().numpy() * w[:, None]
                colour_count[idx] += w
            except Exception as exc:
                log.debug('Colorise frame %d cam %d: %s', fi, ci, exc)

    valid = colour_count > 0
    colours = np.where(
        valid[:, None],
        colour_sum / np.maximum(colour_count[:, None], 1e-8),
        0.5,   # grey for unobserved points
    )
    log.info('Colourised %d / %d points', valid.sum(), N)
    return colours.astype(np.float32)


# ---------------------------------------------------------------------------
# Poisson reconstruction + texturing
# ---------------------------------------------------------------------------

def _poisson_mesh(xyz: np.ndarray, colours: np.ndarray, depth: int = 9) -> 'o3d.geometry.TriangleMesh':
    """Run Open3D Poisson surface reconstruction."""
    if not _O3D:
        raise RuntimeError('open3d required: pip install open3d')

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz.astype(np.float64))
    pcd.colors = o3d.utility.Vector3dVector(np.clip(colours, 0, 1).astype(np.float64))

    log.info('Estimating normals …')
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
    )
    pcd.orient_normals_consistent_tangent_plane(k=15)

    log.info('Poisson reconstruction (depth=%d) …', depth)
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=depth, scale=1.1, linear_fit=False
    )
    # Prune low-density vertices (artefacts)
    thresh = np.quantile(np.asarray(densities), 0.05)
    mesh.remove_vertices_by_mask(np.asarray(densities) < thresh)
    mesh.remove_degenerate_triangles()
    mesh.remove_unreferenced_vertices()
    mesh.compute_vertex_normals()
    log.info('Mesh: %d vertices, %d faces', len(mesh.vertices), len(mesh.triangles))
    return mesh


def _bake_texture(
    mesh: 'o3d.geometry.TriangleMesh',
    xyz: np.ndarray,
    colours: np.ndarray,
    atlas_size: int = 4096,
) -> tuple['o3d.geometry.TriangleMesh', np.ndarray]:
    """UV-unwrap and bake vertex colours into a texture atlas.

    Returns (textured_mesh, atlas_image).
    """
    if not _O3D:
        raise RuntimeError('open3d required')

    # Simple per-vertex colour transfer; proper atlas unwrap is not yet
    # part of Open3D's Python API — we use vertex colours directly and
    # rely on the exporter to convert to a texture atlas where needed.
    verts = np.asarray(mesh.vertices)
    vcolors = np.asarray(mesh.vertex_colors) if mesh.has_vertex_colors() else None

    if vcolors is None or len(vcolors) == 0:
        log.info('Projecting point-cloud colours to mesh vertices …')
        from scipy.spatial import cKDTree
        tree = cKDTree(xyz)
        dists, idxs = tree.query(verts, k=4, workers=-1)
        weights = 1.0 / np.maximum(dists, 1e-6)
        weights /= weights.sum(axis=1, keepdims=True)
        vcolors = (weights[:, :, None] * colours[idxs]).sum(axis=1)
        mesh.vertex_colors = o3d.utility.Vector3dVector(np.clip(vcolors, 0, 1))

    # Build a simple (N_tris * 3, 2) UV map using a planar unwrap approximation
    tris    = np.asarray(mesh.triangles)
    n_tris  = len(tris)
    n_tiles = math.ceil(math.sqrt(n_tris))
    tile_sz = 1.0 / n_tiles

    ti_arr   = np.arange(n_tris)
    t_rows, t_cols = np.divmod(ti_arr, n_tiles)
    u0 = (t_cols * tile_sz).astype(np.float32)
    v0 = (t_rows * tile_sz).astype(np.float32)
    uvs = np.empty((n_tris * 3, 2), dtype=np.float32)
    uvs[0::3, 0] = u0;              uvs[0::3, 1] = v0
    uvs[1::3, 0] = u0 + tile_sz;   uvs[1::3, 1] = v0
    uvs[2::3, 0] = u0;              uvs[2::3, 1] = v0 + tile_sz

    # Rasterise per-triangle mean colour into atlas
    atlas = np.zeros((atlas_size, atlas_size, 3), dtype=np.float32)
    sz    = max(1, int(tile_sz * atlas_size))
    r0_arr = (t_rows * tile_sz * atlas_size).astype(int)
    c0_arr = (t_cols * tile_sz * atlas_size).astype(int)
    tri_colors = np.clip(vcolors[tris].mean(axis=1), 0, 1)  # (T, 3) — vectorized
    for ti in range(n_tris):
        atlas[r0_arr[ti]:r0_arr[ti] + sz, c0_arr[ti]:c0_arr[ti] + sz] = tri_colors[ti]

    mesh.triangle_uvs = o3d.utility.Vector2dVector(uvs)
    return mesh, atlas


# ---------------------------------------------------------------------------
# Public pipeline class
# ---------------------------------------------------------------------------

class MeshPipeline:
    """End-to-end scan dataset → textured polygon mesh pipeline."""

    def __init__(
        self,
        poisson_depth: int = 9,
        atlas_size: int = 4096,
        colorise_stride: int = 10,
        depth_fallback_stride: int = 5,
        prefer_cuda: bool = True,
    ) -> None:
        self.poisson_depth = poisson_depth
        self.atlas_size = atlas_size
        self.colorise_stride = colorise_stride
        self.depth_fallback_stride = depth_fallback_stride
        self.device = _get_device() if prefer_cuda else torch.device('cpu')

    # ------------------------------------------------------------------

    def run(
        self,
        dataset: ScanDataset,
        output_dir: Path,
        output_format: str = 'x3d',
        hdri_frame: Optional[int] = None,
        envmap_width: int = 4096,
        envmap_height: int = 2048,
        trimble_csv: Optional[Path] = None,
        georef_epsg: int = 32605,
    ) -> Path:
        """Run the full mesh pipeline and export.

        Parameters
        ----------
        dataset:       ScanDataset instance.
        output_dir:    Directory to write outputs.
        output_format: One of x3d | x3dv | x3dj | obj | glb.
        hdri_frame:    Frame index used for HDRI generation (None = auto).
        trimble_csv:   Optional path to a Trimble survey CSV for georeferencing.
        georef_epsg:   Target projected CRS (default 32605 = UTM Zone 5N).
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if trimble_csv is not None:
            dataset.apply_trimble_georef(trimble_csv, epsg=georef_epsg)

        valid_frames = dataset.valid_frame_indices()

        # 1. Point cloud (and optional pre-coloured E57 cloud)
        e57_colours: 'np.ndarray | None' = None
        if dataset.platform == 'e57':
            xyz, e57_colours = _extract_e57_cloud(dataset)
        else:
            xyz = self._get_point_cloud(dataset, valid_frames)

        # 2. Colourisation
        if e57_colours is not None:
            colours = e57_colours
            log.info('Using embedded E57 RGB colours — skipping camera reprojection')
        else:
            colours = _colorize_cloud(
                xyz, dataset, valid_frames, self.device,
                stride=self.colorise_stride,
            )

        # 3. Poisson reconstruction + texture bake
        if not _O3D:
            raise RuntimeError('open3d required for mesh reconstruction: pip install open3d')
        mesh = _poisson_mesh(xyz, colours, depth=self.poisson_depth)
        mesh, atlas = _bake_texture(mesh, xyz, colours, atlas_size=self.atlas_size)

        # 4. HDRI for environment light
        from .hdri import HDRIGenerator
        hdri_gen = HDRIGenerator(envmap_width, envmap_height, prefer_cuda=self.device.type == 'cuda')
        equirect  = hdri_gen.generate(dataset, hdri_frame)
        specular  = hdri_gen.to_cubemap(equirect)
        diffuse_e = hdri_gen.generate_diffuse(equirect)
        diffuse   = hdri_gen.to_cubemap(diffuse_e)
        spec_paths = hdri_gen.save_cubemap_hdr(specular, output_dir, 'envmap_spec')
        diff_paths = hdri_gen.save_cubemap_hdr(diffuse,  output_dir, 'envmap_diff')
        equirect_spec_path = output_dir / 'envmap_spec_equirect.hdr'
        equirect_diff_path = output_dir / 'envmap_diff_equirect.hdr'
        hdri_gen.save_equirect_hdr(equirect,  equirect_spec_path)
        hdri_gen.save_equirect_hdr(diffuse_e, equirect_diff_path)

        # 5. Export
        from .export import export_mesh
        out_path = export_mesh(
            mesh=mesh,
            atlas=atlas,
            spec_cubemap_paths=spec_paths,
            diff_cubemap_paths=diff_paths,
            equirect_spec_path=equirect_spec_path,
            equirect_diff_path=equirect_diff_path,
            output_dir=output_dir,
            stem=dataset.dataset_name,
            fmt=output_format,
            geo_origin=dataset.geo_origin(),
        )
        log.info('Mesh export complete → %s', out_path)
        return out_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_point_cloud(
        self, dataset: ScanDataset, valid_frames: list[int]
    ) -> np.ndarray:
        """Try LiDAR bag extraction; fall back to depth estimation."""
        bag = dataset.bag_path('trajectory_slam')
        xyz = _extract_lidar_from_bag(bag)
        if xyz is None:
            log.info('LiDAR bag extraction failed — using depth estimation fallback')
            xyz = _estimate_depth_gpu(
                dataset, valid_frames, self.device,
                stride=self.depth_fallback_stride,
            )
        # Voxel downsample for tractable reconstruction
        if _O3D:
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(xyz.astype(np.float64))
            pcd = pcd.voxel_down_sample(voxel_size=0.02)
            xyz = np.asarray(pcd.points).astype(np.float32)
            log.info('After voxel downsample: %d points', len(xyz))
        return xyz
