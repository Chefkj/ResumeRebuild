#!/usr/bin/env python3
"""
Find embedded section headers in a resume PDF
"""

import os
import sys
import fitz  # PyMuPDF
import re

def find_embedded_headers(pdf_path):
    """Extract embedded section headers from a PDF file."""
    print(f"\nFinding embedded section headers in: {pdf_path}")
    
    # Open the document
    doc = fitz.open(pdf_path)
    
    # Extract full text
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    
    # Common resume section headers to look for
    common_headers = [
        'SUMMARY', 'SKILLS', 'EXPERIENCE', 'EDUCATION', 
        'ACCOMPLISHMENTS', 'LANGUAGE', 'PROFESSIONAL'
    ]
    
    # Print the full text for context
    lines = full_text.split('\n')
    print("\nFull text (first 30 lines):")
    print("-" * 50)
    for i, line in enumerate(lines[:30]):
        print(f"{i:2d}: '{line}'")
    
    # Find all positions where these headers appear
    print("\nFound embedded section headers:")
    print("-" * 50)
    
    for header in common_headers:
        for i, line in enumerate(lines):
            if header in line.upper():
                # Get the context around the header
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                context = "\n".join(lines[start:end])
                
                # Find exact position of the header in the line
                pos = line.upper().find(header)
                
                print(f"Found '{header}' in line {i}:")
                print(f"  Position: {pos}")
                print(f"  Full line: '{line}'")
                print(f"  Context:\n{context}")
                print("-" * 30)

def main():
    pdf_path = "new_resume.pdf"
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    find_embedded_headers(pdf_path)

if __name__ == "__main__":
    main()
