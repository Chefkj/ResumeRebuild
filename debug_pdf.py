#!/usr/bin/env python3
"""
PDF Structure Debugging Tool

This script provides a detailed analysis of a PDF file to debug section detection issues.
It extracts text with position and formatting information to help identify why sections 
aren't being properly detected.
"""

import os
import sys
import fitz  # PyMuPDF
import re
from pprint import pprint

def analyze_pdf_structure(pdf_path):
    """Analyze the structure of a PDF with detailed debug information."""
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
        
    print(f"Analyzing PDF structure: {pdf_path}")
    
    try:
        # Open the document
        doc = fitz.open(pdf_path)
        print(f"Document has {len(doc)} pages")
        
        # Extract metadata
        metadata = doc.metadata
        print("\nMetadata:")
        for key, value in metadata.items():
            if value:
                print(f"  {key}: {value}")
                
        # Analyze each page in detail
        for page_num, page in enumerate(doc):
            print(f"\n==== Page {page_num + 1} ====")
            
            # Get dimensions
            width, height = page.rect.width, page.rect.height
            print(f"Dimensions: {width} x {height} points")
            
            # Extract different text formats
            for format_name in ["text", "html", "dict", "json", "xhtml", "xml"]:
                try:
                    # Just check if the format works
                    text = page.get_text(format_name)
                    print(f"  ✓ Format {format_name} supported")
                except Exception as e:
                    print(f"  ✗ Format {format_name} not supported: {e}")
            
            # Get raw text
            print("\nText content:")
            text = page.get_text("text")
            print("---\n" + text[:500] + "...\n---")
            
            # Analyze blocks
            blocks = page.get_text("dict")["blocks"]
            print(f"\nFound {len(blocks)} text blocks")
            
            # Print the first few blocks with detailed information
            for i, block in enumerate(blocks[:5]):  # Limit to first 5 blocks
                print(f"\nBlock {i+1}:")
                if "lines" in block:
                    print(f"  Position: ({block['bbox'][0]:.1f}, {block['bbox'][1]:.1f}) - ({block['bbox'][2]:.1f}, {block['bbox'][3]:.1f})")
                    print(f"  Contains {len(block['lines'])} line(s)")
                    
                    for j, line in enumerate(block["lines"][:3]):  # Limit to first 3 lines per block
                        for k, span in enumerate(line["spans"][:2]):  # Limit to first 2 spans per line
                            text = span["text"].replace("\n", "\\n")
                            font = span["font"]
                            size = span["size"]
                            color = span.get("color", 0)
                            flags = span.get("flags", 0)
                            
                            # Decode font flags
                            is_bold = bool(flags & 1)
                            is_italic = bool(flags & 2)
                            is_monospace = bool(flags & 64)
                            
                            style = []
                            if is_bold:
                                style.append("bold")
                            if is_italic:
                                style.append("italic")
                            if is_monospace:
                                style.append("monospace")
                            
                            style_str = ", ".join(style) if style else "regular"
                            
                            print(f"    Line {j+1}, Span {k+1}: '{text[:30]}{'...' if len(text) > 30 else ''}'")
                            print(f"      Font: {font}, Size: {size}, Style: {style_str}, Color: {color:06X}")
            
            # Look for potential section headers
            print("\nPotential section headers by formatting:")
            header_candidates = []
            
            for i, block in enumerate(blocks):
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    line_text = ""
                    line_size = 0
                    line_is_bold = False
                    line_is_caps = False
                    
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                            
                        line_text += text + " "
                        font_size = span["size"]
                        is_bold = bool(span.get("flags", 0) & 1)
                        
                        if font_size > line_size:
                            line_size = font_size
                            
                        if is_bold:
                            line_is_bold = True
                            
                        if text.upper() == text and len(text) > 1:
                            line_is_caps = True
                    
                    line_text = line_text.strip()
                    if line_text and (line_size > 11 or line_is_bold or line_is_caps):
                        header_candidates.append({
                            "text": line_text,
                            "size": line_size,
                            "bold": line_is_bold,
                            "caps": line_is_caps,
                            "block": i
                        })
            
            # Sort header candidates by font size then by boldness
            header_candidates.sort(key=lambda x: (-(x["size"]), not x["bold"]))
            
            # Print the header candidates
            for i, header in enumerate(header_candidates):
                print(f"  {i+1}. '{header['text']}' - Size: {header['size']}, Bold: {header['bold']}, Caps: {header['caps']}")
                
                # Check if this might be a section using common section names
                lower_text = header["text"].lower()
                common_sections = [
                    "summary", "experience", "education", "skills", "projects", 
                    "certifications", "languages", "achievements", "contact"
                ]
                matching = [s for s in common_sections if s in lower_text]
                if matching:
                    print(f"     LIKELY SECTION: {matching[0].upper()}")
                elif ":" in header["text"]:
                    print("     Potential section header (contains colon)")
                    
            # Extract images if any
            images = page.get_images()
            if images:
                print(f"\nFound {len(images)} images on the page")
            
            # Extract links if any
            links = page.get_links()
            if links:
                print(f"\nFound {len(links)} links on the page")
                
        # Look for sections using regex patterns
        full_text = ""
        for page in doc:
            full_text += page.get_text("text") + "\n"
            
        section_patterns = [
            (r'(?i)(?:^|\n)(?:EDUCATION|ACADEMIC|QUALIFICATIONS|DEGREES?)(?:\s|:|\n)', "Education"),
            (r'(?i)(?:^|\n)(?:WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT|WORK\s*HISTORY|EXPERIENCE)(?:\s|:|\n)', "Experience"),
            (r'(?i)(?:^|\n)(?:SKILLS|TECHNICAL\s+SKILLS|PROFICIENCIES|EXPERTISE)(?:\s|:|\n)', "Skills"),
            (r'(?i)(?:^|\n)(?:PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE)(?:\s|:|\n)', "Summary"),
            (r'(?i)(?:^|\n)(?:CERTIFICATIONS|CERTIFICATES|CREDENTIALS|LICENSES)(?:\s|:|\n)', "Certifications"),
            (r'(?i)(?:^|\n)(?:LANGUAGE|LANGUAGES)(?:\s|:|\n)', "Languages"),
            (r'(?i)(?:^|\n)(?:PROJECTS|PROJECT\s+EXPERIENCE|PORTFOLIO)(?:\s|:|\n)', "Projects"),
            (r'(?i)(?:^|\n)(?:ACCOMPLISHMENTS|AWARDS|HONORS|ACHIEVEMENTS)(?:\s|:|\n)', "Accomplishments"),
            (r'(?i)(?:^|\n)(?:PUBLICATIONS|PAPERS|RESEARCH)(?:\s|:|\n)', "Publications"),
            (r'(?i)(?:^|\n)(?:VOLUNTEER|COMMUNITY\s+SERVICE)(?:\s|:|\n)', "Volunteer")
        ]
        
        print("\nSearching for section headers using regex patterns:")
        for pattern, section_type in section_patterns:
            matches = re.finditer(pattern, full_text)
            for match in matches:
                match_text = match.group().strip()
                pos = match.start()
                print(f"  Found '{match_text}' at position {pos} - Type: {section_type}")
        
        # Try to find section headers by heuristics
        print("\nLooking for section headers by heuristics:")
        lines = full_text.split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check for heuristic signals
            is_potential_header = (
                (line.isupper() and len(line) > 2) or
                (len(line) < 30 and line.endswith(':')) or
                (len(line.split()) <= 3 and len(line) > 2 and i > 0 and not lines[i-1].strip())
            )
            
            if is_potential_header:
                print(f"  Potential header: '{line}'")
                # Check if it might be a section using common section names
                lower_text = line.lower()
                common_sections = [
                    "summary", "experience", "education", "skills", "projects", 
                    "certifications", "languages", "achievements", "contact"
                ]
                matching = [s for s in common_sections if s in lower_text]
                if matching:
                    print(f"     LIKELY SECTION: {matching[0].upper()}")
        
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_pdf.py path/to/file.pdf")
        return 1
        
    pdf_path = sys.argv[1]
    analyze_pdf_structure(pdf_path)
    
if __name__ == "__main__":
    sys.exit(main() or 0)
