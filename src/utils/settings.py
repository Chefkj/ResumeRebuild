"""
Configuration settings for the Resume Rebuilder application.

This file provides a centralized location for application settings and preferences.
"""

import os
import json
import logging
from pathlib import Path
from enum import Enum
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ApiBackendType(Enum):
    """Enum for available API backend types."""
    LOCAL_SERVER = "local_server"
    MANAGE_AI = "manageai"
    LLM_DIRECT = "llm_direct"

class Settings:
    """Application settings manager."""
    
    # Default settings
    DEFAULT_SETTINGS = {
        "api": {
            "backend": "manageai",  # Can be: "local_server", "manageai", "llm_direct"
            "local_url": "http://localhost:8080",
            "manageai_url": "http://localhost:8080",
            "llm_host": "localhost",
            "llm_port": 1234,
            "llm_model": "qwen-14b",
            "api_key": "",
            "timeout": 30
        },
        "ui": {
            "theme": "system",  # Can be: "light", "dark", "system"
            "font_size": 12,
            "default_template": "modern"
        },
        "paths": {
            "output_dir": "",
            "last_resume_file": ""
        }
    }
    
    def __init__(self):
        """Initialize settings."""
        self.settings_file = self._get_settings_file_path()
        self.settings = self._load_settings()
    
    def _get_settings_file_path(self) -> Path:
        """Get the path to the settings file."""
        # First try the current directory
        current_dir = Path.cwd() / "resume_rebuilder_settings.json"
        if current_dir.exists():
            return current_dir
        
        # Next try the user's home directory
        home_dir = Path.home() / ".resume_rebuilder" / "settings.json"
        return home_dir
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file or create default."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                logger.info(f"Loaded settings from {self.settings_file}")
                
                # Merge with defaults to ensure all settings exist
                merged_settings = self.DEFAULT_SETTINGS.copy()
                for category, values in settings.items():
                    if category in merged_settings:
                        merged_settings[category].update(values)
                
                return merged_settings
            else:
                return self.DEFAULT_SETTINGS.copy()
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            # Create directory if it doesn't exist
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
                
            logger.info(f"Saved settings to {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get(self, category: str, key: str, default=None):
        """
        Get a setting value.
        
        Args:
            category: Category of the setting (api, ui, paths)
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        if category in self.settings and key in self.settings[category]:
            return self.settings[category][key]
        return default
    
    def set(self, category: str, key: str, value) -> bool:
        """
        Set a setting value.
        
        Args:
            category: Category of the setting (api, ui, paths)
            key: Setting key
            value: New value
            
        Returns:
            True if successful, False otherwise
        """
        if category not in self.settings:
            self.settings[category] = {}
            
        self.settings[category][key] = value
        return self.save_settings()
    
    def update_api_settings(
        self, 
        backend: Optional[str] = None, 
        local_url: Optional[str] = None,
        manageai_url: Optional[str] = None,
        llm_host: Optional[str] = None,
        llm_port: Optional[int] = None,
        llm_model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> bool:
        """
        Update API settings.
        
        Args:
            backend: API backend type
            local_url: URL for the local server
            manageai_url: URL for the ManageAI Resume API
            llm_host: Host for direct LLM Studio connection
            llm_port: Port for direct LLM Studio connection
            llm_model: Model name for direct LLM Studio connection
            api_key: API key for authentication
            timeout: Request timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if backend is not None:
                self.settings["api"]["backend"] = backend
            if local_url is not None:
                self.settings["api"]["local_url"] = local_url
            if manageai_url is not None:
                self.settings["api"]["manageai_url"] = manageai_url
            if llm_host is not None:
                self.settings["api"]["llm_host"] = llm_host
            if llm_port is not None:
                self.settings["api"]["llm_port"] = llm_port
            if llm_model is not None:
                self.settings["api"]["llm_model"] = llm_model
            if api_key is not None:
                self.settings["api"]["api_key"] = api_key
            if timeout is not None:
                self.settings["api"]["timeout"] = timeout
                
            return self.save_settings()
        except Exception as e:
            logger.error(f"Error updating API settings: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        Reset settings to default values.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.settings = self.DEFAULT_SETTINGS.copy()
            return self.save_settings()
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False

# Create a singleton instance
app_settings = Settings()
