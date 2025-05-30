#!/usr/bin/env python3
"""
Test script for the LocalLLMAdapter with improved error handling
"""

import sys
import os
import logging
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from utils.local_llm_adapter import LocalLLMAdapter

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to test the LocalLLMAdapter with error handling."""
    
    # Test with valid port (assuming no LLM Studio is running)
    logger.info("=== Testing connection with non-existent server ===")
    adapter = LocalLLMAdapter(port=5000)
    success = adapter.test_connection()
    if success:
        logger.info("✓ Connection successful! (unexpected)")
    else:
        logger.info("✗ Connection failed (expected behavior)")

    # Test with multiple retries
    logger.info("\n=== Testing automatic retry mechanism ===")
    max_retries = 3
    retry_delay = 2  # seconds
    
    for i in range(max_retries):
        logger.info(f"Attempt {i+1}/{max_retries}...")
        try:
            # Test generate method with error handling
            response = adapter.generate(
                system_prompt="You are a helpful assistant.",
                user_prompt="What are the best practices for resume writing?",
                max_tokens=100
            )
            
            if response:
                logger.info(f"Response received: {response[:30]}...")
                break
            else:
                logger.info("No response received, retrying...")
                if i < max_retries - 1:
                    time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Error during generate call: {e}")
            if i < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    # Test with a port we know is working (localhost:8081)
    logger.info("\n=== Testing connection with our local server ===")
    # Using port 8081 where our server is running with our custom API
    from utils.api_client import APIClient
    api_client = APIClient(base_url="http://localhost:8081/", api_key="test-api-key-1234") 
    success = api_client.test_connection()
    if success:
        logger.info("✓ Connection to local server successful!")
    else:
        logger.info("✗ Connection to local server failed")
    
    # Try to connect to a running LLM Studio instance (if available)
    logger.info("\n=== Testing connection with LLM Studio (if running) ===")
    # LLM Studio typically runs on port 5000 with the /v1/chat/completions endpoint
    llm_adapter = LocalLLMAdapter(
        model_name="qwen-14b",  # or whatever model is loaded in LLM Studio
        host="localhost",
        port=5000,
        api_path="/v1/chat/completions"
    )
    
    # Test connection to LLM Studio
    success = llm_adapter.test_connection()
    if success:
        logger.info("✓ Connection to LLM Studio successful!")
        
        # If connection is successful, try generating a response
        logger.info("Generating response from LLM Studio...")
        response = llm_adapter.generate(
            system_prompt="You are a helpful assistant specialized in resume writing.",
            user_prompt="What are three tips for making a resume stand out?",
            max_tokens=150
        )
        
        if response:
            logger.info(f"LLM Studio response: {response}")
        else:
            logger.info("Failed to get a response from LLM Studio")
    else:
        logger.info("✗ Connection to LLM Studio failed (is it running?)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
