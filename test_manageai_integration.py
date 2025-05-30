#!/usr/bin/env python3
"""
Test script for the ManageAI Resume API integration.
"""

import os
import sys
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the API manager and integration
from src.utils.manageai_api_manager import ManageAIAPIManager
from src.utils.resume_api_integration import ResumeAPIIntegration, ConnectionType

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_manager():
    """Test the ManageAI API Manager."""
    logger.info("Testing ManageAI API Manager...")
    
    # Create the API manager
    manager = ManageAIAPIManager(
        host="localhost",
        port=8080
    )
    
    # Test starting the server
    logger.info("Starting ManageAI Resume API server...")
    if not manager.start_server(wait_for_startup=True, timeout=30, retries=3):
        logger.error("Failed to start ManageAI Resume API server.")
        return False
    
    # Test if the server is running
    for i in range(3):  # Give it a few tries
        if manager.is_server_running():
            logger.info("ManageAI Resume API server is running.")
            break
        else:
            logger.warning(f"ManageAI Resume API server not responding (attempt {i+1}/3), waiting...")
            import time
            time.sleep(5)
    else:
        logger.error("ManageAI Resume API server is not running after start.")
        return False
        
    logger.info("ManageAI Resume API server is running.")
    
    # Test stopping the server
    logger.info("Stopping ManageAI Resume API server...")
    if not manager.stop_server():
        logger.error("Failed to stop ManageAI Resume API server.")
        return False
        
    logger.info("ManageAI Resume API server stopped successfully.")
    return True

def test_api_integration():
    """Test the ManageAI API Integration."""
    logger.info("Testing API Integration...")
    
    # Create the API integration
    api_integration = ResumeAPIIntegration(
        connection_type=ConnectionType.MANAGE_AI,
        manageai_url="http://localhost:8080",
        llm_host="localhost",
        llm_port=1234,
        api_key=os.environ.get("RESUME_API_KEY", "test-api-key-1234")
    )
    
    # Test the connection
    if not api_integration.test_connection():
        logger.warning("Failed to connect to ManageAI Resume API.")
        
        # Try switching to local server
        logger.info("Switching to local server...")
        if not api_integration.switch_connection(ConnectionType.LOCAL_SERVER):
            logger.error("Failed to switch to local server.")
            return False
            
    logger.info(f"Successfully connected using {api_integration.connection_type.value}")
    
    # Test switching between connection types
    logger.info("Testing connection switching...")
    
    # Switch to direct LLM
    logger.info("Switching to direct LLM...")
    direct_result = api_integration.switch_connection(ConnectionType.LLM_DIRECT)
    logger.info(f"Switch to direct LLM {'succeeded' if direct_result else 'failed'}")
    
    # Switch back to ManageAI
    logger.info("Switching back to ManageAI...")
    manageai_result = api_integration.switch_connection(ConnectionType.MANAGE_AI)
    logger.info(f"Switch to ManageAI {'succeeded' if manageai_result else 'failed'}")
    
    return True

def main():
    """Main function."""
    # Test API manager
    if test_api_manager():
        logger.info("API Manager test passed!")
    else:
        logger.error("API Manager test failed!")
        return 1
    
    # Test API integration
    if test_api_integration():
        logger.info("API Integration test passed!")
    else:
        logger.error("API Integration test failed!")
        return 1
    
    logger.info("All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
