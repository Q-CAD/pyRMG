# pyRMG
![alt text](RMG_DFT.png?raw=true)

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

Then, create the `config.yml` file with your user settings, which will be used as defaults for `generate_pyrmg`. 

```bash
config pyrmg --allocation MAT123 --partition batch --gpus_per_node 8 --rmg_executable /path/to/your/executable
```

## Executables
`config_pyrmg_cli.py` or `config_pyrmg` - Used to create the configuration .yml file in ~/.pyRMG/. Sets the default rmg executable installation, as well as default information for the system. Setting `nodes: 0` enables node auto-assignment using `processor_grid_search`.   

`submit_pyrmg_cli.py` or `submit_pyrmg` - Used to submit a directory tree of RMG jobs as singular submissions, i.e., multiple single jobs. Takes the path with RMG input files as required input. 

`generate_pyrmg_cli.py` or `generate_pyrmg` - Used to construct RMG input files and submission files (generated from templates in `submission_templates`) from POSCAR files in a subdirectory tree. Takes the POSCARs directory path, a .yml file with RMG input parameters, and a submission script template as required inputs. 

`matsemble_pyrmg_cli.py` or `matsemble_pyrmg` - The executable used to submit a directory tree of RMG jobs into a single Flux job submission. Does not require any inputs, as the default is to search current directory for RMG jobs.  

## MatEnsemble

To integrate `pyRMG` with [MatEnsemble](https://github.com/Q-CAD/MatEnsemble/tree/main), it is most convenient to create a `matensemble` conda environment where `pyRMG` can be installed. You must then make sure that Flux is supported on your machine, or can be activated via Spack.  

```bash
conda activate /path/to/your/matensemble_env
```

Copy `examples/run_directory/` to your scratch directory. Navigate to this directory and run: 

```bash
sbatch submit_matsemble_pyrmg.sh 
```

This provides an example to instantiate and submit a Flux workflow to scf- and ionically-converge a bulk, vdW-layered Bi2Se3 calculation. 

## License
This project is licensed under the MIT License. 

## Contact
For any questions or feedback, please reach out via GitHub Issues or email: rym@ornl.gov
