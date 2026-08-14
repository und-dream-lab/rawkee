#!/bin/bash
#SBATCH --job-name=rawkee-splat-ddp
#SBATCH --partition=dgx-spark          # adjust to your cluster's partition name
#SBATCH --nodes=4                      # number of DGX Spark nodes
#SBATCH --ntasks-per-node=1            # one torchrun process per node
#SBATCH --cpus-per-task=20             # all Arm Cortex-X925 cores per node
#SBATCH --mem=112G                     # leave ~16 GB headroom in the 128 GB unified pool
#SBATCH --gres=gpu:gb10:1             # one GB10 Blackwell GPU per node
#SBATCH --time=04:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

# --- Environment ---
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OPENCV_IO_ENABLE_OPENEXR=1
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=20
# NCCL over InfiniBand / NVLink fabric; set to eth0 if using Ethernet
export NCCL_SOCKET_IFNAME=ib0
export NCCL_DEBUG=WARN

source /path/to/venv/bin/activate

DATASET=/path/to/scan/dataset
OUTPUT_SPLAT=/path/to/output/splat
GEO_CSV=/path/to/survey.csv           # optional; remove --geo-csv flag if not needed
PIPELINE_SCRIPT=/path/to/rawkee/rawkee/tools/lidar/run_pipeline.py

# torchrun rendezvous: use the first allocated node as master
MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
MASTER_PORT=29500
NNODES=$SLURM_NNODES

# --- Gaussian splat pipeline (distributed across all nodes) ---
# srun launches one task per node; torchrun manages the DDP process group.
# Mesh pipeline runs single-node on rank 0 after splat training completes.
srun torchrun \
    --nproc_per_node=1 \
    --nnodes="$NNODES" \
    --rdzv_backend=c10d \
    --rdzv_endpoint="${MASTER_ADDR}:${MASTER_PORT}" \
    "$PIPELINE_SCRIPT" splat \
        --dataset     "$DATASET" \
        --output      "$OUTPUT_SPLAT" \
        --format      x3d \
        --platform    navvis \
        --geo-csv     "$GEO_CSV" \
        --epsg        32605 \
        --image-size  800 \
        --sh-degree   3 \
        --iterations  50000 \
        --frame-stride 2 \
        --init-points 300000 \
        --verbose
