"""Offline SLAM back-end: submap segmentation + loop-closure pose-graph
optimisation for NavVis VLX "rec" (raw, unregistered) datasets.

NavVis's own on-device/cloud processing corrects the raw SLAM trajectory's
drift (mostly vertical, since the horizontal LiDAR scan-matching is largely
self-correcting but there's no absolute height reference) using a
Cartographer-style backend before producing a "registered" export. Raw "rec"
datasets shipped without that reprocessing only contain the *uncorrected*
trajectory, which can drift tens of metres in Z over a multi-minute scan.

This module reproduces the same class of correction from first principles:

1. Segment the LiDAR stream + raw trajectory into short, dead-reckoning-
   accurate "submaps" (a few seconds each).
2. Register consecutive submaps (odometry edges) and any spatially-close,
   non-adjacent submaps (loop-closure edges) with point-to-plane ICP.
3. Run global pose-graph optimisation (Open3D's implementation of
   Kümmerle et al.'s robust pose-graph SLAM) to find the rigid correction
   for every submap that best satisfies all pairwise constraints at once.
4. Apply the resulting per-submap correction back onto the original raw
   trajectory samples (interpolated across submap boundaries), producing a
   drift-corrected trajectory with the same interface as
   ``mesh_pipeline._read_slam_trajectory``.

The corrected trajectory is a drop-in replacement everywhere the raw
trajectory was previously used: LiDAR world-frame decoding *and* per-frame
camera pose lookup (via :meth:`SlamCorrection.correct_pose`).
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional

import numpy as np

from .dataset import _quat_to_rot, ScanDataset

log = logging.getLogger(__name__)

try:
    import open3d as o3d
    _O3D = True
except ImportError:
    _O3D = False


def _rot_to_quat(R: np.ndarray) -> np.ndarray:
    """3×3 rotation matrix → (w, x, y, z) quaternion."""
    m = R
    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0:
        S = math.sqrt(tr + 1.0) * 2
        qw = 0.25 * S
        qx = (m[2, 1] - m[1, 2]) / S
        qy = (m[0, 2] - m[2, 0]) / S
        qz = (m[1, 0] - m[0, 1]) / S
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        S = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        qw = (m[2, 1] - m[1, 2]) / S
        qx = 0.25 * S
        qy = (m[0, 1] + m[1, 0]) / S
        qz = (m[0, 2] + m[2, 0]) / S
    elif m[1, 1] > m[2, 2]:
        S = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        qw = (m[0, 2] - m[2, 0]) / S
        qx = (m[0, 1] + m[1, 0]) / S
        qy = 0.25 * S
        qz = (m[1, 2] + m[2, 1]) / S
    else:
        S = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        qw = (m[1, 0] - m[0, 1]) / S
        qx = (m[0, 2] + m[2, 0]) / S
        qy = (m[1, 2] + m[2, 1]) / S
        qz = 0.25 * S
    return np.array([qw, qx, qy, qz], dtype=np.float64)


def _slerp(q0: np.ndarray, q1: np.ndarray, t: float) -> np.ndarray:
    """Spherical linear interpolation between two (w,x,y,z) quaternions."""
    q0 = q0 / np.linalg.norm(q0)
    q1 = q1 / np.linalg.norm(q1)
    dot = float(np.dot(q0, q1))
    if dot < 0.0:
        q1 = -q1
        dot = -dot
    dot = min(1.0, max(-1.0, dot))
    if dot > 0.9995:
        out = q0 + t * (q1 - q0)
        return out / np.linalg.norm(out)
    theta0 = math.acos(dot)
    theta = theta0 * t
    q2 = q1 - q0 * dot
    q2 = q2 / np.linalg.norm(q2)
    return q0 * math.cos(theta) + q2 * math.sin(theta)


class Submap:
    """A short, internally-consistent chunk of the raw trajectory + LiDAR."""

    __slots__ = ('idx', 't_center', 'raw_pose', 'points_local', 'pcd')

    def __init__(self, idx: int, t_center: float, raw_pose: np.ndarray, points_local: np.ndarray):
        self.idx = idx
        self.t_center = t_center
        self.raw_pose = raw_pose          # 4x4, submap-local → world (raw/uncorrected)
        self.points_local = points_local  # (N,3) in submap-local frame
        self.pcd = None                   # lazily-built o3d.geometry.PointCloud


def _raw_pose_at(traj_ts: np.ndarray, traj_pos: np.ndarray, traj_q: np.ndarray, t_ns: int) -> np.ndarray:
    """Nearest-neighbour raw pose (4x4) at a given time, matching the lookup
    convention used elsewhere in the pipeline (``mesh_pipeline._decode_navvis_lidar``)."""
    idx = int(np.searchsorted(traj_ts, t_ns))
    idx = min(max(idx, 0), len(traj_ts) - 1)
    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = _quat_to_rot(traj_q[idx])
    T[:3, 3] = traj_pos[idx]
    return T


def build_submaps(
    packets_by_sensor: dict,
    traj: tuple,
    window_s: float = 3.0,
    voxel_size: float = 0.05,
) -> list[Submap]:
    """Bucket decoded LiDAR packets (in head frame) + the raw trajectory into
    fixed-duration submaps, each expressed in its own local reference frame.

    packets_by_sensor: {sensor_name: [(msg_ns, pts_head_frame), ...]}
    traj: (timestamps_ns, positions, quats_wxyz) — raw/uncorrected trajectory
    """
    traj_ts, traj_pos, traj_q = traj
    all_pkts = []
    for pkts in packets_by_sensor.values():
        all_pkts.extend(pkts)
    if not all_pkts:
        return []
    all_pkts.sort(key=lambda p: p[0])

    t0 = all_pkts[0][0]
    t1 = all_pkts[-1][0]
    window_ns = int(window_s * 1e9)
    n_windows = max(1, int((t1 - t0) / window_ns) + 1)

    submaps: list[Submap] = []
    pkt_i = 0
    for w in range(n_windows):
        w_start = t0 + w * window_ns
        w_end = w_start + window_ns
        window_pts_world = []
        window_ts = []
        while pkt_i < len(all_pkts) and all_pkts[pkt_i][0] < w_end:
            msg_ns, pts_head = all_pkts[pkt_i]
            if msg_ns >= w_start:
                T_raw = _raw_pose_at(traj_ts, traj_pos, traj_q, msg_ns)
                pts_world = pts_head @ T_raw[:3, :3].T + T_raw[:3, 3]
                window_pts_world.append(pts_world)
                window_ts.append(msg_ns)
            pkt_i += 1
        if not window_pts_world:
            continue
        pts_world = np.concatenate(window_pts_world, axis=0).astype(np.float64)
        t_center = int(np.median(window_ts))
        T_ref = _raw_pose_at(traj_ts, traj_pos, traj_q, t_center)
        # Re-express this submap's points in its own local frame (inverse of T_ref)
        pts_local = (pts_world - T_ref[:3, 3]) @ T_ref[:3, :3]
        if _O3D and voxel_size > 0:
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(pts_local)
            pcd = pcd.voxel_down_sample(voxel_size)
            pts_local = np.asarray(pcd.points)
        submaps.append(Submap(len(submaps), t_center, T_ref, pts_local.astype(np.float32)))

    log.info('SLAM backend: built %d submaps (window=%.1fs) from %d LiDAR messages',
              len(submaps), window_s, len(all_pkts))
    return submaps


def _submap_pcd(sm: Submap) -> 'o3d.geometry.PointCloud':
    if sm.pcd is None:
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(sm.points_local.astype(np.float64))
        pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.3, max_nn=30)
        )
        sm.pcd = pcd
    return sm.pcd


def _pairwise_icp(
    source: 'o3d.geometry.PointCloud',
    target: 'o3d.geometry.PointCloud',
    trans_init: np.ndarray,
    max_dist_coarse: float,
    max_dist_fine: float,
):
    icp_coarse = o3d.pipelines.registration.registration_icp(
        source, target, max_dist_coarse, trans_init,
        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
    )
    icp_fine = o3d.pipelines.registration.registration_icp(
        source, target, max_dist_fine, icp_coarse.transformation,
        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
    )
    information = o3d.pipelines.registration.get_information_matrix_from_point_clouds(
        source, target, max_dist_fine, icp_fine.transformation
    )
    return icp_fine, information


def optimize_pose_graph(
    submaps: list[Submap],
    loop_xy_radius: float = 3.0,
    min_loop_gap: int = 3,
    max_dist_coarse: float = 1.0,
    max_dist_fine: float = 0.1,
    fitness_threshold: float = 0.35,
) -> 'list[np.ndarray] | None':
    """Register submaps pairwise (odometry + loop closure) and globally
    optimise the pose graph. Returns a list of 4x4 correction matrices
    (one per submap, in the *same* per-submap local frame as ``Submap.raw_pose``)
    such that ``corrected_pose_i = correction_i @ raw_pose_i``, or None if
    Open3D is unavailable or too few submaps were found to optimise.
    """
    if not _O3D or len(submaps) < 2:
        return None

    n = len(submaps)
    pose_graph = o3d.pipelines.registration.PoseGraph()
    pose_graph.nodes.append(o3d.pipelines.registration.PoseGraphNode(np.eye(4)))

    odometry = np.eye(4)
    n_loop = 0
    for i in range(n - 1):
        src_pcd = _submap_pcd(submaps[i + 1])   # later submap = source
        tgt_pcd = _submap_pcd(submaps[i])       # earlier submap = target

        # Both submaps are expressed in their OWN local frame, so the initial
        # guess for the relative pose is the raw trajectory's own estimate of
        # submap (i+1) as seen from submap i's local frame — reliable over a
        # few seconds of dead reckoning.
        trans_init = np.linalg.inv(submaps[i].raw_pose) @ submaps[i + 1].raw_pose
        try:
            result, info = _pairwise_icp(src_pcd, tgt_pcd, trans_init, max_dist_coarse, max_dist_fine)
        except Exception as exc:
            log.warning('Odometry ICP %d→%d failed: %s', i, i + 1, exc)
            result = None
        transformation = result.transformation if result is not None else trans_init
        information = info if result is not None else np.eye(6)

        odometry = transformation @ odometry
        pose_graph.nodes.append(o3d.pipelines.registration.PoseGraphNode(np.linalg.inv(odometry)))
        pose_graph.edges.append(o3d.pipelines.registration.PoseGraphEdge(
            i, i + 1, transformation, information, uncertain=False))

    # Loop closures: any non-adjacent pair whose raw XY positions are close
    centers_xy = np.array([sm.raw_pose[:2, 3] for sm in submaps])
    for i in range(n):
        for j in range(i + min_loop_gap, n):
            if np.linalg.norm(centers_xy[i] - centers_xy[j]) > loop_xy_radius:
                continue
            src_pcd = _submap_pcd(submaps[j])
            tgt_pcd = _submap_pcd(submaps[i])
            # Coarse initial guess: align centroids only (rotation drift is
            # usually small relative to translation/Z drift over a long scan).
            src_centroid = np.asarray(src_pcd.points).mean(axis=0) if len(src_pcd.points) else np.zeros(3)
            tgt_centroid = np.asarray(tgt_pcd.points).mean(axis=0) if len(tgt_pcd.points) else np.zeros(3)
            trans_init = np.eye(4)
            trans_init[:3, 3] = tgt_centroid - src_centroid
            try:
                result, info = _pairwise_icp(
                    src_pcd, tgt_pcd, trans_init,
                    max_dist_coarse=max(2.0, loop_xy_radius), max_dist_fine=max_dist_fine,
                )
            except Exception:
                continue
            if result.fitness < fitness_threshold:
                continue
            pose_graph.edges.append(o3d.pipelines.registration.PoseGraphEdge(
                i, j, result.transformation, info, uncertain=True))
            n_loop += 1
            log.info('Loop closure %d↔%d accepted (fitness=%.2f, rmse=%.3f)',
                      i, j, result.fitness, result.inlier_rmse)

    log.info('SLAM backend: pose graph has %d nodes, %d odometry edges, %d loop closures',
              len(pose_graph.nodes), n - 1, n_loop)

    option = o3d.pipelines.registration.GlobalOptimizationOption(
        max_correspondence_distance=max_dist_fine,
        edge_prune_threshold=0.25,
        reference_node=0,
    )
    with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Error):
        o3d.pipelines.registration.global_optimization(
            pose_graph,
            o3d.pipelines.registration.GlobalOptimizationLevenbergMarquardt(),
            o3d.pipelines.registration.GlobalOptimizationConvergenceCriteria(),
            option,
        )

    # node.pose maps submap-local(i) → the graph's shared reference frame.
    # correction_i is defined so that corrected_pose_i = correction_i @ raw_pose_i,
    # i.e. correction_i = node_i.pose @ raw_pose_i^{-1} (both raw_pose_i and
    # node_i.pose already map submap-local(i) → world / graph-frame).
    corrections = []
    for i, sm in enumerate(submaps):
        node_pose = pose_graph.nodes[i].pose
        corrections.append(node_pose @ np.linalg.inv(sm.raw_pose))
    return corrections


class SlamCorrection:
    """Piecewise-smooth correction derived from optimised submap poses.

    Call :meth:`correct_pose` with any raw (position, rotation) pair and its
    capture timestamp (ns) to get the drift-corrected equivalent — used for
    both LiDAR points (via the corrected trajectory) and camera frame poses.
    """

    def __init__(self, submaps: list[Submap], corrections: list[np.ndarray]):
        self._t_center = np.array([sm.t_center for sm in submaps], dtype=np.int64)
        self._corrections = corrections

    def _weights(self, t_ns: int) -> tuple[int, int, float]:
        """Return (i0, i1, alpha) to blend corrections i0 and i1 for a given time."""
        idx = int(np.searchsorted(self._t_center, t_ns))
        if idx <= 0:
            return 0, 0, 0.0
        if idx >= len(self._t_center):
            i = len(self._t_center) - 1
            return i, i, 0.0
        i0, i1 = idx - 1, idx
        span = float(self._t_center[i1] - self._t_center[i0])
        alpha = 0.0 if span <= 0 else float(t_ns - self._t_center[i0]) / span
        return i0, i1, min(1.0, max(0.0, alpha))

    def correct_pose(self, pos: np.ndarray, R: np.ndarray, t_ns: int) -> tuple[np.ndarray, np.ndarray]:
        """Apply the (time-interpolated) drift correction to a raw (pos, R) pose."""
        i0, i1, alpha = self._weights(t_ns)
        C0, C1 = self._corrections[i0], self._corrections[i1]
        if i0 == i1 or alpha == 0.0:
            C = C0
        elif alpha == 1.0:
            C = C1
        else:
            q0 = _rot_to_quat(C0[:3, :3])
            q1 = _rot_to_quat(C1[:3, :3])
            q = _slerp(q0, q1, alpha)
            C = np.eye(4)
            C[:3, :3] = _quat_to_rot(q)
            C[:3, 3] = (1 - alpha) * C0[:3, 3] + alpha * C1[:3, 3]
        pos_c = C[:3, :3] @ pos + C[:3, 3]
        R_c = C[:3, :3] @ R
        return pos_c, R_c

    def correct_trajectory(self, traj: tuple) -> tuple:
        """Apply the correction to every sample of a raw trajectory tuple
        (timestamps_ns, positions, quats_wxyz), returning a corrected copy
        with the exact same interface as ``_read_slam_trajectory``."""
        traj_ts, traj_pos, traj_q = traj
        out_pos = np.empty_like(traj_pos)
        out_q = np.empty_like(traj_q)
        for k in range(len(traj_ts)):
            R = _quat_to_rot(traj_q[k])
            p_c, R_c = self.correct_pose(traj_pos[k], R, int(traj_ts[k]))
            out_pos[k] = p_c
            out_q[k] = _rot_to_quat(R_c)
        return traj_ts, out_pos, out_q


def compute_slam_correction(
    packets_by_sensor: dict,
    traj: tuple,
    window_s: float = 3.0,
    voxel_size: float = 0.05,
    loop_xy_radius: float = 3.0,
) -> Optional[SlamCorrection]:
    """Top-level entry point: build submaps, run pose-graph optimisation, and
    return a :class:`SlamCorrection`, or None if correction isn't possible
    (e.g. Open3D unavailable, or too little data to build ≥2 submaps)."""
    if not _O3D:
        log.warning('SLAM backend requires Open3D; skipping drift correction')
        return None
    submaps = build_submaps(packets_by_sensor, traj, window_s=window_s, voxel_size=voxel_size)
    if len(submaps) < 2:
        log.warning('SLAM backend: not enough submaps (%d) to optimise; skipping correction',
                    len(submaps))
        return None
    corrections = optimize_pose_graph(submaps, loop_xy_radius=loop_xy_radius)
    if corrections is None:
        return None
    return SlamCorrection(submaps, corrections)
