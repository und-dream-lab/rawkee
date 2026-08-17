"""Image-folder → COLMAP SfM → Gaussian splat pipeline.

Steps
-----
1. Read EXIF focal length from the first image and compute fx in pixels.
2. Run COLMAP feature extraction, exhaustive matching, and sparse reconstruction.
3. Load the reconstruction as a COLMAP ScanDataset.
4. Initialise Gaussians from the sparse point cloud.
5. Train 3DGS with gsplat.
6. Export via scan.export in the requested format.

Dependencies
------------
COLMAP must be reachable as one of:
  • Python package  ``pycolmap``  (pip install pycolmap)   ← preferred
  • System binary   ``colmap``    (in PATH or supplied via colmap_bin=)
"""
from __future__ import annotations

import logging
import os
import shutil
import struct
import subprocess
from pathlib import Path
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# EXIF helpers
# ---------------------------------------------------------------------------

# Canon APS-C sensor dimensions (mm) keyed by model substring.
# Used as fallback when FocalPlaneXResolution EXIF tags are absent.
_CANON_APSC_SENSOR = (22.3, 14.9)   # width × height in mm (T7i, 90D, etc.)

_KNOWN_SENSORS: dict[str, tuple[float, float]] = {
    'EOS REBEL T7I': _CANON_APSC_SENSOR,
    'EOS 90D':       _CANON_APSC_SENSOR,
    'EOS 80D':       _CANON_APSC_SENSOR,
    'EOS 77D':       _CANON_APSC_SENSOR,
    'EOS 850D':      _CANON_APSC_SENSOR,
    'EOS 250D':      _CANON_APSC_SENSOR,
    'EOS M50':       (22.3, 14.9),
    'EOS R':         (36.0, 24.0),   # full-frame
    'EOS R5':        (36.0, 24.0),
    'EOS R6':        (36.0, 24.0),
    'ILCE-7M3':      (35.6, 23.8),   # Sony A7 III
    'ILCE-7RM4':     (35.7, 23.8),
    'Z 6':           (35.9, 23.9),   # Nikon Z6
    'Z 7':           (35.9, 24.0),
}


def _exif_focal_px(image_path: Path) -> Optional[tuple[float, int, int]]:
    """Return (focal_px, width, height) from EXIF, or None if not determinable."""
    try:
        from PIL import Image as _PILImage
        with _PILImage.open(image_path) as im:
            w, h = im.size
            exif = im._getexif() or {}

        focal_mm = exif.get(37386)  # FocalLength tag
        if focal_mm is None:
            return None

        # Try FocalPlaneX/YResolution (tags 41486, 41487, 41488)
        fplane_xres = exif.get(41486)
        fplane_unit = exif.get(41488, 2)  # 2 = inch, 3 = cm
        if fplane_xres and fplane_xres > 0:
            unit_mm = 25.4 if fplane_unit == 2 else 10.0
            sensor_w_mm = w / (fplane_xres / unit_mm)
            fx = focal_mm * w / sensor_w_mm
            return float(fx), w, h

        # Fall back to known sensor database from camera model
        model = (exif.get(272) or '').upper()
        for key, (sw, _) in _KNOWN_SENSORS.items():
            if key in model:
                fx = focal_mm * w / sw
                return float(fx), w, h

        return None
    except Exception as exc:
        log.debug('EXIF read failed for %s: %s', image_path, exc)
        return None


# ---------------------------------------------------------------------------
# COLMAP runner
# ---------------------------------------------------------------------------

def _hloc_write_images_no_sift(
    db_path: Path,
    image_dir: Path,
    image_names: list[str],
    focal_px: Optional[float],
    image_width: int,
    image_height: int,
) -> None:
    """Write camera + image records directly into a COLMAP database via SQLite3.

    Bypasses pycolmap.import_images() (which triggers SIFT) and pycolmap.Database
    (which uses a different internal schema than hloc's COLMAPDatabase reader).
    """
    import sqlite3
    import struct

    if image_width <= 0 or image_height <= 0:
        try:
            from PIL import Image as _PIL
            with _PIL.open(image_dir / image_names[0]) as im:
                image_width, image_height = im.size
        except Exception:
            image_width, image_height = 1, 1

    f  = focal_px if focal_px else max(image_width, image_height) * 1.2
    cx, cy, k = image_width / 2.0, image_height / 2.0, 0.0
    SIMPLE_RADIAL = 2
    params_blob = struct.pack('<4d', f, cx, cy, k)

    conn = sqlite3.connect(str(db_path))
    conn.execute('INSERT INTO cameras (model, width, height, params, prior_focal_length) VALUES (?,?,?,?,?)',
                 (SIMPLE_RADIAL, image_width, image_height, params_blob, 1))
    camera_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.executemany('INSERT INTO images (name, camera_id) VALUES (?,?)',
                     [(name, camera_id) for name in image_names])
    conn.commit()
    conn.close()
    log.info('hloc DB: wrote %d image records via SQLite3 (no SIFT)', len(image_names))


def _run_hloc(
    image_dir: Path,
    db_path: Path,
    sparse_dir: Path,
    focal_px: Optional[float],
    image_width: int,
    image_height: int,
) -> None:
    """Feature extraction + matching via SuperPoint/LightGlue (hloc), then COLMAP mapper.

    Calls hloc step functions directly (no SIFT ever runs).
    """
    try:
        from hloc import extract_features, match_features
        from hloc.reconstruction import (
            create_empty_db, import_features,
            import_matches, run_reconstruction, get_image_ids,
        )
    except ImportError:
        raise ImportError(
            'hloc is not installed.  Run the workstation installer, or:\n'
            '  pip install git+https://github.com/cvg/Hierarchical-Localization'
        )

    import pycolmap

    outputs = sparse_dir.parent / '_hloc'
    outputs.mkdir(parents=True, exist_ok=True)
    sfm_pairs     = outputs / 'pairs-exhaustive.txt'
    features_path = outputs / 'features.h5'
    matches_path  = outputs / 'matches.h5'
    hloc_db       = sparse_dir / 'database.db'

    # Prefer SuperPoint+LightGlue; fall back to DISK+LightGlue if SuperGluePretrainedNetwork is absent
    try:
        from hloc.extractors.superpoint import SuperPoint as _SP  # noqa: F401
        feature_conf = extract_features.confs['superpoint_aachen']
        matcher_conf = match_features.confs['superpoint+lightglue']
        log.info('hloc: using SuperPoint+LightGlue')
    except (ImportError, ModuleNotFoundError):
        feature_conf = extract_features.confs['disk']
        matcher_conf = match_features.confs['disk+lightglue']
        log.warning('hloc: SuperGluePretrainedNetwork not installed — using DISK+LightGlue instead.')

    # Step 1: SuperPoint feature extraction → h5
    log.info('hloc: extracting SuperPoint features from %s', image_dir)
    extract_features.main(feature_conf, image_dir, image_list=None, feature_path=features_path)

    # Step 2: Build pairs — sequential window for large sets, exhaustive for small ones.
    # Exhaustive on 256 images = 32,640 pairs (~1.5 h); window=10 = ~2,500 pairs (~6 min).
    image_names = sorted(p.name for p in image_dir.iterdir()
                         if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.tif', '.tiff'))
    n_images = len(image_names)
    exhaustive_threshold = 100   # images; above this, sequential window is used
    window = 10                  # each image matches ±10 neighbours in sorted order
    with open(sfm_pairs, 'w') as f:
        if n_images <= exhaustive_threshold:
            for i, a in enumerate(image_names):
                for b in image_names[i + 1:]:
                    f.write(f'{a} {b}\n')
            n_pairs = n_images * (n_images - 1) // 2
            log.info('hloc: exhaustive pairing — %d pairs', n_pairs)
        else:
            written: set[tuple[str, str]] = set()
            for i, a in enumerate(image_names):
                for delta in range(1, window + 1):
                    b = image_names[(i + delta) % n_images]
                    key = (min(a, b), max(a, b))
                    if key not in written:
                        f.write(f'{a} {b}\n')
                        written.add(key)
            n_pairs = len(written)
            log.info('hloc: sequential window (±%d) pairing — %d pairs (vs %d exhaustive)',
                     window, n_pairs, n_images * (n_images - 1) // 2)
    match_features.main(matcher_conf, sfm_pairs, features=features_path, matches=matches_path)

    # Step 4: (Re)create COLMAP database — always start fresh to avoid stale keypoint constraints
    sparse_dir.mkdir(parents=True, exist_ok=True)
    create_empty_db(hloc_db)  # deletes existing db if present, then creates clean schema
    _hloc_write_images_no_sift(hloc_db, image_dir, image_names, focal_px, image_width, image_height)

    # Step 5: Import SuperPoint keypoints and LightGlue matches into the DB
    image_ids = get_image_ids(hloc_db)
    db = pycolmap.Database.open(hloc_db)
    import_features(image_ids, db, features_path)
    import_matches(image_ids, db, sfm_pairs, matches_path,
                   min_match_score=None, skip_geometric_verification=False)
    db.close()

    # Step 5b: Geometric verification — populates two_view_geometries so the mapper can initialise
    log.info('hloc: running geometric verification on %d pairs', n_pairs)
    pycolmap.verify_matches(hloc_db, sfm_pairs)

    # Step 6: COLMAP incremental mapper — poses + triangulation only, no feature extraction
    log.info('hloc: running COLMAP incremental mapper')
    model = run_reconstruction(sparse_dir, hloc_db, image_dir)
    if model is None:
        raise RuntimeError('hloc reconstruction: COLMAP mapper registered no images')
    log.info('hloc: registered %d images', model.num_reg_images())


def _run_colmap(
    image_dir: Path,
    work_dir: Path,
    focal_px: Optional[float] = None,
    image_width: int = 0,
    image_height: int = 0,
    matcher: str = 'exhaustive',
    colmap_bin: str = 'colmap',
    use_hloc: bool = False,
) -> Path:
    """Run COLMAP SfM on *image_dir* and write the sparse model to *work_dir/sparse/0/*.

    When *use_hloc* is True, SuperPoint+LightGlue (hloc) replace SIFT for feature
    extraction and matching; the COLMAP mapper still triangulates the reconstruction.
    Returns the path to the sparse model directory.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    db_path    = work_dir / 'colmap.db'
    sparse_dir = work_dir / 'sparse'
    sparse_dir.mkdir(exist_ok=True)

    # Skip reconstruction if a valid model already exists.
    # hloc's run_reconstruction places images.bin directly in sparse_dir (not a subdirectory),
    # so check both the directory itself and any subdirectories.
    def _has_model(p: Path) -> bool:
        return (p / 'images.bin').exists() or (p / 'images.txt').exists()

    for _sub in [sparse_dir] + sorted(sparse_dir.iterdir()) if sparse_dir.exists() else []:
        if _has_model(_sub):
            log.info('Existing COLMAP sparse model found at %s — skipping SfM', _sub)
            break
    else:
        camera_model  = 'SIMPLE_RADIAL'
        camera_params = ''
        if focal_px is not None and image_width > 0 and image_height > 0:
            cx, cy = image_width / 2.0, image_height / 2.0
            camera_params = f'{focal_px:.2f},{cx:.2f},{cy:.2f},0.0'

        if use_hloc:
            try:
                _run_hloc(image_dir, db_path, sparse_dir, focal_px, image_width, image_height)
            except (ImportError, ModuleNotFoundError) as exc:
                # Only fall back to SIFT if hloc itself is missing — not for extractor sub-deps
                if 'hloc' in str(exc).lower() or 'hierarchical' in str(exc).lower():
                    log.warning('hloc unavailable (%s) — falling back to SIFT', exc)
                    use_hloc = False
                else:
                    raise RuntimeError(f'hloc extractor dependency missing: {exc}\n'
                                       f'  Run: pip install --force-reinstall git+https://github.com/cvg/Hierarchical-Localization') from exc

        if not use_hloc:
            try:
                import pycolmap
                _run_colmap_pycolmap(
                    image_dir, db_path, sparse_dir,
                    camera_model, focal_px, image_width, image_height, matcher,
                )
            except ImportError:
                log.info('pycolmap not available; using colmap binary "%s"', colmap_bin)
                _colmap_check_binary(colmap_bin)
                _run_colmap_subprocess(
                    image_dir, db_path, sparse_dir,
                    camera_model, camera_params, matcher, colmap_bin,
                )

    # Select the sub-model with the most registered images.
    # hloc places images.bin directly in sparse_dir; COLMAP places it in sparse_dir/0/, /1/, etc.
    candidates = [sparse_dir] + [p for p in sorted(sparse_dir.iterdir()) if p.is_dir()]
    best_sub: Path | None = None
    best_n   = 0
    for sub in candidates:
        imgs_bin = sub / 'images.bin'
        imgs_txt = sub / 'images.txt'
        if not (imgs_bin.exists() or imgs_txt.exists()):
            continue
        try:
            if imgs_bin.exists():
                with open(imgs_bin, 'rb') as f:
                    n = struct.unpack('<Q', f.read(8))[0]
            else:
                n = sum(1 for ln in imgs_txt.read_text().splitlines()
                        if ln.strip() and not ln.startswith('#')) // 2
        except Exception:
            n = 0
        log.info('COLMAP model %s: %d images', sub.name or 'sparse_dir', n)
        if n > best_n:
            best_n, best_sub = n, sub
    if best_sub is None:
        raise RuntimeError(f'COLMAP produced no sparse reconstruction under {sparse_dir}')
    log.info('Using sub-model %s (%d images)', best_sub.name, best_n)
    return best_sub


def _run_colmap_pycolmap(
    image_dir: Path, db_path: Path, sparse_dir: Path,
    camera_model: str, focal_px: Optional[float],
    image_width: int, image_height: int, matcher: str,
) -> None:
    import pycolmap

    camera_mode = pycolmap.CameraMode.SINGLE

    options = pycolmap.ImageReaderOptions()
    options.camera_model = camera_model
    if focal_px is not None and image_width > 0:
        options.default_focal_length_factor = focal_px / max(image_width, image_height)

    log.info('pycolmap: extracting features from %d images in %s', len(list(image_dir.glob('*'))), image_dir)
    pycolmap.extract_features(
        database_path=db_path,
        image_path=image_dir,
        camera_mode=camera_mode,
        reader_options=options,
    )

    log.info('pycolmap: running %s matcher', matcher)
    if matcher == 'exhaustive':
        pycolmap.match_exhaustive(database_path=db_path)
    elif matcher == 'sequential':
        pycolmap.match_sequential(database_path=db_path)
    else:
        pycolmap.match_exhaustive(database_path=db_path)

    log.info('pycolmap: running incremental mapper')
    map_kwargs: dict = dict(database_path=db_path, image_path=image_dir, output_path=sparse_dir)
    try:
        opts = pycolmap.IncrementalMapperOptions()
        opts.multiple_models = False
        map_kwargs['options'] = opts
    except Exception:
        pass  # older pycolmap versions may not expose this option
    maps = pycolmap.incremental_mapping(**map_kwargs)
    if not maps:
        raise RuntimeError('pycolmap incremental_mapping returned no reconstructions')
    n_imgs = sum(r.num_reg_images() for r in maps.values())
    log.info('pycolmap: registered %d images across %d reconstructions', n_imgs, len(maps))


def _colmap_check_binary(colmap_bin: str) -> None:
    """Raise a clear error with install instructions if the colmap binary is not found."""
    import shutil
    if shutil.which(colmap_bin) is None:
        raise RuntimeError(
            f'COLMAP is not available.  Install one of the following and retry:\n'
            f'\n'
            f'  Option A (recommended) — Python bindings:\n'
            f'      pip install pycolmap\n'
            f'\n'
            f'  Option B — standalone binary:\n'
            f'      Windows: download the installer from https://github.com/colmap/colmap/releases\n'
            f'               then add the bin\\ folder to your PATH, or pass\n'
            f'               --colmap-bin "C:\\path\\to\\COLMAP.bat" to the CLI.\n'
            f'      macOS:   brew install colmap\n'
            f'      Linux:   apt install colmap  OR  conda install -c conda-forge colmap\n'
            f'\n'
            f'After installing, restart the GUI (or your terminal) so the new PATH takes effect.\n'
            f'Attempted binary path: "{colmap_bin}"'
        )


def _run_colmap_subprocess(
    image_dir: Path, db_path: Path, sparse_dir: Path,
    camera_model: str, camera_params: str, matcher: str, colmap_bin: str,
) -> None:
    def _run(cmd: list[str]) -> None:
        log.info('COLMAP: %s', ' '.join(str(c) for c in cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f'COLMAP command failed (exit {result.returncode}):\n'
                f'{result.stderr[-2000:]}'
            )

    feat_args = [
        colmap_bin, 'feature_extractor',
        '--database_path', str(db_path),
        '--image_path', str(image_dir),
        '--ImageReader.camera_model', camera_model,
        '--ImageReader.single_focal_length', '1',
        # Cap extraction resolution — 6000px images at full size take hours; 3200px is plenty for SfM
        '--ImageReader.max_image_size', '3200',
    ]
    if camera_params:
        feat_args += ['--ImageReader.camera_params', camera_params]
    _run(feat_args)

    match_cmd = matcher + '_matcher' if not matcher.endswith('_matcher') else matcher
    _run([colmap_bin, match_cmd, '--database_path', str(db_path)])

    _run([
        colmap_bin, 'mapper',
        '--database_path', str(db_path),
        '--image_path',    str(image_dir),
        '--output_path',   str(sparse_dir),
        # Relaxed thresholds for turntable captures (few shared features between distant frames)
        '--Mapper.init_min_num_inliers', '50',
        '--Mapper.min_num_matches', '15',
        '--Mapper.abs_pose_min_num_inliers', '15',
        '--Mapper.min_model_size', '3',
        # Prevent early exit — keep growing a single model instead of abandoning and restarting
        '--Mapper.multiple_models', '0',
    ])


# ---------------------------------------------------------------------------
# Sparse → point cloud helper
# ---------------------------------------------------------------------------

def _load_sparse_points(sparse_dir: Path) -> Optional[np.ndarray]:
    """Load (N,3) float32 world-space points from COLMAP sparse model."""
    bin_path = sparse_dir / 'points3D.bin'
    txt_path = sparse_dir / 'points3D.txt'
    try:
        if bin_path.exists():
            return _read_points3d_bin(bin_path)
        if txt_path.exists():
            return _read_points3d_txt(txt_path)
    except Exception as exc:
        log.warning('Could not load sparse points: %s', exc)
    return None


def _read_points3d_bin(path: Path) -> np.ndarray:
    pts = []
    with open(path, 'rb') as f:
        n = struct.unpack('<Q', f.read(8))[0]
        for _ in range(n):
            point3d_id = struct.unpack('<Q', f.read(8))[0]
            xyz = struct.unpack('<3d', f.read(24))
            rgb = struct.unpack('<3B', f.read(3))
            error = struct.unpack('<d', f.read(8))[0]
            n_tracks = struct.unpack('<Q', f.read(8))[0]
            f.read(n_tracks * 8)  # skip track data
            pts.append(xyz)
    return np.array(pts, dtype=np.float32)


def _read_points3d_txt(path: Path) -> np.ndarray:
    pts = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        pts.append([float(parts[1]), float(parts[2]), float(parts[3])])
    return np.array(pts, dtype=np.float32) if pts else np.zeros((0, 3), dtype=np.float32)


# ---------------------------------------------------------------------------
# Turntable synthetic pose helpers
# ---------------------------------------------------------------------------

def _estimate_turntable_geometry(
    sparse_dir: Path,
) -> tuple[float, float, np.ndarray]:
    """Estimate camera orbit radius, elevation angle (rad), and scene centre
    from a partial COLMAP sparse model.  Falls back to sensible defaults."""
    from rawkee.tools.lidar.dataset import _quat_to_rot

    cam_positions: list[np.ndarray] = []
    imgs_bin = sparse_dir / 'images.bin'
    if imgs_bin.exists():
        try:
            with open(imgs_bin, 'rb') as f:
                n = struct.unpack('<Q', f.read(8))[0]
                for _ in range(n):
                    struct.unpack('<i', f.read(4))                  # image_id
                    qw, qx, qy, qz = struct.unpack('<4d', f.read(32))
                    tx, ty, tz     = struct.unpack('<3d', f.read(24))
                    struct.unpack('<i', f.read(4))                  # camera_id
                    name_bytes = b''
                    while True:
                        c = f.read(1)
                        if c == b'\x00':
                            break
                        name_bytes += c
                    num_pts = struct.unpack('<Q', f.read(8))[0]
                    f.read(num_pts * 24)
                    R_w2c   = _quat_to_rot(np.array([qw, qx, qy, qz]))
                    cam_pos = -R_w2c.T @ np.array([tx, ty, tz])
                    cam_positions.append(cam_pos)
        except Exception as exc:
            log.warning('Could not read COLMAP image poses: %s', exc)

    if not cam_positions:
        log.warning('No camera positions found; using default turntable geometry')
        return 1.0, np.radians(25.0), np.zeros(3)

    pts = _load_sparse_points(sparse_dir)
    center = np.mean(pts, axis=0) if (pts is not None and len(pts) > 10) \
             else np.mean(cam_positions, axis=0)

    offsets  = np.array(cam_positions) - center
    h_dists  = np.sqrt(offsets[:, 0]**2 + offsets[:, 2]**2)
    radii    = np.sqrt(h_dists**2 + offsets[:, 1]**2)
    elevs    = np.arctan2(offsets[:, 1], h_dists)

    radius    = float(np.median(radii))
    elevation = float(np.median(elevs))

    # Clamp elevation to at least 15° — a near-horizontal orbit means COLMAP gave
    # a badly-fragmented reconstruction; 25° is a safe default for real turntable shots.
    _MIN_ELEV = np.radians(15.0)
    if abs(elevation) < _MIN_ELEV:
        log.warning('Estimated elevation %.1f° is too flat (likely a bad COLMAP model); '
                    'clamping to %.0f°', np.degrees(elevation), np.degrees(_MIN_ELEV))
        elevation = np.copysign(_MIN_ELEV, elevation) if elevation != 0 else _MIN_ELEV

    log.info('Turntable geometry: radius=%.3f m  elevation=%.1f°  centre=%s',
             radius, np.degrees(elevation), np.round(center, 3))
    return radius, elevation, center


def _build_turntable_poses(
    n_per_set: int,
    radius: float,
    elevation: float,
    center: np.ndarray,
    n_sets: int = 2,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return (R_w2c, t_w2c) COLMAP-convention poses for a turntable capture.

    Elevations are distributed linearly from +elevation to -elevation across
    the n_sets passes, so:
      n_sets=1 → single ring at +elevation
      n_sets=2 → +elevation (upright), -elevation (flipped)
      n_sets=4 → +elevation, +elevation/3, -elevation/3, -elevation
    Azimuths are uniformly spaced 0→360° within each set.
    """
    poses: list[tuple[np.ndarray, np.ndarray]] = []
    for i_set in range(n_sets):
        if n_sets == 1:
            elev = elevation
        else:
            # Linear interpolation from +elevation to -elevation
            t = i_set / (n_sets - 1)
            elev = elevation * (1.0 - 2.0 * t)
        for i in range(n_per_set):
            az = i * 2.0 * np.pi / n_per_set
            cam_pos = center + np.array([
                radius * np.cos(elev) * np.sin(az),
                radius * np.sin(elev),
                radius * np.cos(elev) * np.cos(az),
            ])
            fwd   = center - cam_pos
            fwd  /= np.linalg.norm(fwd)
            world_up = np.array([0.0, 1.0, 0.0])
            right = np.cross(fwd, world_up)
            if np.linalg.norm(right) < 1e-6:
                world_up = np.array([0.0, 0.0, 1.0])
                right = np.cross(fwd, world_up)
            right /= np.linalg.norm(right)
            up    = np.cross(right, fwd)
            # OpenCV convention: +X=right, +Y=down, +Z=into scene
            R_c2w = np.column_stack([right, -up, fwd])
            R_w2c = R_c2w.T
            t_w2c = -R_w2c @ cam_pos
            poses.append((R_w2c.astype(np.float32), t_w2c.astype(np.float32)))
    return poses


def _build_masks(
    image_paths: list[Path],
    masks_dir: Optional[Path] = None,
    auto_mask: bool = False,
    chroma_rgb: Optional[tuple] = None,
    chroma_tolerance: float = 30.0,
    cache_dir: Optional[Path] = None,
    mask_erosion_px: int = 0,
) -> Optional[dict[str, np.ndarray]]:
    """Return {image_stem: mask_uint8(H,W)} where 255=foreground, 0=background.

    Priority:
      1. masks_dir (explicit folder of pre-made mask images, matched by stem)
      2. auto_mask via rembg (generates masks and caches to cache_dir/masks/)
      3. chroma_rgb colour-key (HSV threshold on the specified background colour)
    Returns None if none of the above are requested/available.
    """
    from PIL import Image as _PIL

    result: dict[str, np.ndarray] = {}

    # ── 1. Explicit masks directory ───────────────────────────────────────
    if masks_dir is not None and masks_dir.is_dir():
        for img_path in image_paths:
            for ext in ('.png', '.jpg', '.jpeg', '.tiff', '.tif'):
                mp = masks_dir / (img_path.stem + ext)
                if mp.exists():
                    m = np.array(_PIL.open(mp).convert('L'))
                    result[img_path.stem] = (m > 127).astype(np.uint8) * 255
                    break
        if result:
            log.info('Loaded %d masks from %s', len(result), masks_dir)
            return _erode_masks(result, mask_erosion_px)

    # ── 2. rembg auto-masking ─────────────────────────────────────────────
    if auto_mask:
        cache = (cache_dir / 'masks') if cache_dir else None
        if cache:
            cache.mkdir(parents=True, exist_ok=True)
        try:
            from rembg import remove as _rembg_remove
        except ImportError:
            log.warning('rembg not installed — cannot auto-mask: pip install "rembg[gpu]"')
            auto_mask = False
        except BaseException as _re:
            # onnxruntime C extension can raise AttributeError/_ARRAY_API errors that bypass
            # normal except Exception; catch BaseException to always fall back gracefully
            log.warning('rembg import error (%s) — falling back to chroma-key masking', _re)
            auto_mask = False

        # Abort if the u2net model hasn't been pre-downloaded (avoids silent 176 MB download)
        if auto_mask:
            from pathlib import Path as _Path
            _u2net = _Path.home() / '.u2net' / 'u2net.onnx'
            if not _u2net.exists():
                log.warning(
                    'u2net.onnx not found at %s — skipping rembg auto-mask to avoid downloading '
                    '176 MB mid-run. Pre-download by running install_workstation_deps.py.',
                    _u2net)
                auto_mask = False

        if auto_mask:
            log.info('Auto-masking %d images with rembg (first run downloads model)…',
                     len(image_paths))
            for img_path in image_paths:
                cache_path = (cache / (img_path.stem + '_mask.png')) if cache else None
                if cache_path and cache_path.exists():
                    m = np.array(_PIL.open(cache_path).convert('L'))
                else:
                    try:
                        img_bytes = img_path.read_bytes()
                        out = _rembg_remove(img_bytes)
                        rgba = np.array(_PIL.open(__import__('io').BytesIO(out)).convert('RGBA'))
                        m = rgba[:, :, 3]   # alpha channel = foreground mask
                        if cache_path:
                            _PIL.fromarray(m).save(cache_path)
                    except Exception as exc:
                        log.debug('rembg failed for %s: %s', img_path.name, exc)
                        continue
                result[img_path.stem] = (m > 127).astype(np.uint8) * 255
            if result:
                log.info('rembg masks generated for %d / %d images',
                         len(result), len(image_paths))
                return _erode_masks(result, mask_erosion_px)

    # ── 3. Chroma-key colour mask ─────────────────────────────────────────
    if chroma_rgb is not None:
        import colorsys
        r0, g0, b0 = [x / 255.0 for x in chroma_rgb]
        h0, s0, v0 = colorsys.rgb_to_hsv(r0, g0, b0)
        tol_h = chroma_tolerance / 360.0
        tol_sv = chroma_tolerance / 100.0
        log.info('Chroma-key masking: background colour RGB%s  tolerance=%.0f',
                 chroma_rgb, chroma_tolerance)
        for idx, img_path in enumerate(image_paths):
            if idx > 0 and idx % 32 == 0:
                log.info('Chroma-key masking: %d / %d images', idx, len(image_paths))
            try:
                rgb = np.array(_PIL.open(img_path).convert('RGB')).astype(np.float32) / 255.0
                # Vectorised RGB → HSV
                Cmax = rgb.max(axis=-1); Cmin = rgb.min(axis=-1); delta = Cmax - Cmin
                with np.errstate(divide='ignore', invalid='ignore'):
                    hue = np.where(delta == 0, 0.0,
                          np.where(Cmax == rgb[..., 0], (rgb[..., 1] - rgb[..., 2]) / delta % 6,
                          np.where(Cmax == rgb[..., 1], (rgb[..., 2] - rgb[..., 0]) / delta + 2,
                                                         (rgb[..., 0] - rgb[..., 1]) / delta + 4))) / 6.0
                    sat = np.where(Cmax == 0, 0.0, delta / Cmax)
                val = Cmax
                is_bg = ((np.abs(hue - h0) < tol_h) &
                         (np.abs(sat - s0) < tol_sv) &
                         (np.abs(val - v0) < tol_sv))
                mask = np.where(is_bg, np.uint8(0), np.uint8(255))
                result[img_path.stem] = mask
            except Exception as exc:
                log.debug('Chroma key failed for %s: %s', img_path.name, exc)
        if result:
            log.info('Chroma-key masks generated for %d images', len(result))
            return _erode_masks(result, mask_erosion_px)

    return None


def _erode_masks(masks: dict[str, np.ndarray], erosion_px: int) -> dict[str, np.ndarray]:
    """Erode each foreground mask inward by erosion_px pixels (removes uncertain edges)."""
    if erosion_px <= 0:
        return masks
    from scipy.ndimage import binary_erosion
    out = {}
    for stem, m in masks.items():
        eroded = binary_erosion(m > 127, iterations=erosion_px).astype(np.uint8) * 255
        out[stem] = eroded
    log.info('Mask erosion applied: %d px inward on %d masks', erosion_px, len(out))
    return out


def _apply_mask(img_rgb8: np.ndarray, mask: Optional[np.ndarray]) -> np.ndarray:
    """Zero out background pixels (mask==0). mask must be same H×W as img."""
    if mask is None:
        return img_rgb8
    h, w = img_rgb8.shape[:2]
    if mask.shape != (h, w):
        from PIL import Image as _PIL
        mask = np.array(_PIL.fromarray(mask).resize((w, h), _PIL.NEAREST))
    fg = mask > 127
    out = img_rgb8.copy()
    out[~fg] = 0
    return out


def _load_images_turntable(
    image_paths: list[Path],
    poses: list[tuple[np.ndarray, np.ndarray]],
    focal_px: float,
    cx: float,
    cy: float,
    target_size: int,
    device: 'torch.device',
    masks: Optional[dict] = None,
) -> tuple[list, list, list, list]:
    """Load and undistort images using synthetic turntable poses.
    Returns (images, Rs, ts, focals) parallel lists.
    """
    import torch
    from PIL import Image as _PIL
    scale  = target_size / max(cx * 2, cy * 2)
    f_out  = focal_px * scale
    images, Rs, ts, focals = [], [], [], []
    for img_path, (R_w2c, t_w2c) in zip(image_paths, poses):
        if not img_path.exists():
            continue
        try:
            rgb = np.array(_PIL.open(img_path).convert('RGB').resize(
                (target_size, target_size), _PIL.LANCZOS))
            if masks:
                rgb = _apply_mask(rgb, masks.get(img_path.stem))
            img_t = torch.from_numpy(rgb).float().div(255.0).permute(2, 0, 1)
            images.append(img_t.to(device))
            Rs.append(R_w2c)
            ts.append(t_w2c)
            focals.append((f_out, f_out))
        except Exception as exc:
            log.debug('Skip %s: %s', img_path.name, exc)
    return images, Rs, ts, focals


# ---------------------------------------------------------------------------
# Public pipeline class
# ---------------------------------------------------------------------------

class FolderSplatPipeline:
    """COLMAP + 3DGS pipeline for a plain folder of images.

    Parameters
    ----------
    image_size:    Training image resolution (square, pixels).
    sh_degree:     Spherical harmonics degree (0–3).
    iterations:    3DGS training iterations.
    matcher:       COLMAP feature matcher: 'exhaustive' or 'sequential'.
    turntable_mode: If True, bypass COLMAP’s mapper and use synthetic circular
                   camera poses derived from the turntable geometry.  Recommended
                   for all turntable captures; trains on ALL images.
    colmap_bin:    Path to the colmap binary (used if pycolmap is not installed).
    """

    def __init__(
        self,
        image_size:             int   = 512,
        sh_degree:              int   = 3,
        iterations:             int   = 10_000,
        matcher:                str   = 'exhaustive',
        turntable_mode:         bool  = False,
        n_sets:                 int   = 1,
        turntable_elevation_deg: float = 0.0,
        turntable_radius:       float = 0.0,
        masks_dir:              Optional[Path] = None,
        auto_mask:              bool  = False,
        chroma_rgb:             Optional[tuple] = None,
        chroma_tolerance:       float = 30.0,
        mask_erosion_px:        int   = 8,
        use_hloc:               bool  = False,
        colmap_bin:             str   = 'colmap',
    ) -> None:
        self.image_size              = image_size
        self.sh_degree               = sh_degree
        self.iterations              = iterations
        self.matcher                 = matcher
        self.turntable_mode          = turntable_mode
        self.n_sets                  = n_sets
        self.turntable_elevation_deg = turntable_elevation_deg
        self.turntable_radius        = turntable_radius
        self.masks_dir               = Path(masks_dir) if masks_dir else None
        self.auto_mask               = auto_mask
        self.chroma_rgb              = chroma_rgb
        self.chroma_tolerance        = chroma_tolerance
        self.mask_erosion_px         = mask_erosion_px
        self.use_hloc                = use_hloc
        self.colmap_bin              = colmap_bin

    def run(
        self,
        image_dir:         Path | str,
        output_dir:        Path | str,
        output_format:     str  = 'x3d',
        focal_px:          Optional[float] = None,
        decode_sh:         bool = False,
        frame_stride:      int  = 1,
        n_sets:            int  = -1,
        densify_grad_mode: str  = '2d',
        densify_until:     int  = 0,
    ) -> Path:
        """Run the full pipeline.

        Parameters
        ----------
        image_dir:      Folder containing only image files (JPEG/PNG/TIFF/…).
        output_dir:     Root output directory; COLMAP work files go in a subfolder.
        output_format:  Splat export format (x3d/x3dv/x3dj/ply/splat/glb).
        focal_px:       Camera focal length in pixels (auto-extracted from EXIF if None).
        decode_sh:      Pre-decode SH to RGB on export.
        frame_stride:   Use every N-th registered image for training (SfM mode only).
        n_sets:         Number of turntable capture sets (default 2 = upright + inverted).

        Returns
        -------
        Path to the exported splat file.
        """
        from .splat_pipeline import SplatPipeline, _init_gaussians_from_pcd, _train, _dist_init, _dist_teardown
        from .dataset import ScanDataset
        from .export import export_splat

        if n_sets < 1:
            n_sets = self.n_sets

        image_dir  = Path(image_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        work_dir = output_dir / '_colmap_work'

        # ── Step 1: focal length from EXIF ─────────────────────────────
        images = sorted(
            p for p in image_dir.iterdir()
            if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp')
        )
        if not images:
            raise ValueError(f'No image files found in {image_dir}')

        # Always read image dimensions from the first image
        img_w = img_h = 0
        try:
            from PIL import Image as _PIL
            with _PIL.open(images[0]) as im:
                img_w, img_h = im.size
        except Exception:
            pass

        if focal_px is None:
            exif_result = _exif_focal_px(images[0])
            if exif_result:
                focal_px, img_w, img_h = exif_result
                log.info('EXIF focal length: %.1f px  (%dx%d)', focal_px, img_w, img_h)
            else:
                log.warning('Could not determine focal length from EXIF; COLMAP will estimate it')
        else:
            log.info('Using supplied focal length: %.1f px  (%dx%d)', focal_px, img_w, img_h)

        # ── Step 2: COLMAP SfM ─────────────────────────────────────────
        # In turntable mode COLMAP is only used to estimate orbit geometry;
        # a failure (common on textureless/reflective objects) is non-fatal.
        log.info('Running COLMAP SfM on %d images in %s', len(images), image_dir)
        try:
            sparse_dir = _run_colmap(
                image_dir, work_dir,
                focal_px=focal_px,
                image_width=img_w,
                image_height=img_h,
                matcher=self.matcher,
                colmap_bin=self.colmap_bin,
                use_hloc=self.use_hloc,
            )
        except RuntimeError as _colmap_err:
            if not self.turntable_mode:
                raise
            log.warning('COLMAP failed (%s) — turntable mode will use default orbit geometry',
                        _colmap_err)
            sparse_dir = work_dir / 'sparse' / '0'
            sparse_dir.mkdir(parents=True, exist_ok=True)

        import torch
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # ── Turntable mode: synthetic poses for all images ──────────────
        if self.turntable_mode:
            log.info('Turntable mode: building synthetic circular camera poses')
            radius, elevation, center = _estimate_turntable_geometry(sparse_dir)            # Apply user overrides if provided
            if self.turntable_elevation_deg > 0:
                elevation = np.radians(self.turntable_elevation_deg)
                log.info('Turntable elevation overridden to %.1f°', self.turntable_elevation_deg)
            if self.turntable_radius > 0:
                radius = self.turntable_radius
                log.info('Turntable radius overridden to %.3f m', self.turntable_radius)

            # Build background masks (chroma-key / rembg / explicit dir)
            masks = _build_masks(
                images,
                masks_dir=self.masks_dir or (image_dir / 'masks' if (image_dir / 'masks').is_dir() else None),
                auto_mask=self.auto_mask,
                chroma_rgb=self.chroma_rgb,
                chroma_tolerance=self.chroma_tolerance,
                cache_dir=work_dir,
                mask_erosion_px=self.mask_erosion_px,
            )
            if masks:
                log.info('Background masking active: %d masks loaded', len(masks))

            n_per_set = len(images) // n_sets
            # Build poses around origin so the rock is centred at (0,0,0) in the export
            poses = _build_turntable_poses(n_per_set, radius, elevation, np.zeros(3), n_sets)
            cx = img_w / 2.0
            cy = img_h / 2.0
            fx = focal_px if focal_px else (img_w * 0.8)  # rough fallback
            log.info('Turntable: %d images × %d sets → %d synthetic poses',
                     n_per_set, n_sets, len(poses))
            all_images, all_Rs, all_ts, all_focals = _load_images_turntable(
                images[:len(poses)], poses, fx, cx, cy, self.image_size, device,
                masks=masks,
            )
            xyz_sparse = _load_sparse_points(sparse_dir)
            if xyz_sparse is not None and len(xyz_sparse) > 0:
                # Translate sparse points to origin so they match the centred camera poses
                xyz_sparse -= center
                log.info('Initialising from %d sparse COLMAP points (centred at origin)', len(xyz_sparse))
                gaussians = _init_gaussians_from_pcd(xyz_sparse, device, self.sh_degree)
            else:
                # Fall back: random sphere around origin
                sphere = 0.3 * np.random.randn(5_000, 3).astype(np.float32)
                gaussians = _init_gaussians_from_pcd(sphere, device, self.sh_degree)
            if not all_images:
                raise RuntimeError('No training images could be loaded')
            log.info('%d turntable training images loaded', len(all_images))

        else:
            # ── Standard SfM mode ──────────────────────────────────────
            # Point ScanDataset at the best sub-model directly
            dataset = ScanDataset(sparse_dir, platform='colmap')

            # Patch image paths to point to the actual image_dir
            for pose in dataset._poses:
                name = Path(pose.get('_image_path', '')).name
                if name:
                    pose['_image_path'] = str(image_dir / name)

            n_frames = dataset.num_frames
            if n_frames == 0:
                raise RuntimeError('COLMAP registered 0 images — reconstruction failed')
            log.info('COLMAP registered %d images', n_frames)

            valid  = dataset.valid_frame_indices()
            frames = valid[::frame_stride]
            log.info('Using %d training frames (stride=%d)', len(frames), frame_stride)

            xyz_sparse = _load_sparse_points(sparse_dir)
            if xyz_sparse is not None and len(xyz_sparse) > 0:
                log.info('Initialising from %d sparse COLMAP points', len(xyz_sparse))
                gaussians = _init_gaussians_from_pcd(xyz_sparse, device, self.sh_degree)
            else:
                gaussians = _init_gaussians_from_pcd(
                    np.random.randn(10_000, 3).astype(np.float32) * 0.5,
                    device, self.sh_degree,
                )

            from .splat_pipeline import _load_training_images
            all_images, all_Rs, all_ts, all_focals = [], [], [], []
            for cam_idx in range(len(dataset.cameras)):
                imgs, Rs, ts, focs = _load_training_images(
                    dataset, frames, cam_idx, self.image_size, device
                )
                all_images.extend(imgs)
                all_Rs.extend(Rs)
                all_ts.extend(ts)
                all_focals.extend(focs)

            if not all_images:
                raise RuntimeError('No training images could be loaded from COLMAP dataset')
        log.info('%d training images loaded', len(all_images))

        # ── Step 6: train ──────────────────────────────────────────────
        rank, world_size = _dist_init()
        try:
            trained = _train(
                gaussians, all_images, all_Rs, all_ts,
                focal=all_focals,
                img_wh=(self.image_size, self.image_size),
                device=device,
                iterations=self.iterations,
                rank=rank,
                world_size=world_size,
                sh_degree=self.sh_degree,
                densify_grad_mode=densify_grad_mode,
                densify_until=densify_until if densify_until > 0 else -1,
            )
        finally:
            _dist_teardown()

        if rank != 0:
            return output_dir

        # ── Step 7: export ─────────────────────────────────────────────
        # COLMAP data is not in ROS Z-up space — skip the ROS→X3D coord transform
        stem = image_dir.name
        out_path = export_splat(
            gaussians=trained,
            output_dir=output_dir,
            stem=stem,
            fmt=output_format,
            sh_degree=self.sh_degree,
            decode_sh=decode_sh,
            apply_coord_transform=False,
        )
        log.info('FolderSplatPipeline complete → %s', out_path)
        return out_path
