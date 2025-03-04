import os
import yaml

# Define config file path
CONFIG_PATH = os.path.expanduser("~/.pyRMG/config.yml")

# Load configuration file
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    return {}  # Return empty dict if no config file exists
