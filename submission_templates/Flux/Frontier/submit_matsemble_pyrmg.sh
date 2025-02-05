#!/bin/bash
#
# Change to your account
# Also change in the srun command below
#SBATCH -A MAT201
#
# Job naming stuff
#SBATCH -J rmgmp-541837
#SBATCH -o %x-%j.out
#SBATCH -e %x-%j.err
#
# Requested time
#SBATCH -t 02:00:00
#
# Requested queue
#SBATCH -p batch
#SBATCH -q debug
#
# Number of frontier nodes to use.
# Set the same value in the SBATCH line and NNODES
#SBATCH -N 1
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

module load PrgEnv-gnu/8.5.0
module load Core/24.00
module load cmake
module load bzip2/1.0.8
module load boost/1.85.0
module load craype-x86-milan
module load cray-fftw
module load cray-hdf5-parallel
module load craype-accel-amd-gfx90a
module load rocm/6.0.0
module load libfabric/1.15.2.0 # Reload previous libfabric

#---------------------- SETUP FOR MATENSEMBLE IN FRONTIER -------------------------------------------------------------------
. /autofs/nccs-svm1_proj/cph162/Sep_11_2024/spack/share/spack/setup-env.sh
which spack
spack env activate spack_matensemble_env
spack load flux-sched
which flux
export PYTHONPATH=$PYTHONPATH:/autofs/nccs-svm1_proj/cph162/python_environments/matensemble_env/lib/python3.11/site-ackages

module load python
conda activate /autofs/nccs-svm1_proj/cph162/python_environments/matensemble_env

# just in case there are python conflicts due to spack and conda
CONDA_PYTHON_EXE=/autofs/nccs-svm1_proj/cph162/python_environments/matensemble_env/bin/python
echo $CONDA_PYTHON_EXE

srun -N $SLURM_NNODES -n $SLURM_NNODES --external-launcher --mpi=pmi2 --gpu-bind=closest flux start matsemble_pyrmg
