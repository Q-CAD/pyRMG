#!/bin/bash
#
# Change to your account
# Also change in the srun command below
#SBATCH -A m5014_g
#SBATCH -C gpu
#
# Job naming stuff
#SBATCH -J rmg_input
#SBATCH -o %x-%j.out
#SBATCH -e %x-%j.err
#
# Requested time
#SBATCH -t 0:30:00
#
# Requested queue
#SBATCH -q debug
#
# Number of frontier nodes to use. Note, with Flux, one node is used for resource management. 
# Set the same value in the SBATCH line and NNODES
#SBATCH -N 2
#
export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS=8
export RMG_NUM_THREADS=9
export OMP_WAIT_POLICY="passive"
#
# Load modules

module load PrgEnv-gnu
module load cmake
module load craype-x86-milan
module load cray-fftw
module load cray-hdf5-parallel
module load cudatoolkit/12.4
module load conda/Miniforge3-24.11.3-0

#---------------------- SETUP FOR Flux + matensemble + pyRMG IN PERLMUTTER -------------------------------------------------------------------

# Unload any currently loaded conda environments and activate pyRMG_conda, allowing pyRMG executables to run
eval "$(command conda 'shell.bash' 'hook' 2> /dev/null)"
conda deactivate
conda activate '/global/homes/r/rym/envs/pyRMG_conda'

# Load the spack environment and Flux
. /global/cfs/cdirs/m526/sbagchi/spack/share/spack/setup-env.sh
spacktivate -p spack_matensemble_env
module load python/3.13

# Activate pyRMG_conda within the spack
conda activate /global/homes/r/rym/envs/pyRMG_conda

# Step 1: Generate the new rmg_input files from any existing POSCAR or rmg_input.*.log files; can specify arguments
echo "Generating new inputs..."
generate_pyrmg -pd . -ry inputs/vdW_single_point.yml -rs inputs/perlmutter_rmg.sh -n 1 -gde 2

# Step 2: Run the main Flux submission workflow; can specify arguments
echo "Running the main Flux submission workflow..."
srun -N $SLURM_NNODES -n $SLURM_NNODES --external-launcher --mpi=pmi2 --gpu-bind=closest flux start matsemble_pyrmg -pd .

