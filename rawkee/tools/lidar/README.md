# RawKee Lidar

**RawKee Lidar** (`rawkee.tools.lidar`) is an open-source GPU-accelerated pipeline that converts raw data from mobile LiDAR scanners and photogrammetry platforms into interoperable 3D assets — textured polygon meshes and Gaussian splat radiance fields — ready for display in web browsers, game engines, XR headsets, and any X3D-capable viewer.

It is part of the [RawKee](https://github.com/und-dream-lab/rawkee) project developed at the University of North Dakota DREAM Lab.

---

## Table of Contents

1. [What RawKee Lidar Does](#1-what-rawkee-lidar-does)
2. [Supported Input Platforms](#2-supported-input-platforms)
3. [Supported Output Formats](#3-supported-output-formats)
4. [Desktop User Guide](#4-desktop-user-guide)
   - 4a. [Convert Splat Tab](#4a-convert-splat-tab)
   - 4b. [Folder → Gaussian Splat Pipeline](#4b-folder--gaussian-splat-pipeline)
5. [Desktop Installation](#5-desktop-installation)
6. [HPC / SLURM Usage](#6-hpc--slurm-usage)
7. [HPC System Administrator Guide](#7-hpc-system-administrator-guide)

---

## 1. What RawKee Lidar Does

RawKee Lidar reads raw scan data from a variety of mobile LiDAR and photogrammetry platforms and runs two parallel processing pipelines:

| Pipeline | What it builds | Best for |
|---|---|---|
| **Mesh** | Textured polygon mesh via Poisson surface reconstruction | CAD, GIS, BIM, print, real-time rendering |
| **Gaussian Splat** | 3D Gaussian splat radiance field via differentiable rasterisation | Photorealistic web/XR viewing, neural rendering |

Both pipelines support **georeferenced output**: when surveyed control points are available the output is positioned in a real-world coordinate system (UTM) and wrapped in the appropriate X3D geospatial nodes (`GeoLocation` / `GeoTransform`).

The mesh pipeline additionally generates an **HDRI environment map** from the scan cameras and embeds it as a `PhysicalMaterial` + `EnvironmentLight` + `ImageCubeMapTexture` in the X3D output, giving photorealistic image-based lighting out of the box.

---

## 2. Supported Input Platforms

RawKee Lidar auto-detects the input format from the file path. Pass any of the following to `--dataset`:

| Platform | `--platform` value | What to pass to `--dataset` |
|---|---|---|
| **NavVis VLX / G11** (rec-v4) | `navvis` | Dataset folder (contains `dataset.json`) |
| **Agisoft Metashape** | `metashape` | `.psx` project file |
| **Meshroom / AliceVision** | `meshroom` | `.mg` project file |
| **Pix4Dmapper** | `pix4d` | `.p4d` project file or project folder |
| **COLMAP** | `colmap` | Sparse reconstruction folder (`cameras.txt` / `cameras.bin`) |
| **E57 point cloud** | `e57` | `.e57` file |
| `auto` *(default)* | — | Any of the above; format is inferred automatically |

> **RealityCapture users:** RealityCapture's native `.rcproj` format is proprietary and cannot be read directly. Use one of these two export paths instead:
>
> - **Option A** — Export *Camera positions and orientations* as **Metashape cameras.xml**, then use `--platform metashape`.
> - **Option B** *(recommended)* — Export as **COLMAP** format, then use `--platform colmap` (or let auto-detection pick it up). RealityCapture supports COLMAP export natively under *Export → Registration → COLMAP*.

### Georeferencing

For NavVis datasets, provide a **Trimble survey CSV** (semicolon-delimited: `point_id;lat;lon;elev`) via `--geo-csv`. The pipeline converts WGS84 coordinates to UTM automatically using `pyproj` (with a pure-Python Helmert fallback if pyproj is not installed).

For Metashape, Meshroom, and Pix4D, georeferencing is read directly from the project file — no separate CSV is needed.

---

## 3. Supported Output Formats

### Mesh pipeline outputs

| Format | Flag | Notes |
|---|---|---|
| **X3D** *(default)* | `--format x3d` | Full PBR materials, EnvironmentLight, geospatial nodes |
| **X3DV** | `--format x3dv` | X3D Classic (VRML-style) encoding |
| **X3DJ** | `--format x3dj` | X3D JSON encoding |
| **OBJ + MTL** | `--format obj` | Widely compatible; no PBR or georef |
| **GLB** | `--format glb` | glTF 2.0 binary; compatible with Three.js, Babylon.js, Unity, Unreal |

### Gaussian splat pipeline outputs

| Format | Flag | Notes |
|---|---|---|
| **X3D** *(default)* | `--format x3d` | `GaussianSplats` node (X3D 4.1 draft); geospatial nodes included when georeferenced |
| **X3DV** | `--format x3dv` | X3D Classic encoding |
| **X3DJ** | `--format x3dj` | X3D JSON encoding |
| **PLY** | `--format ply` | 3DGS-standard binary PLY; compatible with Gaussian Splatting viewers |
| **SPLAT** | `--format splat` | Packed 32-byte binary; compatible with Luma AI web viewer and similar tools |
| **GLB** | `--format glb` | glTF 2.0 with `KHR_gaussian_splatting` extension |

---

## 4. Desktop User Guide

### Launching the GUI

```bash
python rawkee/tools/lidar/scan_gui.py
```

The GUI window has two tabs — **Mesh** and **Gaussian Splat** — sharing a common options panel at the top.

#### Common options panel

| Control | Description |
|---|---|
| **Platform** | Auto-detected when you browse; override manually if needed |
| **Output format** | Select from the supported formats for each pipeline |
| **Geo CSV** | Optional Trimble survey CSV for NavVis georeferencing |
| **Skip georeferencing** | Check to suppress georef even if a CSV is provided |
| **EPSG code** | Target projected CRS (default 32605 = UTM Zone 5N) |

#### Browsing for your dataset

Click the **Browse ▾** button to open a menu:

- **Browse Folder…** — for NavVis dataset folders or Pix4D project folders
- **Browse .psx File…** — for Metashape projects
- **Browse .mg File…** — for Meshroom projects
- **Browse .p4d File…** — for Pix4D `.p4d` files
- **Browse .e57 File…** — for E57 point clouds
- **Browse COLMAP Folder…** — for COLMAP sparse reconstruction folders

After selection, the platform label auto-updates to show what was detected.

#### Running a pipeline

1. Set the **Dataset** path and **Output folder**.
2. Adjust any pipeline-specific parameters (Poisson depth, atlas size, iterations, etc.).
3. Click **Run Mesh Pipeline** or **Run Splat Pipeline**.
4. Progress appears in the log panel. A dialog confirms completion or reports errors.

### Running from the command line

```bash
# Mesh pipeline
python rawkee/tools/lidar/run_pipeline.py mesh \
    --dataset /path/to/dataset \
    --output  /path/to/output \
    --format  x3d \
    --geo-csv /path/to/survey.csv \
    --verbose

# Gaussian splat pipeline
python rawkee/tools/lidar/run_pipeline.py splat \
    --dataset /path/to/dataset \
    --output  /path/to/output \
    --format  x3d \
    --verbose
```

Run `python run_pipeline.py mesh --help` or `splat --help` for the full list of parameters.

#### Key CLI flags (both pipelines)

| Flag | Default | Description |
|---|---|---|
| `--platform` | `auto` | `navvis` \| `metashape` \| `meshroom` \| `pix4d` \| `colmap` \| `e57` \| `auto` |
| `--format` | `x3d` | Output format (see tables above) |
| `--geo-csv FILE` | — | Trimble survey CSV for NavVis georeferencing |
| `--no-georef` | off | Skip georeferencing even if `--geo-csv` is set |
| `--epsg INT` | `32605` | Target projected CRS EPSG code |
| `--verbose` | off | Enable detailed logging |

#### Mesh-specific flags

| Flag | Default | Description |
|---|---|---|
| `--poisson-depth` | 9 | Poisson reconstruction depth (higher = more detail, slower) |
| `--atlas-size` | 4096 | Texture atlas resolution in pixels |
| `--colorise-stride` | 10 | Process every Nth frame for colorisation (lower = better quality) |
| `--depth-stride` | 5 | Use every Nth frame for depth estimation fallback |
| `--hdri-frame` | auto | Frame index used for HDRI environment map generation |
| `--envmap-width/height` | 4096/2048 | HDRI environment map resolution |

#### Splat-specific flags

| Flag | Default | Description |
|---|---|---|
| `--image-size` | 512 | Training image size in pixels |
| `--sh-degree` | 3 | Spherical harmonics degree (0–3; higher = better colour) |
| `--iterations` | 10000 | Training iterations |
| `--frame-stride` | 5 | Use every Nth frame for training |
| `--init-points` | 100000 | Number of Gaussians at initialisation |
| `--decode-sh` | off | Pre-decode SH coefficients to RGB in PLY output (for consumers without SH support) |

---

## 4a. Convert Splat Tab

The **Convert Splat** tab converts an existing Gaussian splat file between formats without any training or COLMAP step.

### Supported input formats

`.ply` (3DGS binary), `.splat` (packed 32-byte binary), `.glb` (KHR_gaussian_splatting), `.x3d` / `.x3dv` / `.x3dj`

### Supported output formats

Same as the [Gaussian splat pipeline outputs](#gaussian-splat-pipeline-outputs) above.

### Controls

| Control | Description |
|---|---|
| **Input file** | Source splat file (any supported format) |
| **Output folder** | Directory where the converted file is written |
| **Output stem** | Base filename (without extension) for the output |
| **Output format** | Target format: `x3d`, `x3dv`, `x3dj`, `ply`, `splat`, `glb` |
| **SH degree** | Spherical harmonics degree to use in output (auto = preserve source degree) |
| **Pre-decode SH → RGB** | Collapse SH coefficients to a single RGB colour; useful for viewers that don't decode SH |
| **Limit to … splats** | Cap the number of Gaussians written. When checked, a random subsample of the specified size is drawn. Default cap is **500 000** for X3D text formats, which keeps file sizes manageable (~580 MB). Uncheck to write all splats. |

### Large file handling

X3D text formats encode every Gaussian as inline text. At 500 000 splats the output is approximately 580 MB — the practical maximum for reliable browser loading. Files with more splats are automatically subsampled to the cap; the subsample is drawn uniformly at random, so the spatial distribution of the full cloud is preserved. Use PLY or SPLAT format if you need all splats without subsampling.

---

## 4b. Folder → Gaussian Splat Pipeline

The **Folder → Splat** pipeline takes any plain folder of photographs and produces a Gaussian splat without requiring a NavVis scanner, Metashape, or any other scan platform. It runs five steps automatically:

1. Extract the camera focal length from EXIF metadata (or accept a manual value)
2. Run COLMAP Structure-from-Motion to recover camera poses and a sparse point cloud
3. Load the COLMAP reconstruction as a `ScanDataset`
4. Initialise Gaussians from the sparse point cloud
5. Train 3DGS with gsplat and export

### Best results checklist

| Requirement | Why it matters |
|---|---|
| **Fixed focal length** — do not zoom between shots | COLMAP assumes identical intrinsics across images |
| **Consistent exposure** — use manual mode | Appearance changes between frames degrade 3DGS quality |
| **Complete coverage** — walk around the object / scene | Gaussians are only placed where multiple cameras overlap |
| **Object or scene visible in every frame** — avoid blank sky / wall frames | Reduces failed COLMAP registrations |
| **Overlap between frames ≥ 60 %** | Minimum for reliable feature matching |

### Turntable capture tips

For turntable captures (e.g. 256 images of an object on a rotating table):

- Use **sequential matching** (the new default). Adjacent frames at 2.8° intervals match each other; exhaustive matching is unnecessary and slower for ordered turntable sequences.
- Photograph at **two elevation angles** if possible (camera level with the equator **and** from above). This covers the top and side surfaces.
- Flip the object upside-down for a second pass to capture the bottom surface. Set **Turntable sets** to the number of distinct passes (e.g. `2` for upright + inverted).
- A **black matte fabric background** is strongly recommended — it contributes zero colour signal to the loss, preventing large background Gaussians (floaters) from forming behind the object. Any coloured background will be modelled by the optimizer.
- Add **visible markers** (e.g. printed dots or stickers) to the turntable surface. COLMAP's feature matcher needs stable features to track between frames; reflective or textureless objects benefit greatly from markers on the surrounding surface.
- Enable **Turntable mode** in the GUI. This bypasses COLMAP's fragmented mapper and constructs synthetic 360° circular poses, giving far better results than free-form SfM for turntable datasets.

#### Multi-pass turntable example (rock with top + bottom passes)

1. Capture 128 images at equal angular intervals with the object upright.
2. Flip the object upside-down and capture another 128 images at the same intervals.
3. Combine both sets in a single images folder (256 images total).
4. In the GUI: check **Turntable mode**, set **Turntable sets = 2**, and run.

**Four-pass example:** If you captured 4 passes of 64 images (e.g. object at 4 different orientations), set **Turntable sets = 4**. The pipeline distributes the elevation angles linearly from +elevation to −elevation across all sets. At elevation 25° the four rings are at **+25°, +8.3°, −8.3°, −25°** — full top-to-bottom coverage. This linear distribution applies for any number of sets.

### Turntable geometry overrides

The pipeline estimates the camera orbit radius and elevation angle automatically from the COLMAP sparse model. If COLMAP only registers a small fragment of the images (common on reflective or textureless objects), the estimates may be inaccurate. Two GUI controls let you override them:

| Control | Default | Description |
|---|---|---|
| **Elevation override (°)** | `0` (auto) | Camera elevation above the object equator for pass 1; pass 2 mirrors it below. Typical desktop turntable shots: `20`–`35°`. Set to `0` to auto-estimate. |
| **Radius override (m)** | `0` (auto) | Camera-to-object distance in metres. Measure with a tape measure, or calculate from EXIF focal length and the object's known size. Set to `0` to auto-estimate. |

**How to calculate the radius from EXIF:**  
If the object spans $W_{px}$ pixels in the frame and its real width is $W_m$ metres:

$$r = \frac{W_m / 2}{\tan\left(W_{px} / (2 \times f_{px})\right)}$$

For example: focal = 14 107 px, object spans 2 000 px, object is 15 cm wide → $r \approx 1.06$ m.

The pipeline also clamps auto-estimated elevation to a minimum of 15° to prevent near-horizontal orbits (a common COLMAP artefact on fragmented reconstructions).

### Background masking

Background pixels in training images are modelled by the optimizer as large, diffuse Gaussians ("floaters") that cloud the object. Masking removes the background before training so the optimizer only fits the foreground object.

Three masking methods are available, applied in priority order:

| Method | How to activate | Notes |
|---|---|---|
| **Explicit masks folder** | Set **Masks folder** to a directory of pre-made binary mask images (white = foreground, black = background), matched to source images by filename stem | Highest control; generate masks in Photoshop, GIMP, or Darktable |
| **rembg auto-mask** | Check **Auto-mask with rembg** | AI model automatically segments foreground from background. Requires the u2net model to be pre-downloaded via `install_workstation_deps.py`. Masks are cached in `_colmap_work/masks/` and reused on re-runs. The installer selects the correct GPU backend automatically per platform (see below). |

If rembg is checked and succeeds, chroma-key is not used. If rembg is not installed, the u2net model is not present, or rembg fails for any reason, the pipeline falls back to chroma-key. If an explicit masks folder is provided it takes priority over both.

#### rembg GPU backend by platform

rembg uses [onnxruntime](https://onnxruntime.ai) to run the u2net AI model. The installer automatically selects the best available GPU backend for your platform — no manual choice required:

| Platform | GPU backend | onnxruntime package | Notes |
|---|---|---|---|
| **Windows + NVIDIA/AMD/Intel GPU** | DirectX 12 (DirectML) | `onnxruntime-directml` | No CUDA toolkit required; works on any DirectX 12 GPU |
| **Linux + NVIDIA GPU** | CUDA | `onnxruntime-gpu>=1.20` | Requires CUDA 12+ driver; numpy 2.x compatible |
| **macOS (Apple Silicon / Intel)** | CoreML / Neural Engine | `onnxruntime` + `coremltools` | Uses Apple Neural Engine on M-series chips |
| **No GPU (any platform)** | CPU fallback | `onnxruntime` | ~3–5 s/image; functional but slower |

The installer also removes any conflicting onnxruntime packages before installing the correct one. If you install onnxruntime manually, install only the package for your platform — having multiple onnxruntime packages installed simultaneously causes import errors.

> **Note for Windows users:** `onnxruntime-directml` is ~2–3× slower than CUDA for inference, but requires no CUDA toolkit installation and works on all DirectX 12 GPUs including AMD and Intel Arc. For turntable captures of 256 images, masking completes in 2–4 minutes.

#### Edge erosion

Mask boundaries are inherently uncertain: pixels at the edge of an object contain a mix of foreground and background colour. These ambiguous edge pixels attract new Gaussians during training, which then drift into the background and become coloured floater artefacts.

The **Edge erosion (px)** control (GUI) / `--mask-erosion-px` (CLI) shrinks the foreground region inward by the specified number of pixels after mask generation. This excludes boundary pixels from the loss, preventing edge-spawned floaters.

- **Default:** 8 px — a conservative trim that removes the most uncertain boundary pixels while preserving the bulk of the foreground.
- **Increase to 15–20 px** if you still see coloured halos after training, or if the object has a fuzzy/translucent boundary (e.g. fur, plant material).
- **Set to 0** to disable erosion and use raw masks as-is.

Erosion is applied at the source image resolution before downscaling to the training `--image-size`.

| **Chroma-key** | Check **Chroma-key colour**, click the colour swatch to set the background colour (or click **🎯 Pick from image** to eyedrop from a source photo), and set the hue tolerance | Simple colour threshold; effective for uniform blue-screen or green-screen backgrounds |

> **rembg model pre-download:** The u2net.onnx model (~176 MB, Apache 2.0 licence) must be downloaded explicitly before first use. Run `install_workstation_deps.py` — it downloads the model to `~/.u2net/u2net.onnx`. The pipeline will not download it automatically mid-run.

**Pick from image eyedropper:** clicking **🎯 Pick from image** opens a thumbnail of your first source image. Click anywhere on the background to sample that pixel's exact colour as the chroma key colour.

**Calculating the chroma-key radius override:** see [Turntable geometry overrides](#turntable-geometry-overrides).

### Re-running without re-running COLMAP

The pipeline automatically skips COLMAP if a valid sparse reconstruction already exists in the `_colmap_work/sparse/` directory. If you change only training parameters (iterations, image size, SH degree) and want to retrain without repeating the SfM step, simply run again — COLMAP will be skipped and training will start immediately.

To force a fresh COLMAP run (e.g. after changing the image set), delete `_colmap_work/sparse/` and `_colmap_work/colmap.db`.

### Additional COLMAP dependency

COLMAP must be available through **one** of the following (in order of preference):

| Option | Install command | Notes |
|---|---|---|
| **pycolmap** Python bindings | `pip install pycolmap` | Recommended; no separate binary needed |
| **colmap** system binary | [colmap.github.io/install.html](https://colmap.github.io/install.html) or `conda install -c conda-forge colmap` | Pass `--colmap-bin /path/to/colmap` if not in `PATH` |

If neither is present the pipeline will raise a clear error listing the install instructions.

### Launching in the GUI

1. Open the desktop GUI:
   ```bash
   python rawkee/tools/lidar/scan_gui.py
   ```
2. Click the **Folder → Splat** tab.
3. Browse to your **images folder** (must contain only image files; no sub-folders).
4. Set an **output folder**. It will be auto-suggested as `<images_folder>_splat/` next to the source.
5. Leave **Auto from EXIF** checked unless you know the exact focal length in pixels. For a Canon T7i at 55 mm on an APS-C sensor that is approximately **14 800 px**.
6. Choose a **COLMAP matcher**:
   - *sequential* — matches each frame only to its neighbours. Default; best for ordered turntable footage.
   - *exhaustive* — tests every image pair. Better for small unordered collections (≤ 500 images).
   - **hloc (SuperPoint+LightGlue)** — deep-learned feature extraction and matching. Strongly recommended for low-texture objects (rocks, minerals, smooth surfaces) where SIFT often registers only a fraction of frames. Requires the `hloc` package (see [installation](#installing-hloc)).
7. For turntable datasets, check **Turntable mode**, set **Turntable sets**, and optionally set the **Elevation override** and **Radius override** if COLMAP gives bad geometry estimates.
8. To remove a coloured background from training images, expand the **Background Masking** section and enable **rembg** (AI auto-mask), **Chroma-key** (colour threshold), or point to a pre-made **Masks folder**. Set **Edge erosion (px)** to shrink masks inward and remove uncertain boundary pixels (default 8 px).
9. Adjust training parameters (image size, SH degree, iterations, densify until, 2D density gradients) if needed.
10. Click **Run (COLMAP → 3DGS)**.

The status label advances through phases:

| Phase label | What is happening |
|---|---|
| *Running COLMAP…* | Feature extraction, matching, and sparse reconstruction |
| *COLMAP: extracting features…* | Detecting SIFT keypoints in every image (or SuperPoint when hloc is selected) |
| *COLMAP: matching features…* | Finding correspondences between image pairs (LightGlue when hloc is selected) |
| *COLMAP: reconstructing…* | Incremental SfM — estimating camera poses |
| *Training 3DGS…* | Gaussian splat optimisation loop |
| *Done.* | Export complete |

> **If the status label stays on "Running COLMAP…" for a long time**, feature matching is running. This is normal for `exhaustive` or `hloc` matching with hundreds of images.

### CLI usage

```bash
# Minimal
python rawkee/tools/lidar/run_pipeline.py folder-splat \
    --images /path/to/2020_05_30 \
    --output /path/to/splat_out

# Full example — turntable with two passes
python run_pipeline.py folder-splat \
    --images     /path/to/photos \
    --output     /path/to/output \
    --format     x3d \
    --focal-px   14800 \
    --matcher    exhaustive \
    --turntable \
    --n-sets     2 \
    --image-size 512 \
    --sh-degree  3 \
    --iterations 30000 \
    --frame-stride 1 \
    --verbose
```

#### Folder-splat CLI flags

| Flag | Default | Description |
|---|---|---|
| `--images DIR` | *(required)* | Folder containing only the input image files |
| `--output DIR` | *(required)* | Output directory |
| `--format FMT` | `x3d` | Export format: `x3d` \| `x3dv` \| `x3dj` \| `ply` \| `splat` \| `glb` |
| `--focal-px FLOAT` | auto-EXIF | Camera focal length in pixels. Omit to read from EXIF |
| `--matcher NAME` | `sequential` | COLMAP feature matcher: `sequential` \| `exhaustive` \| `hloc` |
| `--use-hloc` | off | Use SuperPoint+LightGlue (hloc) for feature extraction and matching. Equivalent to `--matcher hloc`. Recommended for low-texture objects. Requires `pip install git+https://github.com/cvg/Hierarchical-Localization` |
| `--image-size INT` | `1024` | Training image resolution (square, pixels) — see hardware guide below |
| `--sh-degree INT` | `3` | Spherical harmonics degree (0 = colour only, 3 = best for luster/iridescence) |
| `--iterations INT` | `30000` | 3DGS training iterations |
| `--frame-stride INT` | `1` | Use every N-th registered image for training |
| `--turntable` | off | Enable turntable mode (synthetic circular poses; recommended for object-on-turntable captures) |
| `--n-sets INT` | `1` | Number of distinct turntable passes (e.g. `2` = upright + inverted) |
| `--turntable-elevation FLOAT` | `0` | Camera elevation above object equator in degrees. `0` = auto-estimate from COLMAP (clamped to ≥ 15°). Set to `20`–`35` for typical desktop shots if COLMAP gives a bad estimate. |
| `--turntable-radius FLOAT` | `0` | Camera-to-object distance in metres. `0` = auto-estimate. Measure physically or calculate from EXIF focal + object size. |
| `--masks-dir PATH` | — | Folder of pre-made mask images (white = foreground). Matched by filename stem. |
| `--auto-mask` | off | Auto-generate masks using rembg AI model. Requires `pip install "rembg[gpu]"` and the u2net model pre-downloaded by `install_workstation_deps.py`. Masks cached to `_colmap_work/masks/`. |
| `--chroma-rgb R G B` | — | Background colour for chroma-key masking (e.g. `0 80 180` for blue). |
| `--chroma-tolerance FLOAT` | `30` | Hue tolerance in degrees for chroma-key (lower = more precise). |
| `--mask-erosion-px INT` | `8` | Shrink generated masks inward by this many pixels. Removes uncertain edge pixels where background colour bleeds through at object boundaries. Set to `0` to disable. |
| `--densify-until INT` | `0` | Step at which adaptive density control stops spawning new Gaussians. `0` = auto (half of `--iterations`). Increase for large outdoor scenes. |
| `--grad-mode` | `2d` | Density gradient mode: `2d` (screen-space, recommended) or `3d` (world-space). 2D gradients are more robust for masked training. |
| `--decode-sh` | off | Pre-decode SH to RGB on export (for viewers without SH support) |
| `--colmap-bin PATH` | `colmap` | Path to the `colmap` binary (only used if `pycolmap` is absent) |
| `--verbose` | off | Enable detailed logging |

#### Installing hloc

hloc (Hierarchical Localization) provides SuperPoint feature extraction and LightGlue matching, which significantly outperform SIFT on low-texture objects:

```bash
pip install git+https://github.com/cvg/Hierarchical-Localization
```

or run `install_workstation_deps.py` — it installs hloc automatically in the optional packages step. hloc requires PyTorch and a CUDA GPU; the pipeline falls back to SIFT automatically if hloc is not installed.

### Image size and hardware guide

The training image resolution is the single largest factor controlling VRAM usage and training speed. Use this table to choose an appropriate `--image-size` for your hardware:

| Hardware | GPU memory | Recommended `--image-size` | `--iterations` | Notes |
|---|---|---|---|---|
| Laptop GPU (RTX 4000–5000 series) | 8–16 GB | `512`–`1024` | 30 000 | Stay at or below 1024; 2048 spills into shared RAM and slows training by 3–5× |
| Workstation GPU (RTX 4090, A6000) | 24–48 GB | `1024`–`2048` | 30 000–60 000 | 2048 is the practical quality ceiling for typical multi-GPU workstations |
| NVIDIA DGX Spark (GB10 Superchip) | 128 GB unified | `2048`–`3000` | 30 000–60 000 | Matches the benchmark configuration from Richter et al. 2025 |
| NVIDIA GH200 Grace Hopper (base) | 96 GB HBM3 + 480 GB LPDDR5X | full source resolution | 30 000–60 000 | No image-size constraint for typical mineral datasets (256 images × 6 000×4 000 px) |

> **Rule of thumb for turntable mineral scans (256 images):** Use `--image-size 1024 --iterations 30000` as the baseline. Increase to 2048 on workstation/server hardware for finer surface detail.

### Output directory layout

After a successful run the output directory contains:

```
output_dir/
  <folder_name>.<fmt>          ← the Gaussian splat (x3d / ply / splat / …)
  _colmap_work/                ← COLMAP working files (can be deleted)
    colmap.db                  ← COLMAP feature database
    masks/                     ← rembg-generated masks (cached; reused on re-runs)
    sparse/0/
      cameras.bin              ← recovered camera intrinsics
      images.bin               ← recovered camera poses
      points3D.bin             ← sparse 3D point cloud (Gaussian init)
```

The `_colmap_work/` directory is safe to delete once the splat has been exported.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| *COLMAP produced no sparse reconstruction* | Too few matching image pairs | Check overlap; try `--use-hloc` (SuperPoint+LightGlue) for low-texture objects; verify images are sharp |
| *0 training images loaded* | COLMAP registered 0 images | Inspect COLMAP output in `_colmap_work/`; check image quality; enable hloc for textureless objects |
| *Focal length is 0 or wrong* | EXIF not present or ambiguous | Pass `--focal-px` manually |
| *pycolmap not found* and *colmap binary not found* | Neither installed | `pip install pycolmap` or install COLMAP binary |
| *Poor quality splat* | Not enough views, blurry images, or inconsistent lighting | Add more frames, improve lighting consistency, lower `--frame-stride` |
| *Reconstructed only half the object (top or bottom missing)* | Turntable mode not enabled; COLMAP only registered one pass | Enable **Turntable mode** and set **Turntable sets = 2** (or the number of capture passes) |
| *Spiky floater artefacts at object edges* | Missing camera coverage on those surfaces | Add views from those angles; check that COLMAP registered the full image set |
| *Coloured haze or blob surrounds the object* | Background colour modelled as Gaussians | Use a black matte background for future captures; enable **Chroma-key** masking or **rembg** auto-mask; increase **Edge erosion** to 15–20 px to exclude boundary pixels |
| *Coloured floater blob in corner of reconstructed scene* | Edge pixels spawning Gaussians that drift outside the mask | Increase **Edge erosion** (default 8 px); floaters will be culled by opacity reset and large-Gaussian pruning on a re-run |
| *hloc import error / `No module named 'hloc'`* | hloc not installed | `pip install git+https://github.com/cvg/Hierarchical-Localization` or run `install_workstation_deps.py`; pipeline falls back to SIFT automatically |
| *LightGlue downloading weights mid-run* | Weights not pre-cached | Run `install_workstation_deps.py --yes` to pre-download all three weight files to `~/.cache/torch/hub/checkpoints/` |
| *SuperPoint feature extraction running on CPU (slow, ~3 s/image)* | CUDA torch was downgraded by a pip dependency (commonly hloc) | Re-run `install_workstation_deps.py`; step 6b detects and force-reinstalls the CUDA wheel automatically |
| *rembg `cublasLt64_13.dll` error on Windows* | `onnxruntime-gpu` requires CUDA 13 DLLs not present on CUDA 12 systems | Run `install_workstation_deps.py`; it installs `onnxruntime-directml` instead (DirectX 12 GPU, no CUDA toolkit required) |
| *rembg `_ARRAY_API not found`* | `onnxruntime-gpu 1.18.x` is ABI-incompatible with numpy 2.x | Run `install_workstation_deps.py`; it upgrades to the correct platform backend automatically |
| *rembg falls back to CPU unexpectedly* | Wrong onnxruntime package installed, or conflicting packages | Run `install_workstation_deps.py`; it removes conflicting packages and installs the correct backend for your platform |
| *`No module named 'SuperGluePretrainedNetwork'`* | SuperPoint optional package not installed | See "Optional: SuperPoint features" section above; pipeline falls back to DISK+LightGlue automatically |
| *Near-horizontal orbit / elongated smear result* | COLMAP estimated flat orbit (common on textureless/reflective objects) | Set **Elevation override** to `25°`; the pipeline now also clamps auto-estimate to ≥ 15° |
| *Wrong scale / object too large or small* | COLMAP radius estimate wrong | Set **Radius override** to the measured camera-to-object distance in metres |
| *Training starts immediately without re-running COLMAP* | Existing sparse model detected in `_colmap_work/sparse/` | Expected behaviour — COLMAP is intentionally skipped. Delete `sparse/` and `colmap.db` to force a fresh run |
| *Convert Splat output file is smaller than expected* | Splat limit cap applied | Uncheck **Limit to … splats** in the Convert Splat tab, or raise the cap value |

---

## 5. Desktop Installation

### Requirements

- Python 3.10 or newer
- NVIDIA GPU with CUDA support (required for Gaussian splat training; mesh pipeline works on CPU but is slow)
- CUDA driver ≥ 525 (for CUDA 12.x)

### Quick install

Run the bundled installer script. It detects your CUDA driver, installs the matching PyTorch wheel, and installs all other dependencies:

```bash
python rawkee/tools/lidar/install_workstation_deps.py
```

Options:

```bash
# Non-interactive
python install_workstation_deps.py --yes

# Preview without installing anything
python install_workstation_deps.py --dry-run --yes

# After a GPU driver update, reinstall PyTorch for the new CUDA version
python install_workstation_deps.py --reinstall-torch --yes
```

> **Note for multi-Python Windows environments:** Always invoke the installer with the same `python` executable you use to launch RawKee. If `python` and `pip` in your PATH point to different interpreters, packages may land in the wrong location. Use `python -m rawkee.tools.lidar.install_workstation_deps` to guarantee the correct interpreter is used.

> **PyTorch CUDA protection:** Some optional packages (notably `hloc`) pull in a CPU-only `torch` as a dependency, silently downgrading your CUDA-enabled install. The installer detects this automatically at step 6b and force-reinstalls the correct CUDA wheel. No manual action is required.

### Manual installation

```bash
pip install numpy scipy Pillow "imageio[freeimage]" PySide6 open3d
pip install torch --index-url https://download.pytorch.org/whl/cu124   # adjust for your CUDA
pip install gsplat rawpy rosbags pye57 pyproj transformers
pip install git+https://github.com/cvg/Hierarchical-Localization   # hloc: DISK+LightGlue

# rembg + onnxruntime — choose ONE based on your platform:
pip install "rembg[gpu]" onnxruntime-directml          # Windows (any DirectX 12 GPU)
pip install "rembg[gpu]" "onnxruntime-gpu>=1.20.0"     # Linux + NVIDIA CUDA 12+
pip install "rembg[cpu]" onnxruntime coremltools        # macOS
pip install "rembg[cpu]" onnxruntime                   # CPU-only fallback
```

Then install RawKee itself (from the repository root):

```bash
pip install -e .
# or
export PYTHONPATH=/path/to/rawkee:$PYTHONPATH
```

### Optional: SuperPoint features (academic / non-commercial use only)

By default the hloc feature matcher uses **DISK+LightGlue**, which is Apache 2.0 licensed and works for any use case.  Academic and research users can optionally upgrade to **SuperPoint+LightGlue**, which generally produces denser and more accurate matches on low-texture objects such as rocks and minerals.

> **License notice:** SuperGluePretrainedNetwork is released under the [Magic Leap Non-Commercial License](https://github.com/magicleap/SuperGluePretrainedNetwork/blob/master/LICENSE).  It may be used freely for non-commercial academic and research purposes only.  **Do not use SuperPoint if your work is commercial.**

SuperGluePretrainedNetwork is not pip-installable (it has no `setup.py`).  The steps below clone it once to your home directory and register it with Python via a `.pth` file, so it is importable in every future session without any PATH changes.

#### Windows (PowerShell)

```powershell
# 1. Clone to a permanent location  (the folder name SuperGluePretrainedNetwork must be preserved)
$parent = "$env:USERPROFILE\.rawkee"
$repo   = "$parent\SuperGluePretrainedNetwork"
New-Item -ItemType Directory -Force -Path $parent | Out-Null
git clone https://github.com/magicleap/SuperGluePretrainedNetwork $repo

# 2. Find your site-packages folder
$site = python -c "import site; print(site.getsitepackages()[1])"

# 3. Point the .pth file at the PARENT folder (Python imports the SuperGluePretrainedNetwork subfolder as a package)
[System.IO.File]::WriteAllText("$site\superglue_pretrained.pth", "$parent`n")

# 4. Verify
python -c "from SuperGluePretrainedNetwork.models import superpoint; print('SuperPoint OK')"
```

#### Linux / macOS

```bash
# 1. Clone to a permanent location  (the folder name SuperGluePretrainedNetwork must be preserved)
parent="$HOME/.rawkee"
mkdir -p "$parent"
git clone https://github.com/magicleap/SuperGluePretrainedNetwork "$parent/SuperGluePretrainedNetwork"

# 2. Point the .pth file at the PARENT folder
site=$(python -c "import site; print(site.getsitepackages()[-1])")
echo "$parent" > "$site/superglue_pretrained.pth"

# 3. Verify
python -c "from SuperGluePretrainedNetwork.models import superpoint; print('SuperPoint OK')"
```

Once installed, the RawKee pipeline automatically uses SuperPoint+LightGlue instead of DISK+LightGlue — no GUI or config change needed.  Run `hpc_preflight_check.py` to confirm it is detected.

### Feature matcher model weights

The hloc feature matcher requires pretrained model weights that are downloaded automatically on first use and cached to `~/.cache/torch/hub/checkpoints/`. The installer pre-downloads all of them so nothing downloads mid-pipeline:

| Weight file | Size | Used for | License |
|---|---|---|---|
| `superpoint_lightglue_v0-1_arxiv.pth` | 45 MB | LightGlue matching with SuperPoint features | MIT |
| `disk_lightglue_v0-1_arxiv.pth` | 45 MB | LightGlue matching with DISK features (fallback) | MIT |
| `depth-save.pth` | 21 MB | DISK feature extraction | Apache 2.0 |

If you skipped the installer or need to download them manually:

```bash
python rawkee/tools/lidar/install_workstation_deps.py --yes
```

The DISK+LightGlue weights are pre-downloaded even when SuperPoint is available, so the pipeline can fall back without a mid-run download if SuperGluePretrainedNetwork is ever unavailable.

### Verifying your installation

```bash
python rawkee/tools/lidar/hpc_preflight_check.py
```

### Windows-specific notes

#### MSVC C++ compiler required for gsplat

`gsplat` JIT-compiles CUDA kernels at first run using MSVC. You need
**Visual Studio Build Tools 2022** with the *Desktop development with C++* workload:

1. Download from <https://visualstudio.microsoft.com/visual-cpp-build-tools/>
2. Run the installer and select **Desktop development with C++**.
3. After install, verify `cl.exe` is accessible:

   ```python
   import shutil; print(shutil.which('cl'))
   ```

   If it returns `None`, add the MSVC bin directory to your PATH manually or launch
   from a **Developer PowerShell for VS 2022** (Start menu shortcut).

> **Note:** In PowerShell, `where cl` resolves to `Where-Object` (an alias), not the
> Windows `where.exe` locator. Use `where.exe cl` or `shutil.which('cl')` in Python
> to check whether `cl.exe` is actually on your PATH.

#### PyTorch 2.11 + Windows SDK header conflict

PyTorch 2.11's `CUDACachingAllocator.h` contains a parameter named `small`, which the
Windows SDK header `rpcndr.h` macro-expands to `char` (`#define small char`). MSVC then
rejects the resulting `bool char` combination as invalid C++.

**Fix:** rename the conflicting parameter in the PyTorch header, then clear the JIT cache:

```powershell
# 1. Patch the header
$h = "$env:LOCALAPPDATA\Programs\Python\Python312\Lib\site-packages\torch\include\c10\cuda\CUDACachingAllocator.h"
(Get-Content $h -Raw) `
    -replace 'bool small, size_t sz\)', 'bool is_small, size_t sz)' `
    -replace 'is_small_pool\(small\)', 'is_small_pool(is_small)' `
  | Set-Content $h -NoNewline

# 2. Clear the JIT build cache
Remove-Item "$env:USERPROFILE\AppData\Local\torch_extensions" -Recurse -Force -ErrorAction SilentlyContinue
```

Adjust the Python path if your installation is in a different location (e.g. a virtualenv).
This patch is safe to apply; it only renames a local parameter.

---

## 6. HPC / SLURM Usage

### Pre-built SLURM scripts

Three ready-to-use SLURM scripts are provided in `rawkee/tools/lidar/`:

| Script | Target | GPU | Notes |
|---|---|---|---|
| `slurm_scan_gpu.sh` | Generic GPU cluster | Any CUDA GPU | Single-node, both pipelines |
| `slurm_scan_dgx_spark.sh` | DGX Spark (GB10 / Blackwell) | 128 GB unified memory | Single-node, both pipelines |
| `slurm_scan_ddp_dgx_spark.sh` | DGX Spark cluster | Multi-node | Gaussian splat training only; uses PyTorch DDP via `torchrun` |

Edit the path variables at the top of each script before submitting:

```bash
DATASET=/path/to/dataset
OUTPUT_MESH=/path/to/output/mesh
OUTPUT_SPLAT=/path/to/output/splat
GEO_CSV=/path/to/survey.csv        # optional
PIPELINE_SCRIPT=/path/to/rawkee/rawkee/tools/lidar/run_pipeline.py
```

Then submit:

```bash
sbatch slurm_scan_gpu.sh
```

### Writing your own SLURM script

Minimum recommended resources:

| Pipeline | Nodes | CPUs | RAM | GPU |
|---|---|---|---|---|
| Mesh (standard) | 1 | 16 | 128 GB | 1× V100 16 GB or better |
| Mesh (DGX Spark) | 1 | 20 | 112 GB | 1× GB10 |
| Gaussian splat | 1 | 16 | 128 GB | 1× A100 40 GB or better |
| Gaussian splat (DDP) | 2–8 | 20/node | 112 GB/node | 1× GB10/node |

#### Single-node example

```bash
#!/bin/bash
#SBATCH --job-name=rawkee-lidar
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00

source /path/to/venv/bin/activate
export OPENCV_IO_ENABLE_OPENEXR=1
export PYTHONUNBUFFERED=1

SCRIPT=/path/to/rawkee/rawkee/tools/lidar/run_pipeline.py

python "$SCRIPT" mesh  --dataset "$DATASET" --output "$OUT_MESH"  --format x3d --verbose
python "$SCRIPT" splat --dataset "$DATASET" --output "$OUT_SPLAT" --format x3d --no-georef --verbose
```

#### Multi-node Gaussian splat (DDP)

```bash
#!/bin/bash
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G

source /path/to/venv/bin/activate
export NCCL_SOCKET_IFNAME=ib0   # adjust to your fabric interface
MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
SCRIPT=/path/to/rawkee/rawkee/tools/lidar/run_pipeline.py

srun torchrun \
    --nproc_per_node=1 --nnodes=$SLURM_NNODES \
    --rdzv_backend=c10d --rdzv_endpoint="${MASTER_ADDR}:29500" \
    "$SCRIPT" splat --dataset "$DATASET" --output "$OUT_SPLAT" \
        --format x3d --iterations 50000 --verbose
```

> DDP is supported for the **Gaussian splat pipeline only**. The mesh pipeline runs single-node. In a DDP job, only rank 0 writes the output file.

### Grace/Hopper and DGX Spark notes

Both architectures use **NVLink-C2C unified memory** (CPU + GPU share a single pool). Add these environment variables to your job:

```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OMP_NUM_THREADS=20   # all Arm Cortex-X925 cores on DGX Spark
```

The pipeline automatically detects sm_90+ and sm_100 architectures and sets the memory fraction to 90%.

---

## 7. HPC System Administrator Guide

### Preflight environment check

RawKee Lidar ships a read-only diagnostic script that checks all dependencies, CUDA/PyTorch compatibility, driver version, GPU compute capability, and NCCL availability:

```bash
python rawkee/tools/lidar/hpc_preflight_check.py
```

Options:

```bash
# Machine-readable JSON output (for ticketing/monitoring systems)
python hpc_preflight_check.py --json > report.json

# Exit 1 if any WARNING or ERROR is found (use in SLURM prologue)
python hpc_preflight_check.py --strict
```

### Required Python packages

| Package | Purpose | Required |
|---|---|---|
| `numpy ≥ 1.24` | Numeric arrays throughout | Yes |
| `scipy` | KDTree, UTM math | Yes |
| `Pillow` | Image resizing | Yes |
| `imageio[freeimage]` | HDR / PNG saving | Yes |
| `open3d` | Poisson reconstruction, E57 fallback | Yes |
| `torch` (CUDA build) | GPU acceleration (mesh + splat) | Yes |
| `gsplat` | Gaussian splat rasteriser | Yes (splat) |
| `pycolmap` | COLMAP SfM Python bindings | Folder→Splat (or use binary) |
| `hloc` | SuperPoint+LightGlue / DISK+LightGlue deep-learned feature matching | Optional; strongly recommended for low-texture objects. `pip install git+https://github.com/cvg/Hierarchical-Localization` |
| LightGlue weights | Pretrained matcher weights cached to `~/.cache/torch/hub/checkpoints/` | Pre-downloaded by `install_workstation_deps.py`; auto-downloaded on first use otherwise (MIT / Apache 2.0) |
| `PySide6` | Desktop GUI | GUI only |
| `rawpy` | DNG/RAW camera image decoding | Recommended |
| `rembg` | AI background removal for turntable masking | Optional. Install correct onnxruntime backend (see table below); u2net model pre-downloaded by `install_workstation_deps.py`. |
| `onnxruntime-directml` | DirectML GPU backend for rembg | Windows GPU. Installed automatically by `install_workstation_deps.py`. |
| `onnxruntime-gpu>=1.20` | CUDA GPU backend for rembg | Linux + NVIDIA. Requires CUDA 12+ driver and numpy 2.x. |
| `onnxruntime` + `coremltools` | CoreML backend for rembg | macOS. Uses Apple Neural Engine on M-series. |
| `onnxruntime` | CPU backend for rembg | Any platform without GPU. Functional but ~3–5 s/image. |
| `rosbags` | NavVis LiDAR ROS bag reading | NavVis only |
| `pye57` | E57 point cloud reading | E57 only |
| `pyproj` | Precise UTM georeferencing | Recommended |
| `transformers` | Depth Anything V2 (LiDAR fallback) | Optional |

### PyTorch / CUDA wheel selection

| NVIDIA driver version | Recommended PyTorch wheel |
|---|---|
| ≥ 570 (Blackwell) | NGC container `nvcr.io/nvidia/pytorch:26.05-py3` or `--index-url .../cu128` |
| ≥ 545 | `pip install torch --index-url https://download.pytorch.org/whl/cu124` |
| ≥ 528 | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| No GPU | `pip install torch --index-url https://download.pytorch.org/whl/cpu` |

Verify after install:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

### gsplat compilation requirements

`gsplat` compiles CUDA kernels during `pip install`. The **CUDA toolkit** (`nvcc`) must be present and must match the PyTorch CUDA build:

```bash
nvcc --version          # check toolkit version
module load cuda/12.4   # load matching toolkit module
pip install gsplat
```

If compilation fails, build `gsplat` on a build node and install into a shared venv or container that compute nodes mount read-only.

### Recommended module environment (example)

```bash
module load python/3.11
module load cuda/12.4
source /shared/venvs/rawkee/bin/activate
```

Or use the provided NGC container for Blackwell nodes:

```bash
#SBATCH --container-image=nvcr.io/nvidia/pytorch:26.05-py3
#SBATCH --container-mounts=/shared/data:/data
```

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `torch.cuda.is_available()` returns `False` | Driver/wheel CUDA version mismatch | Reinstall torch for your driver version (see table above) |
| `gsplat` import error / missing `.so` | Not compiled for current CUDA | Recompile on build node with matching `nvcc` |
| NCCL timeout in DDP jobs | Fabric interface mismatch | Set `NCCL_SOCKET_IFNAME=ib0` (or `eth0`) to match your interconnect |
| HDR output fails | FreeImage binary not installed | `pip install "imageio[freeimage]"` |
| `rosbags` not found | NavVis LiDAR unavailable | `pip install rosbags`; pipeline falls back to Depth Anything V2 |
| OOM on Grace/Hopper | Memory fraction not set | Add `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` to job |
| `pye57` import error | E57 support unavailable | `pip install pye57`; pipeline falls back to `open3d` reader |
| *(Windows)* gsplat CUDA JIT fails: `cl.exe not found` | MSVC not installed or not on PATH | Install VS Build Tools 2022 with *Desktop development with C++*; verify with `python -c "import shutil; print(shutil.which('cl'))"` |
| *(Windows)* gsplat build error: `invalid combination of type specifiers` / `bool char` | `rpcndr.h` expands `small` → `char` in PyTorch 2.11+ header | Patch `CUDACachingAllocator.h` (rename `small` → `is_small`) then clear `%LOCALAPPDATA%\torch_extensions` — see Windows notes in section 5 |
| *(Windows)* `where cl` finds nothing in PowerShell | `where` is a PowerShell alias for `Where-Object` | Use `where.exe cl` or `python -c "import shutil; print(shutil.which('cl'))"` |

Run `python hpc_preflight_check.py` on the compute node image after any environment change to confirm everything is correct before re-enabling job submission.

---

## References

The Folder → Splat pipeline design, capture workflow recommendations, and default training parameters are informed by the following publication:

> Florian Richter, Fabian Bär, and Bernhard Jung. **Virtual Mineral Collections Using 3D Gaussian Splatting.** In *Proceedings of the 30th International Conference on 3D Web Technology (Web3D ’25)*, September 09–10, 2025, Siena, Italy. ACM, New York, NY, USA, 7 pages.  
> DOI: [10.1145/3746237.3746312](https://doi.org/10.1145/3746237.3746312)

Key findings from this paper that shaped RawKee Lidar defaults:
- **SH degree 3** is essential for minerals with metallic luster, iridescence, or transparency — lower degrees produce flat, unrealistic renderings
- **30 000 iterations** is the practical quality target for a single specimen (60–90 min on a 32 GB V100)
- **Black matte background** and **visible markers on the capture surface** are critical for COLMAP feature matching on reflective or textureless objects
- **Fixed focal length, manual exposure, and white balance** are required for consistent photometric training signal
- The `sequential` COLMAP matcher is preferred for ordered turntable captures; `exhaustive` for small unordered collections

The paper-accurate 3DGS training loop implemented in RawKee Lidar additionally incorporates:
- **2D screen-space gradients** (`absgrad=True` in gsplat) for adaptive density control — more robust than 3D world-space gradients for masked training where background pixels contribute no signal
- **Position learning-rate decay** from 1.6×10⁻⁴ to 1.6×10⁻⁶ over the full training run (multiplicative schedule per Kerbl et al. 2023)
- **SH degree curriculum** — starts at degree 0 (colour only) and increments every 1 000 steps up to the target degree, preventing early overfitting of view-dependent colour
- **Opacity reset** every 1 500 steps during the densification phase — transparent Gaussians with no photometric support are culled at the next pruning pass
- **Large-Gaussian pruning** — Gaussians whose maximum scale exceeds 10% of the scene extent are removed at each densification step
- Training at full source resolution (3000×2000 px) on 32 GB+ GPUs produces the highest quality results for small specimens
