from pyRMG.rmg_input import RMGInput
from pyRMG.forcefield import Forcefield
from pyRMG.rmg_log import RMGLog
from pyRMG.submitter import Submitter
from pyRMG.convergence import RMGConvergence
import argparse
import os

OK_GREEN = '\033[92m'
FAIL_RED = '\033[91m'
NO_YELLOW = '\033[93m'
ENDC = '\033[0m'

def main():
    parser = argparse.ArgumentParser(description="Argument parser to submit RMG jobs")
    parser.add_argument("--poscars_directory", "-pd", required=True, help="Path to the directory tree with editable rmg_inputs (POSCARs)")
    parser.add_argument("--rmg_name", "-rn", help="Naming convention for the RMG files to check/generate", default='rmg_input')
    parser.add_argument("--submit", "-s", action='store_true', help="Whether to resubmit unconverged jobs")
    parser.add_argument("--move", "-m", action="store_true", help="Whether to create converged RMG structure and move them to a new directory")
    parser.add_argument("--move_to", "-mt", default='converged', help="Directory where the converged RMG structures will be moved")
    parser.add_argument("--move_name", "-mn", default='POSCAR', help="Name for the converged RMG structures")
    parser.add_argument("--pass_over", "-po", action="store_true", help="Resubmit continuation jobs or only submit new ones")
   
    args = parser.parse_args()
    submit(args)
    return

def get_diverging_directory(path1, path2):
    #path1 is the shorter (write_to) path
    #path2 is the longer (write_from) path

    path1_parts = path1.split(os.path.sep)
    path2_parts = path2.split(os.path.sep)

    common_path = ['/'] # Must have this to write correctly
    added_path = []

    count = 0
    for i in range(len(path1_parts)):
        if path1_parts[i] == path2_parts[i]:
            common_path.append(path1_parts[i])
        else:
            count = i
            break
    added_path += path1_parts[i:]
    added_path += path2_parts[i+1:]
    return os.path.join(*common_path), os.path.join(*added_path)

def build_tree(root, to_path):
    write_path = os.path.abspath(to_path)
    from_path = os.path.abspath(root)
    existing_write_path, new_add_path = get_diverging_directory(write_path, from_path)
    new_write_path = os.path.join(existing_write_path, new_add_path)
    new_rel_write_path = os.path.relpath(new_write_path, os.getcwd())
    return new_rel_write_path

def submit(args):
    abs_poscars_directory = os.path.abspath(args.poscars_directory)
    for root, _, _ in os.walk(abs_poscars_directory):
        rmg_input_path = os.path.join(root, args.rmg_name)
        forcefield_path = os.path.join(root, 'forcefield.xml')
        available_logs = Submitter.find_files(root, 'rmg_input.*.log')

        if os.path.exists(rmg_input_path):
            rmg_input = RMGInput(input_file=rmg_input_path)
            if available_logs:  # Job has run
                rmg_logs = RMGLog(root)
                if os.path.exists(forcefield_path): # A forcefield.xml was written
                    forcefield = Forcefield(forcefield_path)
                    convergence_checker = RMGConvergence(rmg_input=rmg_input, forcefield=forcefield)
                    if convergence_checker.is_converged():
                        print(f'{OK_GREEN}{convergence_checker.calculation_mode} job at {rmg_input_path} is converged.{ENDC}\n')
                        if args.move:
                            write_directories = build_tree(root, args.move_to)
                            os.makedirs(write_directories, exist_ok=True)
                            write_path = os.path.join(write_directories, args.move_name)
                            log_images = sorted(rmg_logs.logs_data.keys())
                            final_structure = rmg_logs.logs_data[log_images[-1]]['structures'][-1]
                            print(f'Moving final image from {log_images[-1]} to {write_path}.\n')
                            final_structure.to(write_path)
                    else:
                        if args.submit and not args.pass_over:
                            print(f'{FAIL_RED}{convergence_checker.calculation_mode} job in {root} is not converged; submitting continuation.{ENDC}\n')
                            Submitter.submit(abs_poscars_directory, root)
                        else:
                            print(f'{FAIL_RED}{convergence_checker.calculation_mode} job in {root} is not converged; not submitting continuation.{ENDC}\n')

                else:
                    if args.submit and not args.pass_over:
                        print(f'{FAIL_RED}{rmg_input.keywords["calculation_mode"]} job in {root} does not have a forcefield.xml; submitting continuation.{ENDC}\n')
                        Submitter.submit(abs_poscars_directory, root)
                    else:
                        print(f'{FAIL_RED}{rmg_input.keywords["calculation_mode"]} job in {root} does not have a forcefield.xml; not submitting continuation.{ENDC}\n')
            else: 
                if args.submit:
                    print(f'{NO_YELLOW}Submitting new {rmg_input.keywords["calculation_mode"]} job in {root}.{ENDC}\n')
                    Submitter.submit(abs_poscars_directory, root)
                else:
                    print(f'{NO_YELLOW}Unsubmitted {rmg_input.keywords["calculation_mode"]} job in {root}.{ENDC}\n')

if __name__ == '__main__':
    main()
