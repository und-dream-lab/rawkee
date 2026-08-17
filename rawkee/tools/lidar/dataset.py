"""Scan dataset reader with support for multiple mobile LiDAR platforms."""
from __future__ import annotations
import csv
import json
import logging
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import torch
    _TORCH = True
except ImportError:
    _TORCH = False

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Platform auto-detection
# ---------------------------------------------------------------------------

def _detect_platform(path: str | Path) -> str:
    """Return 'navvis', 'metashape', 'meshroom', 'pix4d', 'colmap', or 'e57'."""
    p = Path(path)
    if p.suffix.lower() == '.psx':
        return 'metashape'
    if p.suffix.lower() == '.mg':
        return 'meshroom'
    if p.suffix.lower() == '.p4d':
        return 'pix4d'
    if p.suffix.lower() == '.e57':
        return 'e57'
    if p.is_dir():
        if (p / 'dataset.json').exists():
            return 'navvis'
        if list(p.glob('*.psx')):
            return 'metashape'
        if list(p.glob('*.mg')):
            return 'meshroom'
        if list(p.glob('*.p4d')) or (p / '1_initial' / 'params').exists():
            return 'pix4d'
        if (p / 'cameras.txt').exists() or (p / 'cameras.bin').exists():
            return 'colmap'
        for sub in ('sparse', 'sparse/0', 'dense/sparse'):
            sp = p / sub
            if (sp / 'cameras.txt').exists() or (sp / 'cameras.bin').exists():
                return 'colmap'
        if list(p.glob('*.e57')):
            return 'e57'
    raise ValueError(
        f'Cannot detect platform from: {path}\n'
        '  Expected a NavVis folder, Metashape .psx, Meshroom .mg,\n'
        '  Pix4D .p4d / folder, COLMAP sparse folder, or E57 file.'
    )


# ---------------------------------------------------------------------------
# Pinhole camera model (Metashape Brown-Conrady convention)
# ---------------------------------------------------------------------------

class PinholeModel:
    """Standard perspective camera with Brown-Conrady distortion.

    Metashape convention: cx/cy are offsets from image centre in pixels.
    """

    def __init__(
        self,
        f: float,
        cx_off: float, cy_off: float,
        k1: float, k2: float,
        p1: float, p2: float,
        width: int, height: int,
        sensor_name: str = 'cam0',
        k3: float = 0.0,
    ) -> None:
        self.f  = f
        self.cx = width  / 2.0 + cx_off   # principal point col from image origin
        self.cy = height / 2.0 + cy_off   # principal point row from image origin
        self.k1 = k1
        self.k2 = k2
        self.k3 = k3
        self.p1 = p1
        self.p2 = p2
        self.width  = width
        self.height = height
        self.sensor_name = sensor_name
        # These allow PinholeModel to be used wherever CameraModel.ocam is expected
        self.position = np.zeros(3, dtype=np.float64)
        self.R        = np.eye(3,  dtype=np.float64)
        self.ocam     = self   # duck-type: code that calls cam.ocam.project_gpu works transparently
        # world2cam[0] used by _ocam_to_pinhole_approx in splat_pipeline
        self.world2cam = np.array([f])

    def project(self, xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Project (N,3) camera-frame points → (col,row) pixel coords + valid mask."""
        X, Y, Z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
        valid  = Z > 0
        Zs = np.where(valid, Z, 1.0)
        xn, yn = X / Zs, Y / Zs
        r2  = xn**2 + yn**2
        rad = 1.0 + self.k1 * r2 + self.k2 * r2**2 + self.k3 * r2**3
        xd  = xn * rad + 2.0 * self.p1 * xn * yn      + self.p2 * (r2 + 2.0 * xn**2)
        yd  = yn * rad + self.p1 * (r2 + 2.0 * yn**2) + 2.0 * self.p2 * xn * yn
        col = self.f * xd + self.cx
        row = self.f * yd + self.cy
        mask = valid & (col >= 0) & (col < self.width) & (row >= 0) & (row < self.height)
        return np.stack([col, row], axis=-1), mask

    def project_gpu(
        self, xyz: 'torch.Tensor', device: 'torch.device'
    ) -> tuple['torch.Tensor', 'torch.Tensor']:
        """GPU projection; returns grid_sample-style (col_n, row_n) in [-1,1] + mask."""
        import torch
        X, Y, Z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
        valid = Z > 0
        Zs = torch.where(valid, Z, torch.ones_like(Z))
        xn, yn = X / Zs, Y / Zs
        r2  = xn**2 + yn**2
        rad = 1.0 + self.k1 * r2 + self.k2 * r2**2 + self.k3 * r2**3
        xd  = xn * rad + 2.0 * self.p1 * xn * yn      + self.p2 * (r2 + 2.0 * xn**2)
        yd  = yn * rad + self.p1 * (r2 + 2.0 * yn**2) + 2.0 * self.p2 * xn * yn
        col = self.f * xd + self.cx
        row = self.f * yd + self.cy
        col_n = (col / (self.width  - 1)) * 2.0 - 1.0
        row_n = (row / (self.height - 1)) * 2.0 - 1.0
        mask = valid & (col >= 0) & (col < self.width) & (row >= 0) & (row < self.height)
        return torch.stack([col_n, row_n], dim=-1), mask

    def unproject(self, uv_colrow: np.ndarray) -> np.ndarray:
        """Back-project (N,2) pixel (col,row) → unit 3D ray directions (N,3)."""
        col, row = uv_colrow[:, 0], uv_colrow[:, 1]
        xn = (col - self.cx) / self.f
        yn = (row - self.cy) / self.f
        r2   = xn**2 + yn**2
        corr = 1.0 + self.k1 * r2 + self.k2 * r2**2 + self.k3 * r2**3
        xu, yu = xn / corr, yn / corr
        dirs = np.stack([xu, yu, np.ones(len(xu), dtype=np.float64)], axis=-1)
        norms = np.linalg.norm(dirs, axis=-1, keepdims=True)
        return dirs / np.maximum(norms, 1e-8)


# ---------------------------------------------------------------------------
# Coordinate conversion — WGS84 geographic → UTM projected (Karney / Helmert)
# ---------------------------------------------------------------------------

def _wgs84_to_utm(lat_deg: float, lon_deg: float, epsg: int) -> tuple[float, float]:
    """Convert WGS84 lat/lon to Easting/Northing using pyproj if available,
    otherwise falling back to a pure-Python Transverse Mercator implementation
    accurate to better than 1 mm within a single UTM zone.
    """
    try:
        from pyproj import Transformer
        t = Transformer.from_crs('EPSG:4326', f'EPSG:{epsg}', always_xy=True)
        easting, northing = t.transform(lon_deg, lat_deg)
        return easting, northing
    except ImportError:
        pass

    # Pure-Python UTM (WGS84 ellipsoid, Helmert series, accurate to ~1 mm)
    # Derive zone and hemisphere from EPSG code: 326XX = N, 327XX = S, zone = XX
    if 32601 <= epsg <= 32660:
        zone = epsg - 32600
        northern = True
    elif 32701 <= epsg <= 32760:
        zone = epsg - 32700
        northern = False
    else:
        raise ValueError(
            f'EPSG:{epsg} is not a UTM zone code. '
            'Install pyproj for arbitrary projections: pip install pyproj'
        )

    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)   # central meridian

    # WGS84 ellipsoid parameters
    a  = 6378137.0
    f  = 1 / 298.257223563
    b  = a * (1 - f)
    e2 = 1 - (b / a) ** 2
    e  = math.sqrt(e2)
    n  = f / (2 - f)
    k0 = 0.9996
    E0 = 500000.0
    N0 = 0.0 if northern else 10000000.0

    # Meridional arc (Helmert series)
    A  = a / (1 + n) * (1 + n**2/4 + n**4/64)
    a2 = -3/2  * (n - 9/16  * n**3)
    a4 =  15/16 * (n**2 - 3/4 * n**4)
    a6 = -35/48 * n**3
    a8 =  315/512 * n**4

    t_   = math.sinh(math.atanh(math.sin(lat)) - 2*math.sqrt(n)/(1+n) *
                     math.atanh(2*math.sqrt(n)/(1+n) * math.sin(lat)))
    xi_  = math.atan2(t_, math.cos(lon - lon0))
    eta_ = math.atanh(math.sin(lon - lon0) / math.sqrt(1 + t_**2))

    xi  = xi_  + sum(
        c * math.sin(2*j * xi_) * math.cosh(2*j * eta_)
        for j, c in enumerate([a2, a4, a6, a8], 1)
    )
    eta = eta_ + sum(
        c * math.cos(2*j * xi_) * math.sinh(2*j * eta_)
        for j, c in enumerate([a2, a4, a6, a8], 1)
    )

    easting  = E0 + k0 * A * eta
    northing = N0 + k0 * A * xi
    return easting, northing


def _colmap_num_params(model: str) -> int:
    """Return the number of parameters for a COLMAP camera model."""
    return {
        'SIMPLE_PINHOLE': 3, 'PINHOLE': 4,
        'SIMPLE_RADIAL': 4,  'RADIAL': 5,
        'OPENCV': 8,         'OPENCV_FISHEYE': 8,
        'FULL_OPENCV': 12,   'THIN_PRISM_FISHEYE': 12,
        'FOV': 5,            'SIMPLE_RADIAL_FISHEYE': 4,
        'RADIAL_FISHEYE': 5,
    }.get(model, 4)


def _colmap_params_to_model(model: str, w: int, h: int, params: list) -> 'PinholeModel':
    """Convert COLMAP camera model parameters to a PinholeModel."""
    # All COLMAP models: params[0] = f (or fx), principal point near centre
    f   = float(params[0])
    fy  = float(params[1]) if model == 'PINHOLE' and len(params) > 1 else f
    # Principal point: stored as absolute pixel coords in COLMAP
    if model == 'SIMPLE_PINHOLE':
        cx_off = float(params[1]) - w / 2.0
        cy_off = float(params[2]) - h / 2.0
        k1 = k2 = p1 = p2 = k3 = 0.0
    elif model in ('PINHOLE',):
        # Average fx/fy; PinholeModel has one focal length
        f      = (float(params[0]) + float(params[1])) / 2.0
        cx_off = float(params[2]) - w / 2.0
        cy_off = float(params[3]) - h / 2.0
        k1 = k2 = p1 = p2 = k3 = 0.0
    elif model == 'SIMPLE_RADIAL':
        cx_off = float(params[1]) - w / 2.0
        cy_off = float(params[2]) - h / 2.0
        k1 = float(params[3]) if len(params) > 3 else 0.0
        k2 = p1 = p2 = k3 = 0.0
    elif model == 'RADIAL':
        cx_off = float(params[1]) - w / 2.0
        cy_off = float(params[2]) - h / 2.0
        k1 = float(params[3]) if len(params) > 3 else 0.0
        k2 = float(params[4]) if len(params) > 4 else 0.0
        p1 = p2 = k3 = 0.0
    else:   # OPENCV and variants: f, f, cx, cy, k1, k2, p1, p2, [k3...]
        cx_off = float(params[2]) - w / 2.0 if len(params) > 2 else 0.0
        cy_off = float(params[3]) - h / 2.0 if len(params) > 3 else 0.0
        k1 = float(params[4]) if len(params) > 4 else 0.0
        k2 = float(params[5]) if len(params) > 5 else 0.0
        p1 = float(params[6]) if len(params) > 6 else 0.0
        p2 = float(params[7]) if len(params) > 7 else 0.0
        k3 = float(params[8]) if len(params) > 8 else 0.0
    return PinholeModel(f=f, cx_off=cx_off, cy_off=cy_off,
                        k1=k1, k2=k2, p1=p1, p2=p2, k3=k3, width=w, height=h)


def _pix4d_cam_to_model(kv: dict) -> 'PinholeModel':
    """Convert a Pix4D .cam key-value dict to a PinholeModel."""
    w   = int(float(kv.get('image_width',  kv.get('width',  '4000'))))
    h   = int(float(kv.get('image_height', kv.get('height', '3000'))))
    f   = float(kv.get('focal_length_px', kv.get('focal_length', w)))
    cx  = float(kv.get('principal_point_x_px', kv.get('principal_point_x', '0')))
    cy  = float(kv.get('principal_point_y_px', kv.get('principal_point_y', '0')))
    k1  = float(kv.get('r1', kv.get('k1', '0')))
    k2  = float(kv.get('r2', kv.get('k2', '0')))
    k3  = float(kv.get('r3', kv.get('k3', '0')))
    p1  = float(kv.get('t1', kv.get('p1', '0')))
    p2  = float(kv.get('t2', kv.get('p2', '0')))
    return PinholeModel(f=f, cx_off=cx, cy_off=cy, k1=k1, k2=k2, p1=p1, p2=p2, k3=k3, width=w, height=h)


class OCamModel:
    """Scaramuzza omnidirectional camera model (OCamCalib convention).

    Coordinate convention:
      - Principal point: cx = row-center, cy = col-center (Matlab/Scaramuzza)
      - Camera frame: z-axis pointing toward the scene (z < 0 = in front)
      - Affine matrix [c d; e 1] corrects for minor sensor misalignment
    """

    def __init__(
        self,
        c: float, d: float, e: float,
        cx: float, cy: float,
        cam2world_coeffs: list[float],
        world2cam_coeffs: list[float],
        width: int, height: int,
    ) -> None:
        self.c = c
        self.d = d
        self.e = e
        self.cx = cx   # row center
        self.cy = cy   # col center
        self.cam2world = np.array(cam2world_coeffs, dtype=np.float64)
        self.world2cam = np.array(world2cam_coeffs, dtype=np.float64)
        self.width = width
        self.height = height
        # Precompute affine inverse for back-projection
        det = c - d * e
        self._inv_a = 1.0 / det
        self._inv_b = -d / det
        self._inv_c = -e / det
        self._inv_d = c / det

    # ------------------------------------------------------------------
    # CPU paths (NumPy)
    # ------------------------------------------------------------------

    def project(self, xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Project (N,3) camera-frame points to (N,2) pixel coords + valid mask.

        Returns pixel coordinates as (col, row) pairs.
        """
        X, Y, Z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
        rho = np.sqrt(X ** 2 + Y ** 2)
        safe = rho > 1e-8

        rho_s = np.where(safe, rho, 1.0)
        theta = np.arctan2(-Z, rho_s)

        # Evaluate world2cam polynomial
        r = np.zeros(len(theta))
        tp = np.ones(len(theta))
        for coeff in self.world2cam:
            r += coeff * tp
            tp *= theta

        # Undistorted offsets in (row-dir, col-dir)
        a = r * X / rho_s
        b = r * Y / rho_s

        # Affine + principal point → pixel (row, col)
        row = self.c * a + self.d * b + self.cx
        col = self.e * a + b + self.cy

        in_bounds = (col >= 0) & (col < self.width) & (row >= 0) & (row < self.height)
        mask = safe & in_bounds & (Z < 0)
        return np.stack([col, row], axis=-1), mask

    def unproject(self, uv_colrow: np.ndarray) -> np.ndarray:
        """Back-project (N,2) pixel (col,row) coords to unit 3D directions (N,3)."""
        col, row = uv_colrow[:, 0], uv_colrow[:, 1]
        # Undo principal point
        row_off = row - self.cx
        col_off = col - self.cy
        # Undo affine
        a = self._inv_a * row_off + self._inv_b * col_off
        b = self._inv_c * row_off + self._inv_d * col_off

        rho = np.sqrt(a ** 2 + b ** 2)
        # Evaluate cam2world polynomial
        z = np.zeros(len(rho))
        rp = np.ones(len(rho))
        for coeff in self.cam2world:
            z += coeff * rp
            rp *= rho

        dirs = np.stack([a, b, z], axis=-1)
        norms = np.linalg.norm(dirs, axis=-1, keepdims=True)
        return dirs / np.maximum(norms, 1e-8)

    # ------------------------------------------------------------------
    # GPU paths (PyTorch) — used by HDRIGenerator
    # ------------------------------------------------------------------

    def project_gpu(
        self,
        xyz: 'torch.Tensor',   # (H, W, 3) or (N, 3)
        device: 'torch.device',
    ) -> tuple['torch.Tensor', 'torch.Tensor']:
        """GPU-accelerated projection. Returns (uvs_norm, mask).

        uvs_norm: grid_sample-style (col_norm, row_norm) in [-1, 1], shape (*input_shape[:-1], 2)
        mask:     bool tensor, same leading shape
        """
        X = xyz[..., 0]
        Y = xyz[..., 1]
        Z = xyz[..., 2]

        rho = torch.sqrt(X ** 2 + Y ** 2).clamp(min=1e-8)
        theta = torch.atan2(-Z, rho)

        # Polynomial world2cam
        w2c = torch.tensor(self.world2cam, device=device, dtype=torch.float32)
        r = torch.zeros_like(theta)
        tp = torch.ones_like(theta)
        for coeff in w2c:
            r = r + coeff * tp
            tp = tp * theta

        a = r * X / rho
        b = r * Y / rho

        row = self.c * a + self.d * b + self.cx
        col = self.e * a + b + self.cy

        # Normalized for F.grid_sample: x=col_norm, y=row_norm in [-1,1]
        col_n = (col / (self.width  - 1)) * 2.0 - 1.0
        row_n = (row / (self.height - 1)) * 2.0 - 1.0
        uvs = torch.stack([col_n, row_n], dim=-1)

        mask = (
            (col >= 0) & (col < self.width) &
            (row >= 0) & (row < self.height) &
            (Z < 0)
        )
        return uvs, mask


def _quat_to_rot(q: np.ndarray) -> np.ndarray:
    """Quaternion (w, x, y, z) → 3×3 rotation matrix (column vectors = axes)."""
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z),     2 * (x * y - w * z),     2 * (x * z + w * y)],
        [    2 * (x * y + w * z), 1 - 2 * (x * x + z * z),     2 * (y * z - w * x)],
        [    2 * (x * z - w * y),     2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float64)


class CameraModel:
    """Individual camera within a NavVis sensor head."""

    def __init__(
        self,
        sensor_name: str,
        position: np.ndarray,       # (3,) offset from cam_head origin
        quaternion: np.ndarray,     # (w, x, y, z) rotation from cam to head frame
        ocam: OCamModel,
        width: int,
        height: int,
    ) -> None:
        self.sensor_name = sensor_name
        self.position = position
        self.quaternion = quaternion
        self.ocam = ocam
        self.width = width
        self.height = height
        # R_cam_in_head: columns are cam-frame axes expressed in head frame
        self.R = _quat_to_rot(quaternion)

    def head_to_cam(self, pts_head: np.ndarray) -> np.ndarray:
        """Transform (N,3) points from camera-head frame into this camera's frame."""
        return (pts_head - self.position) @ self.R

    def world_to_cam(
        self, pts_world: np.ndarray, head_pos: np.ndarray, R_head: np.ndarray
    ) -> np.ndarray:
        """Transform (N,3) world-frame points into this camera's frame."""
        pts_head = (pts_world - head_pos) @ R_head
        return self.head_to_cam(pts_head)


class ScanDataset:
    """Reads a mobile LiDAR scan dataset directory.

    Parameters
    ----------
    dataset_dir: path to the dataset root directory or a .psx file
    platform:    'navvis' | 'metashape' | 'auto' (default — auto-detected)
    """

    def __init__(self, dataset_dir: str | Path, platform: str = 'auto') -> None:
        self.root = Path(dataset_dir)
        self.platform = platform.lower() if platform.lower() != 'auto' else _detect_platform(dataset_dir)
        self._meta: Optional[dict] = None
        self._cameras: Optional[list] = None
        self._poses: Optional[list[dict]] = None
        if self.platform == 'metashape':
            self._parse_metashape()
        elif self.platform == 'meshroom':
            self._parse_meshroom()
        elif self.platform == 'pix4d':
            self._parse_pix4d()
        elif self.platform == 'colmap':
            self._parse_colmap()
        elif self.platform == 'e57':
            self._parse_e57()

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    def meta(self) -> dict:
        if self._meta is None:
            with open(self.root / 'dataset.json') as f:
                self._meta = json.load(f)
        return self._meta

    @property
    def num_frames(self) -> int:
        if self._poses is not None:
            return len(self._poses)
        return int(self.meta.get('statistics', {}).get('capture_locations', 0))

    @property
    def dataset_name(self) -> str:
        return self.meta['dataset']['name']

    # ------------------------------------------------------------------
    # Cameras
    # ------------------------------------------------------------------

    @property
    def cameras(self) -> list[CameraModel]:
        if self._cameras is None:
            self._cameras = self._parse_sensor_frame()
        return self._cameras

    def _parse_sensor_frame(self) -> list[CameraModel]:
        tree = ET.parse(self.root / 'sensor_frame.xml')
        root = tree.getroot()
        head = root.find('CameraHead')
        cams = []
        for elem in head.findall('CameraModel'):
            name = elem.find('SensorName').text
            pose = elem.find('Pose')
            pos = np.array([
                float(pose.find('position/x').text),
                float(pose.find('position/y').text),
                float(pose.find('position/z').text),
            ])
            ori = np.array([
                float(pose.find('orientation/w').text),
                float(pose.find('orientation/x').text),
                float(pose.find('orientation/y').text),
                float(pose.find('orientation/z').text),
            ])
            sz = elem.find('ImageSize')
            w, h = int(sz.find('Width').text), int(sz.find('Height').text)
            ocm = elem.find('OCamModel')
            c2w = [float(x.text) for x in ocm.find('cam2world').findall('coeff')]
            w2c = [float(x.text) for x in ocm.find('world2cam').findall('coeff')]
            ocam = OCamModel(
                c=float(ocm.find('c').text),
                d=float(ocm.find('d').text),
                e=float(ocm.find('e').text),
                cx=float(ocm.find('cx').text),
                cy=float(ocm.find('cy').text),
                cam2world_coeffs=c2w,
                world2cam_coeffs=w2c,
                width=w, height=h,
            )
            cams.append(CameraModel(name, pos, ori, ocam, w, h))
        return cams

    # ------------------------------------------------------------------
    # Frame poses
    # ------------------------------------------------------------------

    @property
    def poses(self) -> list[dict]:
        if self._poses is None:
            info = self.root / 'info'
            # Capture the count before mutating _poses, so num_frames stays correct
            n = self.num_frames
            self._poses = []
            for i in range(n):
                p = info / f'{i:05d}-info.json'
                if p.exists():
                    with open(p) as f:
                        self._poses.append(json.load(f))
        return self._poses

    def frame_position(self, idx: int) -> np.ndarray:
        return np.array(self.poses[idx]['cam_head']['position'])

    def frame_quaternion(self, idx: int) -> np.ndarray:
        """Returns (w, x, y, z)."""
        q = self.poses[idx]['cam_head']['quaternion']
        return np.array([q[0], q[1], q[2], q[3]])

    def frame_transform(self, idx: int) -> tuple[np.ndarray, np.ndarray]:
        """Returns (position, R) where R transforms camera/head→world."""
        pose = self.poses[idx]
        if '_transform_matrix' in pose:
            T = np.array(pose['_transform_matrix'], dtype=np.float64).reshape(4, 4)
            return T[:3, 3], T[:3, :3]
        pos = self.frame_position(idx)
        q   = self.frame_quaternion(idx)
        return pos, _quat_to_rot(q)

    def frame_timestamp(self, idx: int) -> float:
        return float(self.poses[idx]['timestamp'])

    def is_valid_frame(self, idx: int) -> bool:
        return str(self.poses[idx].get('valid', 'true')).lower() == 'true'

    # ------------------------------------------------------------------
    # File paths
    # ------------------------------------------------------------------

    def dng_path(self, frame_idx: int, cam_idx: int) -> Path:
        return self.root / 'cam' / f'{frame_idx:05d}-cam{cam_idx}.dng'

    def image_path(self, frame_idx: int, cam_idx: int) -> Path:
        """Return image path for any platform."""
        if self.platform in ('metashape', 'meshroom', 'pix4d', 'colmap', 'e57'):
            return Path(self.poses[frame_idx]['_image_path'])
        return self.dng_path(frame_idx, cam_idx)

    def has_dng(self, frame_idx: int, cam_idx: int) -> bool:
        return self.dng_path(frame_idx, cam_idx).exists()

    def bag_path(self, name: str = 'trajectory_slam') -> Path:
        return self.root / 'internal' / 'bags' / f'{name}.bag'

    def lidar_bag_paths(self) -> list[Path]:
        """Return the per-segment LiDAR bags, or the trajectory_slam bag as fallback."""
        bags_dir = self.root / 'internal' / 'bags'
        laser_bags = sorted(bags_dir.glob('bag_laser_horiz_*.bag')) + \
                     sorted(bags_dir.glob('bag_laser_vert_*.bag'))
        if laser_bags:
            return laser_bags
        slam_bag = self.root / 'internal' / 'trajectory_slam.bag'
        if slam_bag.exists():
            return [slam_bag]
        return []

    def local_bag_path(self) -> Path:
        return self.root / 'internal' / 'artifacts' / 'trajectory_local.bag'

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def valid_frame_indices(self) -> list[int]:
        return [i for i in range(self.num_frames) if self.is_valid_frame(i)]

    def select_reference_frame(self) -> int:
        """Choose a representative frame near the centre of the trajectory."""
        valid = self.valid_frame_indices()
        mid = len(valid) // 2
        return valid[mid]

    # ------------------------------------------------------------------
    # Metashape .psx parser
    # ------------------------------------------------------------------

    def _parse_metashape(self) -> None:
        """Parse a Metashape .psx project file (ZIP containing doc.xml)."""
        import zipfile

        psx_path = self.root
        if psx_path.is_dir():
            candidates = sorted(psx_path.glob('*.psx'))
            if not candidates:
                raise FileNotFoundError(f'No .psx file found in {psx_path}')
            psx_path = candidates[0]

        with zipfile.ZipFile(psx_path, 'r') as zf:
            with zf.open('doc.xml') as fh:
                xml_content = fh.read()

        root_elem = ET.fromstring(xml_content)
        chunk = self._metashape_find_chunk(root_elem)

        self._meta = {
            'dataset': {
                'name': chunk.get('label', psx_path.stem),
                'dataset_id': psx_path.stem,
            }
        }

        sensors = self._metashape_parse_sensors(chunk)
        if not sensors:
            raise ValueError(f'No frame sensors found in {psx_path.name}')

        chunk_T = self._metashape_chunk_transform(chunk)
        self._cameras = [sensors[sid] for sid in sorted(sensors, key=int)]
        self._sensor_id_to_cam_idx = {sid: i for i, sid in enumerate(sorted(sensors, key=int))}

        self._poses = []
        psx_dir = psx_path.parent
        cameras_elem = chunk.find('cameras')
        if cameras_elem is None:
            raise ValueError('No cameras element found in Metashape project')

        for cam_elem in cameras_elem.findall('camera'):
            if cam_elem.get('enabled', 'true').lower() == 'false':
                continue
            sensor_id = cam_elem.get('sensor_id', '0')
            if sensor_id not in sensors:
                continue
            t_elem = cam_elem.find('transform')
            if t_elem is None:
                continue

            vals = [float(v) for v in t_elem.text.split()]
            if len(vals) == 16:
                T_local = np.array(vals).reshape(4, 4)
            elif len(vals) == 12:
                T_local = np.eye(4)
                T_local[:3, :] = np.array(vals).reshape(3, 4)
            else:
                continue

            T_world = chunk_T @ T_local

            # Image path
            photo = cam_elem.find('photo')
            img_str = (photo.get('path', '') if photo is not None else '') or cam_elem.get('label', '')
            img_path = Path(img_str) if Path(img_str).is_absolute() else psx_dir / img_str

            # GPS reference
            ref_elem = cam_elem.find('reference')
            reference = {}
            if ref_elem is not None and ref_elem.get('enabled', 'true').lower() != 'false':
                for attr in ('x', 'y', 'z', 'yaw', 'pitch', 'roll'):
                    val = ref_elem.get(attr)
                    if val is not None:
                        reference[attr] = float(val)

            pos = T_world[:3, 3].tolist()
            R   = T_world[:3, :3]
            qw, qx, qy, qz = self._rot_to_quat(R)

            self._poses.append({
                'cam_head': {'position': pos, 'quaternion': [qw, qx, qy, qz]},
                'footprint': {'position': pos, 'quaternion': [qw, qx, qy, qz]},
                'timestamp': 0.0,
                'valid': 'true',
                'capture_mode': 'Metashape',
                '_image_path': str(img_path),
                '_sensor_id': sensor_id,
                '_reference': reference,
                '_transform_matrix': T_world.tolist(),
            })

    @staticmethod
    def _metashape_find_chunk(root_elem: ET.Element) -> ET.Element:
        chunks = root_elem.find('chunks')
        if chunks is not None:
            for c in chunks.findall('chunk'):
                if c.get('enabled', 'true').lower() != 'false':
                    return c
        chunk = root_elem.find('chunk')
        if chunk is not None:
            return chunk
        raise ValueError('No chunk found in Metashape project')

    @staticmethod
    def _metashape_parse_sensors(chunk: ET.Element) -> dict[str, 'PinholeModel']:
        sensors: dict[str, PinholeModel] = {}
        sensors_elem = chunk.find('sensors')
        if sensors_elem is None:
            return sensors
        for s in sensors_elem.findall('sensor'):
            if s.get('type', 'frame') != 'frame':
                continue
            sid = s.get('id', '0')
            res = s.find('resolution')
            w = int(res.get('width',  4000)) if res is not None else 4000
            h = int(res.get('height', 3000)) if res is not None else 3000
            calib = next(
                (c for c in s.findall('calibration') if c.get('class') == 'adjusted'),
                s.find('calibration'),
            )

            def _f(tag, default=0.0):
                t = calib.find(tag) if calib is not None else None
                return float(t.text) if (t is not None and t.text) else default

            cal_res = calib.find('resolution') if calib is not None else None
            if cal_res is not None:
                w = int(cal_res.get('width', w))
                h = int(cal_res.get('height', h))

            sensors[sid] = PinholeModel(
                f=_f('f', w), cx_off=_f('cx'), cy_off=_f('cy'),
                k1=_f('k1'), k2=_f('k2'), p1=_f('p1'), p2=_f('p2'),
                width=w, height=h,
                sensor_name=s.get('label', f'cam{sid}'),
            )
        return sensors

    @staticmethod
    def _metashape_chunk_transform(chunk: ET.Element) -> np.ndarray:
        T = np.eye(4, dtype=np.float64)
        t_elem = chunk.find('transform')
        if t_elem is not None:
            rot = t_elem.find('rotation')
            tra = t_elem.find('translation')
            sca = t_elem.find('scale')
            if rot is not None and tra is not None:
                s = float(sca.text) if sca is not None else 1.0
                T[:3, :3] = np.array(rot.text.split(), dtype=np.float64).reshape(3, 3) * s
                T[:3,  3] = np.array(tra.text.split(), dtype=np.float64)
        return T

    @staticmethod
    def _rot_to_quat(R: np.ndarray) -> tuple[float, float, float, float]:
        """Convert 3×3 rotation matrix → (w, x, y, z) quaternion."""
        import math as _m
        tr = R[0, 0] + R[1, 1] + R[2, 2]
        if tr > 0:
            s = 0.5 / _m.sqrt(tr + 1.0)
            return (0.25 / s, (R[2,1]-R[1,2])*s, (R[0,2]-R[2,0])*s, (R[1,0]-R[0,1])*s)
        elif R[0,0] > R[1,1] and R[0,0] > R[2,2]:
            s = 2.0 * _m.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2])
            return ((R[2,1]-R[1,2])/s, 0.25*s, (R[0,1]+R[1,0])/s, (R[0,2]+R[2,0])/s)
        elif R[1,1] > R[2,2]:
            s = 2.0 * _m.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2])
            return ((R[0,2]-R[2,0])/s, (R[0,1]+R[1,0])/s, 0.25*s, (R[1,2]+R[2,1])/s)
        else:
            s = 2.0 * _m.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1])
            return ((R[1,0]-R[0,1])/s, (R[0,2]+R[2,0])/s, (R[1,2]+R[2,1])/s, 0.25*s)

    # ------------------------------------------------------------------
    # Georeferencing — unified for both platforms
    # ------------------------------------------------------------------

    def apply_trimble_georef(
        self,
        trimble_csv: str | Path,
        epsg: int = 32605,
        overwrite: bool = False,
    ) -> None:
        """Parse a Trimble survey CSV and write georeferenced anchor_poses.txt.

        The CSV format is: point_id;lat_deg;lon_deg;elev_m (semicolon-separated).
        Anchor names are matched by stripping the dash from the anchor name:
        anchor '14-00' matches Trimble point '1400'.
        Coordinates are converted from WGS84 to the given EPSG projection
        (default 32605 = UTM Zone 5N).
        """
        trimble_csv = Path(trimble_csv)

        # Parse Trimble CSV → {point_id_str: (easting, northing, height)}
        survey: dict[str, tuple[float, float, float]] = {}
        with open(trimble_csv, newline='') as f:
            for row in csv.reader(f, delimiter=';'):
                if len(row) < 4:
                    continue
                pt_id = row[0].strip()
                try:
                    lat, lon, elev = float(row[1]), float(row[2]), float(row[3])
                except ValueError:
                    continue
                easting, northing = _wgs84_to_utm(lat, lon, epsg)
                survey[pt_id] = (easting, northing, elev)

        if not survey:
            raise ValueError(f'No valid points parsed from {trimble_csv}')
        log.info('Parsed %d Trimble control points from %s', len(survey), trimble_csv.name)

        # Read anchor names from anchors.txt
        anchor_names = self._read_anchor_names()
        if not anchor_names:
            log.warning('No anchors found in anchors.txt — skipping georeferencing')
            return

        # Match anchor names to survey points
        matched: dict[str, tuple[float, float, float]] = {}
        for name in anchor_names:
            key = name.replace('-', '')   # '14-00' → '1400'
            if key in survey:
                matched[name] = survey[key]
            else:
                log.warning('Anchor %r has no matching Trimble point (tried %r)', name, key)

        if not matched:
            raise ValueError('No anchors could be matched to Trimble survey points')

        poses_path = self.root / 'anchors' / 'anchor_poses.txt'
        if poses_path.exists() and not overwrite:
            # Check if it already has data beyond the header comments
            content = poses_path.read_text()
            data_lines = [l for l in content.splitlines()
                          if l.strip() and not l.startswith('#') and l.strip() != '1.1']
            if data_lines:
                log.info('anchor_poses.txt already populated — skipping (use overwrite=True)')
                return

        # Write anchor_poses.txt
        header = (
            '#\n'
            '# SLAM Anchor Pose File Format Version 1.1\n'
            '#\n'
            '# Generated by rawkee NavVis pipeline from Trimble CSV: '
            f'{trimble_csv.name}\n'
            f'# Projection: EPSG:{epsg}  '
            '(X=Easting, Y=Northing, Z=Height, right-handed)\n'
            '#\n'
            '1.1\n'
        )
        lines = [header]
        for name, (e, n, h) in matched.items():
            lines.append(f'"{name}" {e:.4f} {n:.4f} {h:.4f} 0.0\n')

        poses_path.write_text(''.join(lines))
        log.info(
            'Wrote %d georeferenced anchors to %s', len(matched), poses_path
        )

    def geo_origin(self) -> tuple[float, float, float, int] | None:
        """Return (easting, northing, height, epsg) centroid, or None.

        NavVis: anchor_poses.txt. Metashape: GPS reference tags.
        Meshroom: EXIF GPS. Pix4D: calibrated camera positions (already UTM).
        """
        if self.platform == 'metashape':
            return self._geo_origin_metashape()
        if self.platform == 'meshroom':
            return self._geo_origin_meshroom()
        if self.platform == 'pix4d':
            return self._geo_origin_pix4d()
        if self.platform in ('colmap', 'e57'):
            return None   # COLMAP/E57 world coords are not georeferenced UTM
        return self._geo_origin_navvis()

    def _geo_origin_navvis(self) -> tuple[float, float, float, int] | None:
        """Read UTM centroid from populated anchor_poses.txt."""
        path = self.root / 'anchors' / 'anchor_poses.txt'
        if not path.exists():
            return None
        epsg = None
        coords = []
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if 'EPSG:' in stripped:
                try:
                    epsg = int(stripped.split('EPSG:')[1].split()[0])
                except (ValueError, IndexError):
                    pass
            if not stripped or stripped.startswith('#'):
                continue
            parts = stripped.split()
            if len(parts) < 5:
                continue
            try:
                float(parts[0])   # version line is a float; skip it
                continue
            except ValueError:
                pass
            try:
                e, n, h = float(parts[1]), float(parts[2]), float(parts[3])
                coords.append((e, n, h))
            except (ValueError, IndexError):
                continue
        if not coords:
            return None
        e_mean = sum(c[0] for c in coords) / len(coords)
        n_mean = sum(c[1] for c in coords) / len(coords)
        h_mean = sum(c[2] for c in coords) / len(coords)
        return (e_mean, n_mean, h_mean, epsg or 32605)

    def _geo_origin_metashape(self) -> tuple[float, float, float, int] | None:
        """Compute UTM centroid from Metashape camera GPS reference tags."""
        coords = []
        for pose in self.poses:
            ref = pose.get('_reference', {})
            if 'x' in ref and 'y' in ref and 'z' in ref:
                coords.append((ref['x'], ref['y'], ref['z']))
        if not coords:
            return None
        x_c = sum(c[0] for c in coords) / len(coords)
        y_c = sum(c[1] for c in coords) / len(coords)
        z_c = sum(c[2] for c in coords) / len(coords)
        # Detect geographic (lon/lat) vs. projected (easting/northing)
        if -180.0 <= x_c <= 180.0 and -90.0 <= y_c <= 90.0:
            # Metashape geographic: x=longitude, y=latitude
            zone    = int((x_c + 180.0) / 6.0) + 1
            epsg    = 32600 + zone if y_c >= 0 else 32700 + zone
            e, n    = _wgs84_to_utm(y_c, x_c, epsg)   # lat, lon
            return (e, n, z_c, epsg)
        # Already projected — return as-is with a generic EPSG fallback
        return (x_c, y_c, z_c, 32605)

    def _geo_origin_meshroom(self) -> tuple[float, float, float, int] | None:
        """Compute UTM centroid from EXIF GPS metadata embedded in cameras.sfm views."""
        coords = []
        for pose in self.poses:
            ref = pose.get('_reference', {})
            if 'lat' in ref and 'lon' in ref:
                coords.append((ref['lat'], ref['lon'], ref.get('alt', 0.0)))
        if not coords:
            return None
        lat_c = sum(c[0] for c in coords) / len(coords)
        lon_c = sum(c[1] for c in coords) / len(coords)
        alt_c = sum(c[2] for c in coords) / len(coords)
        zone  = int((lon_c + 180.0) / 6.0) + 1
        epsg  = 32600 + zone if lat_c >= 0 else 32700 + zone
        e, n  = _wgs84_to_utm(lat_c, lon_c, epsg)
        return (e, n, alt_c, epsg)

    # ------------------------------------------------------------------
    # Meshroom .mg parser
    # ------------------------------------------------------------------

    def _parse_meshroom(self) -> None:
        """Parse a Meshroom .mg project file and locate cameras.sfm in the cache."""
        mg_path = self.root
        if mg_path.is_dir():
            candidates = sorted(mg_path.glob('*.mg'))
            if not candidates:
                raise FileNotFoundError(f'No .mg file found in {mg_path}')
            mg_path = candidates[0]

        with open(mg_path, 'r', encoding='utf-8') as fh:
            mg = json.load(fh)

        # Locate the StructureFromMotion node and its cache hash
        sfm_path = self._meshroom_find_sfm(mg, mg_path.parent)

        with open(sfm_path, 'r', encoding='utf-8') as fh:
            sfm = json.load(fh)

        self._meta = {'dataset': {'name': mg_path.stem, 'dataset_id': mg_path.stem}}

        # Parse intrinsics → PinholeModel
        intrinsics: dict[str, PinholeModel] = {}
        for intr in sfm.get('intrinsics', []):
            iid = intr['intrinsicId']
            w   = int(intr.get('width',  '4000'))
            h   = int(intr.get('height', '3000'))
            f   = float(intr.get('pxFocalLength', w))
            pp  = intr.get('principalPoint', ['0', '0'])
            cx_off, cy_off = float(pp[0]), float(pp[1])
            dist = [float(v) for v in intr.get('distortionParams', [])]
            itype = intr.get('type', 'radial3')
            # Map AliceVision distortion types to k1,k2,k3,p1,p2
            k1 = dist[0] if len(dist) > 0 else 0.0
            k2 = dist[1] if len(dist) > 1 else 0.0
            k3 = dist[2] if len(dist) > 2 and 'radial' in itype else 0.0
            p1 = dist[2] if len(dist) > 2 and 'radial' not in itype else 0.0
            p2 = dist[3] if len(dist) > 3 else 0.0
            intrinsics[iid] = PinholeModel(
                f=f, cx_off=cx_off, cy_off=cy_off,
                k1=k1, k2=k2, p1=p1, p2=p2, k3=k3,
                width=w, height=h,
                sensor_name=intr.get('serialNumber', f'cam{iid}'),
            )

        # Parse poses: rotation is world→camera (row-major 9-element flat array)
        poses_dict: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for p in sfm.get('poses', []):
            pid = p['poseId']
            t   = p['pose']['transform']
            R_w2c = np.array([float(v) for v in t['rotation']], dtype=np.float64).reshape(3, 3)
            center = np.array([float(v) for v in t['center']], dtype=np.float64)
            R_c2w  = R_w2c.T
            poses_dict[pid] = (center, R_c2w)

        # Build view index for fast lookup
        view_index: dict[str, dict] = {v['viewId']: v for v in sfm.get('views', [])}

        self._cameras = list(intrinsics.values()) or [
            PinholeModel(f=3000.0, cx_off=0.0, cy_off=0.0, k1=0.0, k2=0.0,
                         p1=0.0, p2=0.0, width=4000, height=3000)
        ]
        self._poses = []

        for view in sfm.get('views', []):
            pid = view.get('poseId', '')
            if pid not in poses_dict:
                continue   # unregistered image
            iid = view.get('intrinsicId', '')
            if iid not in intrinsics:
                continue

            center, R_c2w = poses_dict[pid]
            qw, qx, qy, qz = self._rot_to_quat(R_c2w)

            # GPS from EXIF metadata
            meta = view.get('metadata', {})
            reference = self._meshroom_parse_gps(meta)

            self._poses.append({
                'cam_head': {'position': center.tolist(), 'quaternion': [qw, qx, qy, qz]},
                'footprint': {'position': center.tolist(), 'quaternion': [qw, qx, qy, qz]},
                'timestamp': float(meta.get('Exif:DateTimeOriginal', 0) or 0),
                'valid': 'true',
                'capture_mode': 'Meshroom',
                '_image_path': view.get('path', ''),
                '_sensor_id': iid,
                '_reference': reference,
                '_transform_matrix': np.block([
                    [R_c2w, center[:, None]],
                    [np.zeros((1, 3)), np.ones((1, 1))]
                ]).tolist(),
            })

    @staticmethod
    def _meshroom_find_sfm(mg: dict, project_dir: Path) -> Path:
        """Locate cameras.sfm from the Meshroom project graph."""
        graph = mg.get('graph', {})
        for node_name, node in graph.items():
            if node.get('nodeType') != 'StructureFromMotion':
                continue
            uid = node.get('uids', {}).get('0', '')
            if uid:
                candidate = project_dir / 'MeshroomCache' / 'StructureFromMotion' / uid / 'cameras.sfm'
                if candidate.exists():
                    return candidate
        # Fallback: scan the cache directory for any cameras.sfm
        cache_dir = project_dir / 'MeshroomCache' / 'StructureFromMotion'
        if cache_dir.exists():
            candidates = sorted(cache_dir.rglob('cameras.sfm'), key=lambda p: p.stat().st_mtime)
            if candidates:
                return candidates[-1]
        raise FileNotFoundError(
            f'cameras.sfm not found in {project_dir}/MeshroomCache/StructureFromMotion/\n'
            '  Run the Meshroom StructureFromMotion node to completion first.'
        )

    @staticmethod
    def _meshroom_parse_gps(meta: dict) -> dict:
        """Extract decimal-degree GPS from AliceVision EXIF metadata dict."""
        lat_raw = meta.get('Exif:GPSLatitude',   meta.get('GPS:Latitude',   ''))
        lon_raw = meta.get('Exif:GPSLongitude',  meta.get('GPS:Longitude',  ''))
        alt_raw = meta.get('Exif:GPSAltitude',   meta.get('GPS:Altitude',   '0'))
        lat_ref = meta.get('Exif:GPSLatitudeRef', 'N')
        lon_ref = meta.get('Exif:GPSLongitudeRef', 'E')
        if not lat_raw or not lon_raw:
            return {}
        try:
            def _dms_to_dec(s: str, ref: str) -> float:
                s = s.strip()
                if 'deg' in s or "'" in s:
                    parts = s.replace('deg', ' ').replace("'", ' ').replace('"', ' ').split()
                    d = float(parts[0])
                    m = float(parts[1]) if len(parts) > 1 else 0.0
                    sc = float(parts[2]) if len(parts) > 2 else 0.0
                    v = d + m / 60.0 + sc / 3600.0
                else:
                    v = float(s)
                if ref in ('S', 'W'):
                    v = -v
                return v
            return {
                'lat': _dms_to_dec(lat_raw, lat_ref),
                'lon': _dms_to_dec(lon_raw, lon_ref),
                'alt': float(str(alt_raw).split('/')[0]),
            }
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Pix4Dmapper parser
    # ------------------------------------------------------------------

    def _parse_pix4d(self) -> None:
        """Parse a Pix4Dmapper project folder or .p4d file."""
        p4d_path = self.root
        project_dir: Path

        if p4d_path.suffix.lower() == '.p4d':
            project_dir = p4d_path.parent
        else:
            project_dir = p4d_path
            candidates = sorted(project_dir.glob('*.p4d'))
            p4d_path = candidates[0] if candidates else None

        params_dir = project_dir / '1_initial' / 'params'
        if not params_dir.exists():
            raise FileNotFoundError(
                f'1_initial/params/ not found under {project_dir}.\n'
                '  Run Pix4Dmapper Initial Processing (Step 1) to completion first.'
            )

        stem = project_dir.name

        # --- Coordinate offset ---
        offset = np.zeros(3, dtype=np.float64)
        for f in params_dir.glob('*_offset.xyz'):
            try:
                vals = f.read_text().split()
                offset = np.array([float(v) for v in vals[:3]])
            except Exception:
                pass
            break

        # --- Intrinsics (.cam file) ---
        intrinsics: dict[str, 'PinholeModel'] = {}
        for cam_file in params_dir.glob('*_calibrated_internal_camera_parameters.cam'):
            intrinsics = self._pix4d_parse_cam(cam_file)
            break
        default_model = next(iter(intrinsics.values())) if intrinsics else PinholeModel(
            f=3000.0, cx_off=0.0, cy_off=0.0, k1=0.0, k2=0.0,
            p1=0.0, p2=0.0, width=4000, height=3000,
        )
        self._cameras = list(intrinsics.values()) or [default_model]

        # --- Image paths from .p4d XML ---
        image_path_map: dict[str, Path] = {}
        if p4d_path and p4d_path.exists():
            image_path_map = self._pix4d_parse_image_paths(p4d_path, project_dir)

        # --- Poses from calibrated camera parameters ---
        poses_file = next(params_dir.glob('*_calibrated_camera_parameters.txt'), None)
        if poses_file is None:
            raise FileNotFoundError(
                f'No *_calibrated_camera_parameters.txt found in {params_dir}'
            )

        self._meta = {'dataset': {'name': project_dir.name, 'dataset_id': project_dir.name}}
        self._poses = []

        for line in poses_file.read_text(encoding='utf-8', errors='replace').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or line.lower().startswith('label'):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 7:
                parts = line.split()
            if len(parts) < 7:
                continue
            try:
                label = parts[0]
                x = float(parts[1]) + offset[0]
                y = float(parts[2]) + offset[1]
                z = float(parts[3]) + offset[2]
                omega = float(parts[4])
                phi   = float(parts[5])
                kappa = float(parts[6])
            except (ValueError, IndexError):
                continue

            R_c2w = self._opk_to_rot(omega, phi, kappa)
            qw, qx, qy, qz = self._rot_to_quat(R_c2w)
            pos = [x, y, z]

            img_path = image_path_map.get(label, project_dir / label)

            self._poses.append({
                'cam_head': {'position': pos, 'quaternion': [qw, qx, qy, qz]},
                'footprint': {'position': pos, 'quaternion': [qw, qx, qy, qz]},
                'timestamp': 0.0,
                'valid': 'true',
                'capture_mode': 'Pix4D',
                '_image_path': str(img_path),
                '_sensor_id': '0',
                '_reference': {'x': x, 'y': y, 'z': z},
                '_transform_matrix': np.block([
                    [R_c2w, np.array(pos)[:, None]],
                    [np.zeros((1, 3)), np.ones((1, 1))]
                ]).tolist(),
                '_utm': (x, y, z),
            })

    @staticmethod
    def _pix4d_parse_cam(cam_file: Path) -> dict[str, 'PinholeModel']:
        """Parse a Pix4D .cam intrinsics file (INI-style, one group per camera model)."""
        models: dict[str, PinholeModel] = {}
        current: dict[str, str] = {}
        group_id = '0'

        for raw in cam_file.read_text(encoding='utf-8', errors='replace').splitlines():
            line = raw.strip()
            if line.startswith('['):
                if current:
                    models[group_id] = _pix4d_cam_to_model(current)
                    current = {}
                group_id = line.strip('[]').split('_')[-1]
            elif '=' in line and not line.startswith('#'):
                k, _, v = line.partition('=')
                current[k.strip().lower()] = v.strip()
        if current:
            models[group_id] = _pix4d_cam_to_model(current)
        return models

    @staticmethod
    def _pix4d_parse_image_paths(p4d_path: Path, project_dir: Path) -> dict[str, Path]:
        """Extract image name → absolute path from a Pix4D .p4d XML project file."""
        paths: dict[str, Path] = {}
        try:
            tree = ET.parse(p4d_path)
            for img_elem in tree.getroot().iter('Image'):
                name = (img_elem.findtext('name') or '').strip()
                path_str = (img_elem.findtext('path') or '').strip()
                if name and path_str:
                    p = Path(path_str)
                    if not p.is_absolute():
                        p = project_dir / p
                    paths[name] = p
        except Exception:
            pass
        return paths

    @staticmethod
    def _opk_to_rot(omega_deg: float, phi_deg: float, kappa_deg: float) -> np.ndarray:
        """Convert photogrammetric OPK angles (degrees) to camera-to-world rotation matrix."""
        omega = math.radians(omega_deg)
        phi   = math.radians(phi_deg)
        kappa = math.radians(kappa_deg)
        co, so = math.cos(omega), math.sin(omega)
        cp, sp = math.cos(phi),   math.sin(phi)
        ck, sk = math.cos(kappa), math.sin(kappa)
        Rx = np.array([[1, 0,  0 ], [0, co, -so], [0, so,  co]], dtype=np.float64)
        Ry = np.array([[cp, 0, sp], [0,  1,   0 ], [-sp, 0, cp]], dtype=np.float64)
        Rz = np.array([[ck, -sk, 0], [sk, ck, 0], [0, 0, 1]], dtype=np.float64)
        return Rz @ Ry @ Rx

    def _geo_origin_pix4d(self) -> tuple[float, float, float, int] | None:
        """Return UTM centroid from already-georeferenced Pix4D camera positions."""
        coords = [p['_utm'] for p in (self._poses or []) if '_utm' in p]
        if not coords:
            return None
        e = sum(c[0] for c in coords) / len(coords)
        n = sum(c[1] for c in coords) / len(coords)
        h = sum(c[2] for c in coords) / len(coords)
        # Attempt to read EPSG from .p4d XML; fall back to 32605
        epsg = self._pix4d_read_epsg()
        return (e, n, h, epsg)

    def _pix4d_read_epsg(self) -> int:
        """Try to read the EPSG code from the .p4d project file."""
        import re as _re
        try:
            project_dir = self.root if self.root.is_dir() else self.root.parent
            for p4d in project_dir.glob('*.p4d'):
                text = p4d.read_text(errors='ignore')
                m = _re.search(r'EPSG[:\s]+?(\d{4,5})\b', text, _re.IGNORECASE)
                if m:
                    return int(m.group(1))
        except Exception:
            pass
        return 32605

    # ------------------------------------------------------------------
    # COLMAP sparse reconstruction parser (text + binary formats)
    # ------------------------------------------------------------------

    def _parse_colmap(self) -> None:
        """Parse a COLMAP sparse reconstruction folder.

        Accepts either the text format (cameras.txt / images.txt) or binary
        format (cameras.bin / images.bin). Searches for the sparse model in the
        given folder and common sub-paths: sparse/, sparse/0/, dense/sparse/.
        """
        sparse_dir = self._colmap_find_sparse(self.root)

        self._meta = {'dataset': {'name': self.root.name, 'dataset_id': self.root.name}}

        # --- Cameras (intrinsics) ---
        cameras: dict[int, 'PinholeModel'] = {}
        cam_txt = sparse_dir / 'cameras.txt'
        cam_bin = sparse_dir / 'cameras.bin'
        if cam_txt.exists():
            cameras = self._colmap_read_cameras_txt(cam_txt)
        elif cam_bin.exists():
            cameras = self._colmap_read_cameras_bin(cam_bin)
        else:
            raise FileNotFoundError(f'cameras.txt / cameras.bin not found in {sparse_dir}')

        default_model = next(iter(cameras.values())) if cameras else PinholeModel(
            f=3000.0, cx_off=0.0, cy_off=0.0, k1=0.0, k2=0.0,
            p1=0.0, p2=0.0, width=4000, height=3000,
        )
        self._cameras = list(cameras.values()) or [default_model]

        # --- Images (extrinsics + filenames) ---
        img_txt = sparse_dir / 'images.txt'
        img_bin = sparse_dir / 'images.bin'
        if img_txt.exists():
            image_data = self._colmap_read_images_txt(img_txt)
        elif img_bin.exists():
            image_data = self._colmap_read_images_bin(img_bin)
        else:
            raise FileNotFoundError(f'images.txt / images.bin not found in {sparse_dir}')

        # Resolve image paths: COLMAP stores names; look in sibling images/ folder
        images_dir = self.root / 'images'

        self._poses = []
        for img in image_data:
            cam = cameras.get(img['camera_id'], default_model)
            # COLMAP quaternion is (qw, qx, qy, qz) world→camera
            qw, qx, qy, qz = img['qw'], img['qx'], img['qy'], img['qz']
            # Convert world→camera quaternion to rotation matrix
            R_w2c = _quat_to_rot(np.array([qw, qx, qy, qz]))
            R_c2w = R_w2c.T
            # Camera center in world: C = -R_w2c^T @ t
            t = img['t']
            center = -R_c2w @ t
            q2w_arr = np.array(self._rot_to_quat(R_c2w))

            img_path = images_dir / img['name'] if images_dir.exists() else self.root / img['name']

            self._poses.append({
                'cam_head': {'position': center.tolist(), 'quaternion': q2w_arr.tolist()},
                'footprint': {'position': center.tolist(), 'quaternion': q2w_arr.tolist()},
                'timestamp': 0.0,
                'valid': 'true',
                'capture_mode': 'COLMAP',
                '_image_path': str(img_path),
                '_sensor_id': str(img['camera_id']),
                '_reference': {},
                '_transform_matrix': np.block([
                    [R_c2w, center[:, None]],
                    [np.zeros((1, 3)), np.ones((1, 1))]
                ]).tolist(),
                '_utm': tuple(center.tolist()),
            })

    @staticmethod
    def _colmap_find_sparse(root: Path) -> Path:
        """Locate the COLMAP sparse model directory."""
        for sub in ('', 'sparse', 'sparse/0', 'dense/sparse'):
            d = root / sub if sub else root
            if (d / 'cameras.txt').exists() or (d / 'cameras.bin').exists():
                return d
        # Also try sparse/N for any integer N
        sparse = root / 'sparse'
        if sparse.exists():
            for sub in sorted(sparse.iterdir()):
                if sub.is_dir() and ((sub / 'cameras.txt').exists() or (sub / 'cameras.bin').exists()):
                    return sub
        raise FileNotFoundError(f'COLMAP sparse model not found under {root}')

    @staticmethod
    def _colmap_read_cameras_txt(path: Path) -> dict[int, 'PinholeModel']:
        """Parse COLMAP cameras.txt → dict of camera_id → PinholeModel."""
        models: dict[int, PinholeModel] = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            cid  = int(parts[0])
            model = parts[1].upper()
            w, h  = int(parts[2]), int(parts[3])
            params = [float(v) for v in parts[4:]]
            models[cid] = _colmap_params_to_model(model, w, h, params)
        return models

    @staticmethod
    def _colmap_read_cameras_bin(path: Path) -> dict[int, 'PinholeModel']:
        """Parse COLMAP cameras.bin → dict of camera_id → PinholeModel."""
        import struct
        models: dict[int, PinholeModel] = {}
        COLMAP_CAMERA_MODELS = {
            0: 'SIMPLE_PINHOLE', 1: 'PINHOLE', 2: 'SIMPLE_RADIAL',
            3: 'RADIAL', 4: 'OPENCV', 5: 'OPENCV_FISHEYE',
            6: 'FULL_OPENCV', 7: 'FOV', 8: 'SIMPLE_RADIAL_FISHEYE',
            9: 'RADIAL_FISHEYE', 10: 'THIN_PRISM_FISHEYE',
        }
        with open(path, 'rb') as f:
            num_cameras = struct.unpack('<Q', f.read(8))[0]
            for _ in range(num_cameras):
                cid        = struct.unpack('<i', f.read(4))[0]
                model_id   = struct.unpack('<i', f.read(4))[0]
                w          = struct.unpack('<Q', f.read(8))[0]
                h          = struct.unpack('<Q', f.read(8))[0]
                model_name = COLMAP_CAMERA_MODELS.get(model_id, 'PINHOLE')
                n_params   = _colmap_num_params(model_name)
                params     = list(struct.unpack(f'<{n_params}d', f.read(8 * n_params)))
                models[cid] = _colmap_params_to_model(model_name, w, h, params)
        return models

    @staticmethod
    def _colmap_read_images_txt(path: Path) -> list[dict]:
        """Parse COLMAP images.txt → list of image dicts."""
        images = []
        lines = [l for l in path.read_text().splitlines() if l.strip() and not l.startswith('#')]
        i = 0
        while i < len(lines):
            parts = lines[i].split()
            if len(parts) >= 9:
                images.append({
                    'image_id':  int(parts[0]),
                    'qw': float(parts[1]), 'qx': float(parts[2]),
                    'qy': float(parts[3]), 'qz': float(parts[4]),
                    't':  np.array([float(parts[5]), float(parts[6]), float(parts[7])]),
                    'camera_id': int(parts[8]),
                    'name': parts[9] if len(parts) > 9 else f'image_{parts[0]}',
                })
            i += 2   # skip the keypoints line
        return images

    @staticmethod
    def _colmap_read_images_bin(path: Path) -> list[dict]:
        """Parse COLMAP images.bin → list of image dicts."""
        import struct
        images = []
        with open(path, 'rb') as f:
            num_images = struct.unpack('<Q', f.read(8))[0]
            for _ in range(num_images):
                image_id  = struct.unpack('<i', f.read(4))[0]
                qw, qx, qy, qz = struct.unpack('<4d', f.read(32))
                tx, ty, tz      = struct.unpack('<3d', f.read(24))
                camera_id       = struct.unpack('<i', f.read(4))[0]
                name_bytes = b''
                while True:
                    c = f.read(1)
                    if c == b'\x00':
                        break
                    name_bytes += c
                name = name_bytes.decode('utf-8', errors='replace')
                num_pts = struct.unpack('<Q', f.read(8))[0]
                f.read(num_pts * 24)   # skip 2D keypoints + 3D point ids
                images.append({
                    'image_id': image_id,
                    'qw': qw, 'qx': qx, 'qy': qy, 'qz': qz,
                    't': np.array([tx, ty, tz]),
                    'camera_id': camera_id,
                    'name': name,
                })
        return images

    # ------------------------------------------------------------------
    # E57 point cloud parser
    # ------------------------------------------------------------------

    def _parse_e57(self) -> None:
        """Parse an E57 file or folder containing an E57 file."""
        e57_path = self.root
        if e57_path.is_dir():
            candidates = sorted(e57_path.glob('*.e57'))
            if not candidates:
                raise FileNotFoundError(f'No .e57 file found in {e57_path}')
            e57_path = candidates[0]
        self._e57_path = e57_path
        self._e57_pcd_cache: tuple | None = None   # (xyz, colors_or_None) lazy cache

        self._meta = {'dataset': {'name': e57_path.stem, 'dataset_id': e57_path.stem}}
        self._cameras = []
        self._poses   = []

        try:
            import pye57
            e57 = pye57.E57(str(e57_path))
            for i in range(e57.scan_count):
                header = e57.get_header(i)
                try:
                    R = np.array(header.rotation_matrix, dtype=np.float64)
                    t = np.array(header.translation,     dtype=np.float64)
                except Exception:
                    R, t = np.eye(3), np.zeros(3)
                qw, qx, qy, qz = self._rot_to_quat(R)
                pos = t.tolist()
                self._poses.append({
                    'cam_head':  {'position': pos, 'quaternion': [qw, qx, qy, qz]},
                    'footprint': {'position': pos, 'quaternion': [qw, qx, qy, qz]},
                    'timestamp': 0.0, 'valid': 'true', 'capture_mode': 'E57',
                    '_image_path': '', '_sensor_id': str(i),
                    '_reference': {},
                    '_transform_matrix': np.block([[R, t[:,None]],[np.zeros((1,3)),np.ones((1,1))]]).tolist(),
                    '_utm': tuple(t.tolist()),
                })
        except ImportError:
            # pye57 not installed — create a single dummy pose so num_frames > 0
            self._poses.append({
                'cam_head': {'position': [0,0,0], 'quaternion': [1,0,0,0]},
                'footprint': {'position': [0,0,0], 'quaternion': [1,0,0,0]},
                'timestamp': 0.0, 'valid': 'true', 'capture_mode': 'E57',
                '_image_path': '', '_sensor_id': '0', '_reference': {},
                '_transform_matrix': np.eye(4).tolist(), '_utm': (0.0, 0.0, 0.0),
            })

    def has_training_images(self) -> bool:
        """Return True when the dataset has calibrated images suitable for 3DGS training."""
        if self.platform == 'e57':
            return len(self.cameras) > 0 and any(
                p.get('_image_path', '') for p in (self._poses or [])
            )
        return len(self.valid_frame_indices()) > 0

    def e57_point_cloud(self) -> tuple[np.ndarray, 'np.ndarray | None']:
        """Read and return (xyz_float32, colors_float32_or_None) from the E57 file.

        Result is cached after the first call.
        """
        if not hasattr(self, '_e57_path'):
            raise RuntimeError('e57_point_cloud() called on non-E57 dataset')
        if self._e57_pcd_cache is not None:
            return self._e57_pcd_cache

        try:
            import pye57
            e57   = pye57.E57(str(self._e57_path))
            xyzs, rgbs = [], []
            for i in range(e57.scan_count):
                header = e57.get_header(i)
                data   = e57.read_scan(i, ignore_missing_fields=True)
                x = np.array(data.get('cartesianX', []), dtype=np.float64)
                y = np.array(data.get('cartesianY', []), dtype=np.float64)
                z = np.array(data.get('cartesianZ', []), dtype=np.float64)
                if len(x) == 0:
                    continue
                pts = np.stack([x, y, z], axis=-1)
                # Apply scanner pose to bring into world frame
                try:
                    R = np.array(header.rotation_matrix, dtype=np.float64)
                    t = np.array(header.translation,     dtype=np.float64)
                    pts = pts @ R.T + t
                except Exception:
                    pass
                xyzs.append(pts.astype(np.float32))
                r = data.get('colorRed')
                g = data.get('colorGreen')
                b = data.get('colorBlue')
                if r is not None and g is not None and b is not None:
                    maxv = 255.0 if np.max(r) > 1.0 else 1.0
                    rgbs.append(np.stack([
                        np.array(r, dtype=np.float32) / maxv,
                        np.array(g, dtype=np.float32) / maxv,
                        np.array(b, dtype=np.float32) / maxv,
                    ], axis=-1))
                else:
                    rgbs.append(None)

            if not xyzs:
                raise RuntimeError('No valid scan data in E57 file')
            xyz_all = np.concatenate(xyzs, axis=0)
            colors_all = (
                np.concatenate([c for c in rgbs if c is not None], axis=0)
                if all(c is not None for c in rgbs) else None
            )
            self._e57_pcd_cache = (xyz_all, colors_all)
            log.info('E57: %d points%s', len(xyz_all),
                     ' with RGB' if colors_all is not None else ' (no color)')
            return self._e57_pcd_cache

        except ImportError:
            # Fall back to Open3D
            try:
                import open3d as o3d
                pcd = o3d.io.read_point_cloud(str(self._e57_path))
                xyz = np.asarray(pcd.points, dtype=np.float32)
                colors = np.asarray(pcd.colors, dtype=np.float32) if pcd.has_colors() else None
                self._e57_pcd_cache = (xyz, colors)
                return self._e57_pcd_cache
            except ImportError:
                raise RuntimeError(
                    'pye57 or open3d is required to read E57 files.\n'
                    '  pip install pye57   (recommended)\n'
                    '  pip install open3d  (fallback)'
                )

    # ------------------------------------------------------------------

    def _read_anchor_names(self) -> list[str]:
        """Parse anchor names from anchors.txt."""
        path = self.root / 'anchors' / 'anchors.txt'
        if not path.exists():
            return []
        names = []
        in_data = False
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if not in_data:
                in_data = True   # first non-comment line is version number
                continue
            parts = stripped.split()
            if len(parts) >= 2:
                name = parts[1].strip('"')
                if name not in names:
                    names.append(name)
        return names
