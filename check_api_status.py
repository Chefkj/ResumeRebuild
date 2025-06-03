#!/usr/bin/env python3
"""
API Key Status Checker.

This tool checks the status and connectivity of the configured API keys.
"""

import os
import sys
import logging
from pathlib import Path
from tabulate import tabulate

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).resolve().parent))

from src.utils.env_loader import load_env_vars, get_api_key
from src.utils.settings import Settings

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_api_key(key_name, key_value):
    """
    Check if an API key exists and is not a placeholder.
    
    Args:
        key_name: Name of the API key
        key_value: Value of the API key
        
    Returns:
        Tuple of (status, message) where status is a boolean
    """
    if not key_value:
        return False, "Not configured"
    elif key_value.startswith("your_") or "api_key_here" in key_value:
        return False, "Placeholder value"
    else:
        return True, "Configured"

def main():
    """Main function to check API key status."""
    # Load environment variables
    env_vars = load_env_vars()
    logger.info("Environment variables loaded")
    
    # Load settings
    settings = Settings()
    
    # Define the API keys to check
    api_keys = [
        # Job search APIs
        ("LinkedIn API", get_api_key("LINKEDIN_API_KEY")),
        ("Indeed API", get_api_key("INDEED_API_KEY")),
        ("Glassdoor API", get_api_key("GLASSDOOR_API_KEY")),
        ("Monster API", get_api_key("MONSTER_API_KEY")),
        
        # ATS APIs
        ("Lever API", get_api_key("LEVER_API_KEY")),
        ("Greenhouse API", get_api_key("GREENHOUSE_API_KEY")),
        ("Workday API", get_api_key("WORKDAY_API_KEY")),
        
        # Resume API
        ("ManageAI Resume API", get_api_key("RESUME_API_KEY")),
    ]
    
    # Check each API key
    results = []
    for key_name, key_value in api_keys:
        status, message = check_api_key(key_name, key_value)
        results.append([key_name, "✅" if status else "❌", message])
    
    # Print results as a table
    print("\nAPI Key Status:")
    print(tabulate(results, headers=["API", "Status", "Message"], tablefmt="grid"))
    
    # Check if ManageAI server is running
    print("\nServer Status:")
    resume_api_url = settings.settings.get("api", {}).get("manageai_url", "http://localhost:8080")
    print(f"ManageAI Resume API URL: {resume_api_url}")
    
    # Check LLM Studio settings
    print("\nLLM Studio Configuration:")
    llm_host = settings.settings.get("api", {}).get("llm_host", "localhost")
    llm_port = settings.settings.get("api", {}).get("llm_port", 5000)
    llm_model = settings.settings.get("api", {}).get("llm_model", "qwen-14b")
    print(f"Host: {llm_host}")
    print(f"Port: {llm_port}")
    print(f"Model: {llm_model}")
    
    # Print environment file locations
    print("\nEnvironment File Locations:")
    root_env = Path("/Users/kj/ResumeRebuild/.env")
    src_env = Path("/Users/kj/ResumeRebuild/src/.env")
    print(f"Root .env file: {root_env} ({'Exists' if root_env.exists() else 'Missing'})")
    print(f"Src .env file: {src_env} ({'Exists' if src_env.exists() else 'Missing'})")
    
    # Provide instructions for configuring missing keys
    print("\nTo configure missing API keys:")
    print("1. Edit the .env file in the project root or src directory")
    print("2. Add the required API keys in the format KEY=value")
    print("3. Restart the application to load the new keys")
    print("\nExample:")
    print("LINKEDIN_API_KEY=your_actual_api_key_here")

if __name__ == "__main__":
    main()
