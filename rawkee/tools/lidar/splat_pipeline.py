"""Gaussian splat pipeline for mobile LiDAR scan datasets.

Strategy
--------
1. Prepare training cameras: load DNG frames, extract poses, build
   a pinhole camera approximation from the OCamModel for the gsplat rasteriser.
2. Initialise Gaussians from the LiDAR point cloud (if available) or from
   random sampling on a unit sphere scaled to the scene bounding box.
3. Train with the gsplat rasteriser:
      - photometric L1 + SSIM loss
      - adaptive density control (split/clone/prune)
4. Export via scan.export.
"""
from __future__ import annotations
import logging
import math
import os
from pathlib import Path
from typing import Optional

import numpy as np

# Ensure the ninja binary bundled with the Python package is on PATH so that
# PyTorch CUDA JIT (which calls `ninja --version` via subprocess) can find it.
try:
    import ninja as _ninja_pkg
    _ninja_bin_dir = _ninja_pkg.BIN_DIR
    if _ninja_bin_dir not in os.environ.get('PATH', ''):
        os.environ['PATH'] = _ninja_bin_dir + os.pathsep + os.environ.get('PATH', '')
except (ImportError, AttributeError):
    pass

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    _TORCH = True
except ImportError:
    _TORCH = False

try:
    from gsplat import rasterization
    _GSPLAT = True
except ImportError:
    _GSPLAT = False
except RuntimeError as _gsplat_err:
    # gsplat found but CUDA JIT compilation failed — ninja is the usual culprit
    _GSPLAT = False
    _GSPLAT_ERR = str(_gsplat_err)

try:
    import open3d as o3d
    _O3D = True
except ImportError:
    _O3D = False

from .dataset import ScanDataset
from .mesh_pipeline import _extract_lidar_from_bag

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


# ---------------------------------------------------------------------------
# Distributed process group helpers
# ---------------------------------------------------------------------------

def _dist_init() -> tuple[int, int]:
    """Initialise torch.distributed if launched via torchrun; return (rank, world_size)."""
    import os
    rank       = int(os.environ.get('RANK',       0))
    world_size = int(os.environ.get('WORLD_SIZE', 1))
    if world_size > 1:
        import torch.distributed as dist
        if not dist.is_initialized():
            dist.init_process_group(
                backend='nccl',
                timeout=__import__('datetime').timedelta(minutes=30),
            )
        log.info('Distributed: rank %d / %d', rank, world_size)
    return rank, world_size


def _dist_teardown() -> None:
    """Destroy the process group if it was initialised."""
    try:
        import torch.distributed as dist
        if dist.is_initialized():
            dist.destroy_process_group()
    except ImportError:
        pass


def _dist_all_reduce_grads(params: dict, world_size: int) -> None:
    """Average gradients across all ranks after backward."""
    import torch.distributed as dist
    for p in params.values():
        if p.grad is not None:
            dist.all_reduce(p.grad, op=dist.ReduceOp.AVG)


# ---------------------------------------------------------------------------
# Device setup (shared pattern with mesh_pipeline)
# ---------------------------------------------------------------------------

def _get_device() -> 'torch.device':
    if _TORCH and torch.cuda.is_available():
        p = torch.cuda.get_device_properties(0)
        log.info('Splat pipeline GPU: %s  sm_%d%d', p.name, p.major, p.minor)
        if p.major >= 9:
            torch.cuda.set_per_process_memory_fraction(0.85)
        return torch.device('cuda')
    _warn_no_gpu('Gaussian splat', require=True)


# ---------------------------------------------------------------------------
# Camera preparation
# ---------------------------------------------------------------------------

def _ocam_to_pinhole_approx(ocam) -> tuple[float, float, float, float]:
    """Approximate OCamModel as a pinhole camera (fx, fy, cx_col, cy_row).

    Uses the world2cam polynomial at theta=0 (on-axis) to derive focal length.
    """
    # world2cam[0] is the on-axis mapping coefficient (scale at centre of FOV)
    f = abs(float(ocam.world2cam[0]))
    return f, f, float(ocam.cy), float(ocam.cx)   # fx, fy, cx_col, cy_row


def _undistort_ocam(img_rgb8: np.ndarray, ocam, target_size: int) -> np.ndarray:
    """Remap a fisheye OCam image to a pinhole image matching _ocam_to_pinhole_approx."""
    fx, _, _, _ = _ocam_to_pinhole_approx(ocam)
    # Scale focal length to output image size (consistent with how training K is built)
    f_out = fx * target_size / ocam.width
    half  = target_size * 0.5

    u = np.arange(target_size, dtype=np.float64)
    v = np.arange(target_size, dtype=np.float64)
    uu, vv = np.meshgrid(u, v)          # uu[row, col]=col, vv[row, col]=row

    # OCam: X_cam -> row direction, Y_cam -> col direction, Z < 0 = forward
    X_cam = (vv - half) / f_out         # row  -> X
    Y_cam = (uu - half) / f_out         # col  -> Y
    Z_cam = -np.ones_like(X_cam)
    norms = np.sqrt(X_cam**2 + Y_cam**2 + 1.0)
    xyz   = np.stack([X_cam.ravel() / norms.ravel(),
                      Y_cam.ravel() / norms.ravel(),
                      Z_cam.ravel() / norms.ravel()], axis=-1)

    uv_src, _valid = ocam.project(xyz)  # (N, 2) col, row in source image
    map_col = uv_src[:, 0].reshape(target_size, target_size).astype(np.float32)
    map_row = uv_src[:, 1].reshape(target_size, target_size).astype(np.float32)

    try:
        import cv2
        return cv2.remap(img_rgb8, map_col, map_row, cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    except ImportError:
        # Nearest-neighbour fallback when OpenCV is absent
        col_i = np.clip(map_col.ravel().round().astype(np.int32), 0, ocam.width  - 1)
        row_i = np.clip(map_row.ravel().round().astype(np.int32), 0, ocam.height - 1)
        out   = img_rgb8[row_i, col_i].reshape(target_size, target_size, 3)
        return out


def _load_training_images(
    dataset: ScanDataset,
    frame_indices: list[int],
    cam_idx: int,
    target_size: int = 512,
    device: 'torch.device' = None,
) -> tuple[list['torch.Tensor'], list[np.ndarray], list[np.ndarray]]:
    """Load DNG images and poses for one camera into GPU tensors.

    Returns:
        images  – list of (3, H, W) float32 tensors on device
        Rs      – list of (3,3) rotation matrices (world → camera)
        ts      – list of (3,) translation vectors (camera origin in world)
    """
    images, Rs, ts = [], [], []
    cam = dataset.cameras[cam_idx]

    for fi in frame_indices:
        img_path = dataset.image_path(fi, cam_idx)
        if not img_path.exists():
            continue
        try:
            # Support DNG/RAW and standard JPEG/TIFF
            from PIL import Image as _PILImage
            if img_path.suffix.lower() in ('.dng', '.nef', '.cr2', '.arw', '.raw', '.rw2'):
                try:
                    import rawpy
                except ImportError as exc:
                    raise ImportError(
                        f'rawpy is required to load RAW images ({img_path.name}): pip install rawpy'
                    ) from exc
                try:
                    with rawpy.imread(str(img_path)) as raw:
                        rgb8 = raw.postprocess(output_bps=8, use_camera_wb=True)
                except Exception:
                    preview = img_path.parent / 'preview' / (img_path.stem + '.jpg')
                    if not preview.exists():
                        raise
                    rgb8 = np.array(_PILImage.open(preview).convert('RGB'))
            else:
                rgb8 = np.array(_PILImage.open(img_path).convert('RGB'))
            # Undistort fisheye images; fall back to simple resize for pinhole cameras
            if hasattr(cam.ocam, 'unproject'):
                img = _undistort_ocam(rgb8, cam.ocam, target_size)
            else:
                img = np.array(_PILImage.fromarray(rgb8).resize((target_size, target_size)))
            img_t = torch.from_numpy(img).float().div(255.0).permute(2, 0, 1)
            if device is not None:
                img_t = img_t.to(device)
            images.append(img_t)

            # Pose: world → camera
            head_pos, R_head = dataset.frame_transform(fi)
            # R_head rotates head→world; we need world→cam = (R_head @ R_cam)^T
            R_head_to_world = R_head                   # (3,3) cols are head-axes in world
            R_cam_to_head   = cam.R                    # (3,3)
            R_cam_to_world  = R_head_to_world @ R_cam_to_head
            R_world_to_cam  = R_cam_to_world.T
            # Camera origin in world = head_pos + R_head @ cam.position
            cam_origin = head_pos + R_head @ cam.position
            t_world_to_cam = -R_world_to_cam @ cam_origin

            Rs.append(R_world_to_cam.astype(np.float32))
            ts.append(t_world_to_cam.astype(np.float32))
        except Exception as exc:
            log.debug('Skip frame %d cam %d: %s', fi, cam_idx, exc)

    log.info('Loaded %d training images for cam%d', len(images), cam_idx)
    return images, Rs, ts


# ---------------------------------------------------------------------------
# Gaussian initialisation
# ---------------------------------------------------------------------------

def _init_gaussians_from_pcd(
    xyz: np.ndarray,
    device: 'torch.device',
    sh_degree: int = 3,
) -> dict[str, 'torch.Tensor']:
    """Initialise Gaussian parameters from an (N,3) point cloud."""
    N = len(xyz)
    means = torch.tensor(xyz, dtype=torch.float32, device=device)

    # Estimate initial scale from nearest-neighbour distance
    if _O3D and N > 1000:
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(xyz.astype(np.float64))
        pcd = pcd.voxel_down_sample(0.05)
        pts_ds = np.asarray(pcd.points)
        from scipy.spatial import cKDTree
        tree = cKDTree(pts_ds)
        d, _ = tree.query(pts_ds, k=2)
        nn_dist = float(np.median(d[:, 1]))
    else:
        nn_dist = 0.05

    nn_dist = max(nn_dist, 1e-6)
    log_scale_val = math.log(nn_dist)
    log_scales = torch.full((N, 3), log_scale_val, dtype=torch.float32, device=device)

    # Identity quaternion (w, x, y, z)
    quats = torch.zeros(N, 4, dtype=torch.float32, device=device)
    quats[:, 0] = 1.0

    # Initialise SH DC with grey; higher-order = 0
    n_sh = (sh_degree + 1) ** 2
    sh_coeffs = torch.zeros(N, n_sh, 3, dtype=torch.float32, device=device)
    # DC=0 decodes to rgb=0.5 (grey) via: rgb = dc * sh0 + 0.5

    # Opacity: inverse-sigmoid of 0.1
    opacities = torch.full((N,), math.log(0.1 / (1 - 0.1)), dtype=torch.float32, device=device)

    return {
        'means':      means,
        'log_scales': log_scales,
        'quats':      quats,
        'sh_coeffs':  sh_coeffs,
        'opacities':  opacities,
    }


def _random_init_gaussians(
    n: int,
    scene_bbox: tuple[np.ndarray, np.ndarray],
    device: 'torch.device',
    sh_degree: int = 3,
) -> dict[str, 'torch.Tensor']:
    """Initialise Gaussians randomly within scene bounding box."""
    lo, hi = scene_bbox
    xyz = np.random.uniform(lo, hi, (n, 3)).astype(np.float32)
    return _init_gaussians_from_pcd(xyz, device, sh_degree)


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def _pcd_to_gaussians_direct(
    xyz: np.ndarray,
    colors: 'np.ndarray | None',
    device: 'torch.device',
    sh_degree: int = 3,
) -> dict[str, 'torch.Tensor']:
    """Convert a colored point cloud to Gaussian parameters without training.

    One Gaussian per point: scale from nearest-neighbour distance, opacity=0.99,
    color from RGB (DC SH coefficient). Exports valid splats instantly.
    """
    gaussians = _init_gaussians_from_pcd(xyz, device, sh_degree)
    if colors is not None:
        sh0 = 0.28209479177387814  # 1 / (2*sqrt(pi))
        dc  = (torch.from_numpy(colors.astype(np.float32)).to(device) - 0.5) / sh0
        gaussians['sh_coeffs'][:, 0, :] = dc
    # Set fully opaque (inverse sigmoid of 0.99)
    gaussians['opacities'][:] = math.log(0.99 / 0.01)
    return {k: v.detach() for k, v in gaussians.items()}


def _ssim_loss(pred: 'torch.Tensor', target: 'torch.Tensor') -> 'torch.Tensor':
    """Simple patch-based SSIM approximation."""
    mu1 = F.avg_pool2d(pred,   11, 1, 5)
    mu2 = F.avg_pool2d(target, 11, 1, 5)
    s1  = F.avg_pool2d(pred   ** 2, 11, 1, 5) - mu1 ** 2
    s2  = F.avg_pool2d(target ** 2, 11, 1, 5) - mu2 ** 2
    s12 = F.avg_pool2d(pred * target,  11, 1, 5) - mu1 * mu2
    C1, C2 = 0.01 ** 2, 0.03 ** 2
    ssim = ((2 * mu1 * mu2 + C1) * (2 * s12 + C2)) / (
        (mu1 ** 2 + mu2 ** 2 + C1) * (s1 + s2 + C2)
    )
    return 1 - ssim.mean()


def _train(
    gaussians: dict[str, 'torch.Tensor'],
    images: list['torch.Tensor'],
    Rs: list[np.ndarray],
    ts: list[np.ndarray],
    focal: tuple[float, float],
    img_wh: tuple[int, int],
    device: 'torch.device',
    iterations: int = 10_000,
    densify_every: int = 500,
    densify_until: int = 7_000,
    rank: int = 0,
    world_size: int = 1,
    sh_degree: int = 3,
) -> dict[str, 'torch.Tensor']:
    """3DGS training loop using gsplat rasteriser, with optional multi-node DDP."""
    if not _GSPLAT:
        err = globals().get('_GSPLAT_ERR', '')
        if 'ninja' in err.lower():
            raise RuntimeError(
                'gsplat CUDA JIT compilation failed — ninja build tool is missing.\n'
                'Fix:  pip install ninja\n'
                'ninja is a small (~1 MB) C++ build helper, not a language model.'
            )
        raise RuntimeError('gsplat required: pip install gsplat')

    if world_size > 1:
        import torch.distributed as dist

    fx, fy = focal
    W, H   = img_wh

    # Each rank trains on its own image shard
    local_images = images[rank::world_size]
    local_Rs     = Rs[rank::world_size]
    local_ts     = ts[rank::world_size]
    if not local_images:
        raise RuntimeError(f'Rank {rank} received no training images (total={len(images)}, world={world_size})')

    # Make Gaussian parameters trainable
    params = {k: nn.Parameter(v.clone()) for k, v in gaussians.items()}

    def _make_opt():
        return torch.optim.Adam([
            {'params': [params['means']],      'lr': 1.6e-4},
            {'params': [params['log_scales']], 'lr': 5e-3},
            {'params': [params['quats']],      'lr': 1e-3},
            {'params': [params['sh_coeffs']],  'lr': 2.5e-3},
            {'params': [params['opacities']],  'lr': 5e-2},
        ])

    # Pre-compute intrinsics and pose tensors to avoid per-iteration allocation
    K = torch.tensor([[fx, 0, W / 2], [0, fy, H / 2], [0, 0, 1]],
                      device=device, dtype=torch.float32).unsqueeze(0)
    R_tensors = [torch.tensor(r, device=device, dtype=torch.float32).unsqueeze(0)
                 for r in local_Rs]
    t_tensors = [torch.tensor(t_, device=device, dtype=torch.float32).unsqueeze(0)
                 for t_ in local_ts]

    opt = _make_opt()
    scheduler = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.999)

    N_local = len(local_images)
    if rank == 0:
        log.info('Training %d Gaussians for %d iterations  world_size=%d  local_cams=%d',
                 len(params['means']), iterations, world_size, N_local)

    for step in range(1, iterations + 1):
        ci     = step % N_local
        img_gt = local_images[ci].unsqueeze(0).to(device)
        R      = R_tensors[ci]
        t      = t_tensors[ci]

        scales_exp  = torch.exp(params['log_scales'])
        quats_n     = F.normalize(params['quats'].clamp(min=-1e6, max=1e6), dim=-1)
        opacities_a = torch.sigmoid(params['opacities'])

        Rt     = torch.cat([R, t.unsqueeze(-1)], dim=-1)          # (1, 3, 4)
        bottom = torch.tensor([[[0., 0., 0., 1.]]], device=device) # (1, 1, 4)
        rendered, _, _ = rasterization(
            means=params['means'], quats=quats_n, scales=scales_exp,
            opacities=opacities_a, colors=params['sh_coeffs'],
            viewmats=torch.cat([Rt, bottom], dim=1),               # (1, 4, 4)
            Ks=K, width=W, height=H, sh_degree=sh_degree, packed=True,
        )
        rendered = rendered.permute(0, 3, 1, 2).clamp(0, 1)

        loss = 0.8 * F.l1_loss(rendered, img_gt) + 0.2 * _ssim_loss(rendered, img_gt)
        opt.zero_grad()
        loss.backward()

        # Average gradients across ranks before the optimiser step
        if world_size > 1:
            _dist_all_reduce_grads(params, world_size)

        opt.step()
        scheduler.step()

        if step % 500 == 0 and rank == 0:
            log.info('step %5d / %d  loss=%.5f  N=%d',
                     step, iterations, loss.item(), len(params['means']))

        # Adaptive density control
        if step % densify_every == 0 and step < densify_until:
            with torch.no_grad():
                if world_size > 1:
                    dist.barrier()  # ensure all ranks finish their optimizer step first
                    keep = torch.zeros(len(params['means']), dtype=torch.bool, device=device)
                    if rank == 0:
                        keep = torch.sigmoid(params['opacities']) > 0.005
                    dist.broadcast(keep, src=0)
                else:
                    keep = torch.sigmoid(params['opacities']) > 0.005

                for k in params:
                    params[k] = nn.Parameter(params[k][keep])

                # After pruning, broadcast rank-0 data so all ranks stay identical
                if world_size > 1:
                    for p in params.values():
                        dist.broadcast(p.data, src=0)

                opt = _make_opt()
                scheduler = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.999)
            if rank == 0:
                log.info('Density control: %d Gaussians remaining', keep.sum().item())

    return {k: v.detach() for k, v in params.items()}


# ---------------------------------------------------------------------------
# Public pipeline class
# ---------------------------------------------------------------------------

class SplatPipeline:
    """End-to-end scan dataset → Gaussian splat pipeline."""

    def __init__(
        self,
        image_size: int = 512,
        sh_degree: int = 3,
        iterations: int = 10_000,
        frame_stride: int = 5,
        init_points: int = 100_000,
        prefer_cuda: bool = True,
    ) -> None:
        self.image_size  = image_size
        self.sh_degree   = sh_degree
        self.iterations  = iterations
        self.frame_stride = frame_stride
        self.init_points = init_points
        self.device      = _get_device() if prefer_cuda else torch.device('cpu')

    def run(
        self,
        dataset: ScanDataset,
        output_dir: Path,
        output_format: str = 'x3d',
        trimble_csv: Optional[Path] = None,
        georef_epsg: int = 32605,
        decode_sh: bool = False,
    ) -> Path:
        """Run the full Gaussian splat pipeline and export.

        Parameters
        ----------
        dataset:       ScanDataset instance.
        output_dir:    Directory to write output file(s).
        output_format: One of x3d | x3dv | x3dj | ply | splat | glb.
        trimble_csv:   Optional path to a Trimble survey CSV for georeferencing.
        georef_epsg:   Target projected CRS (default 32605 = UTM Zone 5N).
        decode_sh:     When True and output_format is ply, pre-decode SH coefficients
                       to linear RGB so consumers without SH support see correct colours.
        """
        if not _TORCH:
            raise RuntimeError('PyTorch is required for Gaussian splat training')
        if not _GSPLAT:
            raise RuntimeError('gsplat is required: pip install gsplat')

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if trimble_csv is not None:
            dataset.apply_trimble_georef(trimble_csv, epsg=georef_epsg)

        # E57 without embedded images: bypass training entirely
        if dataset.platform == 'e57' and not dataset.has_training_images():
            log.info('E57 input with no training images — using direct point-cloud-to-splat conversion')
            xyz, colors = dataset.e57_point_cloud()
            if len(xyz) > self.init_points:
                idx = np.random.choice(len(xyz), self.init_points, replace=False)
                xyz    = xyz[idx]
                colors = colors[idx] if colors is not None else None
            trained = _pcd_to_gaussians_direct(xyz, colors, self.device, self.sh_degree)
            from .export import export_splat
            out_path = export_splat(
                gaussians=trained, output_dir=output_dir,
                stem=dataset.dataset_name, fmt=output_format,
                sh_degree=self.sh_degree, geo_origin=dataset.geo_origin(),
                decode_sh=decode_sh,
            )
            log.info('E57 direct splat export → %s', out_path)
            return out_path

        valid = dataset.valid_frame_indices()
        frames = valid[::self.frame_stride]
        log.info('Training on %d frames (every %dth of %d valid)',
                 len(frames), self.frame_stride, len(valid))

        # 1. Initialise from LiDAR or fallback
        xyz = None
        bags = dataset.lidar_bag_paths()
        if bags:
            xyz = _extract_lidar_from_bag(bags, max_clouds=200)
        if xyz is None or len(xyz) < 1000:
            # Compute scene bbox from frame positions
            positions = np.array([dataset.frame_position(fi) for fi in valid])
            lo = positions.min(axis=0) - 3.0
            hi = positions.max(axis=0) + 3.0
            log.info('Random Gaussian init within bbox %s … %s', lo, hi)
            gaussians = _random_init_gaussians(
                self.init_points, (lo, hi), self.device, self.sh_degree
            )
        else:
            # Subsample LiDAR to init_points
            if len(xyz) > self.init_points:
                idx = np.random.choice(len(xyz), self.init_points, replace=False)
                xyz = xyz[idx]
            gaussians = _init_gaussians_from_pcd(xyz, self.device, self.sh_degree)

        # 2. Load training data (all 4 cameras combined)
        all_images, all_Rs, all_ts = [], [], []
        for cam_idx in range(len(dataset.cameras)):
            imgs, Rs, ts = _load_training_images(
                dataset, frames, cam_idx, self.image_size, self.device
            )
            all_images.extend(imgs)
            all_Rs.extend(Rs)
            all_ts.extend(ts)

        if not all_images:
            raise RuntimeError('No training images could be loaded')

        # Approximate focal length from cam0
        cam0 = dataset.cameras[0]
        fx, fy, _, _ = _ocam_to_pinhole_approx(cam0.ocam)
        scale = self.image_size / cam0.ocam.width
        focal = (fx * scale, fy * scale)

        # 3. Train
        rank, world_size = _dist_init()
        try:
            trained = _train(
                gaussians, all_images, all_Rs, all_ts,
                focal=focal,
                img_wh=(self.image_size, self.image_size),
                device=self.device,
                iterations=self.iterations,
                rank=rank,
                world_size=world_size,
                sh_degree=self.sh_degree,
            )
        finally:
            _dist_teardown()

        # 4. Only rank 0 exports
        if rank != 0:
            return Path(output_dir)
        from .export import export_splat
        from .mesh_pipeline import _collect_scan_viewpoints
        viewpoints = _collect_scan_viewpoints(dataset)
        out_path = export_splat(
            gaussians=trained,
            output_dir=output_dir,
            stem=dataset.dataset_name,
            fmt=output_format,
            sh_degree=self.sh_degree,
            geo_origin=dataset.geo_origin(),
            decode_sh=decode_sh,
            viewpoints=viewpoints,
        )
        log.info('Splat export complete → %s', out_path)
        return out_path
