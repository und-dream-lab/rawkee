"""Textured polygon mesh pipeline for mobile LiDAR scan datasets.

Strategy
--------
1. Extract LiDAR point clouds from the SLAM ROS bag (PandarXTM laser_horiz +
   laser_vert).
2. Colorize point cloud: reproject each LiDAR point into every camera frame
   that sees it, average colour using inverse-distance weighting.
3. Run Open3D Poisson surface reconstruction on the coloured cloud.
4. UV unwrap and bake a texture atlas.
5. Export via scan.export in the requested format.
"""
from __future__ import annotations
import logging
import math
import struct
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
    bag_paths: 'Path | list[Path]',
    lidar_topics: tuple[str, ...] = ('/laser_horiz', '/laser_vert',
                                      '/velodyne_points', '/points_raw'),
    max_clouds: int = 500,
) -> Optional[np.ndarray]:
    """Return combined (N,3) float32 point cloud from one or more ROS1 bags, or None."""
    if not _ROSBAGS:
        log.warning('rosbags not installed — cannot read ROS bags: pip install rosbags')
        return None

    paths = [bag_paths] if isinstance(bag_paths, Path) else list(bag_paths)
    paths = [p for p in paths if p.exists()]
    if not paths:
        log.warning('No bag files found')
        return None

    clouds: list[np.ndarray] = []
    count = 0
    try:
        from rosbags.typesys import Stores, get_typestore
        ts = get_typestore(Stores.ROS1_NOETIC)
        for bag_path in paths:
            if count >= max_clouds:
                break
            try:
                with Rosbag1Reader(bag_path) as reader:
                    topics_in_bag = {c.topic for c in reader.connections}
                    active = [t for t in lidar_topics if t in topics_in_bag]
                    if not active:
                        log.debug('No LiDAR topics in %s (have: %s)', bag_path.name, topics_in_bag)
                        continue
                    log.info('Reading LiDAR from %s topics: %s', bag_path.name, active)
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
                log.warning('Bag read error %s: %s', bag_path.name, exc)
    except Exception as exc:
        log.warning('rosbags init error: %s', exc)
        return None

    if not clouds:
        return None
    combined = np.concatenate(clouds, axis=0)
    log.info('Extracted %d LiDAR clouds → %d points total', count, len(combined))
    return combined


# ---------------------------------------------------------------------------
# NavVis PandarXTM raw-packet decoder
# ---------------------------------------------------------------------------

_PANDAR_HDR   = 12      # constant header bytes per UDP packet
_PANDAR_BLKS  = 6       # data blocks per 820-byte packet
_PANDAR_CHS   = 32      # laser channels per block
_PANDAR_BSIZE = 130     # bytes per block: 2 (azimuth) + 32*4 (returns)
_PANDAR_PKT        = 820   # expected data bytes per UDP packet
_PANDAR_MIN_RANGE  = 0.5   # metres (NavVis Range/Minimum)
_PANDAR_MAX_RANGE  = 150.0 # metres (NavVis Range/Maximum)
# XTM sensor-housing offsets from Hesai SDK pandarGeneral_internal.h
_PANDAR_H = 0.0305   # horizontal aperture offset (metres)
_PANDAR_B = 0.013    # baseline aperture offset (metres)


def _navvis_lidar_extrinsic(dataset: ScanDataset) -> 'tuple[np.ndarray, np.ndarray] | None':
    """Return (position, quat_wxyz) of laser_horiz in device frame from sensor_frame.xml."""
    result = _navvis_lidar_extrinsics(dataset)
    return result.get('laser_horiz') or next(iter(result.values()), None) if result else None


def _navvis_lidar_extrinsics(dataset: ScanDataset) -> 'dict[str, tuple[np.ndarray, np.ndarray]]':
    """Return {sensor_name: (position, quat_wxyz)} for every laser sensor in sensor_frame.xml."""
    import xml.etree.ElementTree as ET
    xml_path = dataset.root / 'sensor_frame.xml'
    if not xml_path.exists():
        return {}
    result = {}
    try:
        root = ET.parse(xml_path).getroot()
        for laser in root.findall('.//VelodyneLaserModel'):
            name = laser.findtext('SensorName', '')
            if not name:
                continue
            pose = laser.find('Pose')
            if pose is None:
                continue
            pos_el = pose.find('position')
            ori_el = pose.find('orientation')
            if pos_el is None or ori_el is None:
                continue
            pos  = np.array([float(pos_el.findtext(k, '0')) for k in ('x', 'y', 'z')],
                            dtype=np.float64)
            quat = np.array([float(ori_el.findtext(k, '0')) for k in ('w', 'x', 'y', 'z')],
                            dtype=np.float64)
            result[name] = (pos, quat)
    except Exception as exc:
        log.warning('sensor_frame.xml read failed: %s', exc)
    return result


def _pandar_elevation_rad(bag_paths: list[Path]) -> 'np.ndarray | None':
    """Extract per-channel elevation angles from the ASCII calibration packet in a laser bag."""
    for bag_path in bag_paths:
        try:
            with Rosbag1Reader(bag_path) as reader:
                for conn, _ts, raw in reader.messages(connections=list(reader.connections)):
                    raw = bytes(raw)
                    off = 4 + 8  # seq + header stamp
                    fid_len = struct.unpack_from('<I', raw, off)[0]; off += 4
                    off += fid_len
                    n = struct.unpack_from('<I', raw, off)[0]; off += 4
                    for _ in range(n):
                        off += 8  # packet stamp
                        dl = struct.unpack_from('<I', raw, off)[0]; off += 4
                        pkt = raw[off:off + dl]; off += dl
                        off += 12  # size(4) + duration(8)
                        if dl != _PANDAR_PKT:
                            try:
                                text = bytes(pkt).decode('ascii')
                                rows = [ln.split(',') for ln in text.strip().splitlines()[1:]]
                                elevs = [float(r[1]) for r in rows if len(r) >= 2]
                                if len(elevs) == _PANDAR_CHS:
                                    return np.deg2rad(np.array(elevs, dtype=np.float32))
                            except Exception:
                                pass
        except Exception:
            pass
    return None


def _read_slam_trajectory(traj_path: Path) -> 'tuple[np.ndarray, np.ndarray, np.ndarray] | None':
    """Return (timestamps_ns, positions, quats_wxyz) from /trajectory in trajectory_slam.bag."""
    if not _ROSBAGS or not traj_path.exists():
        return None
    try:
        from rosbags.typesys import Stores, get_typestore
        ts = get_typestore(Stores.ROS1_NOETIC)
        stamps, positions, quats = [], [], []
        with Rosbag1Reader(traj_path) as reader:
            traj_conns = [c for c in reader.connections
                          if c.topic in ('trajectory', '/trajectory')]
            if not traj_conns:
                return None
            for conn, _, raw in reader.messages(connections=traj_conns):
                msg = ts.deserialize_ros1(raw, conn.msgtype)
                t_ns = int(msg.header.stamp.sec) * 1_000_000_000 + int(msg.header.stamp.nanosec)
                p, q = msg.pose.position, msg.pose.orientation
                stamps.append(t_ns)
                positions.append([p.x, p.y, p.z])
                quats.append([q.w, q.x, q.y, q.z])
        if not stamps:
            return None
        order = np.argsort(stamps)
        return (np.array(stamps)[order],
                np.array(positions, np.float64)[order],
                np.array(quats,     np.float64)[order])
    except Exception as exc:
        log.warning('Trajectory read failed: %s', exc)
        return None


def _decode_pandar_pkt(
    pkt: bytes,
    sin_elev: np.ndarray,
    cos_elev: np.ndarray,
) -> 'np.ndarray | None':
    """Decode one 820-byte PandarXTM packet to (M,3) float32 points in sensor frame."""
    buf = np.frombuffer(pkt, dtype=np.uint8)
    dis_mul = int(buf[9]) * 0.001  # chDisUnit from header byte 9 → metres per count
    xs, ys, zs = [], [], []
    for b in range(_PANDAR_BLKS):
        blk = _PANDAR_HDR + b * _PANDAR_BSIZE
        az_rad = math.radians((int(buf[blk]) | (int(buf[blk + 1]) << 8)) * 0.01)
        sin_az, cos_az = math.sin(az_rad), math.cos(az_rad)
        ch = buf[blk + 2 : blk + 2 + _PANDAR_CHS * 4].reshape(_PANDAR_CHS, 4)
        dist = (ch[:, 0].astype(np.uint32) + (ch[:, 1].astype(np.uint32) << 8)).astype(np.float32)
        d = dist * dis_mul
        valid = (dist > 0) & (d >= _PANDAR_MIN_RANGE) & (d <= _PANDAR_MAX_RANGE)
        d = d[valid]
        # XTM aperture-offset correction (azimuth offset is 0 for all XTM channels)
        d_c = d - _PANDAR_H * cos_elev[valid]
        r   = d_c * cos_elev[valid]
        xs.append(r * sin_az - _PANDAR_B * cos_az + _PANDAR_H * sin_az)
        ys.append(r * cos_az + _PANDAR_B * sin_az + _PANDAR_H * cos_az)
        zs.append(d_c * sin_elev[valid])
    if not xs:
        return None
    return np.stack([np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)], axis=-1)


def _decode_navvis_lidar(
    bag_paths: list[Path],
    traj_bag: Path,
    extr_pos: np.ndarray,
    extr_quat: np.ndarray,
    max_packets: int = 6000,
    sensor_name: str = 'laser_horiz',
) -> 'np.ndarray | None':
    """Decode NavVis PandarXTM bags → (N,3) float32 world-space point cloud."""
    if not _ROSBAGS:
        return None

    elev_rad = _pandar_elevation_rad(bag_paths)
    if elev_rad is None:
        log.warning('PandarXTM: calibration packet not found; using default elevation angles')
        elev_rad = np.deg2rad(np.linspace(19.5, -20.8, _PANDAR_CHS, dtype=np.float32))

    sin_elev = np.sin(elev_rad).astype(np.float32)
    cos_elev = np.cos(elev_rad).astype(np.float32)

    traj = _read_slam_trajectory(traj_bag)
    if traj is None:
        log.warning('No SLAM trajectory; LiDAR points will be in sensor frame only')

    R_extr = _quat_to_rot(extr_quat)
    t_extr = extr_pos

    all_pts: list[np.ndarray] = []
    count = 0

    # Filter bags to the requested sensor head
    key = sensor_name.split('_')[-1]   # 'horiz' or 'vert'
    sensor_bags = [p for p in bag_paths if key in p.name]
    decode_bags = sensor_bags if sensor_bags else bag_paths

    for bag_path in decode_bags:
        if count >= max_packets:
            break
        try:
            with Rosbag1Reader(bag_path) as reader:
                for conn, _bag_ts, raw in reader.messages(connections=list(reader.connections)):
                    if count >= max_packets:
                        break
                    raw = bytes(raw)
                    off = 4
                    h_secs  = struct.unpack_from('<I', raw, off)[0]; off += 4
                    h_nsecs = struct.unpack_from('<I', raw, off)[0]; off += 4
                    msg_ns  = int(h_secs) * 1_000_000_000 + int(h_nsecs)
                    fid_len = struct.unpack_from('<I', raw, off)[0]; off += 4
                    off += fid_len
                    n_pkts  = struct.unpack_from('<I', raw, off)[0]; off += 4

                    if traj is not None:
                        traj_ts, traj_pos, traj_q = traj
                        idx = int(np.searchsorted(traj_ts, msg_ns))
                        idx = min(max(idx, 0), len(traj_ts) - 1)
                        R_dev = _quat_to_rot(traj_q[idx])
                        t_dev = traj_pos[idx]
                    else:
                        R_dev = np.eye(3, dtype=np.float64)
                        t_dev = np.zeros(3, dtype=np.float64)

                    R_total = (R_dev @ R_extr).astype(np.float32)
                    t_total = (R_dev @ t_extr + t_dev).astype(np.float32)

                    for _ in range(n_pkts):
                        off += 8  # packet stamp
                        dl = struct.unpack_from('<I', raw, off)[0]; off += 4
                        pkt = raw[off:off + dl]; off += dl
                        off += 12  # size(4) + duration(8)
                        if dl != _PANDAR_PKT:
                            continue
                        pts = _decode_pandar_pkt(bytes(pkt), sin_elev, cos_elev)
                        if pts is not None and len(pts):
                            all_pts.append(pts @ R_total.T + t_total)
                            count += 1
        except Exception as exc:
            log.warning('PandarXTM decode error %s: %s', bag_path.name, exc)

    if not all_pts:
        return None
    combined = np.concatenate(all_pts, axis=0).astype(np.float32)
    log.info('PandarXTM [%s]: %d packets → %d points', sensor_name, count, len(combined))
    return combined


# ---------------------------------------------------------------------------
# Depth estimation fallback (Depth Anything V2 via transformers)
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Scan viewpoints
# ---------------------------------------------------------------------------

def _collect_scan_viewpoints(
    dataset: ScanDataset,
    max_viewpoints: int = 16,
) -> list:
    """Return (pos_ros, R_ros, description) for evenly-spaced valid frames."""
    try:
        valid = dataset.valid_frame_indices()
    except Exception:
        return []
    if not valid:
        return []
    step = max(1, len(valid) // max_viewpoints)
    result = []
    for fi in valid[::step][:max_viewpoints]:
        try:
            pos, R = dataset.frame_transform(fi)
            result.append((pos.copy(), R.copy(), f'Frame {fi}'))
        except Exception:
            pass
    return result


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

    # Pre-compute per-camera rotation (transposed: head→cam) and position tensors once
    cam_R_t   = [torch.tensor(c.R.T,      device=device, dtype=torch.float32) for c in dataset.cameras]
    cam_pos_t = [torch.tensor(c.position, device=device, dtype=torch.float32) for c in dataset.cameras]

    for fi in frame_indices[::stride]:
        head_pos, R_head = dataset.frame_transform(fi)
        head_pos_t = torch.tensor(head_pos, device=device, dtype=torch.float32)
        R_head_t   = torch.tensor(R_head.T, device=device, dtype=torch.float32)  # world→head

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


def _assign_vertex_colors(
    mesh: 'o3d.geometry.TriangleMesh',
    xyz: np.ndarray,
    colours: np.ndarray,
) -> 'o3d.geometry.TriangleMesh':
    """Transfer point-cloud colours to mesh vertices via weighted KD-tree lookup."""
    if not _O3D:
        raise RuntimeError('open3d required')
    verts   = np.asarray(mesh.vertices)
    vcolors = np.asarray(mesh.vertex_colors) if mesh.has_vertex_colors() else None
    if vcolors is None or len(vcolors) == 0:
        log.info('Projecting point-cloud colours to mesh vertices …')
        from scipy.spatial import cKDTree
        tree    = cKDTree(xyz)
        dists, idxs = tree.query(verts, k=4, workers=-1)
        weights = 1.0 / np.maximum(dists, 1e-6)
        weights /= weights.sum(axis=1, keepdims=True)
        vcolors = (weights[:, :, None] * colours[idxs]).sum(axis=1)
        mesh.vertex_colors = o3d.utility.Vector3dVector(np.clip(vcolors, 0, 1))
    return mesh


def _project_mesh_uvs_per_camera(
    mesh: 'o3d.geometry.TriangleMesh',
    dataset: 'ScanDataset',
    frame_indices: list,
    device: 'torch.device',
    max_dist: float = 30.0,
    stride: int = 10,
) -> list:
    """Project mesh vertices through each camera/frame and assign each triangle to its
    closest visible camera.  Returns a list of patch dicts:
      { tri_indices, uvs (M*3,2) [0,1] X3D, image (H,W,3) uint8 sRGB, label }
    """
    from .hdri import _load_image_hdr

    verts_ros = np.asarray(mesh.vertices)          # (V, 3) ROS world
    tris      = np.asarray(mesh.triangles)         # (T, 3)
    n_tris    = len(tris)
    c0, c1, c2 = tris[:, 0], tris[:, 1], tris[:, 2]

    best_dist = np.full(n_tris, np.inf, dtype=np.float32)
    best_ci   = np.full(n_tris, -1,    dtype=np.int32)
    best_fi   = np.full(n_tris, -1,    dtype=np.int32)
    # per-corner raw grid_sample UVs for the winning (ci, fi)
    best_uvs  = np.zeros((n_tris, 3, 2), dtype=np.float32)

    verts_t   = torch.from_numpy(verts_ros).float().to(device)
    cam_R_t   = [torch.tensor(c.R.T,      device=device, dtype=torch.float32) for c in dataset.cameras]
    cam_pos_t = [torch.tensor(c.position, device=device, dtype=torch.float32) for c in dataset.cameras]

    for fi in frame_indices[::stride]:
        head_pos, R_head = dataset.frame_transform(fi)
        head_pos_t = torch.tensor(head_pos, device=device, dtype=torch.float32)
        R_head_t   = torch.tensor(R_head.T, device=device, dtype=torch.float32)

        for ci, cam in enumerate(dataset.cameras):
            if not dataset.dng_path(fi, ci).exists():
                continue

            pts_head = (verts_t - head_pos_t) @ R_head_t
            pts_cam  = (pts_head - cam_pos_t[ci]) @ cam_R_t[ci]

            uvs_norm, vmask = cam.ocam.project_gpu(pts_cam, device)
            dist_all        = torch.norm(pts_cam, dim=-1)
            vmask           = vmask & (dist_all < max_dist)

            vm_np  = vmask.cpu().numpy()
            uvs_np = uvs_norm.cpu().numpy()
            dn_np  = dist_all.cpu().numpy()

            all_valid = vm_np[c0] & vm_np[c1] & vm_np[c2]
            if not all_valid.any():
                continue

            tri_dist = (dn_np[c0] + dn_np[c1] + dn_np[c2]) / 3.0
            improve  = all_valid & (tri_dist < best_dist)
            if not improve.any():
                continue

            best_dist[improve]   = tri_dist[improve]
            best_ci[improve]     = ci
            best_fi[improve]     = fi
            best_uvs[improve, 0] = uvs_np[c0][improve]
            best_uvs[improve, 1] = uvs_np[c1][improve]
            best_uvs[improve, 2] = uvs_np[c2][improve]

    covered   = best_ci >= 0
    patches   = []
    pair_set  = sorted(set(zip(best_ci[covered].tolist(), best_fi[covered].tolist())))

    for (ci, fi) in pair_set:
        sel   = (best_ci == ci) & (best_fi == fi)
        t_idx = np.where(sel)[0]

        # grid_sample (col_n, row_n): col_n=-1 left, +1 right; row_n=-1 top, +1 bottom
        # X3D UV: u=0 left, u=1 right; v=0 bottom, v=1 top  →  flip row axis
        uvc = best_uvs[t_idx]                           # (M, 3, 2)
        u   = (uvc[..., 0] + 1.0) * 0.5
        v   = (1.0 - uvc[..., 1]) * 0.5
        uvs = np.stack([u, v], axis=-1).reshape(-1, 2).astype(np.float32)

        dng = dataset.dng_path(fi, ci)
        try:
            img_lin = _load_image_hdr(dng)
            srgb    = np.where(img_lin <= 0.0031308,
                               img_lin * 12.92,
                               1.055 * np.power(np.clip(img_lin, 0, 1), 1.0 / 2.4) - 0.055)
            img     = (np.clip(srgb, 0, 1) * 255).astype(np.uint8)
        except Exception as exc:
            log.warning('Camera patch image fi=%d ci=%d: %s', fi, ci, exc)
            continue

        patches.append({
            'tri_indices': t_idx,
            'uvs':         uvs,
            'image':       img,
            'label':       f'cam{ci}_f{fi:04d}',
            'cam_idx':     ci,
            'frame_idx':   fi,
        })
        log.info('Patch cam%d_f%04d: %d triangles', ci, fi, len(t_idx))

    log.info('Camera UV projection: %d patches, %d/%d triangles covered',
             len(patches), int(covered.sum()), n_tris)
    return patches


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
        max_packets: int = 6000,
        prefer_cuda: bool = True,
    ) -> None:
        self.poisson_depth = poisson_depth
        self.atlas_size = atlas_size
        self.colorise_stride = colorise_stride
        self.max_packets = max_packets
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
            xyz = self._get_point_cloud(dataset, valid_frames, max_packets=self.max_packets)
        if e57_colours is not None:
            colours = e57_colours
            log.info('Using embedded E57 RGB colours — skipping camera reprojection')
        else:
            colours = _colorize_cloud(
                xyz, dataset, valid_frames, self.device,
                stride=self.colorise_stride,
            )

        # 3. Poisson reconstruction + per-camera UV projection
        if not _O3D:
            raise RuntimeError('open3d required for mesh reconstruction: pip install open3d')
        mesh = _poisson_mesh(xyz, colours, depth=self.poisson_depth)
        mesh = _assign_vertex_colors(mesh, xyz, colours)
        cam_patches = _project_mesh_uvs_per_camera(
            mesh, dataset, valid_frames, self.device,
            stride=self.colorise_stride,
        )

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
        viewpoints = _collect_scan_viewpoints(dataset)
        out_path = export_mesh(
            mesh=mesh,
            cam_patches=cam_patches,
            spec_cubemap_paths=spec_paths,
            diff_cubemap_paths=diff_paths,
            equirect_spec_path=equirect_spec_path,
            equirect_diff_path=equirect_diff_path,
            output_dir=output_dir,
            stem=dataset.dataset_name,
            fmt=output_format,
            geo_origin=dataset.geo_origin(),
            viewpoints=viewpoints,
        )
        log.info('Mesh export complete → %s', out_path)
        return out_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_point_cloud(
        self, dataset: ScanDataset, valid_frames: list[int], max_packets: int = 6000
    ) -> np.ndarray:
        bags = dataset.lidar_bag_paths()
        if not bags:
            raise RuntimeError(
                f'No LiDAR bag files found under {dataset.root / "internal"}. '
                'Expected bag_laser_horiz_*.bag / bag_laser_vert_*.bag in internal/bags/.'
            )

        # NavVis PandarXTM: decode both laser heads and merge before voxel downsample
        extrinsics = _navvis_lidar_extrinsics(dataset)
        if extrinsics:
            traj_bag = dataset.root / 'internal' / 'trajectory_slam.bag'
            head_pts = []
            for sensor_name, (extr_pos, extr_quat) in extrinsics.items():
                pts = _decode_navvis_lidar(bags, traj_bag, extr_pos, extr_quat,
                                           max_packets=max_packets, sensor_name=sensor_name)
                if pts is not None and len(pts):
                    head_pts.append(pts)
            if head_pts:
                xyz = np.concatenate(head_pts, axis=0)
                if _O3D:
                    pcd = o3d.geometry.PointCloud()
                    pcd.points = o3d.utility.Vector3dVector(xyz.astype(np.float64))
                    pcd = pcd.voxel_down_sample(voxel_size=0.02)
                    xyz = np.asarray(pcd.points).astype(np.float32)
                    log.info('After voxel downsample: %d points', len(xyz))
                return xyz
            log.warning('PandarXTM decode returned no points; falling back to PointCloud2 search')

        xyz = _extract_lidar_from_bag(bags)
        if xyz is None:
            raise RuntimeError(
                f'LiDAR extraction produced no points from {len(bags)} bag(s) in '
                f'{dataset.root / "internal" / "bags"}.'
            )
        # Voxel downsample for tractable reconstruction
        if _O3D:
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(xyz.astype(np.float64))
            pcd = pcd.voxel_down_sample(voxel_size=0.02)
            xyz = np.asarray(pcd.points).astype(np.float32)
            log.info('After voxel downsample: %d points', len(xyz))
        return xyz
