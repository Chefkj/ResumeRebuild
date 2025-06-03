#!/usr/bin/env python3
"""
Test script for Tesseract OCR PDF text extraction

This script tests the OCR-based extraction of text from PDF resumes,
focusing particularly on correct section header detection and separation.
"""

import os
import sys
import argparse
from pprint import pprint

# Import the PDFExtractor class
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.utils.pdf_extractor import PDFExtractor

def test_ocr_extraction(pdf_path):
    """Test the OCR-based extraction on a PDF file."""
    print(f"\nTesting OCR extraction on: {pdf_path}")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
    
    # Initialize the PDF extractor
    pdf_extractor = PDFExtractor()
    
    # Extract text using OCR
    try:
        ocr_text = pdf_extractor._extract_with_tesseract_ocr(pdf_path)
        
        # Display the results
        print("\nOCR Extraction Results:")
        print("="*80)
        print(ocr_text[:2000] + "..." if len(ocr_text) > 2000 else ocr_text)
        print("="*80)
        
        # Check for section headers
        print("\nDetected Section Headers:")
        print("-"*50)
        
        # Look for common section headers in the extracted text
        section_headers = [
            "EDUCATION", "EXPERIENCE", "SKILLS", "SUMMARY", "PROFILE",
            "PROJECTS", "CERTIFICATIONS", "AWARDS", "PUBLICATIONS",
            "VOLUNTEER", "LANGUAGES", "INTERESTS", "REFERENCES"
        ]
        
        for header in section_headers:
            import re
            # Find all occurrences of the header (case insensitive)
            matches = list(re.finditer(r'\b' + re.escape(header) + r'\b', ocr_text, re.IGNORECASE))
            
            if matches:
                print(f"Found {len(matches)} occurrences of '{header}':")
                
                for i, match in enumerate(matches[:3]):  # Show only first 3 matches
                    # Get surrounding context
                    start = max(0, match.start() - 50)
                    end = min(len(ocr_text), match.end() + 50)
                    context = ocr_text[start:end].replace('\n', ' | ')
                    
                    print(f"  {i+1}: ...{context}...")
                    
                if len(matches) > 3:
                    print(f"  ... and {len(matches) - 3} more occurrences")
        
        # Extract sections using the PDFExtractor
        print("\nExtracting full resume content with OCR:")
        print("="*50)
        resume_content = pdf_extractor.extract(pdf_path)
        
        print(f"Extracted {len(resume_content.sections)} sections:")
        for i, section in enumerate(resume_content.sections):
            print(f"\nSection {i+1}: {section.title}")
            print("-"*30)
            
            # Print summary of section content (first 200 chars)
            content_preview = section.content[:200].replace('\n', ' | ')
            print(f"{content_preview}...")
            
        return True
    
    except Exception as e:
        print(f"Error during OCR extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test OCR-based PDF text extraction")
    parser.add_argument("pdf_path", nargs="?", default="new_resume.pdf", 
                        help="Path to the PDF file to test (default: new_resume.pdf)")
    args = parser.parse_args()
    
    # Run the test
    test_ocr_extraction(args.pdf_path)
