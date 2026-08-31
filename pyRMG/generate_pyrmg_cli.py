from pyRMG.load_config import load_config
from pyRMG.forcefield import Forcefield
from pyRMG.rmg_input import RMGInput
from pyRMG.convergence import RMGConvergence
from pyRMG.pick_structure import pick_best_structure
from pathlib import Path
import argparse
import os
import sys

OK_GREEN = '\033[92m'
FAIL_RED = '\033[91m'
NO_YELLOW = '\033[93m'
ENDC = '\033[0m'

def main():
    config = load_config()
    parser = argparse.ArgumentParser(description="Argument parser to generate rmg_inputs from POSCAR files")

    # Divisibility exponent check
    def divisibility_exponent(exponent):
        if int(exponent) < 1: 
            raise argparse.ArgumentTypeError(f"--grid_divisibility_exponent = {exponent} must be greater than or equal to 1")
        return int(exponent)

    # Add arguments

    # Input and ouput paths, files and names
    parser.add_argument("--parent_directory", "-pd", help="Path to the directory tree with editable POSCARs", required=True)
    parser.add_argument("--rmg_yaml", "-ry", help="Path to the YAML file with RMG parameters", required=True)
    parser.add_argument("--rmg_submission", "-rs", help="Path to a rmg submission script template", required=True)
    parser.add_argument("--rmg_name", "-rn", help="Naming convention for the RMG files to check/generate", default='rmg_input')
    parser.add_argument("--structure_filename", "-sfn", help="Filename to be checked for and read by pymatgen.core.Structure. Supported formats include POSCAR, .cif", 
                        default='POSCAR') 
    parser.add_argument("--magmom_name", "-mn", help="Naming convention for the .json files containing magnetic moments", default='MAGMOM.json')

    # Parameters for the submission script
    parser.add_argument("--allocation", "-a", help="Allocation", type=str, default=config.get("allocation", "XXX"))
    parser.add_argument("--partition", "-p", help="Partition", type=str, default=config.get("partition", "batch"))
    parser.add_argument("--nodes", "-n", help="Number of nodes to request", type=int, default=config.get("nodes", 0))
    parser.add_argument("--cpus_per_node", "-c", help="Number of cpus per node on your resource", type=int, default=config.get("cpus_per_node", 1))
    parser.add_argument("--gpus_per_node", "-g", help="Number of gpus per node on your resource", type=int, default=config.get("gpus_per_node", 1))
    parser.add_argument("--rmg_executable", "-re", help="Path to rmg executable", default=config.get("rmg_executable", None))
    parser.add_argument("--cpus_per_task", "-cpt", help="CPUs per task", type=int, default=config.get("cpus_per_task", 1))
    parser.add_argument("--gpus_per_task", "-gpt", help="GPUs per task", type=int, default=config.get("gpus_per_task", 1))
    parser.add_argument("--pseudopotentials_directory", "-pspd", help="Path to pseudopotentials directory", type=str, default=config.get("pseudopotentials_directory", '')) 

    parser.add_argument("--electrons_per_gpu", "-epg", help="Number of valence electrons (based on atoms and PPs) per gpu", type=int, default=10)
    parser.add_argument("--grid_divisibility_exponent", "-gde", help="Exponential factor for processor grid divisibility", type=divisibility_exponent, default=3)
    parser.add_argument("--debug", "-d", help="Whether to write debug QOS to submission script", action="store_true")
    parser.add_argument("--time", "-t", help="Calculation wall time, with default format hours:minutes:seconds", type=str, default=config.get("time", "02:00:00"))

    # Parse arguments and run function
    args = parser.parse_args()
    if not args.rmg_executable:
        print('No valid rmg_executable path provided! check ~/.pyRMG/config.yml')
        sys.exit(1)

    generate(args)
    return

def read_text(path):
    ''' Reads in as a string '''
    with open(path, 'r') as input_file:
        input_str = input_file.read()
    return input_str

def write_text(text, path):
    with open(path, 'w') as file:
        file.write(text)
    return 

def create_rmg_submission(copy_path, write_path, nodes, args):
    ''' Reads a template submission file from copy_path and edits it with user parameters before writing it to write_path'''
    submission_lines = read_text(copy_path)
    lines = submission_lines.split('\n')
    final_lines = ''
    write_debug = args.debug
    for i, line in enumerate(lines):
        if '{ALLOCATION}' in line:
            line = line.replace('{ALLOCATION}', args.allocation)
        if '{PARTITION}' in line:
            line = line.replace('{PARTITION}', args.partition)
        if '{RMG_EXECUTABLE}' in line:
            line = line.replace('{RMG_EXECUTABLE}', args.rmg_executable)
        if '{CPUS_PER_TASK}' in line:
            line = line.replace('{CPUS_PER_TASK}', str(args.cpus_per_task))
        if '{GPUS_PER_TASK}' in line:
            line = line.replace('{GPUS_PER_TASK}', str(args.gpus_per_task))
        if '{JOB_NAME}' in line:
            line = line.replace('{JOB_NAME}', args.rmg_name.replace(' ', '')) # Get rid of spaces
        if '{NODES}' in line:
            line = line.replace('{NODES}', str(nodes))
        if '{TIME}' in line:
            line = line.replace('{TIME}', args.time)
        if '{RMG_FILE_PATH}' in line:
            line = line.replace('{RMG_FILE_PATH}', args.rmg_name)
        if '{CPUS_PER_NODE}' in line:
            line = line.replace('{CPUS_PER_NODE}', str(args.cpus_per_node))
        if '{GPUS_PER_NODE}' in line:
            line = line.replace('{GPUS_PER_NODE}', str(args.gpus_per_node))
        final_lines += line + '\n'

        if "SBATCH -p" in line and write_debug is True:
            final_lines += '#SBATCH -q debug\n#'
            write_debug = False
    write_text(final_lines, write_path)
    return

def generate(args):
    abs_poscars_directory = os.path.abspath(args.parent_directory)
    for root, _, _ in os.walk(abs_poscars_directory):
        generate_inputs = True

        # Check convergence
        forcefield_path = os.path.join(root, 'forcefield.xml')
        rmg_path = os.path.join(root, args.rmg_name)

        if os.path.exists(forcefield_path) and os.path.exists(rmg_path):
            forcefield = Forcefield(forcefield_xml_path=forcefield_path)
            rmg_input = RMGInput(input_file=rmg_path)
            convergence_checker = RMGConvergence(forcefield=forcefield, 
                                                 rmg_input=rmg_input)
            if convergence_checker.is_converged():
                print(f'{OK_GREEN}{convergence_checker.calculation_mode} job in {root} is converged, no inputs generated.{ENDC}\n')
                generate_inputs = False
            else:
                print(f'{FAIL_RED}Unconverged {convergence_checker.calculation_mode} job in {root}, inputs generated.{ENDC}')

        # Choose the input structure -- delegated to pick_best_structure,
        # which implements the same logs -> existing rmg_input ->
        # structure_filename priority order this used to duplicate inline,
        # plus the existing-rmg_input site_params merge (selective_dynamics/
        # magnetic_properties) and MAGMOM.json-based magnetic-moment
        # attachment that used to be done separately here too. Consolidated
        # into one place so the two copies can't drift apart again -- the
        # site-properties handling here had gotten a real fix on the
        # MatEnsemble side that this copy hadn't picked up.
        final_structure = None

        if generate_inputs:
            try:
                final_structure, source = pick_best_structure(
                    root, structure_filename=args.structure_filename,
                    rmg_name=args.rmg_name, magmom_name=args.magmom_name)
                print(f'Generating input for {root} from {source}')
            except FileNotFoundError:
                continue  # no usable structure in this directory

        # Create the new rmg_input file if final_structure exists
        if final_structure:
            # magmom_path deliberately not passed here -- pick_best_structure
            # already attached 'magnetic_properties' as a site property
            # (from MAGMOM.json if present, else from an existing rmg_input's
            # own site_params), and from_yaml falls back to reading it off
            # structure_obj's own site properties when magmom_path is None.
            rmg_input = RMGInput.from_yaml(yaml_path=args.rmg_yaml,
                                 structure_path=None,
                                 structure_obj=final_structure,
                                 pseudopotentials_directory=args.pseudopotentials_directory,
                                 target_nodes=args.nodes,
                                 gpus_per_node=args.gpus_per_node,
                                 electrons_per_gpu=args.electrons_per_gpu,
                                 grid_divisibility_exponent=args.grid_divisibility_exponent)
            rmg_input.save(filename=os.path.join(root, args.rmg_name))

            # Create the submission script template
            submission_name = Path(args.rmg_submission).name
            write_path = os.path.join(root, submission_name)
            
            print(f'Generating {submission_name} for {root}\n')
            create_rmg_submission(copy_path=args.rmg_submission, 
                                  write_path=write_path, 
                                  nodes=rmg_input.target_nodes,
                                  args=args)

    return 

if __name__ == '__main__':
    main()

