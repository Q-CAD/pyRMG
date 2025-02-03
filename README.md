# pyRMG

## Overview
`pyRMG` allows the user to rapidly generate RMGDFT input files to facilitate high-throughput RMGDFT calculations.

## Features
- Input parameters passed through .yml file format
- Automatically solves for the processor grid distribution based on system specifications
- Includes checks for force and scf-convergence based on the `forcefield.xml` and `rmg_input` files 

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

## License
This project is licensed under the MIT License. 

## Contact
For any questions or feedback, please reach out via GitHub Issues or email: rym@ornl.gov
