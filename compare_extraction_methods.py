#!/usr/bin/env python3
"""
Comprehensive Test for Resume PDF Text Extraction Methods

This script compares different text extraction methods for resume PDFs, 
focusing particularly on section header detection.
"""

import os
import sys
import argparse
from pprint import pprint
import fitz  # PyMuPDF
import re
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

# Import the various extraction methods
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.utils.pdf_extractor import PDFExtractor
from src.utils.ocr_text_extraction import OCRTextExtractor
from src.utils.simple_section_extractor import SimpleSectionExtractor
from src.utils.ocr_section_extractor import OCRSectionExtractor
from src.utils.ocr_section_extractor_improved import OCRSectionExtractorImproved

def extract_with_pymupdf(pdf_path):
    """Extract text using PyMuPDF."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n\n"
    return text

def test_extraction_methods(pdf_path):
    """Test and compare different extraction methods on a PDF file."""
    print(f"\n{Fore.CYAN}Testing extraction methods on: {pdf_path}{Style.RESET_ALL}")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"{Fore.RED}Error: File not found: {pdf_path}{Style.RESET_ALL}")
        return False
    
    # Initialize extractors
    pdf_extractor = PDFExtractor()
    ocr_extractor = OCRTextExtractor()
    
    # Extract text using different methods
    print(f"\n{Fore.GREEN}1. Extracting text with PyMuPDF (baseline)...{Style.RESET_ALL}")
    pymupdf_text = extract_with_pymupdf(pdf_path)
    
    print(f"\n{Fore.GREEN}2. Extracting text with PDFExtractor (multiple methods)...{Style.RESET_ALL}")
    resume_content = pdf_extractor.extract(pdf_path)
    pdf_extractor_text = resume_content.raw_text
    
    print(f"\n{Fore.GREEN}3. Extracting text with OCR...{Style.RESET_ALL}")
    try:
        ocr_text = ocr_extractor.extract_text(pdf_path)
    except Exception as e:
        print(f"{Fore.RED}OCR extraction failed: {e}{Style.RESET_ALL}")
        ocr_text = "OCR extraction failed"
    
    # Compare section header detection
    section_headers = [
        'SUMMARY', 'PROFILE', 'OBJECTIVE', 
        'EXPERIENCE', 'EMPLOYMENT', 'WORK HISTORY',
        'EDUCATION', 'ACADEMIC', 'QUALIFICATIONS',
        'SKILLS', 'COMPETENCIES', 'EXPERTISE',
        'PROJECTS', 'ACCOMPLISHMENTS', 'ACHIEVEMENTS',
        'CERTIFICATIONS', 'LANGUAGES', 'INTERESTS',
        'REFERENCES', 'VOLUNTEER'
    ]
    
    print(f"\n{Fore.CYAN}=== Section Header Detection Comparison ==={Style.RESET_ALL}")
    
    # Find section headers in each extracted text
    print(f"\n{Fore.YELLOW}Headers detected in PyMuPDF extraction:{Style.RESET_ALL}")
    find_section_headers(pymupdf_text, section_headers)
    
    print(f"\n{Fore.YELLOW}Headers detected in PDFExtractor extraction:{Style.RESET_ALL}")
    find_section_headers(pdf_extractor_text, section_headers)
    
    print(f"\n{Fore.YELLOW}Headers detected in OCR extraction:{Style.RESET_ALL}")
    find_section_headers(ocr_text, section_headers)
    
    # Test section extraction methods
    print(f"\n{Fore.CYAN}=== Section Extraction Comparison ==={Style.RESET_ALL}")
    
    # Initialize section extractors
    simple_extractor = SimpleSectionExtractor()
    ocr_section_extractor = OCRSectionExtractor()
    improved_ocr_extractor = OCRSectionExtractorImproved()
    
    # Extract sections using different methods
    print(f"\n{Fore.GREEN}1. Extracting sections with SimpleSectionExtractor...{Style.RESET_ALL}")
    try:
        simple_sections = simple_extractor.extract_sections(pdf_path)
        print(f"  {Fore.GREEN}Found {len(simple_sections)} sections{Style.RESET_ALL}")
        for key, section in simple_sections.items():
            print(f"  - {Fore.YELLOW}{section['display_name']}{Style.RESET_ALL} ({section['type']})")
    except Exception as e:
        print(f"{Fore.RED}SimpleSectionExtractor failed: {e}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}2. Extracting sections with OCRSectionExtractor...{Style.RESET_ALL}")
    try:
        ocr_sections = ocr_section_extractor.extract_sections(pdf_path)
        print(f"  {Fore.GREEN}Found {len(ocr_sections)} sections{Style.RESET_ALL}")
        for key, section in ocr_sections.items():
            print(f"  - {Fore.YELLOW}{section['display_name']}{Style.RESET_ALL} ({section['type']})")
    except Exception as e:
        print(f"{Fore.RED}OCRSectionExtractor failed: {e}{Style.RESET_ALL}")
        
    print(f"\n{Fore.GREEN}3. Extracting sections with Improved OCRSectionExtractor...{Style.RESET_ALL}")
    try:
        improved_ocr_sections = improved_ocr_extractor.extract_sections(pdf_path)
        print(f"  {Fore.GREEN}Found {len(improved_ocr_sections)} sections{Style.RESET_ALL}")
        for key, section in improved_ocr_sections.items():
            print(f"  - {Fore.YELLOW}{section['display_name']}{Style.RESET_ALL} ({section['type']})")
    except Exception as e:
        print(f"{Fore.RED}Improved OCRSectionExtractor failed: {e}{Style.RESET_ALL}")
    
    return True

def find_section_headers(text, header_patterns):
    """Find all section headers in the text."""
    headers_found = []
    
    for header in header_patterns:
        # Find all occurrences of the header (case insensitive)
        matches = list(re.finditer(r'\b' + re.escape(header) + r'\b', text, re.IGNORECASE))
        
        if matches:
            print(f"  {Fore.GREEN}- Found {len(matches)} occurrence(s) of '{header}'{Style.RESET_ALL}")
            headers_found.append(header)
            
            # Show context for the first occurrence
            if len(matches) > 0:
                match = matches[0]
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].replace('\n', ' | ')
                print(f"    Context: ...{context}...")
    
    if not headers_found:
        print(f"  {Fore.RED}No section headers found{Style.RESET_ALL}")
    
    return headers_found

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test PDF text extraction methods")
    parser.add_argument("pdf_path", nargs="?", default="new_resume.pdf", 
                        help="Path to the PDF file to test (default: new_resume.pdf)")
    args = parser.parse_args()
    
    # Run the test
    test_extraction_methods(args.pdf_path)
