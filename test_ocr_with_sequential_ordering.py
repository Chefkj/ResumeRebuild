#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test for Improved OCR Text Extraction with Sequential Ordering on Real Resume

This script tests the improved OCR text extraction on a real resume PDF.
It demonstrates the complete OCR pipeline with sequential text ordering.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from src.utils.ocr_text_extraction import OCRTextExtractor

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run the test on a real resume PDF."""
    parser = argparse.ArgumentParser(description='Test OCR extraction on a real resume PDF.')
    parser.add_argument('pdf_path', help='Path to PDF resume file')
    parser.add_argument('--output', '-o', help='Output text file path (default: output.txt)')
    args = parser.parse_args()

    if not args.output:
        args.output = 'output.txt'

    pdf_path = args.pdf_path
    output_path = args.output

    # Check if PDF file exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file {pdf_path} not found!")
        return 1

    # Create an instance of OCR Text Extractor
    extractor = OCRTextExtractor()

    try:
        # Extract text from the PDF using our improved OCR extraction
        print(f"Extracting text from {pdf_path}...")
        extracted_text = extractor.extract_text(pdf_path)

        # Write the extracted text to output file
        with open(output_path, 'w') as f:
            f.write(extracted_text)

        # Display some statistics
        section_count = sum(1 for header in extractor.section_headers 
                           if header in extracted_text.upper())
        lines_count = len(extracted_text.split('\n'))

        print("\n===== EXTRACTION COMPLETED SUCCESSFULLY =====")
        print(f"Text written to: {output_path}")
        print(f"Total characters: {len(extracted_text)}")
        print(f"Total lines: {lines_count}")
        print(f"Detected sections: {section_count}")
        print("\nFirst 500 characters of extracted text:")
        print("----------------------------------------")
        print(extracted_text[:500] + "...")

    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
