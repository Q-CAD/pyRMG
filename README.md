# pyRMG

## Overview
`pyRMG` enables the rapid auto-generation of [RMG DFT](https://github.com/RMGDFT) input files from VASP POSCAR files for high-throughput calculations. `pyRMG` is currently (Feb. 2025) built off of the develop branch of RMG, and all features may not work properly for other releases.

## Features
- Accepts input parameters as .yml files, which can be applied to directories of POSCAR files. 
- Automatically solves for the number of nodes and processor grid distribution so that they are evenly spaced across the computed cells. 
- Includes checks for force and scf-convergence based on `forcefield.xml` and `rmg_input` files.
- Integrated into matsemble + Flux scheduler workflows for high-throughput calculations.   

## Installation
You can install `pyRMG` using pip:

```bash
pip install git+https://code.ornl.gov/rym/pyrmg.git
```

Alternatively, if you're developing the package, clone the repository and install it in editable mode. 

```bash
git clone https://code.ornl.gov/rym/pyrmg.git
cd pyrmg
pip install -e .
```

## Executables

`submit_pyrmg_cli.py` - Used to submit a directory tree of RMG jobs as singular submissions, i.e., multiple single jobs. Takes the path with RMG input files as required input. 

`generate_pyrmg_cli.py` - Used to constructure RMG input files and submission files (generated from templates in `submission_templates`) from POSCAR files in a subdirectory tree. Takes the POSCARs directory path, a .yml file with RMG input parameters, and a submission script template as required inputs. 

`matsemble_pyrmg_cli.py` - The executable used to submit a directory tree of RMG jobs into a single Flux job submission. Does not require any inputs, as the default is to search current directory for RMG jobs.  

## Examples

NOTE: You must first activate the matensemble conda environment where `pyRMG` is installed in your shell instance. 

```bash
conda activate /autofs/nccs-svm1_proj/cph162/python_environments/matensemble_env
```

Copy `examples/run_directory/` to your scratch directory. Navigate to this directory and run: 

```bash
sbatch submit_matsemble_pyrmg.sh 
```

This will instantiate and submit a Flux workflow to scf- and ionically-converge a bulk, vdW-layered Bi2Se3 calculation. 

## License
This project is licensed under the MIT License. 

## Contact
For any questions or feedback, please reach out via GitHub Issues or email: rym@ornl.gov
