#!/usr/bin/env python3
"""
Test script for the simplified section extractor

This script demonstrates our minimal probabilistic approach to resume section extraction.
"""

import os
import sys
import argparse
from pprint import pprint

# Import the tools from the proper paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from src.utils.simple_section_extractor import SimpleSectionExtractor
except ImportError:
    from utils.simple_section_extractor import SimpleSectionExtractor

def test_simple_extractor(pdf_path):
    """Test the simple probabilistic section extractor on a PDF file."""
    print(f"\nTesting simple section extraction on: {pdf_path}")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
    
    # Initialize the simple section extractor
    extractor = SimpleSectionExtractor()
    
    # Extract sections
    print("\n" + "="*50)
    print("USING MINIMAL PROBABILISTIC APPROACH")
    print("="*50)
    
    try:
        sections = extractor.extract_sections(pdf_path)
        print(f"\nExtracted {len(sections)} sections:")
        
        # Calculate overall confidence
        if sections:
            avg_confidence = sum(section.get('confidence', 0) for section in sections.values()) / len(sections)
            print(f"Overall extraction confidence: {avg_confidence:.2f}\n")
        
        for section_name, section_data in sections.items():
            # Get section metadata
            section_type = section_data.get('type', 'unknown')
            confidence = section_data.get('confidence', 0.0)
            word_count = len(section_data.get('content', '').split())
            original_header = section_data.get('original_header', '')
            
            # Display section information
            print(f"• {section_name} ({section_type})")
            print(f"  Confidence: {confidence:.2f}, Words: {word_count}")
            if original_header and original_header != section_name:
                print(f"  Original header: '{original_header}'")
            
            # Print a small preview of the content
            content_preview = section_data.get('content', '')[:80].replace('\n', ' ')
            if content_preview:
                print(f"  Preview: {content_preview}...")
            print()
            
    except Exception as e:
        print(f"Error using SimpleSectionExtractor: {e}")

def main():
    parser = argparse.ArgumentParser(description="Test simple probabilistic resume section extraction")
    parser.add_argument("pdf_path", nargs="?", default="new_resume.pdf", 
                      help="Path to the PDF resume to analyze")
    args = parser.parse_args()
    
    # Test the extractor
    test_simple_extractor(args.pdf_path)

if __name__ == "__main__":
    main()
