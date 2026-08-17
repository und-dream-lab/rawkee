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


# ---------------------------------------------------------------------------
# Sky background helpers
# ---------------------------------------------------------------------------

def _build_sky_panorama(
    dataset: ScanDataset,
    panorama_width: int = 1024,
    panorama_height: int = 512,
) -> 'Optional[np.ndarray]':
    """Return a tone-mapped equirectangular (H, W, 3) uint8 in ROS Z-up convention.

    Used as the training background; kept separate from the cubemap export.
    """
    try:
        from .hdri import HDRIGenerator
        gen = HDRIGenerator(panorama_width, panorama_height, prefer_cuda=False)
        frame_idx = dataset.select_reference_frame()
        eq_hdr = gen.generate(dataset, frame_idx)          # (H, W, 3) float32
        eq_ldr = np.clip(eq_hdr / (1.0 + eq_hdr), 0.0, 1.0)
        return (eq_ldr * 255).astype(np.uint8)
    except Exception as exc:
        log.warning('Sky panorama generation failed: %s', exc)
        return None


def _build_sky_cubemap(
    equirect_ldr: np.ndarray,
    output_dir: Path,
    stem: str,
    face_size: int = 512,
) -> 'Optional[dict[str, Path]]':
    """Convert a ROS Z-up equirectangular panorama to 6 PNG cube face images
    oriented for the X3D Background node (Y-up convention).

    Returns a dict mapping X3D face name → Path, or None on failure.

    Mapping from X3D face to ROS ENU look direction / image-up direction:
      front  → look +Y (North),   up = +Z (sky)
      back   → look -Y (South),   up = +Z (sky)
      left   → look -X (West),    up = +Z (sky)
      right  → look +X (East),    up = +Z (sky)
      top    → look +Z (sky),     up = +Y (North/forward in X3D)
      bottom → look -Z (ground),  up = -Y (South/backward in X3D)
    """
    try:
        from PIL import Image as _PIL
        H, W = equirect_ldr.shape[:2]
        eq = equirect_ldr.astype(np.float32) / 255.0

        # (fwd_in_ROS, up_in_ROS) for each X3D face
        x3d_faces: dict[str, tuple[np.ndarray, np.ndarray]] = {
            'front':  (np.array([ 0.,  1.,  0.]), np.array([0., 0., 1.])),
            'back':   (np.array([ 0., -1.,  0.]), np.array([0., 0., 1.])),
            'left':   (np.array([-1.,  0.,  0.]), np.array([0., 0., 1.])),
            'right':  (np.array([ 1.,  0.,  0.]), np.array([0., 0., 1.])),
            'top':    (np.array([ 0.,  0.,  1.]), np.array([0., 1., 0.])),
            'bottom': (np.array([ 0.,  0., -1.]), np.array([0.,-1., 0.])),
        }

        lin = np.linspace(-1.0, 1.0, face_size, dtype=np.float32)
        gx, gy = np.meshgrid(lin, lin)   # (F, F)  gx=right, gy=up in image

        face_paths: dict[str, Path] = {}
        for face_name, (fwd, up) in x3d_faces.items():
            right_vec = np.cross(fwd, up)
            dirs = (fwd[None, None, :]
                    + right_vec[None, None, :] * gx[:, :, None]
                    + up[None, None, :]        * gy[:, :, None])
            norms = np.linalg.norm(dirs, axis=-1, keepdims=True)
            dirs /= np.maximum(norms, 1e-8)

            # ROS ENU: lon = atan2(Y,X), lat = arcsin(Z)
            lon = np.arctan2(dirs[..., 1], dirs[..., 0])
            lat = np.arcsin(np.clip(dirs[..., 2], -1.0, 1.0))
            u = ((lon / np.pi + 1.0) / 2.0 * (W - 1)).astype(np.float32)
            v = ((1.0 - (lat / (np.pi * 0.5) + 1.0) / 2.0) * (H - 1)).astype(np.float32)

            u0 = np.clip(np.floor(u).astype(int), 0, W - 2)
            v0 = np.clip(np.floor(v).astype(int), 0, H - 2)
            fu = (u - u0)[..., None]
            fv = (v - v0)[..., None]
            face_img = (
                eq[v0,     u0    ] * (1 - fu) * (1 - fv) +
                eq[v0,     u0 + 1] *      fu  * (1 - fv) +
                eq[v0 + 1, u0    ] * (1 - fu) *      fv  +
                eq[v0 + 1, u0 + 1] *      fu  *      fv
            )
            p = Path(output_dir) / f'{stem}_sky_{face_name}.jpg'
            _PIL.fromarray((face_img.clip(0, 1) * 255).astype(np.uint8)).save(p, quality=90)
            face_paths[face_name] = p

        log.info('Sky cubemap built: 6 × %dx%d faces', face_size, face_size)
        return face_paths
    except Exception as exc:
        log.warning('Sky cubemap build failed: %s', exc)
        return None


def _project_sky_backgrounds(
    panorama: np.ndarray,
    Rs: list['np.ndarray'],
    ts: list['np.ndarray'],
    img_wh: tuple[int, int],
    apply_coord_transform: bool,
    device: 'torch.device',
) -> 'list[torch.Tensor]':
    """Project equirectangular panorama through each camera to produce per-image
    background tensors (3, H, W) in [0, 1] for the gsplat rasterizer.

    For sky pixels (no Gaussian coverage) the rasterizer composites the
    Gaussian render on top of these backgrounds via alpha blending.
    """
    W, H = img_wh
    pan_h, pan_w = panorama.shape[:2]
    pan_t = torch.from_numpy(panorama.astype(np.float32) / 255.0
                             ).to(device).permute(2, 0, 1).unsqueeze(0)  # (1,3,H,W)

    # Build normalised pixel grid [–1,1] for the training image resolution
    ys = torch.linspace(-1, 1, H, device=device)
    xs = torch.linspace(-1, 1, W, device=device)
    grid_y, grid_x = torch.meshgrid(ys, xs, indexing='ij')  # (H, W)

    backgrounds = []
    _ROS_TO_X3D_t = torch.tensor(
        [[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=torch.float32, device=device
    )

    for R_wc, t_wc in zip(Rs, ts):
        # Build camera-to-world rotation: R_wc is world→cam, so cam→world = R_wc.T
        R_cw = torch.tensor(R_wc.T, dtype=torch.float32, device=device)  # (3,3)

        # Pixel ray directions in camera frame (pinhole, normalised)
        ray_x = grid_x.reshape(-1)          # (N,)
        ray_y = -grid_y.reshape(-1)         # flip Y: image top = +Y camera
        ray_z = torch.full_like(ray_x, -1.0)
        rays_cam = torch.stack([ray_x, ray_y, ray_z], dim=-1)             # (N,3)
        norms = rays_cam.norm(dim=-1, keepdim=True).clamp_min(1e-9)
        rays_cam = rays_cam / norms

        # Rotate rays to world frame
        rays_world = rays_cam @ R_cw.T                                     # (N,3)

        # Optionally un-rotate back to ROS frame if coords were transformed
        if apply_coord_transform:
            # The training is in X3D Y-up; panorama is in ROS Z-up.
            # Un-apply _ROS_TO_X3D to get ROS-frame directions for panorama lookup.
            rays_world = rays_world @ _ROS_TO_X3D_t.T

        # Spherical coordinates → equirectangular UV
        X, Y, Z = rays_world[:, 0], rays_world[:, 1], rays_world[:, 2]
        lon = torch.atan2(Y, X)                                            # [-π, π]
        lat = torch.asin(Z.clamp(-1.0, 1.0))                              # [-π/2, π/2]

        u = lon / math.pi                                                  # [-1, 1]
        v = lat / (math.pi / 2)                                            # [-1, 1]
        grid = torch.stack([u, v], dim=-1).reshape(1, H, W, 2)            # (1,H,W,2)

        sky = F.grid_sample(pan_t, grid, mode='bilinear',
                            padding_mode='border', align_corners=True)     # (1,3,H,W)
        backgrounds.append(sky.squeeze(0))                                 # (3,H,W)

    return backgrounds


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

    Uses world2cam[1], the derivative dr/dtheta at theta=0, which equals the
    effective focal length in pixels.  world2cam[0] is the constant term (~0).
    """
    f = abs(float(ocam.world2cam[1]))
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
) -> tuple[list['torch.Tensor'], list[np.ndarray], list[np.ndarray], list[tuple[float,float]]]:
    """Load images and poses; also returns per-image (fx, fy) at target_size."""
    images, Rs, ts, focals = [], [], [], []
    cam = dataset.cameras[cam_idx]
    # OCamModel has cam2world polynomial; PinholeModel does not
    is_ocam = hasattr(cam.ocam, 'cam2world')

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
            h_src, w_src = rgb8.shape[:2]
            if is_ocam:
                # Fisheye (OCamModel): full undistortion remap
                img = _undistort_ocam(rgb8, cam.ocam, target_size)
                fx_t = abs(float(cam.ocam.world2cam[1])) * target_size / cam.ocam.width
                focal_t = (fx_t, fx_t)
            else:
                # Pinhole (COLMAP/Metashape): simple resize; compute per-axis focal
                img = np.array(_PILImage.fromarray(rgb8).resize(
                    (target_size, target_size), _PILImage.LANCZOS))
                fx_t = cam.ocam.world2cam[0] * target_size / w_src
                fy_t = cam.ocam.world2cam[0] * target_size / h_src
                focal_t = (float(abs(fx_t)), float(abs(fy_t)))
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
            focals.append(focal_t)
        except Exception as exc:
            log.debug('Skip frame %d cam %d: %s', fi, cam_idx, exc)

    log.info('Loaded %d training images for cam%d', len(images), cam_idx)
    return images, Rs, ts, focals


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

    # Identity quaternion (x, y, z, w) — w in last position, matching xyzw storage convention
    quats = torch.zeros(N, 4, dtype=torch.float32, device=device)
    quats[:, 3] = 1.0

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
    focal: 'tuple[float, float] | list[tuple[float, float]]',
    img_wh: tuple[int, int],
    device: 'torch.device',
    iterations: int = 10_000,
    densify_every: int = 100,
    densify_until: int = -1,   # -1 = auto: min(iterations//2, 15000)
    rank: int = 0,
    world_size: int = 1,
    sh_degree: int = 3,
    backgrounds: 'Optional[list[torch.Tensor]]' = None,
    densify_grad_mode: str = '2d',   # '2d' = screen-space (robust for masked training); '3d' = world-space
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

    W, H = img_wh

    if densify_until < 0:
        # -1 = auto: half of iterations, no hard cap (caller sets their own limit via densify_until)
        densify_until = iterations // 2
    local_images = images[rank::world_size]
    local_Rs     = Rs[rank::world_size]
    local_ts     = ts[rank::world_size]
    # Support per-image focal lengths (list of (fx,fy)) or a single shared focal
    if isinstance(focal, list):
        local_focals = focal[rank::world_size]
    else:
        local_focals = [focal] * len(local_images)
    local_bgs = backgrounds[rank::world_size] if backgrounds else None
    if not local_images:
        raise RuntimeError(f'Rank {rank} received no training images (total={len(images)}, world={world_size})')

    # Make Gaussian parameters trainable
    params = {k: nn.Parameter(v.clone()) for k, v in gaussians.items()}

    # Position LR decays from 1.6e-4 → 1.6e-6 over `iterations` steps (paper schedule)
    _lr_means_init  = 1.6e-4
    _lr_means_final = 1.6e-6
    _lr_means_gamma = (_lr_means_final / _lr_means_init) ** (1.0 / max(iterations, 1))

    def _make_opt():
        return torch.optim.Adam([
            {'params': [params['means']],      'lr': _lr_means_init},
            {'params': [params['log_scales']], 'lr': 5e-3},
            {'params': [params['quats']],      'lr': 1e-3},
            {'params': [params['sh_coeffs']],  'lr': 2.5e-3},
            {'params': [params['opacities']],  'lr': 5e-2},
        ])

    def _make_schedulers(opt):
        # Per-parameter-group schedulers: only positions decay aggressively
        pos_sched   = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=_lr_means_gamma)
        other_sched = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.9999)
        return pos_sched, other_sched

    # Pre-compute intrinsics and pose tensors to avoid per-iteration allocation
    def _make_K(fx, fy):
        return torch.tensor([[fx, 0, W / 2], [0, fy, H / 2], [0, 0, 1]],
                            device=device, dtype=torch.float32).unsqueeze(0)
    K_tensors = [_make_K(f[0], f[1]) for f in local_focals]
    R_tensors = [torch.tensor(r, device=device, dtype=torch.float32).unsqueeze(0)
                 for r in local_Rs]
    t_tensors = [torch.tensor(t_, device=device, dtype=torch.float32).unsqueeze(0)
                 for t_ in local_ts]

    # Probe whether gsplat supports absgrad (2D screen-space gradient mode)
    _absgrad_supported = False
    if densify_grad_mode == '2d':
        try:
            import inspect as _inspect
            _absgrad_supported = 'absgrad' in _inspect.signature(rasterization).parameters
        except Exception:
            pass
        if not _absgrad_supported:
            log.warning('gsplat does not support absgrad — falling back to 3D gradient mode')
            densify_grad_mode = '3d'

    opt = _make_opt()
    pos_sched, other_sched = _make_schedulers(opt)

    # Per-Gaussian 2D-gradient accumulator for adaptive density control
    _grads2d   = torch.zeros(len(params['means']), device=device)
    _grads2d_n = 0

    # SH degree curriculum: start at 0, +1 every 1000 steps up to target sh_degree
    _active_sh = 0

    # Scene extent for large-Gaussian pruning (10% of extent = max allowed scale)
    _cam_positions = torch.stack([
        (-torch.tensor(r, device=device).T @ torch.tensor(t_, device=device))
        for r, t_ in zip(local_Rs, local_ts)
    ])
    _scene_extent = float((_cam_positions.max(dim=0).values - _cam_positions.min(dim=0).values).norm())
    _max_scale    = _scene_extent * 0.1   # prune Gaussians larger than 10% of scene

    N_local = len(local_images)
    if rank == 0:
        log.info('Training %d Gaussians for %d iterations  world_size=%d  local_cams=%d',
                 len(params['means']), iterations, world_size, N_local)

    for step in range(1, iterations + 1):
        # SH degree curriculum: increase active degree every 1000 steps
        _active_sh = min(sh_degree, (step - 1) // 1000)

        ci     = step % N_local
        img_gt = local_images[ci].unsqueeze(0).to(device)
        R      = R_tensors[ci]
        t      = t_tensors[ci]
        K      = K_tensors[ci]
        bg_img = local_bgs[ci].unsqueeze(0) if local_bgs else None

        scales_exp  = torch.exp(params['log_scales'])
        quats_n     = F.normalize(params['quats'].clamp(min=-1e6, max=1e6), dim=-1)
        opacities_a = torch.sigmoid(params['opacities'])

        Rt     = torch.cat([R, t.unsqueeze(-1)], dim=-1)          # (1, 3, 4)
        bottom = torch.tensor([[[0., 0., 0., 1.]]], device=device) # (1, 1, 4)
        _use_absgrad = _absgrad_supported and step < densify_until
        rendered, alpha, _info = rasterization(
            means=params['means'], quats=quats_n, scales=scales_exp,
            opacities=opacities_a, colors=params['sh_coeffs'],
            viewmats=torch.cat([Rt, bottom], dim=1),               # (1, 4, 4)
            Ks=K, width=W, height=H, sh_degree=_active_sh, packed=True,
            **({'absgrad': True} if _use_absgrad else {}),
        )
        # retain_grad on means2d so .grad is available after backward
        # regardless of gsplat version (1.5.x removed the .absgrad attribute)
        _means2d = _info.get('means2d') if _info else None
        if _use_absgrad and _means2d is not None:
            _means2d.retain_grad()
        rendered = rendered.permute(0, 3, 1, 2).clamp(0, 1)       # (1,3,H,W)

        if bg_img is not None:
            # Composite Gaussians over the sky background: out = render + (1-alpha)*sky
            alpha_map = alpha.permute(0, 3, 1, 2).clamp(0, 1)     # (1,1,H,W)
            rendered = rendered + (1.0 - alpha_map) * bg_img

        loss = 0.8 * F.l1_loss(rendered, img_gt) + 0.2 * _ssim_loss(rendered, img_gt)
        opt.zero_grad()
        loss.backward()

        # Accumulate per-Gaussian gradient norms for adaptive density control
        if step < densify_until:
            with torch.no_grad():
                g = None
                if _use_absgrad:
                    # 2D screen-space gradients: use .grad on the retained means2d tensor.
                    # gsplat 1.5.x removed the .absgrad attribute; .retain_grad() + .grad
                    # is the version-agnostic approach.
                    means2d  = _means2d
                    gauss_ids = _info.get('gaussian_ids') if _info else None
                    if (means2d is not None and means2d.grad is not None):
                        g_packed = means2d.grad.detach().abs().norm(dim=-1)  # (M,)
                        if gauss_ids is not None and len(gauss_ids) > 0:
                            N = len(params['means'])
                            g = torch.zeros(N, device=device)
                            g.scatter_add_(0, gauss_ids.long().clamp(0, N - 1), g_packed)
                        elif g_packed.shape[0] == len(params['means']):
                            g = g_packed
                if g is None and params['means'].grad is not None:
                    # 3D fallback when absgrad unavailable or returns nothing
                    g = params['means'].grad.detach().norm(dim=-1)
                if g is not None and g.shape[0] == _grads2d.shape[0]:
                    _grads2d.add_(g)
                    _grads2d_n += 1

        # Average gradients across ranks before the optimiser step
        if world_size > 1:
            _dist_all_reduce_grads(params, world_size)

        opt.step()
        # Step position LR separately from other params
        pos_sched.step()
        other_sched.step()

        if step % 500 == 0 and rank == 0:
            log.info('step %5d / %d  loss=%.5f  N=%d',
                     step, iterations, loss.item(), len(params['means']))

        # Adaptive density control: clone + split + prune
        if step % densify_every == 0 and step < densify_until:
            with torch.no_grad():
                N      = len(params['means'])
                opac   = torch.sigmoid(params['opacities'])
                scales = torch.exp(params['log_scales'])
                max_sc = scales.amax(dim=-1)

                avg_grad   = _grads2d[:N] / max(_grads2d_n, 1)
                # Catch all Gaussians above the mean gradient (paper uses fixed 2e-4;
                # mean×1.5 is adaptive and equivalent for any scene scale)
                grad_thresh = avg_grad.mean().item() * 1.5
                high_grad  = avg_grad > max(grad_thresh, 1e-10)
                clone_mask = high_grad & (max_sc < 0.05)
                split_mask = high_grad & (max_sc >= 0.05)
                log.info('Density ctrl @ %d: %d → %d  (clone=%d, split=%d, prune=%d)'
                         '  grad_n=%d  avg_max=%.2e  avg_mean=%.2e  scale_mean=%.4f',
                         step, N, N,
                         clone_mask.sum().item(), split_mask.sum().item(),
                         (prune_mask := (opac < 0.005) | (max_sc > _max_scale)).sum().item(),
                         _grads2d_n, avg_grad.max().item(), avg_grad.mean().item(),
                         max_sc.mean().item())
                # Prune: too transparent OR too large (> 10% scene extent)
                prune_mask = (opac < 0.005) | (max_sc > _max_scale)
                keep_mask  = ~prune_mask

                # Split: replace each large high-grad Gaussian with 2 smaller ones
                sp: dict = {}
                if split_mask.any():
                    q   = params['quats'][split_mask]          # (M, 4) xyzw
                    qx, qy, qz, qw = q[:,0], q[:,1], q[:,2], q[:,3]
                    # Rotation matrix columns from quaternion
                    Rc = torch.stack([
                        torch.stack([1-2*(qy*qy+qz*qz), 2*(qx*qy+qz*qw), 2*(qx*qz-qy*qw)], -1),
                        torch.stack([2*(qx*qy-qz*qw),   1-2*(qx*qx+qz*qz), 2*(qy*qz+qx*qw)], -1),
                        torch.stack([2*(qx*qz+qy*qw),   2*(qy*qz-qx*qw), 1-2*(qx*qx+qy*qy)], -1),
                    ], -1)                                       # (M, 3, 3)
                    sc   = scales[split_mask]
                    pai  = sc.argmax(dim=-1)                    # principal axis index
                    pdir = Rc[torch.arange(Rc.shape[0]), :, pai]  # (M, 3)
                    psc  = sc[torch.arange(sc.shape[0]), pai]     # (M,)
                    off  = pdir * (psc * 0.8).unsqueeze(-1)       # (M, 3)
                    sm   = params['means'][split_mask]
                    new_ls = torch.log((sc / 1.6).clamp_min(1e-10))
                    sp['means']      = torch.cat([sm + off, sm - off])
                    sp['log_scales'] = torch.cat([new_ls, new_ls])
                    sp['quats']      = torch.cat([params['quats'][split_mask]] * 2)
                    sp['sh_coeffs']  = torch.cat([params['sh_coeffs'][split_mask]] * 2)
                    sp['opacities']  = torch.full((2 * split_mask.sum().item(),), -3.0, device=device)

                # Build updated param tensors
                for k in params:
                    pieces = [params[k][keep_mask]]
                    if clone_mask.any():
                        pieces.append(params[k][clone_mask])
                    if k in sp:
                        pieces.append(sp[k])
                    params[k] = nn.Parameter(torch.cat(pieces))

                _grads2d   = torch.zeros(len(params['means']), device=device)
                _grads2d_n = 0

                if world_size > 1:
                    dist.barrier()
                    for p in params.values():
                        dist.broadcast(p.data, src=0)

                opt = _make_opt()
                pos_sched, other_sched = _make_schedulers(opt)
                _n_clone = clone_mask.sum().item()
                _n_split = split_mask.sum().item()
                _n_prune = prune_mask.sum().item()

            if rank == 0:
                log.info('Density ctrl @ %d: %d → %d  (clone=%d, split=%d, prune=%d)',
                         step, N, len(params['means']), _n_clone, _n_split, _n_prune)

        # Opacity reset: only after meaningful densification has occurred.
        # Resetting while N is still at the sparse-init count kills gradients —
        # near-zero opacities cause the packed rasterizer to skip all Gaussians,
        # returning a constant zero image with no gradient to params['means'].
        if step % 1500 == 0 and step < densify_until and len(params['means']) > 2000:
            with torch.no_grad():
                params['opacities'].fill_(math.log(0.01 / 0.99))  # sigmoid^-1(0.01)
            if rank == 0:
                log.info('Opacity reset @ step %d', step)

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
        densify_grad_mode: str = '2d',
        densify_until: int = -1,
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

        # 1. Initialise from LiDAR, COLMAP sparse cloud, or random fallback
        xyz = None
        bags = dataset.lidar_bag_paths()
        if bags:
            if dataset.platform == 'navvis':
                # Use NavVis PandarXTM decoder with per-sensor extrinsics for better alignment
                from .mesh_pipeline import _navvis_lidar_extrinsics, _decode_navvis_lidar
                extrinsics = _navvis_lidar_extrinsics(dataset)
                if extrinsics:
                    traj_bag = dataset.root / 'internal' / 'trajectory_slam.bag'
                    head_pts = []
                    for sensor_name, (extr_pos, extr_quat) in extrinsics.items():
                        pts = _decode_navvis_lidar(bags, traj_bag, extr_pos, extr_quat,
                                                   max_packets=200, sensor_name=sensor_name)
                        if pts is not None and len(pts):
                            head_pts.append(pts)
                    if head_pts:
                        xyz = np.concatenate(head_pts, axis=0)
                        log.info('NavVis PandarXTM init: %d points from %d sensor(s)',
                                 len(xyz), len(head_pts))
            if xyz is None:
                xyz = _extract_lidar_from_bag(bags, max_clouds=200)
        if (xyz is None or len(xyz) < 1000) and dataset.platform in ('colmap', 'metashape', 'meshroom', 'pix4d'):
            # Use the COLMAP/SfM sparse point cloud instead of random init
            from .dataset import ScanDataset as _SD
            try:
                sparse_dir = _SD._colmap_find_sparse(dataset.root)
                from .colmap_splat_pipeline import _load_sparse_points
                xyz = _load_sparse_points(sparse_dir)
                if xyz is not None and len(xyz) > 0:
                    log.info('Initialising from %d SfM sparse points', len(xyz))
            except Exception as exc:
                log.debug('SfM sparse init failed: %s', exc)
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
            if len(xyz) > self.init_points:
                idx = np.random.choice(len(xyz), self.init_points, replace=False)
                xyz = xyz[idx]
            gaussians = _init_gaussians_from_pcd(xyz, self.device, self.sh_degree)

        # 2. Load training data (all cameras combined) with per-camera focal lengths
        all_images, all_Rs, all_ts, all_focals = [], [], [], []
        for cam_idx in range(len(dataset.cameras)):
            imgs, Rs, ts, focs = _load_training_images(
                dataset, frames, cam_idx, self.image_size, self.device
            )
            all_images.extend(imgs)
            all_Rs.extend(Rs)
            all_ts.extend(ts)
            all_focals.extend(focs)

        if not all_images:
            raise RuntimeError('No training images could be loaded')

        # Defined early — needed by both sky projection and export
        ros_origin = (dataset.platform == 'navvis')

        # Build sky panorama for outdoor/NavVis scenes — used as training background
        # and written to the X3D output so viewers show it behind the Gaussians.
        sky_panorama: Optional[np.ndarray] = None
        all_backgrounds: Optional[list] = None
        sky_face_paths: Optional[dict] = None
        if dataset.platform == 'navvis':
            sky_panorama = _build_sky_panorama(dataset)
            if sky_panorama is not None:
                log.info('Sky panorama built (%dx%d) — using as training background',
                         sky_panorama.shape[1], sky_panorama.shape[0])
                all_backgrounds = _project_sky_backgrounds(
                    sky_panorama, all_Rs, all_ts,
                    img_wh=(self.image_size, self.image_size),
                    apply_coord_transform=ros_origin,
                    device=self.device,
                )
                # Build cubemap faces for X3D Background node export
                sky_face_paths = _build_sky_cubemap(
                    sky_panorama, Path(output_dir), dataset.dataset_name,
                )

        # 3. Train
        rank, world_size = _dist_init()
        try:
            trained = _train(
                gaussians, all_images, all_Rs, all_ts,
                focal=all_focals,
                img_wh=(self.image_size, self.image_size),
                device=self.device,
                iterations=self.iterations,
                rank=rank,
                world_size=world_size,
                sh_degree=self.sh_degree,
                backgrounds=all_backgrounds,
                densify_grad_mode=densify_grad_mode,
                densify_until=densify_until,
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
            apply_coord_transform=ros_origin,
            sky_face_paths=sky_face_paths,
        )
        log.info('Splat export complete → %s', out_path)
        return out_path
