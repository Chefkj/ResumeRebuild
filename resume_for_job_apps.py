#!/usr/bin/env python3
"""
Resume OCR for Job Applications

This script processes your resume PDF using our optimized OCR pipeline
and outputs a clean text version that can be used for job applications.
It uses the targeted OCR improvement techniques we developed to fix
common recognition issues.
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime

from targeted_ocr_improvement import TargetedOCRImprover

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_resume_for_job_application(resume_pdf_path, output_dir="."):
    """
    Process a resume using our optimized OCR pipeline for job applications.
    
    Args:
        resume_pdf_path: Path to the resume PDF file
        output_dir: Directory to save the processed text
        
    Returns:
        str: Path to the output text file
    """
    start_time = time.time()
    print(f"\n===== RESUME OCR FOR JOB APPLICATIONS =====")
    print(f"Processing resume: {resume_pdf_path}")
    
    # Define the resume-specific problem words we need to correct
    problem_words = {
        # Resume-specific corrections
        "ciplomacy": "diplomacy",
        "Ciplomacy": "Diplomacy", 
        "villereek": "millcreek",
        "Villereek": "Millcreek",
        "villereek,": "millcreek,", 
        
        # Common OCR errors in resumes
        "cornpany": "company",
        "Cornpany": "Company", 
        "rnanagement": "management", 
        "Rnanagement": "Management",
        "tearn": "team",
        "Tearn": "Team",
        "horne": "home",
        "Horne": "Home",
        "tirne": "time",
        "Tirne": "Time",
        "developrnent": "development",
        "Developrnent": "Development"
    }
    
    # Use the targeted OCR improver with our optimized settings
    improver = TargetedOCRImprover(
        dpi=1500,  # High quality for best results
        known_problematic_words=problem_words
    )
    
    # Process the resume
    print("\nExtracting text with optimized OCR (this may take a few minutes)...\n")
    resume_text = improver.process_pdf(resume_pdf_path)
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(resume_pdf_path))[0]
    
    # Make sure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"{base_name}_job_app_{timestamp}.txt")
    
    # Save the processed text
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(resume_text)
    
    # Calculate processing time
    elapsed_time = time.time() - start_time
    print(f"\nProcessing completed in {elapsed_time:.1f} seconds")
    print(f"Output saved to: {output_file}")
    print(f"Word count: {len(resume_text.split())}")
    
    # Show a sample of the processed text
    print("\n--- Resume Text Sample (first 500 characters) ---")
    print("="*70)
    print(resume_text[:500] + "..." if len(resume_text) > 500 else resume_text)
    print("="*70)
    
    print("\n✅ Your resume is ready for job applications!")
    print("   Use this text when filling out online applications.")
    
    return output_file

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Process your resume for job applications")
    parser.add_argument("resume_pdf", help="Path to your resume PDF file")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    
    args = parser.parse_args()
    
    # Validate PDF path
    if not os.path.exists(args.resume_pdf):
        print(f"Error: Resume PDF not found at {args.resume_pdf}")
        return 1
    
    try:
        process_resume_for_job_application(args.resume_pdf, args.output)
        return 0
    except Exception as e:
        logger.error(f"Error processing resume: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
