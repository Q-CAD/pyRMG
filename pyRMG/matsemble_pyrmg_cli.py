from pyRMG.rmg_input import RMGInput
from pyRMG.forcefield import Forcefield
from pyRMG.submitter import Submitter
import glob
import argparse
import os
import numpy as np
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Argument parser to generate rmg_inputs from POSCAR files")

    # Add arguments

    # Input and ouput paths, files and names
    parser.add_argument("--rmg_inputs_directory", "-rid", help="Path to the directory tree with RMG input files", default='.')
    parser.add_argument("--rmg_name", "-rn", help="Naming convention for the RMG files to check/generate", default='rmg_input')
    parser.add_argument("--rmg_executable", "-re", help="Path to rmg executable", 
                        default='/lustre/orion/world-shared/cph162/rjmorelock/rmgdft/build-frontier-gpu/rmg-gpu')
    
    parser.add_argument("--cores_per_task", "-cpt", help="Cores per task", type=int, default=7)
    parser.add_argument("--gpus_per_task", "-gpt", help="GPUs per task", type=int, default=1)
    parser.add_argument("--write_restart_freq", "-wrf", help="Write restart frequency", type=int, default=5)
    parser.add_argument("--dry_run", "-dry", help="Only print the structures to be run", action='store_true')

    # Parse arguments and run function
    args = parser.parse_args()
    execute_Flux(args)
    return

def get_total_gpus(rmg_input_root):
    nodes = False
    gpus_per_node = False

    try:
        sh_file = Submitter.find_files(rmg_input_root, '.sh')[0]
    except IndexError:
        print(f'No .sh file in {rmg_input_root}')
        return None

    with open(sh_file, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if 'NNODES' in line:
            try:
                nodes = int(line.split('=')[1].strip())
            except:
                pass

        if 'GPUS_PER_NODE' in line:
            try:
                gpus_per_node = int(line.split('=')[1].strip())
            except:
                pass
    
    if nodes and gpus_per_node:
        return nodes * gpus_per_node
    else:
        print(f'Found NNODES={nodes} and found GPUS_PER_NODE={gpus_per_node}; check .sh file in {rmg_input_root}!')
        return None
    
def execute_Flux(args):
    rmg_roots, rmg_input_paths, total_gpus_lst = [], [], []

    abs_rmg_inputs_directory = os.path.abspath(args.rmg_inputs_directory)
    for root, _, _ in os.walk(abs_rmg_inputs_directory):
        append_path = False
        rmg_input_path = os.path.join(root, args.rmg_name)
        if os.path.exists(rmg_input_path):
            rmg_input = RMGInput(input_file=rmg_input_path)
            forcefield_path = os.path.join(root, 'forcefield.xml')
            
            total_gpus = get_total_gpus(root)
            if total_gpus:
                if os.path.exists(forcefield_path):
                    forcefield = Forcefield(forcefield_path)
                    convergence_checker = RMGConvergence(rmg_input=rmg_input, forcefield=forcefield)
                    if not convergence_checker.is_converged():
                        append_path = True
                else:
                    append_path = True
        if append_path is True:
            rmg_roots.append(root)
            rmg_input_paths.append(rmg_input_path)
            total_gpus_lst.append(total_gpus)
    
    task_list = list(np.arange(len(rmg_roots)))
    tasks_per_job = np.array(total_gpus_lst)

    if args.dry_run:
        total_gpus = 0
        print(f'Printing all RMG directories to run...\n')
        for i in task_list:
            print(f'Task ID: {task_list[i]}, Path: {rmg_input_paths[i]}, Task GPUs: {total_gpus_lst[i]}')
            total_gpus += total_gpus_lst[i]
        print(f'\nTotal GPUs = {total_gpus}. Do not forget to request 1 additional node for resource management!')
        return 

    else:
        # Now instantiate a task_manager object, which is a Superflux Manager sitting on top of evey smaller Fluxlets
        job_record = pd.DataFrame({'Task id': task_list,
        'Task path': rmg_roots
        })
        job_record.to_csv('job_record.txt', sep=' ', index=None)

        from matensemble.matfluxGen import SuperFluxManager

        master = SuperFluxManager(task_list, 
                              args.rmg_executable, 
                              None,
                              tasks_per_job=tasks_per_job, 
                              cores_per_task=args.cores_per_task,
                              gpus_per_task=args.gpus_per_task, 
                              write_restart_freq=args.write_restart_freq)

        # For multiple args per task each if the elements could be a list i.e. task_args_list = [['x0f','x14'],['xa9','xf3'],[]...]
        # finally execute the whole pool of tasks
        master.poolexecutor(task_arg_list=rmg_input_paths, 
                        buffer_time=1, 
                        task_dir_list=rmg_roots)

        return 

if __name__ == '__main__':
    main()
