#!/usr/bin/env python3
"""
Analyze potential section headers in a PDF document
"""

import os
import sys
import fitz  # PyMuPDF
import re

def analyze_headers(pdf_path):
    """Extract potential headers from a PDF file."""
    print(f"\nAnalyzing potential headers in: {pdf_path}")
    
    # Open the document
    doc = fitz.open(pdf_path)
    
    # Extract full text first
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    
    # Print the first 20 lines of the document
    print("\nFirst 20 lines of document:")
    print("-" * 50)
    lines = full_text.split('\n')
    for i, line in enumerate(lines[:20]):
        print(f"{i:2d}: '{line}'")
    
    # Get text with format information
    print("\nAll text blocks with formatting details:")
    print("-" * 50)
    
    for page_num, page in enumerate(doc):
        print(f"\n=== Page {page_num + 1} ===\n")
        
        # Get blocks with format information
        blocks = page.get_text("dict")["blocks"]
        
        for block_num, block in enumerate(blocks):
            if "lines" not in block:
                continue
                
            print(f"\nBlock {block_num}:")
            
            for line_num, line in enumerate(block["lines"]):
                # Get text from spans
                text = ""
                max_size = 0
                is_bold = False
                
                for span in line["spans"]:
                    text += span["text"]
                    font_size = span["size"]
                    if font_size > max_size:
                        max_size = font_size
                    
                    font_flags = span.get("flags", 0)
                    if bool(font_flags & 2**0):  # Check for bold flag
                        is_bold = True
                
                if not text.strip():
                    continue
                    
                # Calculate a header score for this line
                header_score = 0
                if text.strip() == text.strip().upper() and len(text.strip()) > 3:
                    header_score += 2
                if is_bold:
                    header_score += 2
                if max_size > 12:
                    header_score += 2
                    
                header_indicator = ""
                if header_score >= 2:
                    header_indicator = " *** POTENTIAL HEADER ***"
                    
                print(f"  Line {line_num}: '{text.strip()}'")
                print(f"    Size: {max_size:.1f}, Bold: {is_bold}{header_indicator}")

def main():
    pdf_path = "new_resume.pdf"
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    analyze_headers(pdf_path)

if __name__ == "__main__":
    main()
