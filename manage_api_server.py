#!/usr/bin/env python3
"""
ManageAI Resume API Server Management Script

This script provides a command-line interface to start, stop, restart, or check
the status of the ManageAI Resume API server.
"""

import os
import sys
import time
import argparse
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the API manager
from src.utils.manageai_api_manager import ManageAIAPIManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Manage the ManageAI Resume API server"
    )
    
    parser.add_argument(
        'action',
        choices=['start', 'stop', 'restart', 'status'],
        help='Action to perform on the server'
    )
    
    parser.add_argument(
        '--host',
        default='localhost',
        help='Host for the server (default: localhost)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port for the server (default: 8080)'
    )
    
    parser.add_argument(
        '--api-path',
        default=None,
        help='Path to the ManageAI resume_api.py file'
    )
    
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    # Create the API manager
    manager = ManageAIAPIManager(
        api_path=args.api_path,
        host=args.host,
        port=args.port
    )
    
    # Perform the requested action
    if args.action == 'start':
        logger.info(f"Starting ManageAI Resume API server on {args.host}:{args.port}...")
        if manager.start_server(wait_for_startup=True, timeout=15, retries=3):
            logger.info("Server started successfully")
            print("Server is running. Press Ctrl+C to exit (server will remain running in the background)")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Exiting... server will continue running")
        else:
            logger.error("Failed to start server")
            return 1
    
    elif args.action == 'stop':
        logger.info("Stopping ManageAI Resume API server...")
        if manager.stop_server():
            logger.info("Server stopped successfully")
        else:
            logger.error("Failed to stop server")
            return 1
    
    elif args.action == 'restart':
        logger.info("Restarting ManageAI Resume API server...")
        if manager.restart_server():
            logger.info("Server restarted successfully")
            print("Server is running. Press Ctrl+C to exit (server will remain running in the background)")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Exiting... server will continue running")
        else:
            logger.error("Failed to restart server")
            return 1
    
    elif args.action == 'status':
        if manager.is_server_running():
            logger.info(f"ManageAI Resume API server is running on {args.host}:{args.port}")
        else:
            logger.info("ManageAI Resume API server is not running")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
