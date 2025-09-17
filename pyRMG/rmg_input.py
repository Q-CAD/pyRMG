import yaml
import re
import json
import os
import sys
import math
from pymatgen.core import Structure
import numpy as np
from pyRMG.valence import ONCVValences, GeneralValences
from pyRMG.processor_grid import get_processor_grid

# Conversion factor from Bohr to Angstrom
BOHR_TO_ANGSTROM = 0.529177

class RMGInput:
    def __init__(self, structure: Structure = None, site_params: dict = None, keywords: dict = None, input_file: str = None, target_nodes: int = 0):
        """
        Initialize the RMGInput class.

        Parameters:
        - structure (pymatgen.core.Structure): Structure object defining the system.
        - keywords (dict): Dictionary of settings (likely from a .yml file).
        - input_file (str): Path to an existing rmg_input file (if reading from a file).
        """
        self.target_nodes = target_nodes

        if input_file:
            # Load from an existing file
            try:
                self._load_from_file(input_file)
            except ValueError:
                print(f'Cannot generate structure, keywords, and site_params from {input_file}')
                sys.exit(1)
        elif structure and keywords and site_params:
            # Initialize from a structure and a dictionary of settings
            self.structure = structure
            self.keywords = keywords
            self.site_params = site_params
        else:
            raise ValueError("Must provide either input_file or (structure and keywords).")

    def _load_from_file(self, input_file: str):
        """Loads an existing RMG input file."""
        with open(input_file, "r") as f:
            lines = f.readlines()

        # Process input file contents (this part depends on the RMG input format)
        self.structure, self.site_params, self.keywords = self._parse_rmg_input(lines)

    def _parse_rmg_input(self, lines):
        """
        Parses an RMG input file into a dictionary of settings and extracts structure information.

        Parameters:
        - lines (list of str): Lines from the input file.

        Returns:
        - structure (pymatgen Structure or None): Parsed structure, if available.
        - keywords (dict): Dictionary of input settings.
        """
        keywords = {}
        structure_params = {
            "lattice_vectors": [],
            "atomic_positions": [],
            "atomic_coordinate_type": None,
            "crds_units": None,
            "bravais_lattice_type": None,
        }
        site_params = {
            "selective_dynamics": [], 
            "magnetic_properties": [], 
        }
        current_key = None  # Tracks ongoing multi-line values
        multiline_buffer = []  # Stores accumulated lines for multi-line values
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith('"'):  # Skip empty lines and comments
                if current_key and multiline_buffer:
                    keywords[current_key] = '\n'.join(multiline_buffer).replace('"', '').strip()
                current_key = None
                multiline_buffer = []
            elif any(line.startswith(k) for k in ["lattice_vector", "atoms"]):
                current_key = line.split("=")[0].strip()  # Get the key (e.g., "lattice_vector")
                multiline_buffer.append(line.split("=")[1])
            elif current_key and multiline_buffer:
                multiline_buffer.append(line)
            else:
                match = re.match(r'(\w+)\s*=\s*"([^"]*)"', line)
                if match:
                    key, value = match.groups()
                    # Store normal key-value pairs
                    keywords[key] = value.rstrip()

                    # Store relevant structure parameters
                    if key in structure_params:
                        structure_params[key] = value.rstrip()

        # Determine if conversion from Bohr to Angstrom is needed
        conversion_factor = 1.0  # Default (Angstrom)
        if structure_params["crds_units"] == "Bohr":
            conversion_factor = BOHR_TO_ANGSTROM

        # Convert lattice vectors if present
        if "lattice_vector" in keywords:
            structure_params["lattice_vectors"] = np.array([
                list(map(float, line.strip('"').split())) for line in keywords["lattice_vector"].split("\n") if line
            ]) * conversion_factor  # Apply unit conversion

        # Convert atomic positions if present
        if "atoms" in keywords:
            structure_params["atomic_positions"] = [
                line.strip('"').split() for line in keywords["atoms"].split("\n") if line
            ]

        # Build pymatgen Structure if possible
        structure = None
        if structure_params["lattice_vectors"] is not [] and structure_params["atomic_positions"] is not []:
            species = [atom[0] for atom in structure_params["atomic_positions"]]
            coords = np.array([[float(x) for x in atom[1:4]] for atom in structure_params["atomic_positions"]])
            site_params['selective_dynamics'] = [[atom[i] == "1" for i in range(4, 7)] for atom in structure_params["atomic_positions"]]
            site_params['magnetic_properties'] = [[float(atom[i]) for i in range(7, len(atom))] for atom in structure_params["atomic_positions"]]
            coords *= conversion_factor  # Apply unit conversion to atomic positions
            
            # Set coords_are_cartesian
            if structure_params["atomic_coordinate_type"] == "Absolute":
                coords_are_cartesian = True
            else:
                coords_are_cartesian = False

            structure = Structure(
                structure_params["lattice_vectors"], species, coords,
                coords_are_cartesian=coords_are_cartesian
            )
        
        # Remove the structure-specific keys from the keywords dictionary
        for key in ('atoms', 'lattice_vector', 'bravais_lattice_type', 'crds_units', 'lattice_units', 'atomic_coordinate_type'):
            keywords.pop(key, 0)

        return structure, site_params, keywords

    def save(self, filename: str):
        """Writes the RMG input file from the current structure and settings."""
        with open(filename, "w") as f:
            f.write(self._generate_rmg_input())

    def _generate_rmg_input(self) -> str:
        """
        Converts structure and keywords into the RMG input file format.

        Returns:
        - str: Formatted input file content.
        """
        writelines = ""
        for key in sorted(self.keywords.keys()):
            writelines += f'{key} = "{self.keywords[key]}"\n'
        writelines += '\n'

        writelines += f'atomic_coordinate_type = "Absolute"\n'
        writelines += f'crds_units = "Angstrom"\n'
        writelines += f'lattice_units = "Angstrom"\n\n'

        lattice_vector_lines = 'lattice_vector = "\n'
        for row in self.structure.lattice.matrix:
            lattice_vector_lines += ' '.join(f"{f:.12e}" for f in row) + '\n'
        lattice_vector_lines += '"\n'
        writelines += lattice_vector_lines

        writelines += f'atoms = "\n'
        for i, site in enumerate(self.structure):
            atom_line = ''
            atom_line += str(site.specie) + ' '
            atom_line += " ".join(f"{val:.12e}" for val in site.coords) + ' '
            atom_line += self.site_params['selective_dynamics'][i] + ' '
            atom_line += self.site_params['magnetic_properties'][i] + '\n'
            writelines += atom_line
        writelines += '"'

        return writelines

    @classmethod
    def from_yaml(cls, yaml_path, structure_path=None, structure_obj=None, pseudopotentials_directory='', 
                  magmom_path=None, target_nodes=0, gpus_per_node=8, electrons_per_gpu=10, grid_divisibility_exponent=3):
        with open(yaml_path, 'r') as f:
            input_args = yaml.safe_load(f)
        
        if not structure_obj:
            structure_obj = Structure.from_file(structure_path)
        site_params = {'selective_dynamics': cls._read_selective_dynamics(structure_obj), 
                       'magnetic_properties': cls._read_magnetic_occupancies(structure_obj)}
        
        if magmom_path and os.path.exists(magmom_path):
            print(f'Reading magnetic moments from {magmom_path}')
            with open(magmom_path, 'r') as f:
                site_params['magnetic_properties'] = [" ".join(map(str, mag)) for mag in json.load(f)]
        elif site_params['magnetic_properties']:
            pass
        else:
            site_params['magnetic_properties'] = ["0.0 0.0 0.0" for site in structure_obj]

        # User-supplied tag logic
        if 'cutoff' in input_args:
            wavefunction_grid = cls._generate_wavefunction_grid(structure_obj, input_args['cutoff'])
            input_args['wavefunction_grid'] = wavefunction_grid
            input_args.pop('cutoff', 0)
        elif 'wavefunction_grid' in input_args:
            wavefunction_grid = input_args['wavefunction_grid']
        else:
            raise KeyError(f'Input .yml must contain "cutoff" or "wavefunction_grid"')
        
        # Kpoints from mesh density
        if 'kdelt' in input_args:
            kpoint_mesh = cls._generate_kpoint_mesh(structure_obj, input_args['kdelt'])
            input_args['kpoint_mesh'] = kpoint_mesh
            input_args.pop('kdelt', 0)
        elif 'kpoint_mesh' in input_args:
            pass
        else:
            raise KeyError(f'Input .yml must contain "kdelt" or "kpoint_mesh"')

        # Auto-generate kpoint distribution
        if 'kpoint_distribution' in input_args and input_args['kpoint_distribution'] > 0:
            kpoint_distribution = input_args['kpoint_distribution']
        else:
            # Externally set kpoint_distribution, similar to 'kpoint_distribution = -1' default
            kpoint_distribution = int(np.prod([int(i) for i in input_args['kpoint_mesh'].split()]))
            input_args['kpoint_distribution'] = kpoint_distribution

        # Path to different pseudos than default
        pseudo_dct = {}
        if 'pseudo_dir' in input_args:
            pseudopotentials_directory = input_args['pseudo_dir'] # Overwrite default from passed .yml file
            if 'pseudopotential' in input_args:
                pseudo_dct = cls._parse_map(input_args['pseudopotential'])

        total_electrons = cls._sum_electrons(structure_obj, pseudopotentials_directory, pseudo_dct)

        # Set unoccupied levels; can improve convergence
        if 'unoccupied_fraction' in input_args:
            electronic_states = np.ceil(0.5 * total_electrons)
            input_args['unoccupied_states_per_kpoint'] = int(input_args['unoccupied_fraction'] * electronic_states)
            input_args.pop('unoccupied_fraction', 0)

        # Per atom convergence criterion
        if 'per_atom_energy' in input_args:
            energy_convergence_criterion = input_args['per_atom_energy'] * len(structure_obj)
            if energy_convergence_criterion < 1e-20:
                energy_convergence_criterion = 1e-20
            elif energy_convergence_criterion > 1e-07:
                energy_convergence_criterion = 1e-07
            else:
                pass
            input_args['energy_convergence_criterion'] = cls._round_sig(energy_convergence_criterion) 
            input_args.pop('per_atom_energy', 0)

        # Per atom rms convergence
        if 'per_atom_rms' in input_args:
            rms_convergence_criterion = input_args['per_atom_rms'] * len(structure_obj)
            if rms_convergence_criterion > 1e-03:
                rms_convergence_criterion = 1e-03
            input_args['rms_convergence_criterion'] = cls._round_sig(rms_convergence_criterion)
            input_args.pop('per_atom_rms', 0)

        # Processor grid generation
        if not 'processor_grid' in input_args:
            fix_nodes = True
            if not target_nodes:
                target_nodes = (total_electrons / (electrons_per_gpu * gpus_per_node))
                fix_nodes = False
            processor_grid, target_nodes = get_processor_grid([int(g) for g in wavefunction_grid.split()],
                                                              target_nodes, gpus_per_node, kpoint_distribution, 
                                                              grid_divisibility_exponent, fix_nodes)
            input_args['processor_grid'] = processor_grid

        return cls(structure=structure_obj, keywords=input_args, site_params=site_params, target_nodes=target_nodes)
    
    @staticmethod
    def _parse_map(text: str) -> dict[str, str]:
        tokens = text.split()
        if len(tokens) % 2 != 0:
            raise ValueError("Expected an even number of tokens (key/value pairs) from 'pseudopotential' input parameter")
        # take every even token as a key, the following one as its value
        return dict(zip(tokens[0::2], tokens[1::2]))

    @staticmethod
    def _sum_electrons(structure, pseudopotentials_directory, pseudo_dct):
        if pseudopotentials_directory == '': 
            valence = ONCVValences()
        else:
            valence = GeneralValences(pseudopotentials_directory, pseudo_dct) 
        try:
            total_electrons = np.sum([valence.get_valence(str(site.specie)) for site in structure])
            return total_electrons
        except TypeError:
            print(f'Not all elements in {structure_obj.composition.reduced_formula} have ONCV pseudopotentials! Exiting...')
            sys.exit(1)

    @staticmethod
    def _read_selective_dynamics(structure):
        return [" ".join("1" if x else "0" for x in sd) if "selective_dynamics" in structure.site_properties else "1 1 1"
            for sd in structure.site_properties.get("selective_dynamics", [[True, True, True]] * len(structure))]
    
    @staticmethod
    def _read_magnetic_occupancies(structure):
        return [" ".join(str(x) for x in sd) if "magnetic_properties" in structure.site_properties else "0.0 0.0 0.0"
            for sd in structure.site_properties.get("magnetic_properties", [])]

    @staticmethod
    def _generate_wavefunction_grid(structure, cutoff):
        rca = np.pi / np.sqrt(cutoff) * BOHR_TO_ANGSTROM
        nx, ny, nz = np.rint(structure.lattice.abc / rca).astype(int)

        def grid_spacing_factors(nx, ny, nz, factor):
            return [(dim + factor - 1) // factor * factor for dim in [nx, ny, nz]]
        
        def anisotropy_check(structure, nxg, nyg, nzg):
            h_max = np.max(np.divide(structure.lattice.abc, [nxg, nyg, nzg]))
            h_min = np.min(np.divide(structure.lattice.abc, [nxg, nyg, nzg]))
            return h_max / h_min <= 1.1
        
        use_i = 1
        for _ in range(4):
            use_i *= 2
            nxg, nyg, nzg = grid_spacing_factors(nx, ny, nz, use_i)
            if anisotropy_check(structure, nxg, nyg, nzg):
                break
        return " ".join(str(n) for n in [nxg, nyg, nzg])
    
    @staticmethod
    def _generate_kpoint_mesh(structure, kdelt):
        kpoints = [int(max(1, np.rint(np.divide(mag, kdelt)))) for mag in np.multiply(structure.lattice.reciprocal_lattice.abc, BOHR_TO_ANGSTROM)]
        return " ".join([str(k) for k in kpoints])
   
    def _generate_keywords(self):
        self.keywords['positions'] = self.site_params['selective_dynamics']
        if 'cutoff' in self.input_args:
            self.keywords['wavefunction_grid'] = self._generate_wavefunction_grid(self.structure, self.input_args['cutoff'])

    @staticmethod
    def _round_sig(number, sig=3):
        power = "{:e}".format(number).split('e')[1]
        return round(number, -(int(power) - sig))
