# Processing the NavVis VLX Scan → Gaussian Splat

**Dataset:** `/home/smiller/VLX/green-room`
**Output:** `/home/smiller/VLX/processed/green-room-splat`

## Context: what this scan is

This is a **NavVis VLX mobile LiDAR scan of an indoor room** ("green-room") — a walked, room-scale interior capture, **not** a turntable/object capture. That distinction matters for how you judge the result and which flags apply:

- Ignore anything in the lidar `README.md` about turntable mode, turntable sets, elevation/radius overrides, or background masking (rembg/chroma-key) — those are for the `folder-splat` object pipeline and do not apply to a NavVis room scan processed with `run_pipeline.py splat --platform navvis`.
- Expect walls, floor, ceiling, and any furniture/fixtures in the room, viewed from the trolley's walked path through the space, not a 360° orbit around a single object.

## 0. Use the project virtual environment

```bash
cd /home/smiller/Source/rawkee.worktrees/fix-navvis-vlx-file-processing

# Create it if it doesn't exist yet
[ -d .venv ] || python3 -m venv .venv

source .venv/bin/activate
```

Run every subsequent command below **inside this activated venv** (i.e. after `source .venv/bin/activate`).

## 1. One-time environment setup

```bash
python rawkee/tools/lidar/install_workstation_deps.py --yes
```

## 2. Verify the install

```bash
python rawkee/tools/lidar/hpc_preflight_check.py
```

Fix any `ERROR` items before continuing.

## 3. Run the Gaussian splat pipeline

```bash
python rawkee/tools/lidar/run_pipeline.py splat \
    --dataset /home/smiller/VLX/green-room \
    --output  /home/smiller/VLX/processed/green-room-splat \
    --platform navvis \
    --format  x3d \
    --image-size 1024 \
    --sh-degree 3 \
    --iterations 30000 \
    --frame-stride 1 \
    --verbose
```

### Flag notes

| Flag | Value used | Why |
|---|---|---|
| `--dataset` | `/home/smiller/VLX/green-room` | Path to the NavVis dataset folder (must contain `dataset.json`) |
| `--output` | `/home/smiller/VLX/processed/green-room-splat` | Destination folder for the exported splat |
| `--platform navvis` | forced, not auto | The folder would auto-detect as NavVis anyway, but set it explicitly so the run is deterministic and doesn't silently mis-detect if the folder layout changes |
| `--format x3d` | X3D `GaussianSplats` node | Viewable directly in any X3D-capable browser/viewer without extra conversion. Switch to `--format ply` if the file needs to go into a dedicated 3DGS viewer, or `--format splat` for Luma-AI-style web viewers |
| `--image-size 1024` | training resolution | Safe default for 8–16 GB VRAM GPUs. Only raise to `2048` on a workstation GPU with ≥24 GB VRAM (RTX 4090/A6000) or better — a room scan has many frames, so higher resolution costs more time/memory than an object capture |
| `--sh-degree 3` | spherical harmonics degree | Highest quality option (0–3); needed to reproduce view-dependent effects like reflections on glossy room surfaces (windows, screens, glossy paint) |
| `--iterations 30000` | training steps | Standard 3DGS training length; a room typically needs the full 30k to resolve fine detail across a large volume. Raise to 60000 only if artefacts remain after review (see below) |
| `--frame-stride 1` | use every frame | Use all trolley frames for maximum coverage. Do **not** raise this for a room scan — skipping frames leaves gaps in coverage (untextured walls/ceiling corners) that are much more noticeable in an interior than on a small object |
| `--verbose` | on | Prints progress through NavVis loading, camera pose recovery, and each training phase so failures are easy to localize |
| `--geo-csv` | *(omitted)* | No Trimble survey CSV was provided for this scan, so the output will **not** carry real-world UTM coordinates. If a survey CSV becomes available later, re-run with `--geo-csv /path/to/survey.csv` to embed `GeoLocation`/`GeoTransform` nodes |

## 4. What a good result should look like

Before considering the job done, Muse should visually inspect the exported `.x3d` (or convert to `.ply` and load in a 3DGS viewer) and check for all of the following:

- **Complete room shell** — floor, ceiling, and all four walls are solid and continuous, with no holes or missing patches, especially at corners and where the trolley path was sparse (e.g. behind furniture, inside doorways).
- **Sharp, stable geometry at typical viewing distance** — edges of walls, door frames, and furniture should look crisp when viewed from where the trolley actually walked. Blurring is expected only when zooming in far closer than the original camera ever got.
- **No floaters** — no stray coloured blobs, hazy smears, or disconnected splats hanging in open space (mid-room, above furniture, near windows). Floaters most often appear near reflective/transparent surfaces (windows, mirrors, screens) or where camera coverage was thin.
- **Consistent color and exposure across the room** — no visible seams or brightness/color jumps where one part of the trolley path's images meet another, and no strong banding on flat walls.
- **Correct scale** — the room's real-world dimensions should look proportionate (e.g. a doorway shouldn't look oversized/undersized relative to a person-height reference) even though this run is unreferenced (no georeferencing CSV).
- **Reflective/glossy surfaces look plausible** — windows, glass, and glossy paint should show soft view-dependent highlights (thanks to `--sh-degree 3`) rather than flat, dead color or noisy speckle.
- **No large blank/black gaps** in the point density when orbiting a virtual camera through the room — thin or empty patches indicate the trolley didn't get close enough or the frame stride skipped too much data (shouldn't happen here since `--frame-stride 1` is used).

If any of the floater/incomplete-coverage/blurring symptoms show up, see the troubleshooting table below before re-running.

## 5. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `0 training images loaded` / pipeline exits immediately | NavVis dataset folder is incomplete or `dataset.json` is missing/corrupt | Verify `/home/smiller/VLX/green-room/dataset.json` and `cam/` exist and are intact; re-copy the scan from the NavVis device/export if needed |
| CUDA out of memory during training | `--image-size` too high for the GPU | Lower `--image-size` to `768` or `512` and re-run |
| Training is extremely slow | Large room, high image count, or `--image-size 2048`+ on modest hardware | Lower `--image-size`; confirm a CUDA GPU is actually being used (`hpc_preflight_check.py`) rather than falling back to CPU |
| Floater blobs near windows/mirrors/screens | Reflective/transparent surfaces are hard for any photogrammetry/3DGS method to reconstruct correctly | Expected limitation; no room-scan masking option exists for this (masking flags are folder-splat/object-only). Note it in the review rather than trying to "fix" it with turntable/masking flags |
| Holes or missing patches in walls/ceiling | Trolley path didn't get close-enough camera coverage in that area | Nothing to change in software — flag the scan itself as needing a re-walk of that area if the gap is significant |
| Room looks the wrong size / distorted proportions | Expected — no `--geo-csv` was supplied, so there's no real-world scale reference beyond the SfM-derived scale | If a Trimble survey CSV becomes available, re-run with `--geo-csv` to georeference and fix scale/orientation |
| Color seams or exposure jumps between sections of the room | Inconsistent exposure across the original camera captures (auto-exposure changes as trolley moved between bright/dark areas) | Known limitation of the source capture; cannot be corrected post-hoc by pipeline flags |
| Output file is huge / slow to load in a browser (X3D) | X3D text format doesn't cap splat count for the NavVis `splat` pipeline (unlike the Convert Splat tab's 500k cap) | Re-export with `--format ply` or `--format splat` for a smaller, faster-loading binary file |
| `pycolmap not found` / `colmap binary not found` errors | Not applicable — the NavVis `splat` command does not use COLMAP (only `folder-splat` does) | Ignore; re-check that `--platform navvis` and `--dataset` point at the NavVis folder, not a COLMAP folder |

## 6. Expected output

```
/home/smiller/VLX/processed/green-room-splat/
  green-room.x3d   ← the Gaussian splat scene (GaussianSplats node)
```

Note: no `--geo-csv` was passed (no survey CSV available), so output is not georeferenced.
