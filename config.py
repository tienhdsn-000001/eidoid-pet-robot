"""
Configuration loader for Eidoid Pet Robot
Handles environment variables and .env file
"""

import os
from pathlib import Path


def load_env_file(env_path: str = ".env"):
    """Load environment variables from .env file"""
    env_file = Path(env_path)
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
        print(f"Loaded environment from {env_path}")
    else:
        print(f"No .env file found at {env_path}")


# Auto-load .env when module is imported
load_env_file()