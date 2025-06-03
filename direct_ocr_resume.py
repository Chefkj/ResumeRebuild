#!/usr/bin/env python3
"""
Direct Resume OCR

This script provides a direct path to OCR your resume without dependencies on the
resume_rebuilder API or other complex systems. It focuses on extracting high-quality
text to use for job applications.
"""

import os
import sys
import argparse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def direct_ocr_resume(pdf_path, output_dir="."):
    """
    Process a resume PDF directly using our OCR optimization methods
    without dependencies on external APIs.
    
    Args:
        pdf_path: Path to the resume PDF file
        output_dir: Directory to save the processed text
    
    Returns:
        str: Path to the output text file
    """
    logger.info(f"Processing resume: {pdf_path}")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Try multiple OCR approaches
    output_files = []
    exit_code = 0
    
    # Try the targeted OCR improvement if available
    if os.path.exists("targeted_ocr_improvement.py"):
        logger.info("Running targeted OCR improvement...")
        try:
            import subprocess
            cmd = ["python3", "targeted_ocr_improvement.py", pdf_path, "--dpi", "1500", "--output", output_dir]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Targeted OCR completed successfully")
                # Find the output file
                import glob
                output_files = glob.glob(f"{output_dir}/*_targeted_ocr_*.txt")
            else:
                logger.warning(f"Targeted OCR failed: {result.stderr}")
                exit_code = 1
        except Exception as e:
            logger.error(f"Error running targeted OCR: {e}")
            exit_code = 1
    
    # Try traditional OCR if targeted OCR failed or isn't available
    if not output_files and os.path.exists("traditional_ocr.py"):
        logger.info("Running traditional OCR...")
        try:
            import subprocess
            cmd = ["python3", "traditional_ocr.py", pdf_path, "--dpi", "1200", "--output", output_dir]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Traditional OCR completed successfully")
                # Find the output file
                import glob
                output_files = glob.glob(f"{output_dir}/*_trad_ocr_*.txt")
            else:
                logger.warning(f"Traditional OCR failed: {result.stderr}")
                exit_code = 1
        except Exception as e:
            logger.error(f"Error running traditional OCR: {e}")
            exit_code = 1
    
    # Try pytesseract directly if previous methods failed
    if not output_files:
        logger.info("Falling back to direct pytesseract OCR...")
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_file = os.path.join(output_dir, f"{base_name}_direct_ocr_{timestamp}.txt")
            
            # Convert PDF to images
            logger.info("Converting PDF to images")
            images = convert_from_path(pdf_path, dpi=300)
            
            # Extract text from each page
            all_text = []
            for i, img in enumerate(images):
                logger.info(f"Processing page {i+1}")
                text = pytesseract.image_to_string(img)
                all_text.append(text)
            
            # Save the combined text
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n\n".join(all_text))
                
            logger.info(f"Direct OCR completed successfully")
            output_files = [output_file]
        except Exception as e:
            logger.error(f"Error running direct OCR: {e}")
            import traceback
            traceback.print_exc()
            exit_code = 1
    
    # Create a job-ready version if we have an output file
    if output_files:
        latest_file = sorted(output_files, key=os.path.getmtime)[-1]
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        job_ready_file = os.path.join(output_dir, f"{base_name}_job_ready.txt")
        
        try:
            # Read the OCR text
            with open(latest_file, "r", encoding="utf-8") as f:
                ocr_text = f.read()
            
            # Make simple ATS-friendly improvements
            import re
            # Replace special characters with standard ones
            ats_text = re.sub(r'[•◦⦿⁃◘◙■►▷➢▪◾◽⬤]', '-', ocr_text)
            # Fix problematic words
            ats_text = re.sub(r'[Cc]iplomacy', 'Diplomacy', ats_text)
            ats_text = re.sub(r'[Vv]illereek', 'Millcreek', ats_text)
            
            # Write the job-ready version
            with open(job_ready_file, "w", encoding="utf-8") as f:
                f.write(ats_text)
                
            logger.info(f"Job-ready version created: {job_ready_file}")
            
            # Get word count
            word_count = len(ats_text.split())
            logger.info(f"Word count: {word_count}")
            
            return job_ready_file
        except Exception as e:
            logger.error(f"Error creating job-ready version: {e}")
            return latest_file
    else:
        logger.error("All OCR methods failed, no output file produced")
        return None

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Direct OCR for resume job applications')
    parser.add_argument('pdf_path', help='Path to your resume PDF file')
    parser.add_argument('--output', '-o', default='direct_ocr_output', help='Output directory')
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.pdf_path):
        logger.error(f"File not found: {args.pdf_path}")
        return 1
    
    output_file = direct_ocr_resume(args.pdf_path, args.output)
    
    if output_file and os.path.exists(output_file):
        print(f"\n✅ Resume processing successful!")
        print(f"Your job-ready text is available at: {output_file}")
        
        # Show a sample
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                sample = f.read(500)
            print("\n--- Sample of extracted text (first 500 characters) ---")
            print("="*70)
            print(sample + "..." if len(sample) == 500 else sample)
            print("="*70)
        except:
            pass
        
        return 0
    else:
        logger.error("Resume processing failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
