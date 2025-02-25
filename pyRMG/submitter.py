import os
import glob
import subprocess
from pathlib import Path

class Submitter:
    @staticmethod
    def submit(top, root):
        os.chdir(root)
        for script_type, command in {'.sh': 'sbatch', '.lsf': 'bsub'}.items():
            script_files = Submitter.find_files(root, script_type)
            if script_files:
                subprocess.call([command, str(script_files[0].name)]) # Submits the first found
                print(f'{root} resubmitted using {script_type}\n')
                break
        else:
            print(f'No submission script in {root}; check that input files exist\n')
        os.chdir(top)

    @staticmethod
    def find_files(path, identifier):
        return list(Path(path).glob(f'*{identifier}'))
