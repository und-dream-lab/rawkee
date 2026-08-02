# =============================================================================
# RKTools.py  —  standalone HDRI → KTX2 cubemap converter
#
# RKTools.hdri2ktx2() is intentionally Maya/Blender-agnostic; it depends only
# on numpy, imageio, and scipy so it can be used from any Python environment.
# The PySide6 application classes (_ConvertWorker, RKToolsApp) are defined only
# when PySide6 is present and are never imported in the DCC plug-in paths.
# =============================================================================
import io
import os
import sys

# numpy and imageio are the only non-stdlib runtime dependencies for the core
# conversion.  Wrapping in try/except lets the module import cleanly even when
# they are absent; __main__ checks _CORE_IMPORT_ERROR before launching the UI.
try:
    import numpy as np
    import imageio.v3 as iio
    _CORE_IMPORT_ERROR = None
except ImportError as _e:
    np  = None  # type: ignore
    iio = None  # type: ignore
    _CORE_IMPORT_ERROR = str(_e)

# PySide6 is optional; its absence only disables the standalone GUI.
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
        QFileDialog, QFrame, QMessageBox,
    )
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtGui import QFont
    _HAS_PYSIDE6 = True
except ImportError:
    _HAS_PYSIDE6 = False


class RKTools():

    @staticmethod
    def hdri2ktx2(hdr_path, ktx2_path, isEXR=False, maxFaceSize=4096):
        """Converts an HDRI to a KTX2 TEXTURE_CUBE_MAP (faceCount=6).

        Input projection is auto-detected: equirectangular (2:1 aspect), cubemap cross (4:3 or
        3:4), angular/fisheye (square with dark corners), or octahedral (square, full coverage).
        Output format is auto-detected: VK_FORMAT_R32G32B32A32_SFLOAT when auto-exposure cannot
        bring values into float16 range; VK_FORMAT_R16G16B16A16_SFLOAT with log-average
        auto-exposure otherwise.
        Cubemap cross assumes OpenGL/Vulkan face order and orientation conventions.
        Face order follows Vulkan spec: +X(0) -X(1) +Y(2) -Y(3) +Z(4) -Z(5).
        Face size is auto-determined from source resolution, rounded to nearest power of 2, capped at maxFaceSize.
        """
        # struct is only needed at conversion time, not at import time.
        import struct
        # map_coordinates provides sub-pixel bilinear sampling for all four layouts.
        from scipy.ndimage import map_coordinates

        # Each face is defined by three orthonormal basis vectors in right-handed Y-up world space.
        # (label, forward, right, up)  —  right and up define the face's local texture axes.
        _FACES = [
            ('+X', ( 1,  0,  0), ( 0,  0, -1), ( 0,  1,  0)),
            ('-X', (-1,  0,  0), ( 0,  0,  1), ( 0,  1,  0)),
            ('+Y', ( 0,  1,  0), ( 1,  0,  0), ( 0,  0, -1)),
            ('-Y', ( 0, -1,  0), ( 1,  0,  0), ( 0,  0,  1)),
            ('+Z', ( 0,  0,  1), ( 1,  0,  0), ( 0,  1,  0)),
            ('-Z', ( 0,  0, -1), (-1,  0,  0), ( 0,  1,  0)),
        ]
        _KTX2_ID  = bytes([0xAB,0x4B,0x54,0x58,0x20,0x32,0x30,0xBB,0x0D,0x0A,0x1A,0x0A])  # KTX2 file-identifier magic bytes
        _DFD_SIZE = 92  # fixed size: 4-byte total + 88-byte descriptor block (4 channel samples × 16 bytes each)

        # 1. Load HDR/EXR as float32 RGB
        # The EXR plugin path tries the dedicated EXR plugin first; some builds require
        # it explicitly, while others handle it automatically through the generic path.
        if isEXR:
            try:
                hdr = iio.imread(hdr_path, plugin='EXR').astype(np.float32)
            except Exception:
                hdr = iio.imread(hdr_path).astype(np.float32)
        else:
            hdr = iio.imread(hdr_path).astype(np.float32)
        if hdr is None or hdr.size == 0:
            print(f"Error: Could not read {hdr_path}")
            return
        if hdr.ndim == 2:
            # Single-channel (e.g. luma-only) image — replicate to RGB so sampling is uniform.
            hdr = np.stack([hdr, hdr, hdr], axis=-1)
        elif hdr.shape[2] != 3:  # strip alpha and any extra EXR AOV channels
            hdr = hdr[:, :, :3]
        # Clamp NaN / ±Inf to a valid float32 range before any statistics are taken.
        _float32_max = np.finfo(np.float32).max
        hdr = np.clip(np.nan_to_num(hdr, nan=0.0, posinf=_float32_max, neginf=0.0), 0.0, _float32_max)
        H, W = hdr.shape[:2]

        # ── Layout detection ─────────────────────────────────────────────────
        # Detection must happen BEFORE the exposure calculation so that angular
        # probes can exclude their black corners from the log-average (see below).
        _HALF_MAX = 65504.0  # maximum representable value in float16 (IEEE 754 half)
        aspect    = W / H
        # Rec.709 luminance weights — match the same coefficients used later for auto-exposure.
        lum       = 0.2126*hdr[:,:,0] + 0.7152*hdr[:,:,1] + 0.0722*hdr[:,:,2]
        if abs(aspect - 2.0) < 0.2:
            # 2:1 is the canonical equirectangular panorama ratio; ±10% tolerance covers
            # common non-power-of-two resolutions (e.g. 4096×2160).
            layout = 'equirectangular'
        elif abs(aspect - 4.0/3.0) < 0.15 or abs(aspect - 3.0/4.0) < 0.15:
            # 4:3 = horizontal cross (4 columns × 3 rows); 3:4 = vertical cross.
            layout = 'cubemap_cross'
        elif abs(aspect - 1.0) < 0.05:
            # Square image: distinguish Debevec angular probes (circle on dark background)
            # from octahedral maps (full-coverage square).
            cs         = max(1, W // 20)  # corner sample region: 5% of image width
            # Sort the four corner means; use the second-lowest so one bright corner (e.g. a
            # text watermark) doesn't prevent correct angular detection.
            _cvals = sorted([
                float(np.mean(lum[:cs, :cs])),  float(np.mean(lum[:cs, -cs:])),
                float(np.mean(lum[-cs:, :cs])), float(np.mean(lum[-cs:, -cs:])),
            ])
            corner_lum = _cvals[1]
            center_lum = float(np.mean(lum[H//4:3*H//4, W//4:3*W//4]))
            layout = 'angular' if center_lum > 1e-6 and corner_lum < center_lum * 0.05 else 'octahedral'
        else:
            # No recognised aspect ratio — assume equirectangular as the safest fallback.
            layout = 'equirectangular'
        print(f"  input layout: {layout}  ({W}x{H}, aspect={aspect:.3f})")

        # ── Exposure / output-format detection ───────────────────────────────
        # Angular black corners (~21% of square) bias log-average to near-zero → ae_scale explodes.
        # Use only the circular region for lw_bar; white_pt over the full image is unaffected.
        if layout == 'angular':
            yy, xx     = np.mgrid[:H, :W].astype(np.float32)
            _circ_mask = ((xx - W/2.0)**2 + (yy - H/2.0)**2) < (min(W, H)/2.0)**2
            lum_exp    = lum[_circ_mask]
        else:
            lum_exp = lum.ravel()

        # Log-average (geometric mean) luminance — the Reinhard "key" for auto-exposure.
        # 1e-6 floor prevents log(0) from driving lw_bar to -inf on black regions.
        lw_bar   = float(np.exp(np.mean(np.log(np.maximum(lum_exp, 1e-6)))))
        # 0.18 is the standard middle-grey key used in Reinhard's photographic tone-mapping paper.
        ae_scale = 0.18 / max(lw_bar, 1e-6)
        # 99.9th-percentile white point: clips the top 0.1% of specular highlights without
        # affecting the bulk of the image content.
        white_pt = float(np.percentile(hdr * ae_scale, 99.9))
        # Choose float32 if the scene is so bright that even after auto-exposure the 99.9th
        # percentile still exceeds the float16 maximum — typically physically-calibrated EXRs.
        use32    = white_pt > _HALF_MAX
        print(f"  auto-detect: {'R32G32B32A32_SFLOAT' if use32 else 'R16G16B16A16_SFLOAT + auto-expose'}"
              f"  (lw_bar={lw_bar:.4f}, white_pt={white_pt:.4f})")

        _clip_max = _float32_max if use32 else _HALF_MAX
        if not use32:
            hdr       = hdr * ae_scale
            hdr       = np.clip(hdr, 0.0, white_pt)
            _clip_max = white_pt

        # nearest for angular prevents cval=0 artifacts at the -Z pole boundary
        _sample_mode = ('wrap'    if layout == 'equirectangular' else
                        'nearest' if layout == 'angular'         else 'constant')

        # ── Face size ─────────────────────────────────────────────────────────
        # Cubemap cross panels are already the exact face size; all other formats
        # use W/4 as a heuristic (each face ≈ 1/4 the panorama width).
        ideal = (W // 4 if W >= H else H // 4) if layout == 'cubemap_cross' else W / 4
        # Round ideal to the nearest power of 2 (required by most GPU cubemap samplers).
        TILE  = 1
        while TILE * 2 <= ideal:
            TILE *= 2
        if (ideal - TILE) > (TILE * 2 - ideal):
            TILE *= 2
        while TILE > maxFaceSize:
            TILE //= 2
        print(f"  source: {W}x{H}  →  face: {TILE}x{TILE}")

        # 2. Build coordinate grids — computed once, shared across all faces.
        # s and t are NDC coordinates in [-1, 1] with pixel-center sampling (texel offset of 0.5).
        # s increases left-to-right (along the face's right axis), t increases bottom-to-top (along up).
        idx = np.arange(TILE, dtype=np.float32)
        px_grid, py_grid = np.meshgrid(idx, idx)
        s = (2.0 * px_grid + 1.0) / TILE - 1.0
        t = 1.0 - (2.0 * py_grid + 1.0) / TILE

        # 3. Sample each face from the source image
        face_arrays = []
        for label, fwd_t, rgt_t, upd_t in _FACES:
            fwd = np.array(fwd_t, dtype=np.float32)
            rgt = np.array(rgt_t, dtype=np.float32)
            upd = np.array(upd_t, dtype=np.float32)

            # Reconstruct the world-space 3D direction for each texel by combining the face
            # forward vector with scaled right and up offsets, then normalize to unit sphere.
            x = fwd[0] + s * rgt[0] + t * upd[0]
            y = fwd[1] + s * rgt[1] + t * upd[1]
            z = fwd[2] + s * rgt[2] + t * upd[2]
            r = np.sqrt(x*x + y*y + z*z)
            x /= r;  y /= r;  z /= r

            # Project unit-sphere direction to source pixel coords (layout-dependent).
            _eps = 1e-8
        # ── Equirectangular ──────────────────────────────────────────────────
            if layout == 'equirectangular':
                # Standard lat/long: longitude from arctan2, latitude from arcsin.
                # Negating z in arctan2 aligns the front (+Z) with the image centre.
                lon   = np.arctan2(x, -z)
                lat   = np.arcsin(np.clip(y, -1.0, 1.0))
                src_x = ((lon + np.pi) / (2.0 * np.pi) * W - 0.5).ravel()
                # v=0 at top of image = +Y (up); v increases downward.
                src_y = ((0.5 - lat / np.pi) * H - 0.5).ravel()

            elif layout == 'angular':
                # Debevec angular / light-probe: centre of image = -Z direction (the direction
                # reflected directly back at the camera from the mirror ball centre).
                # r = arccos(-z)/π maps [-Z→centre, +Z→edge]; reference: PBRT v3 acos(-d.z).
                theta  = np.arccos(np.clip(-z, -1.0, 1.0))
                r_norm = theta / np.pi
                # sin(theta) = sqrt(1-z²) regardless of the sign flip; used to unproject (x,y).
                sin_th = np.maximum(np.sqrt(np.maximum(1.0 - z*z, 0.0)), _eps)
                # Guard the degenerate pole (-Z exact centre) against 0/0.
                u_a    = np.where(theta < _eps, 0.5, 0.5 + 0.5 * r_norm * (x / sin_th))
                v_a    = np.where(theta < _eps, 0.5, 0.5 - 0.5 * r_norm * (y / sin_th))
                src_x  = (u_a * W - 0.5).ravel()
                src_y  = (v_a * H - 0.5).ravel()

            elif layout == 'octahedral':
                # Full-sphere octahedral unwrap (Cigolle et al. 2014):
                # 1. L1-normalise the direction onto the octahedron surface → (px, py) in [-1,1].
                # 2. For z < 0 (lower hemisphere), fold the triangular corners inward so the
                #    entire sphere fits in the [-1,1]² square without holes.
                l1   = np.maximum(np.abs(x) + np.abs(y) + np.abs(z), _eps)
                px   = x / l1;  py = y / l1
                sx   = np.where(px >= 0,  1.0, -1.0)
                sy   = np.where(py >= 0,  1.0, -1.0)
                fp_x = np.where(z < 0, (1.0 - np.abs(py)) * sx, px)
                fp_y = np.where(z < 0, (1.0 - np.abs(px)) * sy, py)
                src_x = (( fp_x * 0.5 + 0.5) * W - 0.5).ravel()
                src_y = ((1.0 - (fp_y * 0.5 + 0.5)) * H - 0.5).ravel()

            else:  # cubemap_cross — OpenGL / Vulkan face UV convention (OpenGL ES 3.0 §3.8.10)
                # Determine which of the 6 faces owns this direction (largest absolute component).
                ax = np.abs(x);  ay = np.abs(y);  az = np.abs(z)
                x_dom  = (ax >= ay) & (ax >= az)
                y_dom  = (~x_dom) & (ay >= az)
                z_dom  = ~(x_dom | y_dom)
                plus_x = x_dom & (x >= 0);  minus_x = x_dom & (x < 0)
                plus_y = y_dom & (y >= 0);  minus_y = y_dom & (y < 0)
                plus_z = z_dom & (z >= 0)
                # ma = the dominant component magnitude; used to project onto the unit face plane.
                ma     = np.maximum(np.where(x_dom, ax, np.where(y_dom, ay, az)), _eps)
                # u_f/v_f are face-local UV in [0,1]; the expressions match OpenGL ES §3.8.10 table.
                u_f = np.where(plus_x,  (-z/ma+1)*0.5, np.where(minus_x, ( z/ma+1)*0.5,
                      np.where(plus_y,  ( x/ma+1)*0.5, np.where(minus_y, ( x/ma+1)*0.5,
                      np.where(plus_z,  ( x/ma+1)*0.5,                   (-x/ma+1)*0.5)))))
                v_f = np.where(plus_x,  (-y/ma+1)*0.5, np.where(minus_x, (-y/ma+1)*0.5,
                      np.where(plus_y,  ( z/ma+1)*0.5, np.where(minus_y, (-z/ma+1)*0.5,
                      np.where(plus_z,  (-y/ma+1)*0.5,                   (-y/ma+1)*0.5)))))
                if W >= H:  # horizontal cross: -X(0,1) +Z(1,1) +X(2,1) -Z(3,1) +Y(1,0) -Y(1,2)
                    fw, fh = W // 4, H // 3
                    col = np.where(plus_x, 2, np.where(minus_x, 0, np.where(plus_y, 1,
                          np.where(minus_y, 1, np.where(plus_z, 1, 3)))))
                    row = np.where(plus_x, 1, np.where(minus_x, 1, np.where(plus_y, 0,
                          np.where(minus_y, 2, np.where(plus_z, 1, 1)))))
                else:        # vertical cross: +Y(1,0) -X(0,1) +Z(1,1) +X(2,1) -Y(1,2) -Z(1,3)
                    fw, fh = W // 3, H // 4
                    col = np.where(plus_x, 2, np.where(minus_x, 0, np.where(plus_y, 1,
                          np.where(minus_y, 1, np.where(plus_z, 1, 1)))))
                    row = np.where(plus_x, 1, np.where(minus_x, 1, np.where(plus_y, 0,
                          np.where(minus_y, 2, np.where(plus_z, 1, 3)))))
                src_x = (col * fw + u_f * fw - 0.5).ravel()
                src_y = (row * fh + v_f * fh - 0.5).ravel()

            face = np.empty((TILE, TILE, 3), dtype=np.float32)
            for c in range(3):
                face[:, :, c] = map_coordinates(
                    hdr[:, :, c], [src_y, src_x],
                    order=1, mode=_sample_mode, cval=0.0
                ).reshape(TILE, TILE)

            face_arrays.append(np.clip(
                np.nan_to_num(face, nan=0.0, posinf=_clip_max, neginf=0.0), 0.0, _clip_max
            ))
            print(f"  face {label:3s}  sampled")

        # ── Mip chain ─────────────────────────────────────────────────────────
        # 4. Generate mip chain for each face (box filter in float32 linear space).
        # Each level halves both dimensions; the reshape groups 2×2 pixel blocks so mean(axis=(1,3))
        # averages them in a single vectorized op. Filtering is done in linear light (no gamma).
        def make_mip_chain(f32):
            mips = [f32]
            while max(mips[-1].shape[:2]) > 1:
                prev = mips[-1]
                nh   = max(1, prev.shape[0] // 2)
                nw   = max(1, prev.shape[1] // 2)
                ph   = nh * 2 if nh * 2 <= prev.shape[0] else prev.shape[0]
                pw   = nw * 2 if nw * 2 <= prev.shape[1] else prev.shape[1]
                down = prev[:ph, :pw].reshape(nh, ph//nh, nw, pw//nw, 3).mean(axis=(1, 3))
                mips.append(down.astype(np.float32))
            return mips

        mip_chains = [make_mip_chain(f) for f in face_arrays]
        num_levels = len(mip_chains[0])

        # ── KTX2 file layout ─────────────────────────────────────────────────
        # 5. Compute KTX2 file layout: header + level index + DFD + 8-byte-aligned padding + pixel data.
        # KTX2 requires pixel data to start on an 8-byte boundary; pad_bytes bridges any gap.
        # Level index size: 24 bytes per level (byteOffset + byteLength + uncompressedByteLength).
        LEVEL_IDX_SIZE = num_levels * 24
        HEADER_END     = 80 + LEVEL_IDX_SIZE + _DFD_SIZE
        pad_bytes      = (8 - HEADER_END % 8) % 8
        PIXEL_OFFSET   = HEADER_END + pad_bytes

        # 16 bytes/pixel for float32 RGBA, 8 bytes/pixel for float16 RGBA.
        _bytes_per_pixel = 16 if use32 else 8
        level_byte_sizes = [6 * max(1, TILE >> lvl)**2 * _bytes_per_pixel for lvl in range(num_levels)]

        # KTX2 stores mip levels smallest-first (level N-1) → largest-last (level 0) in the file.
        level_file_offsets = {}
        cum = 0
        for lvl in range(num_levels - 1, -1, -1):
            level_file_offsets[lvl] = PIXEL_OFFSET + cum
            cum += level_byte_sizes[lvl]

        # ── KTX2 header (80 bytes fixed) ────────────────────────────────────
        # 6. KTX2 header (80 bytes)
        hdr_bytes = _KTX2_ID
        hdr_bytes += struct.pack('<I', 109 if use32 else 97)   # VK_FORMAT_R32G32B32A32_SFLOAT or R16G16B16A16_SFLOAT
        hdr_bytes += struct.pack('<I', 4 if use32 else 2)        # typeSize: bytes/component
        hdr_bytes += struct.pack('<I', TILE)                  # pixelWidth
        hdr_bytes += struct.pack('<I', TILE)                  # pixelHeight
        hdr_bytes += struct.pack('<I', 0)                     # pixelDepth: 0 for 2D
        hdr_bytes += struct.pack('<I', 0)                     # layerCount: non-array
        hdr_bytes += struct.pack('<I', 6)                     # faceCount: 6 = TEXTURE_CUBE_MAP
        hdr_bytes += struct.pack('<I', num_levels)
        hdr_bytes += struct.pack('<I', 0)                     # supercompression: none
        hdr_bytes += struct.pack('<I', 80 + LEVEL_IDX_SIZE)   # dfdByteOffset
        hdr_bytes += struct.pack('<I', _DFD_SIZE)
        hdr_bytes += struct.pack('<I', 0)                     # kvdByteOffset
        hdr_bytes += struct.pack('<I', 0)                     # kvdByteLength
        hdr_bytes += struct.pack('<Q', 0)                     # sgdByteOffset
        hdr_bytes += struct.pack('<Q', 0)                     # sgdByteLength

        # ── Level index ───────────────────────────────────────────────────
        # 6. Level index (num_levels × 24 bytes, level 0 → N-1)
        # The third field (uncompressedByteLength) equals byteLength because we use no supercompression.
        level_idx = b''
        for lvl in range(num_levels):
            level_idx += struct.pack('<Q', level_file_offsets[lvl])
            level_idx += struct.pack('<Q', level_byte_sizes[lvl])
            level_idx += struct.pack('<Q', level_byte_sizes[lvl])

        # ── Data Format Descriptor ───────────────────────────────────────────
        # 8. Data Format Descriptor (DFD): describes the per-texel channel layout so Vulkan/KTX
        # loaders know the bit widths, signedness, and color model without inspecting pixel data.
        dfd = struct.pack('<I', _DFD_SIZE)                   # dfdTotalSize
        dfd += struct.pack('<I', 0)                           # vendorId=0, descriptorType=0
        dfd += struct.pack('<I', (88 << 16) | 2)             # descriptorBlockSize=88, versionNumber=2
        dfd += struct.pack('<I', (1 << 16) | (1 << 8) | 1)  # RGBSDA, BT709, LINEAR, flags=0
        dfd += struct.pack('<I', 0)                           # texelBlockDimensions
        dfd += bytes([16 if use32 else 8, 0, 0, 0, 0, 0, 0, 0])  # bytesPlane: plane0
        # _stride=2 for float32 (32-bit channels = 2×16-bit units); _stride=1 for float16.
        _bit_len = 31 if use32 else 15                           # bitLength = bits-per-channel minus 1
        _stride  = 2 if use32 else 1
        # Channel IDs: 0=R 1=G 2=B 15=A.  0xC0 sets FLOAT|SIGNED flags in the DFD sample.
        for bit_off, ch_id in [(0*_stride, 0), (16*_stride, 1), (32*_stride, 2), (48*_stride, 15)]:
            dfd += struct.pack('<H', bit_off)
            dfd += struct.pack('<B', _bit_len)
            dfd += struct.pack('<B', ch_id | 0xC0)           # FLOAT|SIGNED, no extra flags
            dfd += bytes(4)                                   # samplePosition[4]
            dfd += struct.pack('<I', 0xBF800000)              # sampleLower: float32(-1.0)
            dfd += struct.pack('<I', 0x3F800000)              # sampleUpper: float32(+1.0)

        # ── Pixel data ───────────────────────────────────────────────────────
        # 9. Pixel data (level N-1 first → level 0 last, per KTX2 spec).
        # Within each level the 6 faces are interleaved in Vulkan order (+X … -Z).
        # A constant alpha=1.0 channel is appended so the output format is RGBA (required by the VK_FORMAT).
        _pix_dtype = np.float32 if use32 else np.float16
        pixel_data = bytearray()
        for lvl in range(num_levels - 1, -1, -1):
            for face_mips in mip_chains:
                mip = face_mips[lvl]
                rgb = mip.astype(_pix_dtype)
                alpha = np.ones((*mip.shape[:2], 1), dtype=_pix_dtype)
                pixel_data += np.concatenate([rgb, alpha], axis=-1).tobytes()

        # 10. Write file
        try:
            total_mb = (HEADER_END + pad_bytes + sum(level_byte_sizes)) / 1_048_576
            with open(ktx2_path, 'wb') as f:
                f.write(hdr_bytes)
                f.write(level_idx)
                f.write(dfd)
                f.write(bytes(pad_bytes))
                f.write(bytes(pixel_data))
            fmt_label = 'R32G32B32A32_SFLOAT' if use32 else 'R16G16B16A16_SFLOAT'
            print(f"Saved {ktx2_path}  ({TILE}x{TILE} faces × 6, {num_levels} mip levels, "
                  f"{total_mb:.1f} MB, {fmt_label} TEXTURE_CUBE_MAP)")
        except Exception as e:
            print(f"Error: Could not write KTX2 file to {ktx2_path}: {e}")


if _HAS_PYSIDE6:
    class _StdoutCapture(io.TextIOBase):
        """Intercepts print() calls on the worker thread and routes each line to a Qt signal.

        Replacing sys.stdout with this object lets the conversion function's existing
        print() statements feed directly into the GUI log without any code changes.
        """
        def __init__(self, emit_fn):
            # emit_fn is typically a Qt Signal.emit — safe to call from non-main threads.
            self._emit = emit_fn

        def write(self, text):
            stripped = text.rstrip('\n')
            if stripped:
                self._emit(stripped)
            return len(text)

        def flush(self):
            pass


    class _ConvertWorker(QThread):
        """Runs RKTools.hdri2ktx2() on a background thread to keep the UI responsive.

        Emits 'logged' once per print() line and 'done' with a success flag when
        the conversion finishes or raises an exception.
        """
        logged = Signal(str)
        done   = Signal(bool, str)  # success flag, summary message

        def __init__(self, hdr_path, ktx2_path, is_exr, max_face_size, parent=None):
            super().__init__(parent)
            self._hdr_path      = hdr_path
            self._ktx2_path     = ktx2_path
            self._is_exr        = is_exr
            self._max_face_size = max_face_size

        def run(self):
            # Redirect stdout for the duration of the conversion so all print() output
            # goes to the GUI log.  The finally block guarantees restoration even if
            # the thread is terminated mid-run via closeEvent.
            old_stdout = sys.stdout
            sys.stdout = _StdoutCapture(self.logged.emit)
            try:
                RKTools.hdri2ktx2(
                    self._hdr_path, self._ktx2_path,
                    isEXR=self._is_exr,
                    maxFaceSize=self._max_face_size,
                )
                self.done.emit(True, "Done.")
            except Exception as exc:
                self.done.emit(False, f"Error: {exc}")
            finally:
                sys.stdout = old_stdout


    class RKToolsApp(QMainWindow):
        """Standalone PySide6 window for HDRI → KTX2 conversion.

        Provides input/output file pickers, a max-face-size selector, a monospaced
        log area, and a Convert button.  Conversion runs on _ConvertWorker so the
        UI stays responsive.  Missing pip dependencies are offered as a one-click
        install from the _on_done handler.
        """
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("RawKee: HDRI \u2192 KTX2 Converter")
            self.setMinimumWidth(640)
            self._worker = None
            self._build_ui()

        def _build_ui(self):
            """Construct all widgets and lay them out.  Called once from __init__."""
            root = QWidget()
            self.setCentralWidget(root)
            layout = QVBoxLayout(root)
            layout.setSpacing(8)
            layout.setContentsMargins(12, 12, 12, 12)

            # Input file row
            row = QHBoxLayout()
            lbl = QLabel("Input HDRI:")
            lbl.setFixedWidth(90)
            row.addWidget(lbl)
            self._input_edit = QLineEdit()
            self._input_edit.setPlaceholderText(".hdr or .exr file")
            row.addWidget(self._input_edit)
            btn = QPushButton("Browse\u2026")
            btn.setFixedWidth(80)
            btn.clicked.connect(self._browse_input)
            row.addWidget(btn)
            layout.addLayout(row)

            # Output file row
            row = QHBoxLayout()
            lbl = QLabel("Output KTX2:")
            lbl.setFixedWidth(90)
            row.addWidget(lbl)
            self._output_edit = QLineEdit()
            self._output_edit.setPlaceholderText(".ktx2 output path")
            row.addWidget(self._output_edit)
            btn = QPushButton("Browse\u2026")
            btn.setFixedWidth(80)
            btn.clicked.connect(self._browse_output)
            row.addWidget(btn)
            layout.addLayout(row)

            # Options row
            row = QHBoxLayout()
            lbl = QLabel("Max face size:")
            lbl.setFixedWidth(90)
            row.addWidget(lbl)
            self._face_combo = QComboBox()
            for s in (256, 512, 1024, 2048, 4096):
                self._face_combo.addItem(str(s), s)
            self._face_combo.setCurrentIndex(4)  # default 4096
            self._face_combo.setFixedWidth(80)
            row.addWidget(self._face_combo)
            row.addStretch()
            layout.addLayout(row)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setFrameShadow(QFrame.Shadow.Sunken)
            layout.addWidget(sep)

            layout.addWidget(QLabel("Log:"))
            self._log = QTextEdit()
            self._log.setReadOnly(True)
            self._log.setFont(QFont("Courier New", 9))
            self._log.setMinimumHeight(220)
            layout.addWidget(self._log)

            self._convert_btn = QPushButton("Convert")
            self._convert_btn.clicked.connect(self._run)
            layout.addWidget(self._convert_btn)

        def _browse_input(self):
            """Open file picker; auto-fill the output path when the output field is empty."""
            path, _ = QFileDialog.getOpenFileName(
                self, "Select HDRI", "",
                "HDR/EXR Images (*.hdr *.exr);;All Files (*)"
            )
            if not path:
                return
            self._input_edit.setText(path)
            if not self._output_edit.text():
                self._output_edit.setText(os.path.splitext(path)[0] + ".ktx2")

        def _browse_output(self):
            path, _ = QFileDialog.getSaveFileName(
                self, "Save KTX2", self._output_edit.text(),
                "KTX2 Files (*.ktx2);;All Files (*)"
            )
            if path:
                self._output_edit.setText(path)

        def _run(self):
            """Validate inputs, disable the button, then launch the worker thread."""
            hdr_path  = self._input_edit.text().strip()
            ktx2_path = self._output_edit.text().strip()
            if not hdr_path or not ktx2_path:
                self._log.append("<b>Error:</b> both input and output paths are required.")
                return

            is_exr        = os.path.splitext(hdr_path)[1].lower() == '.exr'
            max_face_size = self._face_combo.currentData()

            self._convert_btn.setEnabled(False)
            self._log.clear()
            self._log.append(f"Converting: {hdr_path}")

            self._worker = _ConvertWorker(
                hdr_path, ktx2_path, is_exr, max_face_size, self
            )
            self._worker.logged.connect(self._log.append)
            self._worker.done.connect(self._on_done)
            self._worker.start()

        def closeEvent(self, event):
            # Stop any in-progress conversion before the window is destroyed;
            # terminate() + wait() prevents the QThread from outliving the process.
            if self._worker:
                if self._worker.isRunning():
                    self._worker.terminate()
                # Always wait() regardless of running state: a recently-finished thread
                # may not be fully joined yet, which can block event-loop exit on Windows.
                self._worker.wait(3000)
                self._worker = None
            # Restore stdout if the worker was killed mid-capture
            if isinstance(sys.stdout, _StdoutCapture):
                sys.stdout = sys.__stdout__
            event.accept()
            # Hard-exit here rather than letting exec() return: scipy/numpy leave persistent
            # C-level thread pools that prevent exec() from unwinding reliably on Windows.
            os._exit(0)

        def _on_done(self, success, message):
            """Handle worker completion: show result in log, re-enable Convert button.

            If the failure message contains 'No module named', extracts the package
            name and offers a QMessageBox pip-install prompt before returning.
            """
            if not success and 'No module named' in message:
                import re, subprocess
                m   = re.search(r"No module named '([^'.]+)", message)
                pkg = m.group(1) if m else None
                if pkg:
                    reply = QMessageBox.question(
                        self, "Missing Package",
                        f"The conversion requires '{pkg}' which is not installed.\n\nInstall it now via pip?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self._log.append(f"  pip install {pkg} ...")
                        try:
                            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
                            self._log.append(
                                f"<b><span style='color:green'>{pkg} installed — click Convert to retry.</span></b>"
                            )
                        except Exception as exc:
                            self._log.append(
                                f"<b><span style='color:red'>pip install failed: {exc}</span></b>"
                            )
                    self._convert_btn.setEnabled(True)
                    if self._worker:
                        self._worker.wait()
                    self._worker = None
                    return
            color = "green" if success else "red"
            self._log.append(f"<b><span style='color:{color}'>{message}</span></b>")
            self._convert_btn.setEnabled(True)
            # wait() ensures the C++ thread is fully joined before the Python reference
            # is dropped; skipping this can leave a zombie thread that blocks exec() exit.
            if self._worker:
                self._worker.wait()
            self._worker = None


if __name__ == '__main__':
    # Pre-flight: if numpy or imageio failed to import, Qt cannot start.  Fall back
    # to a plain console prompt so the user can install the missing packages first.
    if _CORE_IMPORT_ERROR:
        # numpy or imageio missing — Qt can't start; fall back to a console pip prompt
        print(f"Missing dependency: {_CORE_IMPORT_ERROR}")
        ans = input("Install missing packages via pip? [y/N] ").strip().lower()
        if ans == 'y':
            import subprocess
            _pkgs = (["numpy"]  if np  is None else []) + \
                    (["imageio"] if iio is None else [])
            subprocess.call([sys.executable, '-m', 'pip', 'install', *_pkgs])
            print("Done. Please restart the application.")
        sys.exit(1)
    if not _HAS_PYSIDE6:
        print("Missing dependency: PySide6 is required to run the standalone application.")
        ans = input("Install PySide6 now via pip? [y/N] ").strip().lower()
        if ans == 'y':
            import subprocess
            subprocess.call([sys.executable, '-m', 'pip', 'install', 'PySide6'])
            print("Done. Please restart the application.")
        sys.exit(1)
    _app = QApplication(sys.argv)
    _win = RKToolsApp()
    _win.show()
    _app.exec()
    # os._exit bypasses Python's atexit/thread cleanup so any lingering QThread
    # cannot hold the terminal open after the window is closed on Windows.
    os._exit(0)  # force process exit so background threads don't hold the terminal
