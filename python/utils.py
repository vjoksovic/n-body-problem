import json
import os

def load_config(config_path="../config/config.json"):
    """Load configuration from JSON file."""
    # Get the absolute path relative to this file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.normpath(os.path.join(script_dir, config_path))
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # If NUM_PROCESSES is null, use CPU count
    if config.get("NUM_PROCESSES") is None:
        config["NUM_PROCESSES"] = os.cpu_count()
    
    return config
