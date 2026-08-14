# RawKee Lidar

**RawKee Lidar** (`rawkee.tools.lidar`) is an open-source GPU-accelerated pipeline that converts raw data from mobile LiDAR scanners and photogrammetry platforms into interoperable 3D assets — textured polygon meshes and Gaussian splat radiance fields — ready for display in web browsers, game engines, XR headsets, and any X3D-capable viewer.

It is part of the [RawKee](https://github.com/und-dream-lab/rawkee) project developed at the University of North Dakota DREAM Lab.

---

## Table of Contents

1. [What RawKee Lidar Does](#1-what-rawkee-lidar-does)
2. [Supported Input Platforms](#2-supported-input-platforms)
3. [Supported Output Formats](#3-supported-output-formats)
4. [Desktop User Guide](#4-desktop-user-guide)
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

### Manual installation

```bash
pip install numpy scipy Pillow "imageio[freeimage]" PySide6 open3d
pip install torch --index-url https://download.pytorch.org/whl/cu124   # adjust for your CUDA
pip install gsplat rawpy rosbags pye57 pyproj transformers
```

Then install RawKee itself (from the repository root):

```bash
pip install -e .
# or
export PYTHONPATH=/path/to/rawkee:$PYTHONPATH
```

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
| `PySide6` | Desktop GUI | GUI only |
| `rawpy` | DNG/RAW camera image decoding | Recommended |
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
