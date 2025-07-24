import argparse
import yaml
import os
import sys

CONFIG_PATH = os.path.expanduser("~/.pyRMG/config.yml")


def main():
    parser = argparse.ArgumentParser(description="Generate pyRMG configuration file.")

    # RMG parameters
    parser.add_argument("--rmg_executable", "-re", type=str, required=True, help="Path to RMG executable")
    parser.add_argument("--pseudopotentials_directory", "-pspd", type=str, default='', 
                        help="Path to pseudopotentials directory; default of '' uses in-built ONCV potentials")
    
    # System-specific parameters
    parser.add_argument("--allocation", "-a", type=str, required=True, help="Job allocation name")
    parser.add_argument("--partition", "-p", type=str, required=True, help="Cluster partition")
    parser.add_argument("--time", "-t", type=str, required=True, help="Job time limit (HH:MM:SS)")
    parser.add_argument("--nodes", "-n", type=int, default=0, help="Number of nodes; setting nodes = 0 enables auto-node assignment!")
    parser.add_argument("--cpus_per_node", "-cpn", type=int, default=64, help="Number of CPUs per node on resource")
    parser.add_argument("--cpus_per_task", "-cpt", type=int, default=7, help="Number of cores to use per RMG task")
    parser.add_argument("--gpus_per_node", "-gpn", type=int, default=8, help="Number of GPUs per node on resource")
    parser.add_argument("--gpus_per_task", "-gpt", type=int, default=1, help="Number of GPUs to use per RMG task")

    args = parser.parse_args()

    if os.path.exists(args.rmg_executable) is False:
        print(f"No RMG executable located at {args.rmg_executable}! exiting without writing config.yml")
        sys.exit(1)

    config = {
        "allocation": args.allocation,
        "partition": args.partition,
        "nodes": args.nodes,
        "cpus_per_node": args.cpus_per_node, 
        "gpus_per_node": args.gpus_per_node,
        "time": args.time,
        "rmg_executable": args.rmg_executable,
        "pseudopotentials_directory": args.pseudopotentials_directory, 
        "cpus_per_task": args.cpus_per_task,
        "gpus_per_task": args.gpus_per_task
    }

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f)

    print(f"Configuration file saved at {CONFIG_PATH}")

if __name__ == "__main__":
    main()
