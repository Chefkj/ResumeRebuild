#!/usr/bin/env python3
"""
Test script for the Resume Rebuilder API client
"""

import sys
import os
import logging
# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from utils.api_client import APIClient

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to test the API client."""
    # Initialize API client with localhost URL and test API key
    api_client = APIClient(base_url="http://localhost:8081/", api_key="test-api-key-1234")
    
    # Test connection
    logger.info("Testing API connection...")
    if api_client.test_connection():
        logger.info("✓ Connection successful!")
        
        # Test getting templates
        try:
            logger.info("Getting resume templates...")
            templates = api_client.get_resume_templates()
            logger.info(f"Templates retrieved: {templates}")
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
        
        # Test analyze resume endpoint
        try:
            logger.info("Testing resume analysis...")
            mock_resume = {
                "contact": {"name": "John Doe", "email": "john@example.com"},
                "experience": [{"title": "Developer", "company": "Tech Co"}]
            }
            analysis = api_client.analyze_resume(mock_resume)
            logger.info(f"Analysis result: {analysis}")
        except Exception as e:
            logger.error(f"Error analyzing resume: {e}")
            
    else:
        logger.error("✗ Connection failed!")
        return 1
        
    logger.info("All tests completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
