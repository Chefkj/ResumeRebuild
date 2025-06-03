#!/usr/bin/env python3
"""
Test script for improved OCR-based section extraction

This script tests the improved OCR-based section extractor on PDF resumes.
It compares the results from regular OCR extraction and the improved OCR extraction
to show how the new implementation fixes issues with the "RESUME" header and job title handling.
"""

import os
import sys
import argparse
from pprint import pprint
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

# Import the extractors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.utils.simple_section_extractor import SimpleSectionExtractor
from src.utils.ocr_section_extractor import OCRSectionExtractor
from src.utils.ocr_section_extractor_improved import OCRSectionExtractorImproved

def test_improved_extraction(pdf_path):
    """Test both OCR-based extraction methods on a PDF file."""
    print(f"\n{Fore.CYAN}Comparing OCR section extraction methods on: {pdf_path}{Style.RESET_ALL}")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"{Fore.RED}Error: File not found: {pdf_path}{Style.RESET_ALL}")
        return False
    
    # Initialize the extractors
    original_ocr_extractor = OCRSectionExtractor()
    improved_ocr_extractor = OCRSectionExtractorImproved()
    
    print(f"\n{Fore.GREEN}1. Extracting sections with original OCR-based method...{Style.RESET_ALL}")
    original_ocr_sections = original_ocr_extractor.extract_sections(pdf_path)
    
    print(f"\n{Fore.GREEN}2. Extracting sections with improved OCR-based method...{Style.RESET_ALL}")
    improved_ocr_sections = improved_ocr_extractor.extract_sections(pdf_path)
    
    # Compare the results
    print(f"\n{Fore.CYAN}=== Comparison of extraction results ==={Style.RESET_ALL}")
    print("="*80)
    
    # Print section counts
    print(f"{Fore.YELLOW}Original OCR extraction: {len(original_ocr_sections)} sections{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Improved OCR extraction: {len(improved_ocr_sections)} sections{Style.RESET_ALL}")
    
    # Compare section types found
    original_types = set(section['type'] for section in original_ocr_sections.values())
    improved_types = set(section['type'] for section in improved_ocr_sections.values())
    
    print(f"\n{Fore.YELLOW}Section types found by original OCR extraction:{Style.RESET_ALL}")
    print(', '.join(sorted(original_types)))
    
    print(f"\n{Fore.YELLOW}Section types found by improved OCR extraction:{Style.RESET_ALL}")
    print(', '.join(sorted(improved_types)))
    
    # Show sections from both methods
    print(f"\n{Fore.CYAN}Detailed section comparison:{Style.RESET_ALL}")
    print("-"*80)
    
    print(f"\n{Fore.YELLOW}Original OCR extraction sections:{Style.RESET_ALL}")
    for key, section in original_ocr_sections.items():
        content_preview = section['content'][:100].replace('\n', ' ') + '...'
        print(f"  - {Fore.GREEN}{section['display_name']}{Style.RESET_ALL} ({section['type']}): {content_preview}")
    
    print(f"\n{Fore.YELLOW}Improved OCR extraction sections:{Style.RESET_ALL}")
    for key, section in improved_ocr_sections.items():
        content_preview = section['content'][:100].replace('\n', ' ') + '...'
        print(f"  - {Fore.GREEN}{section['display_name']}{Style.RESET_ALL} ({section['type']}): {content_preview}")
    
    # Check for specific improvements
    print(f"\n{Fore.CYAN}=== Specific Improvements ==={Style.RESET_ALL}")
    
    # Check if "RESUME" is no longer a section
    resume_section_original = any(section['display_name'] == 'RESUME' for section in original_ocr_sections.values())
    resume_section_improved = any(section['display_name'] == 'RESUME' for section in improved_ocr_sections.values())
    
    if resume_section_original and not resume_section_improved:
        print(f"{Fore.GREEN}✓ Fixed: 'RESUME' is no longer treated as a separate section{Style.RESET_ALL}")
    elif not resume_section_original and not resume_section_improved:
        print(f"{Fore.YELLOW}⚠ 'RESUME' was not a section in either extraction{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ 'RESUME' is still being treated as a section{Style.RESET_ALL}")
    
    # Check for improvements in handling job positions in experience sections
    exp_section_original = None
    exp_section_improved = None
    
    for section in original_ocr_sections.values():
        if section['type'] == 'experience':
            exp_section_original = section
            break
            
    for section in improved_ocr_sections.values():
        if section['type'] == 'experience':
            exp_section_improved = section
            break
    
    if exp_section_original and exp_section_improved:
        # Check for merged text like "UtahActed" and if it's properly handled
        merged_text_patterns = ["UtahActed", "UtahBene", r'([A-Z][a-z]+)([A-Z][a-z]+ed)']
        
        # Function to check if any merged text patterns are found in content
        def contains_merged_text(content, patterns):
            import re
            for pattern in patterns:
                if isinstance(pattern, str) and pattern in content:
                    return True, pattern
                elif isinstance(pattern, str) == False:  # It's a regex
                    match = re.search(pattern, content)
                    if match:
                        return True, match.group(0)
            return False, None
        
        # Check both extraction methods for merged text
        has_merged_original, merged_text_original = contains_merged_text(exp_section_original['content'] if exp_section_original else "", merged_text_patterns)
        has_merged_improved, merged_text_improved = contains_merged_text(exp_section_improved['content'] if exp_section_improved else "", merged_text_patterns)
        
        # Find separated text that should now be in the improved version
        # For example, looking for "Utah\nActed" instead of "UtahActed"
        def contains_separated_text(content, merged_pattern):
            import re
            if not isinstance(merged_pattern, str):
                return False
            
            parts = re.findall(r'[A-Z][a-z]+', merged_pattern)
            if len(parts) >= 2:
                separated_pattern = f"{parts[0]}[\\s\\n]+{parts[1]}"
                match = re.search(separated_pattern, content)
                return bool(match)
            return False
        
        has_separated_improved = False
        if merged_text_original:
            has_separated_improved = contains_separated_text(exp_section_improved['content'] if exp_section_improved else "", merged_text_original)
        
        # Report findings
        if has_merged_original and not has_merged_improved and has_separated_improved:
            print(f"{Fore.GREEN}✓ Fixed: Merged text '{merged_text_original}' has been properly separated in the Experience section{Style.RESET_ALL}")
        elif has_merged_original and has_merged_improved:
            print(f"{Fore.RED}✗ Merged text '{merged_text_improved}' is still present in the improved extraction{Style.RESET_ALL}")
        elif not has_merged_original:
            print(f"{Fore.YELLOW}⚠ No merged text was found in the original extraction to compare with{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Unable to determine if merged text issue was fixed{Style.RESET_ALL}")
    
    # Check overall number of sections (should be fewer in improved version as job titles are grouped properly)
    if len(improved_ocr_sections) < len(original_ocr_sections):
        print(f"{Fore.GREEN}✓ Improved: Reduced number of sections from {len(original_ocr_sections)} to {len(improved_ocr_sections)}{Style.RESET_ALL}")
    elif len(improved_ocr_sections) == len(original_ocr_sections):
        print(f"{Fore.YELLOW}⚠ Same number of sections in both extractions: {len(original_ocr_sections)}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ Number of sections increased from {len(original_ocr_sections)} to {len(improved_ocr_sections)}{Style.RESET_ALL}")
    
    return True

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test improved OCR-based section extraction")
    parser.add_argument("pdf_path", nargs="?", default="new_resume.pdf", 
                        help="Path to the PDF file to test (default: new_resume.pdf)")
    args = parser.parse_args()
    
    # Run the test
    test_improved_extraction(args.pdf_path)
