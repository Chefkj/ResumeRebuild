#!/usr/bin/env python3
"""
Test script for enhanced OCR text extraction

This script tests the enhanced OCR text extraction capabilities with more aggressive
preprocessing and multiple OCR approaches.
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

def test_enhanced_ocr(pdf_path, output_folder=".", dpi=1400):
    """
    Test the enhanced OCR extraction on a PDF file with aggressive settings.
    
    Args:
        pdf_path: Path to the PDF file to extract text from
        output_folder: Folder to save output files to
        dpi: DPI value for PDF to image conversion
    """
    print(f"\n--- Testing ENHANCED OCR extraction on: {pdf_path} ---\n")
    print(f"Using DPI: {dpi}, with aggressive preprocessing and multi-scale extraction")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
    
    # Initialize the raw OCR text extractor with enhanced settings
    ocr_extractor = RawOCRTextExtractor(
        dpi=dpi,
        aggressive_mode=True,
        try_multiple_scales=True
    )
    
    # Extract text using OCR
    try:
        # Start timer
        start_time = datetime.now()
        
        print("Extracting OCR text with enhanced settings (this may take a while)...")
        ocr_text = ocr_extractor.extract_raw_text(pdf_path, ocr_mode="all")
        
        # Create a timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate output filenames
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        raw_output_file = os.path.join(output_folder, f"{base_filename}_enhanced_ocr_{timestamp}.txt")
        
        # Save raw OCR text to file
        with open(raw_output_file, 'w', encoding='utf-8') as f:
            f.write(ocr_text)
        
        # Display processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"Processing completed in {processing_time:.2f} seconds")
        
        # Display the results and file locations
        print(f"\nEnhanced OCR text saved to: {raw_output_file}")
        
        print("\n--- Enhanced OCR Text Sample (first 1000 characters) ---")
        print("="*80)
        print(ocr_text[:1000] + "..." if len(ocr_text) > 1000 else ocr_text)
        print("="*80)
        
        # Text analysis
        word_count = len(ocr_text.split())
        print(f"Total words: {word_count}")
        
        return True
        
    except Exception as e:
        print(f"Error extracting text: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Test enhanced OCR text extraction on a PDF file.')
    parser.add_argument('pdf_path', nargs='?', default='improved_resume.pdf',
                        help='Path to the PDF file to extract text from')
    parser.add_argument('--output', '-o', help='Output folder for extracted text files', default='.')
    parser.add_argument('--dpi', '-d', type=int, help='DPI value for PDF to image conversion', default=1400)
    
    args = parser.parse_args()
    
    test_enhanced_ocr(args.pdf_path, args.output, args.dpi)

if __name__ == '__main__':
    main()
