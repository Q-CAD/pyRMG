#!/bin/bash
#
# Change to your account
# Also change in the srun command below
#SBATCH -A {ALLOCATION}
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
#SBATCH -p {PARTITION}

# Number of frontier nodes to use.
#SBATCH -N {NODES}
#
# OMP num threads. Frontier reserves 8 of 64 cores on a node
# for the system. There are 8 logical GPUs per node so we use
# 8 MPI tasks/node with 7 OMP threads per node
export OMP_NUM_THREADS=7
#
# RMG threads. Max of 7 same as for OMP_NUM_THREADS but in some
# cases running with fewer may yield better performance because
# of cache effects.
export RMG_NUM_THREADS=5
#
# Don't change these
export MPICH_OFI_NIC_POLICY=NUMA
export MPICH_GPU_SUPPORT_ENABLED=0
#
# Load modules

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

# Set variables
RMG_BINARY={RMG_EXECUTABLE}
NNODES={NODES}
GPUS_PER_NODE={GPUS_PER_NODE}

srun -A {ALLOCATION} --ntasks=$(($GPUS_PER_NODE * $NNODES)) -u -c{CPUS_PER_TASK} --gpus-per-node=$GPUS_PER_NODE  --ntasks-per-gpu={GPUS_PER_TASK} --gpu-bind=closest $RMG_BINARY {RMG_FILE_PATH}
