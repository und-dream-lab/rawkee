#!/bin/bash
#SBATCH --job-name=rawkee-scan
#SBATCH --partition=dgx-spark          # adjust to your cluster's partition name
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20             # all Arm Cortex-X925 cores on the node
#SBATCH --mem=112G                     # leave ~16 GB headroom in the 128 GB unified pool
#SBATCH --gres=gpu:gb10:1             # GB10 Blackwell GPU
#SBATCH --time=06:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

# --- Environment ---
# NVLink-C2C means CPU and GPU share physical memory; expandable_segments
# lets PyTorch grow into the unified pool without pre-reserving a fixed block.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0
export OPENCV_IO_ENABLE_OPENEXR=1
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=20

source /path/to/venv/bin/activate

DATASET=/path/to/field-training/Field-Training/woodcrest-003
OUTPUT_MESH=/path/to/output/woodcrest-mesh
OUTPUT_SPLAT=/path/to/output/woodcrest-splat
GEO_CSV=/path/to/Trimble/site14_aug24.csv   # optional; remove flag if not needed
PIPELINE_SCRIPT=/path/to/rawkee/rawkee/tools/lidar/run_pipeline.py

# --- Mesh pipeline ---
python "$PIPELINE_SCRIPT" mesh \
    --dataset   "$DATASET" \
    --output    "$OUTPUT_MESH" \
    --format    x3d \
    --platform  navvis \
    --geo-csv     "$GEO_CSV" \
    --epsg      32605 \
    --poisson-depth   11 \
    --atlas-size      8192 \
    --colorise-stride 3 \
    --envmap-width    4096 \
    --envmap-height   2048 \
    --verbose

# --- Gaussian splat pipeline ---
python "$PIPELINE_SCRIPT" splat \
    --dataset      "$DATASET" \
    --output       "$OUTPUT_SPLAT" \
    --format       x3d \
    --platform     navvis \
    --geo-csv      "$GEO_CSV" \
    --no-georef \
    --epsg         32605 \
    --image-size   800 \
    --sh-degree    3 \
    --iterations   50000 \
    --frame-stride 2 \
    --init-points  300000 \
    --verbose
