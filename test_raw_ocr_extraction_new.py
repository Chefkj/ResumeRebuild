#!/usr/bin/env python3
"""
Test script for raw OCR text extraction

This script tests only the raw OCR text extraction from PDF resumes without any header processing.
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

# Import the raw OCR extractor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.utils.raw_ocr_extractor import RawOCRTextExtractor

def test_raw_ocr_extraction(pdf_path, output_folder=".", dpi=1400, ocr_mode="all", aggressive=True, multi_scale=True):
    """
    Test the raw OCR text extraction on a PDF file without any header processing.
    
    Args:
        pdf_path: Path to the PDF file to extract text from
        output_folder: Folder to save output files to
        dpi: DPI value for PDF to image conversion
        ocr_mode: OCR mode to use ("psm3", "psm4", or "all" for both)
        aggressive: Whether to use aggressive image enhancement
        multi_scale: Whether to try multiple scale factors
    """
    print(f"\n--- Testing raw OCR extraction on: {pdf_path} ---\n")
    print(f"Using DPI: {dpi}, OCR Mode: {ocr_mode}, Aggressive: {aggressive}, Multi-scale: {multi_scale}")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
    
    # Initialize the raw OCR text extractor with specified parameters
    ocr_extractor = RawOCRTextExtractor(
        dpi=dpi,
        aggressive_mode=aggressive,
        try_multiple_scales=multi_scale
    )
    
    # Extract text using OCR
    try:
        # Start timer
        start_time = datetime.now()
        
        print("Extracting raw OCR text (this may take a while)...")
        ocr_text = ocr_extractor.extract_raw_text(pdf_path, ocr_mode=ocr_mode)
        
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
        
        # Raw text analysis
        print("\nRaw text analysis (informational only - not altering text):")
        print("-"*50)
        
        # Count words
        word_count = len(ocr_text.split())
        print(f"Total words: {word_count}")
        
        # Count capitalized words
        capitalized_words = len([w for w in ocr_text.split() if w and len(w) > 0 and w[0].isupper()])
        print(f"Capitalized words: {capitalized_words}")
        
        # Show count of all-uppercase "words" which might be headers but we're not processing them
        uppercase_words = [w for w in ocr_text.split() if w.isupper() and len(w) > 2]
        print(f"All-uppercase words (potential headers): {len(uppercase_words)}")
        if uppercase_words:
            print(f"Examples: {', '.join(uppercase_words[:5])}")
                
        # Check for potential OCR issues - just informational
        problem_patterns = {
            "MergedWords": r'([a-z][A-Z][a-z]+)',
            "MissingSpaces": r'([a-zA-Z])(\d{4})([a-zA-Z])',
            "JoinedSections": r'([a-z])([A-Z]{3,})'
        }
        
        print("\nPotential OCR issues detected:")
        print("-"*50)
        import re
        for issue, pattern in problem_patterns.items():
            matches = re.findall(pattern, ocr_text)
            if matches:
                print(f"{issue}: {len(matches)} occurrences found")
                # Show a few examples
                sample = matches[:3]
                print(f"Examples: {', '.join(str(m) for m in sample)}")
                
        return True
        
    except Exception as e:
        print(f"Error extracting text: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Test raw OCR text extraction on a PDF file.')
    parser.add_argument('pdf_path', help='Path to the PDF file to extract text from')
    parser.add_argument('--output', '-o', help='Output folder for extracted text files', default='.')
    parser.add_argument('--dpi', '-d', type=int, help='DPI value for PDF to image conversion', default=1400)
    parser.add_argument('--mode', '-m', choices=['psm3', 'psm4', 'all'], 
                        help='OCR mode to use (psm3, psm4, or all)', default='all')
    parser.add_argument('--aggressive', '-a', action='store_true', default=True,
                        help='Use aggressive image enhancement techniques')
    parser.add_argument('--no-aggressive', action='store_false', dest='aggressive',
                        help='Disable aggressive image enhancement')
    parser.add_argument('--multi-scale', '-s', action='store_true', default=True,
                        help='Try multiple scale factors for OCR')
    parser.add_argument('--no-multi-scale', action='store_false', dest='multi_scale',
                        help='Disable multi-scale OCR')
    
    args = parser.parse_args()
    
    test_raw_ocr_extraction(
        args.pdf_path, 
        args.output, 
        args.dpi, 
        args.mode, 
        args.aggressive,
        args.multi_scale
    )

if __name__ == '__main__':
    main()
