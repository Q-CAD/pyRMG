#!/bin/bash
#
# Change to your account
# Also change in the srun command below
#SBATCH -A {ALLOCATION}
#SBATCH -C gpu
#
# Job naming stuff
#SBATCH -J {JOB_NAME}
#SBATCH -o %x-%j.out
#SBATCH -e %x-%j.err
#
# Requested time
#SBATCH -t {TIME}
#
# Requested queue
#SBATCH -q {PARTITION}

# Number of frontier nodes to use.
#SBATCH -N {NODES}
#

module purge
module load PrgEnv-gnu
module load cmake
module load craype-x86-milan
module load cray-fftw
module load cray-hdf5-parallel
module load cudatoolkit/12.4

export SLURM_CPU_BIND="cores"
#
export OMP_NUM_THREADS=8
export RMG_NUM_THREADS=9
export OMP_WAIT_POLICY="passive"
#
# Load modules

# Set variables
RMG_BINARY={RMG_EXECUTABLE}
NNODES={NODES}
GPUS_PER_NODE={GPUS_PER_NODE}

srun -A {ALLOCATION} --ntasks-per-node=$GPUS_PER_NODE -c {CORES_PER_TASK} --gpus-per-task={GPUS_PER_TASK} $RMG_BINARY {RMG_FILE_PATH}
