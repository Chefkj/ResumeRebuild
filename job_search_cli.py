#!/usr/bin/env python3
"""
Job Search CLI.

Command-line tool for searching for jobs using various job search APIs.
"""

import os
import sys
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).resolve().parent))

from src.utils.env_loader import load_env_vars
from src.utils.job_search_api import JobSearchAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Job Search CLI')
    
    # Required arguments
    parser.add_argument('query', help='Job search query (e.g. "Python Developer")')
    
    # Optional arguments
    parser.add_argument('-l', '--location', help='Job location (e.g. "San Francisco" or "Remote")')
    parser.add_argument('-s', '--sources', help='Comma-separated list of job sources (linkedin,indeed,glassdoor,monster)', default='all')
    parser.add_argument('-n', '--limit', type=int, help='Maximum number of results per source', default=5)
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-f', '--format', choices=['text', 'json'], help='Output format', default='text')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--resume', help='Path to resume file for matching')
    
    return parser.parse_args()

def format_job_results_text(jobs: List[Dict[str, Any]]) -> str:
    """
    Format job search results as text.
    
    Args:
        jobs: List of job postings
        
    Returns:
        Formatted text output
    """
    if not jobs:
        return "No job postings found."
        
    output = []
    for i, job in enumerate(jobs, 1):
        output.append(f"Job #{i} - {job['title']}")
        output.append(f"Company: {job['company']}")
        output.append(f"Location: {job['location']}")
        output.append(f"Source: {job['source']}")
        if 'url' in job:
            output.append(f"URL: {job['url']}")
        if 'description' in job:
            # Truncate description if too long
            desc = job['description']
            if len(desc) > 200:
                desc = desc[:197] + "..."
            output.append(f"Description: {desc}")
        output.append("-" * 50)
        
    return "\n".join(output)

def main():
    """Main function to run the job search CLI."""
    # Parse arguments
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load environment variables
    load_env_vars()
    logger.info("Environment variables loaded")
    
    # Initialize job search client
    job_search_client = JobSearchAPIClient()
    
    # Determine which sources to search
    sources = args.sources.lower().split(',')
    
    # Search for jobs
    logger.info(f"Searching for '{args.query}' in '{args.location or 'any location'}'")
    
    all_jobs = []
    
    if args.sources == 'all':
        all_jobs = job_search_client.search_all_apis(args.query, args.location, args.limit)
    else:
        for source in sources:
            if source == 'linkedin':
                jobs = job_search_client.search_linkedin(args.query, args.location, args.limit)
                all_jobs.extend(jobs)
            elif source == 'indeed':
                jobs = job_search_client.search_indeed(args.query, args.location, args.limit)
                all_jobs.extend(jobs)
            elif source == 'glassdoor':
                jobs = job_search_client.search_glassdoor(args.query, args.location, args.limit)
                all_jobs.extend(jobs)
            elif source == 'monster':
                jobs = job_search_client.search_monster(args.query, args.location, args.limit)
                all_jobs.extend(jobs)
            else:
                logger.warning(f"Unknown job source: {source}")
    
    # Format output
    if args.format == 'json':
        output = json.dumps(all_jobs, indent=2)
    else:
        output = format_job_results_text(all_jobs)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        logger.info(f"Results saved to {args.output}")
    else:
        print(output)
    
    logger.info(f"Found {len(all_jobs)} job postings")

if __name__ == "__main__":
    main()
