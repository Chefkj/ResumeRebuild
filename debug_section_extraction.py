#!/usr/bin/env python3
"""
Debug script for section extractor

This script helps debug issues with section extraction by showing detailed information
about detected sections and their headers.
"""

import os
import sys
import argparse
import fitz  # PyMuPDF
import re
from pprint import pprint

# Import the tools from the proper paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from src.utils.section_extractor import SectionExtractor
    from src.utils.simple_section_extractor import SimpleSectionExtractor
except ImportError:
    from utils.section_extractor import SectionExtractor
    from utils.simple_section_extractor import SimpleSectionExtractor

def debug_section_extraction(pdf_path):
    """Debug the section extraction on a PDF file."""
    print(f"\nDebugging section extraction on: {pdf_path}")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
    
    # Initialize the section extractor
    section_extractor = SectionExtractor()
    
    # Extract full text for analysis
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    
    # Define section patterns to search for
    section_patterns = [
        (r'(?i)(?:^|\n|\s)(EDUCATION|ACADEMIC|QUALIFICATIONS|DEGREES?)(?:\s|:|\n)', "EDUCATION"),
        (r'(?i)(?:^|\n|\s)(WORK\s+EXPERIENCE|EMPLOYMENT|WORK\s*HISTORY|EXPERIENCE|PROFESSIONAL\s+BACKGROUND)(?:\s|:|\n)', "EXPERIENCE"),
        (r'(?i)(?:^|\n|\s)(SKILLS|TECHNICAL\s+SKILLS|PROFICIENCIES|EXPERTISE|CORE\s+COMPETENCIES)(?:\s|:|\n)', "SKILLS"),
        (r'(?i)(?:^|\n|\s)(PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE|CAREER\s+OBJECTIVE)(?:\s|:|\n)', "SUMMARY"),
        (r'(?i)(?:^|\n|\s)(CERTIFICATIONS?|CERTIFICATES|CREDENTIALS|LICENSES)(?:\s|:|\n)', "CERTIFICATIONS"),
        (r'(?i)(?:^|\n|\s)(PROJECTS|PORTFOLIO|PERSONAL\s+PROJECTS|PROFESSIONAL\s+PROJECTS)(?:\s|:|\n)', "PROJECTS")
    ]
    
    # Find all section matches in the text
    print("\nSearching for section patterns in text:")
    print("="*50)
    
    for pattern, section_name in section_patterns:
        print(f"\nLooking for {section_name} sections using pattern: {pattern}")
        matches = list(re.finditer(pattern, full_text))
        
        if matches:
            print(f"  Found {len(matches)} potential {section_name} sections:")
            for i, match in enumerate(matches):
                # Get the match and surrounding context
                start = max(0, match.start() - 50)
                end = min(len(full_text), match.end() + 50)
                context = full_text[start:end].replace('\n', '\\n')
                
                # Find the complete line containing the match
                line_start = full_text.rfind('\n', 0, match.start()) + 1
                line_end = full_text.find('\n', match.start())
                if line_end == -1:
                    line_end = len(full_text)
                full_line = full_text[line_start:line_end]
                
                print(f"  Match {i+1}:")
                print(f"    Position: {match.start()}")
                try:
                    print(f"    Matched text: '{match.group(1)}'")
                except IndexError:
                    print(f"    Matched text: '{match.group(0)}'")
                print(f"    Full line: '{full_line}'")
                print(f"    Context: '...{context}...'")
                print()
        else:
            print(f"  No {section_name} sections found.")
    
    # Extract sections using the SectionExtractor
    print("\nExtracting sections with SectionExtractor:")
    print("="*50)
    sections = section_extractor.extract_sections(pdf_path)
    
    print(f"\nExtracted {len(sections)} sections:")
    for key, section_data in sections.items():
        section_type = section_data.get('type', 'unknown')
        confidence = section_data.get('confidence', 0.0)
        word_count = len(section_data.get('content', '').split())
        display_name = section_data.get('display_name', key)
        original_header = section_data.get('original_header', '')
        
    # Now test the SimpleSectionExtractor
    print("\nExtracting sections with SimpleSectionExtractor:")
    print("="*50)
    simple_extractor = SimpleSectionExtractor()
    simple_sections = simple_extractor.extract_sections(pdf_path)
    
    print(f"\nExtracted {len(simple_sections)} sections:")
    for key, section_data in simple_sections.items():
        section_type = section_data.get('type', 'unknown')
        confidence = section_data.get('confidence', 0.0)
        word_count = len(section_data.get('content', '').split())
        display_name = section_data.get('display_name', key)
        original_header = section_data.get('original_header', '')
        
        print(f"\nSection: {key}")
        print(f"  Type: {section_type}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Word count: {word_count}")
        if display_name and display_name != key:
            print(f"  Display name: {display_name}")
        if original_header:
            print(f"  Original header: '{original_header}'")
            
        # Print a preview of the content
        content_preview = section_data.get('content', '')[:100].replace('\n', '\\n')
        print(f"  Content preview: {content_preview}...")

def main():
    parser = argparse.ArgumentParser(description="Debug resume section extraction")
    parser.add_argument("pdf_path", nargs="?", default="new_resume.pdf", 
                      help="Path to the PDF resume to analyze")
    args = parser.parse_args()
    
    # Debug the section extractor
    debug_section_extraction(args.pdf_path)

if __name__ == "__main__":
    main()
