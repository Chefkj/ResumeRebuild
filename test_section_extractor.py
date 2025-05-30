#!/usr/bin/env python3
"""
Test for the SectionExtractor class

This script tests the improved section detection capabilities of our SectionExtractor class.
"""

import os
import sys
import argparse
from pprint import pprint

# Import the tools from the proper paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from src.utils.pdf_content_replacer import PDFContentReplacer
    from src.utils.pdf_extractor import PDFExtractor
    from src.utils.section_extractor import SectionExtractor
except ImportError:
    from utils.pdf_content_replacer import PDFContentReplacer
    from utils.pdf_extractor import PDFExtractor
    from utils.section_extractor import SectionExtractor

def test_section_extractor(pdf_path):
    """Test the section extractor on a specific PDF file."""
    print(f"\nTesting section extraction on: {pdf_path}")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
    
    # Initialize the section extractor
    section_extractor = SectionExtractor()
    
    # Extract sections
    print("\n" + "="*50)
    print("USING SectionExtractor")
    print("="*50)
    
    try:
        sections = section_extractor.extract_sections(pdf_path)
        print(f"\nExtracted {len(sections)} sections:")
        
        for section_name, section_data in sections.items():
            section_type = section_data.get('type', 'unknown')
            confidence = section_data.get('confidence', 0.0)
            word_count = len(section_data.get('content', '').split())
            display_name = section_data.get('display_name', section_name)
            original_header = section_data.get('original_header', '')
            
            print(f"  • {section_name} ({section_type}) - {word_count} words, confidence: {confidence:.2f}")
            if display_name and display_name != section_name:
                print(f"    Display name: {display_name}")
            if original_header and original_header != section_name and original_header != display_name:
                print(f"    Original header: {original_header}")
            
            # Print a small preview of the content
            content_preview = section_data.get('content', '')[:50].replace('\n', ' ')
            if content_preview:
                print(f"    Preview: {content_preview}...")
    except Exception as e:
        print(f"Error using SectionExtractor: {e}")
    
    # Compare with PDFContentReplacer results
    print("\n" + "="*50)
    print("USING PDFContentReplacer")
    print("="*50)
    
    try:
        # Initialize the content replacer with all features enabled
        replacer = PDFContentReplacer(use_enhanced=True, use_llm=False, use_ocr=False, use_direct=True)
        
        # Analyze the PDF structure
        structure = replacer.analyze_structure(pdf_path)
        
        # Print the detected sections
        print(f"\nDetected {len(structure.get('sections', {}))} sections:")
        for section_name, section_data in structure.get('sections', {}).items():
            section_type = section_data.get('type', 'unknown')
            confidence = section_data.get('confidence', 0.0)
            word_count = len(section_data.get('content', '').split())
            display_name = section_data.get('display_name', section_name)
            original_header = section_data.get('original_header', '')
            
            print(f"  • {section_name} ({section_type}) - {word_count} words, confidence: {confidence:.2f}")
            if display_name and display_name != section_name:
                print(f"    Display name: {display_name}")
            if original_header and original_header != section_name and original_header != display_name:
                print(f"    Original header: {original_header}")
            
            # Print a small preview of the content
            content_preview = section_data.get('content', '')[:50].replace('\n', ' ')
            if content_preview:
                print(f"    Preview: {content_preview}...")
    except Exception as e:
        print(f"Error using PDFContentReplacer: {e}")

def main():
    parser = argparse.ArgumentParser(description="Test resume section extraction")
    parser.add_argument("pdf_path", nargs="?", default="new_resume.pdf", 
                      help="Path to the PDF resume to analyze")
    args = parser.parse_args()
    
    # Test the section extractor
    test_section_extractor(args.pdf_path)

if __name__ == "__main__":
    main()
