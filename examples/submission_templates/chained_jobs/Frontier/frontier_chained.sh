#!/bin/bash
#
# Change to your account
# Also change in the srun command below
#SBATCH -A MAT201
#
# Job naming stuff
#SBATCH -J rmg-ht-hetero
#SBATCH -o %x-%j.out
#SBATCH -e %x-%j.err
#
# Requested time
#SBATCH -t 12:00:00
#
# Requested queue
#SBATCH -p batch
#
# Number of frontier nodes to use. Note, with Flux, one node is used for resource management.
#SBATCH -N 4125
#
export OMP_NUM_THREADS=7
export RMG_NUM_THREADS=5
export MPICH_OFI_NIC_POLICY=NUMA
export MPICH_GPU_SUPPORT_ENABLED=0

module load PrgEnv-gnu/8.6.0
module load gcc-native/13.2
module load cmake
module load Core/24.00
module load bzip2
module load boost/1.85.0
module load craype-x86-milan
module load cray-fftw
module load cray-hdf5-parallel
module load craype-accel-amd-gfx90a
module load rocm/6.3.1

#---------------------- SETUP FOR job chaining + pyRMG IN FRONTIER -------------------------

# User settings
FRONTIER_NAME="frontier_rmg.sh"
GPUS_PER_NODE=8
RMG_BINARY="/lustre/orion/mat201/world-shared/rjmorelock/rmgdft/build-frontier-gpu/rmg-gpu"
INPUT_FILE="rmg_input"
CONDA_ENV="/lustre/orion/world-shared/lrn090/build_matensemble_env"
SUBMISSION_DIR="/newest_heteros"

# Unload any currently loaded conda environments and activate matensemble_env, allowing pyRMG executables to run
eval "$(command conda 'shell.bash' 'hook' 2> /dev/null)"
conda deactivate
conda activate $CONDA_ENV

# Step 1: Generate the new rmg_input files from any existing rmg_input.*.log files; specify arguments
echo "Generating new inputs..."
generate_pyrmg -pd "$SUBMISSION_DIR" -ry inputs/vdW_quench.yml -rs inputs/frontier_rmg.sh -epg 8 -gde 4 -re /lustre/orion/mat201/world-shared/rjmorelock/build_2/rmgdft/build-frontier-gpu/rmg-gpu -t 02:00:00

# Step 2: Check for $FRONTIER_NAME submission files in subdirectories, pull the required nodes and launch jobs from inside these directories
set -euo pipefail

mapfile -t FRONTIER_FILES < <(find "$SUBMISSION_DIR" -type f -name "$FRONTIER_NAME" | sort)

if [[ ${#FRONTIER_FILES[@]} -eq 0 ]]; then
    echo "No $FRONTIER_NAME files found."
    exit 1
fi

echo "Found ${#FRONTIER_FILES[@]} jobs to run."

for f in "${FRONTIER_FILES[@]}"; do
    dir=$(dirname "$f")
    NNODES=$(sed -nE 's/^[[:space:]]*#SBATCH[[:space:]]+(-N[[:space:]]+|--nodes=)([0-9]+).*/\2/p' "$f" | head -n1)
    NNODES=${NNODES:-1}

    echo "Launching job in $dir using $NNODES nodes..."

    (
        cd "$dir"
        # Redirect stdout/stderr to files in this directory called "stdout" and "stderr"
        srun --exclusive -A MAT201 \
	     -N "$NNODES" \
             --ntasks=$((GPUS_PER_NODE * NNODES)) \
             -u -c7 \
             --gpus-per-node=$GPUS_PER_NODE \
             --ntasks-per-gpu=1 \
             --gpu-bind=closest \
             "$RMG_BINARY" "$INPUT_FILE" > stdout 2> stderr
    ) &
done

echo "All jobs launched. Waiting for completion..."
wait
echo "All jobs finished."

