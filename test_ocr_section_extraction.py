#!/usr/bin/env python3
"""
Test script for OCR-based section extraction

This script tests the OCR-based section extractor on PDF resumes.
It directly compares the results from regular extraction and OCR-based extraction.
"""

import os
import sys
import argparse
from pprint import pprint

# Import the extractors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.utils.simple_section_extractor import SimpleSectionExtractor
from src.utils.ocr_section_extractor import OCRSectionExtractor

def test_section_extraction(pdf_path):
    """Test both regular and OCR-based section extraction on a PDF file."""
    print(f"\nComparing section extraction methods on: {pdf_path}")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
    
    # Initialize the extractors
    regular_extractor = SimpleSectionExtractor()
    ocr_extractor = OCRSectionExtractor()
    
    # Extract sections using regular method
    print("\nExtracting sections with regular method...")
    regular_sections = regular_extractor.extract_sections(pdf_path)
    
    # Extract sections using OCR-based method
    print("\nExtracting sections with OCR-based method...")
    ocr_sections = ocr_extractor.extract_sections(pdf_path)
    
    # Compare the results
    print("\nComparison of extraction results:")
    print("="*80)
    
    # Print section counts
    print(f"Regular extraction: {len(regular_sections)} sections")
    print(f"OCR-based extraction: {len(ocr_sections)} sections")
    
    # Compare section types found
    regular_types = set(section['type'] for section in regular_sections.values())
    ocr_types = set(section['type'] for section in ocr_sections.values())
    
    print("\nSection types found by regular extraction:")
    print(', '.join(sorted(regular_types)))
    
    print("\nSection types found by OCR-based extraction:")
    print(', '.join(sorted(ocr_types)))
    
    # Show sections from both methods
    print("\nDetailed section comparison:")
    print("-"*80)
    
    print("\nRegular extraction sections:")
    for key, section in regular_sections.items():
        content_preview = section['content'][:100].replace('\n', ' ') + '...'
        print(f"- {section['display_name']} ({section['type']}): {content_preview}")
    
    print("\nOCR-based extraction sections:")
    for key, section in ocr_sections.items():
        content_preview = section['content'][:100].replace('\n', ' ') + '...'
        print(f"- {section['display_name']} ({section['type']}): {content_preview}")
    
    return True

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test OCR-based section extraction")
    parser.add_argument("pdf_path", nargs="?", default="new_resume.pdf", 
                        help="Path to the PDF file to test (default: new_resume.pdf)")
    args = parser.parse_args()
    
    # Run the test
    test_section_extraction(args.pdf_path)
