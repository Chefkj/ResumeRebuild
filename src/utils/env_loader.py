"""
Environment Variable Loader.

Utility module for loading environment variables from .env file.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

def load_env_vars(env_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Optional path to .env file. If None, will search in standard locations.
        
    Returns:
        Dictionary of environment variables loaded from .env file.
    """
    if env_path:
        env_file = Path(env_path)
    else:
        # Try to find .env file in current directory or parent directories
        current_dir = Path.cwd()
        project_root = current_dir
        
        # Start with current directory
        env_file = current_dir / '.env'
        
        # If not found, try src directory
        if not env_file.exists():
            env_file = current_dir / 'src' / '.env'
            
        # If still not found, try parent directory
        if not env_file.exists():
            env_file = current_dir.parent / '.env'
            
    if env_file.exists():
        logger.info(f"Loading environment variables from {env_file}")
        load_dotenv(dotenv_path=env_file)
        # Filter environment variables to only include those we added to .env
        # This avoids returning all system environment variables
        env_vars = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key = line.split('=')[0]
                        env_vars[key] = os.environ.get(key, '')
        return env_vars
    else:
        logger.warning(f"No .env file found at {env_file}. Using existing environment variables.")
        return {}
        
def get_api_key(key_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get API key from environment variables.
    
    Args:
        key_name: Name of the environment variable containing the API key.
        default: Default value to return if key is not found.
        
    Returns:
        API key or default value.
    """
    api_key = os.environ.get(key_name, default)
    if api_key is None or api_key == '' or 'your_' in api_key.lower():
        logger.warning(f"API key {key_name} not found in environment variables")
        return default
    return api_key

def get_setting(setting_name: str, default: Any = None) -> Any:
    """
    Get setting from environment variables.
    
    Args:
        setting_name: Name of the environment variable containing the setting.
        default: Default value to return if setting is not found.
        
    Returns:
        Setting value or default value.
    """
    return os.environ.get(setting_name, default)

# Load environment variables when module is imported
load_env_vars()
