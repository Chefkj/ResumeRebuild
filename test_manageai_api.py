#!/usr/bin/env python3
"""
Test script for the ManageAI Resume API integration
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from utils.manageai_adapter import ManageAIResumeAdapter

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_manageai_connection(api_url="http://localhost:8080", api_key=None):
    """Test the connection to the ManageAI Resume API"""
    logger.info(f"Testing connection to ManageAI Resume API at {api_url}")
    
    # Initialize the adapter
    adapter = ManageAIResumeAdapter(api_url=api_url, api_key=api_key)
    
    # Test the connection
    if adapter.test_connection():
        logger.info("✓ Connection successful!")
        return True
    else:
        logger.error("✗ Connection failed!")
        return False

def main():
    """Main function to test the ManageAI Resume API integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ManageAI Resume API integration")
    parser.add_argument("--api-url", default="http://localhost:8080", help="ManageAI Resume API URL")
    parser.add_argument("--api-key", help="ManageAI Resume API key")
    
    args = parser.parse_args()
    
    # Test the connection
    if test_manageai_connection(args.api_url, args.api_key):
        logger.info("ManageAI Resume API is available!")
        
        # Define a simple resume for testing
        resume = {
            "contact": {
                "name": "John Test",
                "email": "john.test@example.com"
            },
            "sections": [
                {
                    "name": "EXPERIENCE",
                    "content": "Software Developer at Test Company"
                },
                {
                    "name": "EDUCATION",
                    "content": "BS in Computer Science"
                }
            ]
        }
        
        # Create an instance of the adapter
        adapter = ManageAIResumeAdapter(api_url=args.api_url, api_key=args.api_key)
        
        try:
            # Test analyze_resume endpoint
            logger.info("Testing analyze_resume endpoint...")
            result = adapter.analyze_resume(resume)
            logger.info(f"Analysis successful: {result.keys()}")
            
            # Test analyze_job endpoint
            job_description = "Software Developer position requiring Python skills"
            logger.info("Testing analyze_job endpoint...")
            result = adapter.analyze_job(job_description)
            logger.info(f"Job analysis successful: {result.keys()}")
            
            logger.info("All API tests completed successfully!")
            return 0
        
        except Exception as e:
            logger.error(f"Error testing API endpoints: {e}")
            return 1
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
