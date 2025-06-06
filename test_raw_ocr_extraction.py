#!/usr/bin/env python3
"""
Test script for raw OCR text extraction

This script tests only the raw OCR text extraction from PDF resumes,
showing both the original text and the text after sequential ordering is applied.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the OCRTextExtractor class directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.utils.ocr_text_extraction import OCRTextExtractor
from src.utils.sequential_text_ordering import apply_sequential_ordering

def test_raw_ocr_extraction(pdf_path, output_folder="."):
    """
    Test the raw OCR text extraction on a PDF file,
    showing both the original OCR text and the text after sequential ordering.
    """
    print(f"\n--- Testing raw OCR extraction on: {pdf_path} ---\n")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
    
    # Initialize the OCR text extractor
    ocr_extractor = OCRTextExtractor()
    
    # Extract text using OCR
    try:
        # Start timer
        start_time = datetime.now()
        
        print("Extracting raw OCR text (this may take a while)...")
        ocr_text = ocr_extractor.extract_text(pdf_path)
        
        # Create a timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate output filenames
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        raw_output_file = os.path.join(output_folder, f"{base_filename}_raw_ocr_{timestamp}.txt")
        
        # Save raw OCR text to file
        with open(raw_output_file, 'w', encoding='utf-8') as f:
            f.write(ocr_text)
        
        # Display processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"Processing completed in {processing_time:.2f} seconds")
        
        # Display the results and file locations
        print(f"\nRaw OCR text saved to: {raw_output_file}")
        
        print("\n--- Raw OCR Text Sample (first 1000 characters) ---")
        print("="*80)
        print(ocr_text[:1000] + "..." if len(ocr_text) > 1000 else ocr_text)
        print("="*80)
        
        # Show counts for common section headers
        section_headers = [
            "EDUCATION", "EXPERIENCE", "SKILLS", "SUMMARY", "PROFILE",
            "PROJECTS", "CERTIFICATIONS", "AWARDS", "WORK", "HISTORY"
        ]
        
        print("\nSection header detection:")
        print("-"*50)
        for header in section_headers:
            import re
            matches = list(re.finditer(r'\b' + re.escape(header) + r'\b', ocr_text, re.IGNORECASE))
            if matches:
                print(f"Found {len(matches)} occurrences of '{header}'")
                
        # Check for potential OCR issues
        problem_patterns = {
            "MergedWords": r'([a-z][A-Z][a-z]+)',
            "MissingSpaces": r'([a-zA-Z])(\d{4})([a-zA-Z])',
            "JoinedSections": r'([a-z])([A-Z]{3,})'
        }
        
        print("\nPotential OCR issues detected:")
        print("-"*50)
        for issue, pattern in problem_patterns.items():
            matches = re.findall(pattern, ocr_text)
            if matches:
                print(f"{issue}: {len(matches)} occurrences found")
                # Show a few examples
                sample = matches[:3]
                print(f"Examples: {', '.join(str(m) for m in sample)}")
        
        return True
    
    except Exception as e:
        print(f"Error during OCR extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test raw OCR text extraction")
    parser.add_argument("pdf_path", nargs="?", default="improved_resume.pdf", 
                        help="Path to the PDF file to test (default: improved_resume.pdf)")
    parser.add_argument("--output", "-o", default=".", 
                        help="Output folder for extracted text files (default: current directory)")
    args = parser.parse_args()
    
    # Run the test
    test_raw_ocr_extraction(args.pdf_path, args.output)
