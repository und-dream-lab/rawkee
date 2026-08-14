#!/bin/bash
#SBATCH --job-name=rawkee-scan
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

# --- Environment ---
module load cuda/12.4          # adjust to your cluster's module name
source /path/to/venv/bin/activate

export OPENCV_IO_ENABLE_OPENEXR=1
export PYTHONUNBUFFERED=1

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
    --poisson-depth   9 \
    --atlas-size      4096 \
    --colorise-stride 5 \
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
    --image-size   512 \
    --sh-degree    3 \
    --iterations   30000 \
    --frame-stride 3 \
    --init-points  100000 \
    --verbose
