import os
import glob
import numpy as np
from pymatgen.core import Structure

class RMGLog:
    def __init__(self, directory_path):
        self.directory_path = directory_path
        self.logs_data = self._parse_logs()
        self.logs_keys = list(self.logs_data.keys())
    
    def _parse_logs(self):
        log_files = glob.glob(os.path.join(self.directory_path, 'rmg_input.*.log'))
        poscar_paths = glob.glob(os.path.join(self.directory_path, 'POSCAR'))
        original_structure = Structure.from_file(poscar_paths[-1]) if poscar_paths else None
        
        logs_data = {}
        bohr_factor = 1.8897259886  # Convert Bohr to Angstroms
        rydberg_factor = 2
        bohr_rydberg = np.divide(rydberg_factor, bohr_factor)  # Convert forces
        
        for log_file in sorted(log_files):
            structures, forces, energies = [], [], []
            all_lattices, all_positions, all_species, all_forces = [], [], [], []
            current_lattice, current_position, current_specie, current_force = [], [], [], []
            
            with open(log_file, 'r') as f:
                for line in f:
                    if "X Basis Vector" in line or "Y Basis Vector" in line or "Z Basis Vector" in line:
                        split_lines = line.split()
                        try:
                            current_lattice.append([float(split_lines[3]), float(split_lines[4]), float(split_lines[5])])
                            if len(current_lattice) == 3:
                                all_lattices.append(current_lattice)
                                current_lattice = []
                        except IndexError:
                            continue
                    
                    elif "lattice" in line:
                        split_lines = line.split()
                        try:
                            current_lattice.append([float(split_lines[2]), float(split_lines[3]), float(split_lines[4])])
                            if len(current_lattice) == 3:
                                all_lattices.append(current_lattice)
                                current_lattice = []
                        except IndexError:
                            continue
                    
                    elif "@ION" in line:
                        split_lines = line.split()
                        try:
                            if isinstance(eval(split_lines[1]), int):  # Integer indicating species number
                                current_position.append([float(split_lines[3]), float(split_lines[4]), float(split_lines[5])])
                                current_specie.append(split_lines[2])
                                current_force.append([float(split_lines[7]), float(split_lines[8]), float(split_lines[9])])
                        except (NameError, IndexError):
                            continue
                    
                    if len(current_specie) == len(original_structure):
                        all_positions.append(current_position)
                        all_species.append(current_specie)
                        all_forces.append(current_force)
                        current_position, current_specie, current_force = [], [], []
                    
                    if "final total energy from eig sum" in line:
                        energies.append(float(line.split('=')[-1].strip().split()[0]))
            
            if len(all_lattices) == 1:
                check_lattices = [all_lattices[0] for _ in range(len(all_positions))]
            else:
                check_lattices = all_lattices
            
            number_complete = min(len(check_lattices), len(all_positions))
            energies = energies[:number_complete] 

            for i in range(number_complete):
                lattice_angstroms = np.divide(np.array(check_lattices[i]), bohr_factor)
                lattice_positions = np.divide(np.array(all_positions[i]), bohr_factor)
                force_hartree_angstrom = np.multiply(np.array(all_forces[i]), bohr_rydberg)
                #print(force_hartree_angstrom) 
                s = Structure(lattice=lattice_angstroms, species=all_species[i],
                              coords=lattice_positions, coords_are_cartesian=True)
                structures.append(s)
                forces.append(force_hartree_angstrom)
            
            logs_data[log_file] = {
                "structures": structures,
                "forces": forces,
                "energies": energies
            }
        
        return logs_data
    
    def get_log_data(self, log_file=None):
        if log_file:
            return self.logs_data.get(log_file, None)
        return self.logs_data

