# pyRMG
![alt text](RMG_DFT.png?raw=true)

## Overview
`pyRMG` enables the rapid auto-generation of [RMG DFT](https://github.com/RMGDFT) input files from VASP POSCAR files for high-throughput calculations. `pyRMG` is currently (Feb. 2025) built off of the develop branch of RMG, and all features may not work properly for other releases.

## Features
- Accepts input parameters as .yml files, which can be applied to directories of POSCAR files. 
- Automatically solves for the number of nodes and processor grid distribution so that they are evenly spaced across the computed cells. 
- Includes checks for force and scf-convergence based on `forcefield.xml` and `rmg_input` files.
- `rmg_calculator.RMG`, an ASE `FileIOCalculator` wrapping the compiled `rmg-gpu`/`rmg-cpu` binary, and
  `pick_structure.pick_best_structure`, which resolves the authoritative starting structure for a run
  (latest structure from an `rmg_input.*.log`, else an existing `rmg_input`, else a static structure file)
  -- these back the current MatEnsemble+Flux integration; see the MatEnsemble section below.

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

`matsemble_pyrmg_cli.py` or `matsemble_pyrmg` - **Deprecated.** Used to submit a directory tree of RMG jobs into a single Flux job submission via `matensemble.matfluxGen.SuperFluxManager`, an old MatEnsemble API that no longer exists in current MatEnsemble releases. Kept for reference only; will not run against a current `matensemble` install. See the MatEnsemble section below for the current integration path.

## MatEnsemble

`pyRMG`'s own `matsemble_pyrmg` entry point (above) is deprecated -- current MatEnsemble+Flux integration goes through [Ensemble-FF-Fit](https://github.com/Q-CAD/Ensemble-FF-Fit)'s `DFTMatEnsemble` instead, using `pyRMG.rmg_calculator.RMG` (an ASE `Calculator` wrapping the RMG binary) and `pyRMG.pick_structure.pick_best_structure` (restart-aware structure resolution) as the building blocks a site-specific driver script calls into. See
`Ensemble-FF-Fit/examples/Frontier/RMG_MACE_ASE/` for a full worked example (RMG DFT convergence -> MACE
ensemble fitting -> ASE finite-temperature MD), including its own driver script
(`DFT/rmg_dft.py`) showing how a MatEnsemble chore dispatches into `pyRMG`.

To install `pyRMG` for that integration, add it as an optional dependency of `Ensemble-FF-Fit`
(the `rmg` extra: `pip install -e ".[rmg]"`) rather than installing it standalone -- `Ensemble-FF-Fit`
owns the MatEnsemble/Flux `Pipeline`/chore submission logic; `pyRMG` only provides the RMG-specific
input generation, execution, and log-parsing pieces that driver script calls into.

For submitting RMG jobs *without* MatEnsemble/Flux, `submit_pyrmg`/`generate_pyrmg` (above) remain the
standalone entry points and don't depend on any of this.

## License
This project is licensed under the MIT License. 

## Contact
For any questions or feedback, please reach out via GitHub Issues or email: rym@ornl.gov
