#!/usr/bin/env python3
"""
Test script for direct PDF content replacement.

This script demonstrates the new PDF direct manipulation capabilities
by applying them to a resume PDF.
"""

import os
import sys
import argparse
from src.utils.pdf_content_replacer import PDFContentReplacer

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test PDF Content Replacement with Direct Manipulation"
    )
    parser.add_argument(
        "--pdf", 
        required=True,
        help="Path to input PDF resume"
    )
    parser.add_argument(
        "--job", 
        help="Path to job description file"
    )
    parser.add_argument(
        "--output", 
        help="Path for output PDF (default: improved_resume.pdf)"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the test script."""
    args = parse_args()
    
    # Check that the PDF file exists
    if not os.path.exists(args.pdf):
        print(f"Error: PDF file not found: {args.pdf}")
        sys.exit(1)
        
    # Read job description if provided
    job_description = None
    if args.job:
        if not os.path.exists(args.job):
            print(f"Error: Job description file not found: {args.job}")
            sys.exit(1)
        with open(args.job, 'r', encoding='utf-8') as f:
            job_description = f.read()
    
    # Set output path
    output_path = args.output or 'improved_resume.pdf'
    
    print(f"Processing resume: {args.pdf}")
    print(f"Job description: {'Provided' if job_description else 'None'}")
    print(f"Output will be saved to: {output_path}")
    
    # Initialize the replacer with direct PDF manipulation
    replacer = PDFContentReplacer(use_enhanced=True, use_llm=True, use_direct=True)
    
    try:
        # Process the resume
        result_path = replacer.improve_resume(
            args.pdf,
            job_description,
            output_path
        )
        
        print(f"\nSuccess! Resume processed and saved to: {result_path}")
        print("\nContent was replaced using direct PDF manipulation for better format preservation.")
        
    except Exception as e:
        print(f"\nError processing resume: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
