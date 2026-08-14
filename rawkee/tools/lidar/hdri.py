"""GPU-accelerated HDRI panorama generator from fisheye scan cameras.

Pipeline
--------
1. Load 4 DNG images as linear float32 HDR arrays (rawpy, CPU).
2. Build equirectangular ray grid on GPU (PyTorch).
3. Rotate rays to each camera frame using the frame pose + per-camera extrinsics.
4. Project rays via OCamModel on GPU (polynomial + affine, fully vectorised).
5. Bilinear sample each camera image on GPU (F.grid_sample).
6. Blend: weight by cosine of angle from optical axis; fill uncovered pixels with
   a neutral sky/floor gradient.
7. Optionally convolve a downsampled copy for the diffuse irradiance map.
8. Save equirectangular .hdr and cubemap faces for X3D ImageCubeMapTexture.
"""
from __future__ import annotations
import logging
import math
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import rawpy
    _RAWPY = True
except ImportError:
    _RAWPY = False

try:
    import imageio.v3 as iio
    _IMAGEIO = True
except ImportError:
    _IMAGEIO = False

try:
    import torch
    import torch.nn.functional as F
    _TORCH = True
except ImportError:
    _TORCH = False

from .dataset import ScanDataset, CameraModel

log = logging.getLogger(__name__)


def _warn_no_gpu(require: bool = False) -> None:
    """Print actionable GPU diagnostic and optionally raise."""
    lines = ['', 'WARNING: No CUDA GPU is available for the HDRI generator.']
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
        '  Continuing on CPU — HDRI generation will be slow.',
        '',
    ]
    print('\n'.join(lines), flush=True)
    if require:
        raise RuntimeError('A CUDA GPU is required but none is available.')

# Neutral fill: warm grey for the floor hemisphere, cool grey for the sky
_FLOOR_RGB = np.array([0.18, 0.16, 0.14], dtype=np.float32)
_SKY_RGB   = np.array([0.20, 0.22, 0.26], dtype=np.float32)

CUBEMAP_FACES = ['px', 'nx', 'py', 'ny', 'pz', 'nz']
_FACE_FORWARD = {
    'px': np.array([ 1,  0,  0]),
    'nx': np.array([-1,  0,  0]),
    'py': np.array([ 0,  1,  0]),
    'ny': np.array([ 0, -1,  0]),
    'pz': np.array([ 0,  0,  1]),
    'nz': np.array([ 0,  0, -1]),
}
_FACE_UP = {
    'px': np.array([0, -1, 0]),
    'nx': np.array([0, -1, 0]),
    'py': np.array([0,  0, 1]),
    'ny': np.array([0,  0,-1]),
    'pz': np.array([0, -1, 0]),
    'nz': np.array([0, -1, 0]),
}


def _get_device(prefer_cuda: bool = True) -> 'torch.device':
    if _TORCH and prefer_cuda and torch.cuda.is_available():
        dev = torch.device('cuda')
        p = torch.cuda.get_device_properties(0)
        log.info('GPU: %s  %d GB  sm_%d%d', p.name, p.total_memory >> 30, p.major, p.minor)
        if p.major >= 9:
            torch.cuda.set_per_process_memory_fraction(0.90)
            log.info('Unified-memory architecture detected — memory fraction set to 90%%')
        return dev
    _warn_no_gpu(require=False)
    return torch.device('cpu')


def _load_image_hdr(path: Path) -> np.ndarray:
    """Load any image format as linear float32 HDR (H, W, 3).

    DNG/RAW: decoded via rawpy (16-bit, no gamma).
    JPEG/TIFF/PNG: decoded via imageio, then sRGB inverse-gamma applied.
    """
    if path.suffix.lower() in ('.dng', '.nef', '.cr2', '.arw', '.raw', '.rw2'):
        if not _RAWPY:
            raise RuntimeError('rawpy is required for raw images: pip install rawpy')
        with rawpy.imread(str(path)) as raw:
            rgb = raw.postprocess(
                output_bps=16, no_auto_bright=True,
                use_camera_wb=True, gamma=(1, 1),
                output_color=rawpy.ColorSpace.sRGB,
            )
        return rgb.astype(np.float32) / 65535.0
    else:
        if not _IMAGEIO:
            raise RuntimeError('imageio is required: pip install imageio')
        img = iio.imread(str(path))
        if img.ndim == 2:
            img = np.stack([img, img, img], axis=-1)
        elif img.shape[2] == 4:
            img = img[:, :, :3]
        f = img.astype(np.float32) / 255.0
        # sRGB → linear
        return np.where(f <= 0.04045, f / 12.92, ((f + 0.055) / 1.055) ** 2.4)


# Keep legacy name as alias
_load_dng_hdr = _load_image_hdr


def _build_equirect_rays(width: int, height: int, device: 'torch.device') -> 'torch.Tensor':
    """Return (H, W, 3) unit directions for an equirectangular grid.

    Convention: X=East (right), Y=North (forward), Z=Up.
    Longitude ∈ [-π, π], Latitude ∈ [π/2, -π/2] (top row = zenith).
    """
    lon = torch.linspace(-math.pi, math.pi,  width,  device=device)
    lat = torch.linspace(math.pi / 2, -math.pi / 2, height, device=device)
    lat_g, lon_g = torch.meshgrid(lat, lon, indexing='ij')  # (H, W)
    cos_lat = torch.cos(lat_g)
    x = cos_lat * torch.cos(lon_g)
    y = cos_lat * torch.sin(lon_g)
    z = torch.sin(lat_g)
    return torch.stack([x, y, z], dim=-1)   # (H, W, 3)


def _neutral_fill(height: int, width: int) -> np.ndarray:
    """Generate a neutral sky-to-floor gradient as fallback for uncovered pixels."""
    t    = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None, None]
    fill = (1.0 - t) * np.array(_SKY_RGB,   dtype=np.float32) \
               + t   * np.array(_FLOOR_RGB, dtype=np.float32)
    return np.broadcast_to(fill, (height, width, 3)).copy()


def _equirect_to_cubemap_face(
    equirect: np.ndarray, face: str, face_size: int
) -> np.ndarray:
    """Sample equirectangular image into a single cubemap face."""
    H, W = equirect.shape[:2]
    fwd = _FACE_FORWARD[face].astype(np.float64)
    up  = _FACE_UP[face].astype(np.float64)
    right = np.cross(fwd, up)

    lin = np.linspace(-1, 1, face_size)
    gx, gy = np.meshgrid(lin, lin)              # (F, F)
    # Ray direction for each pixel on this face
    dirs = (fwd[None, None, :]
            + right[None, None, :] * gx[:, :, None]
            + up[None, None, :]    * gy[:, :, None])
    norms = np.linalg.norm(dirs, axis=-1, keepdims=True)
    dirs /= np.maximum(norms, 1e-8)

    lon = np.arctan2(dirs[..., 1], dirs[..., 0])           # [-π, π]
    lat = np.arcsin(np.clip(dirs[..., 2], -1, 1))           # [-π/2, π/2]
    u = ((lon / math.pi + 1.0) / 2.0 * (W - 1)).astype(np.float32)
    v = ((1.0 - (lat / (math.pi / 2) + 1.0) / 2.0) * (H - 1)).astype(np.float32)

    # Bilinear sampling
    u0 = np.clip(np.floor(u).astype(int), 0, W - 2)
    v0 = np.clip(np.floor(v).astype(int), 0, H - 2)
    fu = (u - u0)[..., None]
    fv = (v - v0)[..., None]
    face_img = (
        equirect[v0,     u0    ] * (1 - fu) * (1 - fv) +
        equirect[v0,     u0 + 1] *      fu  * (1 - fv) +
        equirect[v0 + 1, u0    ] * (1 - fu) *      fv  +
        equirect[v0 + 1, u0 + 1] *      fu  *      fv
    )
    return face_img.astype(np.float32)


class HDRIGenerator:
    """Generate georeferenced equirectangular HDRI from a NavVis capture frame."""

    def __init__(
        self,
        envmap_width: int = 4096,
        envmap_height: int = 2048,
        cubemap_size: int = 1024,
        diffuse_blur_passes: int = 4,
        prefer_cuda: bool = True,
    ) -> None:
        self.envmap_width  = envmap_width
        self.envmap_height = envmap_height
        self.cubemap_size  = cubemap_size
        self.diffuse_blur_passes = diffuse_blur_passes
        self.device = _get_device(prefer_cuda)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        dataset: ScanDataset,
        frame_idx: Optional[int] = None,
    ) -> np.ndarray:
        """Return an equirectangular HDR float32 image (H, W, 3).

        Uses the fisheye cameras at `frame_idx` (defaults to the dataset's
        central valid frame) to fill the sphere. Missing sectors are blended
        with a neutral sky/floor gradient.
        """
        if frame_idx is None:
            frame_idx = dataset.select_reference_frame()

        log.info('Generating HDRI from frame %d / %d', frame_idx, dataset.num_frames)

        head_pos, R_head = dataset.frame_transform(frame_idx)

        # Load DNG images as HDR float32 tensors on GPU
        images_gpu = []
        for ci, cam in enumerate(dataset.cameras):
            p = dataset.dng_path(frame_idx, ci)
            if not p.exists():
                p = dataset.image_path(frame_idx, ci)
            if not p.exists():
                log.warning('Missing DNG %s — camera %d skipped', p.name, ci)
                images_gpu.append(None)
                continue
            img_np = _load_image_hdr(p)
            # grid_sample expects (1, C, H, W)
            t = torch.from_numpy(img_np).to(self.device).permute(2, 0, 1).unsqueeze(0)
            images_gpu.append(t)
            log.debug('Loaded cam%d  %s', ci, p.name)

        # Build equirectangular ray grid
        rays = _build_equirect_rays(
            self.envmap_width, self.envmap_height, self.device
        )  # (H, W, 3)

        # Rotate world rays into camera-head frame (R_head^T maps world → head)
        R_head_t = torch.tensor(R_head.T, device=self.device, dtype=torch.float32)
        rays_head = rays @ R_head_t  # (H, W, 3)

        accum  = torch.zeros(self.envmap_height, self.envmap_width, 3, device=self.device)
        weight = torch.zeros(self.envmap_height, self.envmap_width,    device=self.device)

        for ci, cam in enumerate(dataset.cameras):
            if images_gpu[ci] is None:
                continue
            # Rotate from head frame to this camera's frame (R_cam.T maps head → cam)
            R_cam_t = torch.tensor(cam.R.T, device=self.device, dtype=torch.float32)
            rays_cam = (rays_head - torch.tensor(cam.position, device=self.device, dtype=torch.float32)) @ R_cam_t
            # (We only rotate direction for unprojection; position offset is negligible vs scene scale)
            rays_cam_dir = rays_head @ R_cam_t   # (H, W, 3)

            uvs, mask = cam.ocam.project_gpu(rays_cam_dir, self.device)  # (H,W,2), (H,W)

            # Cosine weight: prefer rays closer to optical axis (z < 0, negate for cos)
            cos_w = (-rays_cam_dir[..., 2]).clamp(min=0.0)   # (H, W)

            # grid_sample: input (1,C,H_img,W_img), grid (1,H,W,2)
            grid = uvs.unsqueeze(0)   # (1, H, W, 2)
            sampled = F.grid_sample(
                images_gpu[ci], grid, mode='bilinear',
                padding_mode='border', align_corners=True
            ).squeeze(0).permute(1, 2, 0)   # (H, W, 3)

            w = cos_w * mask.float()
            accum  += sampled * w.unsqueeze(-1)
            weight += w

        # Normalise blended pixels
        covered = weight > 1e-6
        result = torch.where(
            covered.unsqueeze(-1),
            accum / weight.unsqueeze(-1).clamp(min=1e-8),
            torch.zeros_like(accum),
        )

        # Fill uncovered pixels with neutral gradient
        fill_np = _neutral_fill(self.envmap_height, self.envmap_width)
        fill_t  = torch.from_numpy(fill_np).to(self.device)
        result = torch.where(covered.unsqueeze(-1), result, fill_t)

        equirect = result.cpu().numpy().astype(np.float32)
        log.info('HDRI generation complete  coverage=%.1f%%',
                 covered.float().mean().item() * 100)
        return equirect

    def to_cubemap(self, equirect: np.ndarray) -> dict[str, np.ndarray]:
        """Convert equirectangular HDR to a dict of 6 cubemap faces."""
        return {
            face: _equirect_to_cubemap_face(equirect, face, self.cubemap_size)
            for face in CUBEMAP_FACES
        }

    def generate_diffuse(self, equirect: np.ndarray) -> np.ndarray:
        """Return a blurred equirectangular map suitable for diffuse IBL."""
        if not _TORCH:
            return equirect
        t = torch.from_numpy(equirect).to(self.device).permute(2, 0, 1).unsqueeze(0)
        # Repeated box blur with large kernel approximates Lambertian convolution
        k = max(equirect.shape[1] // 32, 3) | 1   # odd kernel
        for _ in range(self.diffuse_blur_passes):
            t = F.avg_pool2d(
                F.pad(t, [k // 2] * 4, mode='circular'),
                kernel_size=k, stride=1, padding=0,
            )
        return t.squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.float32)

    # ------------------------------------------------------------------
    # Save helpers
    # ------------------------------------------------------------------

    def save_equirect_hdr(self, equirect: np.ndarray, path: Path) -> None:
        if not _IMAGEIO:
            raise RuntimeError('imageio is required: pip install imageio[freeimage]')
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        iio.imwrite(str(path), equirect, extension='.hdr')
        log.info('Saved equirectangular HDR → %s', path)

    def save_cubemap_hdr(
        self, cubemap: dict[str, np.ndarray], output_dir: Path, stem: str
    ) -> dict[str, Path]:
        if not _IMAGEIO:
            raise RuntimeError('imageio is required: pip install imageio[freeimage]')
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {}
        for face, img in cubemap.items():
            p = output_dir / f'{stem}_{face}.hdr'
            iio.imwrite(str(p), img, extension='.hdr')
            paths[face] = p
        log.info('Saved cubemap faces → %s/%s_*.hdr', output_dir, stem)
        return paths
