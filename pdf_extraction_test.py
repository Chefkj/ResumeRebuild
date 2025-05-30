#!/usr/bin/env python3
"""
PDF Extraction Diagnostic Tool

This script extracts and displays text and metadata from a PDF file
to help diagnose issues with section detection.
"""

import os
import sys
import json
import argparse
from pprint import pprint

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the PDF extractor and replacer components
from src.utils.pdf_extractor import PDFExtractor
from src.utils.pdf_direct_replacer import PDFDirectReplacer
from src.utils.pdf_content_replacer import PDFContentReplacer
from src.utils.section_classifier import SectionClassifier

def test_text_extraction(pdf_path):
    """Test basic text extraction."""
    print("\n=== Basic Text Extraction ===")
    extractor = PDFExtractor()
    try:
        text = extractor.extract(pdf_path)
        print(f"Extracted {len(text)} characters")
        print("First 500 characters:")
        print("-" * 40)
        print(text[:500])
        print("-" * 40)
        
        # Check for potential section headers
        print("\nPotential section headers (lines with uppercase or ending with :)")
        for line in text.split('\n'):
            line = line.strip()
            if (line.isupper() and len(line) > 3) or (line.endswith(':') and len(line) > 3):
                print(f"  - {line}")
    except Exception as e:
        print(f"Error in basic extraction: {e}")
        
def test_direct_replacer(pdf_path):
    """Test the PyMuPDF direct replacer."""
    print("\n=== Direct Replacer ===")
    
    try:
        pdf_replacer = PDFDirectReplacer()
        structure = pdf_replacer.extract_document_structure(pdf_path)
        
        print(f"Document metadata: {structure.get('meta', {})}")
        print(f"Pages: {len(structure.get('pages', []))}")
        
        # Get section details
        print(f"\nFound {len(structure.get('sections', []))} sections:")
        for i, section in enumerate(structure.get('sections', [])):
            print(f"  {i+1}. {section.get('title', 'Untitled')}: {len(section.get('content', '').split())} words")
        
        # Classified sections
        print("\nClassified sections:")
        for title, info in structure.get('classified_sections', {}).items():
            print(f"  - {title} ({info.get('type', 'unknown')}): {info.get('confidence', 0):.2f} confidence")
    
        # Look for formatting clues
        text_blocks = 0
        for page in structure.get('pages', []):
            text_blocks += len(page.get('blocks', []))
            
        print(f"\nText blocks across all pages: {text_blocks}")
        
        # Show text formatting samples
        if structure.get('pages'):
            first_page = structure.get('pages')[0]
            print("\nSample text formatting from first page:")
            for i, block in enumerate(first_page.get('blocks', [])[:5]):  # Show first 5 blocks
                if 'lines' in block and block['lines']:
                    for line in block['lines'][:2]:  # Show first 2 lines
                        for span in line.get('spans', []):
                            print(f"  Text: '{span.get('text', '').strip()}', Size: {span.get('size')}, Bold: {bool(span.get('flags', 0) & 1)}")
    except Exception as e:
        print(f"Error in direct replacement: {e}")
        
def test_content_replacer(pdf_path):
    """Test the unified PDF content replacer."""
    print("\n=== Content Replacer ===")
    
    try:
        pdf_replacer = PDFContentReplacer(use_enhanced=True, use_llm=False, use_ocr=False, use_direct=True)
        structure = pdf_replacer.analyze_structure(pdf_path)
        
        print(f"Page count: {structure.get('page_count', 0)}")
        print(f"Text blocks: {structure.get('text_block_count', 0)}")
        print(f"Format type: {structure.get('format_type', 'Unknown')}")
        
        # Show sections
        print(f"\nDetected sections: {len(structure.get('sections', {}))}")
        for name, info in structure.get('sections', {}).items():
            print(f"  - {name} ({info.get('type', 'unknown')}): {len(info.get('content', '').split())} words")
            
    except Exception as e:
        print(f"Error in content replacer: {e}")

def test_classifier(pdf_path):
    """Test the section classifier directly."""
    print("\n=== Section Classifier Test ===")
    
    try:
        extractor = PDFExtractor()
        text = extractor.extract(pdf_path)
        
        # Split text into potential sections based on formatting
        lines = text.split('\n')
        potential_sections = []
        current_section = {"title": "Unknown", "content": ""}
        
        # Simple heuristic: lines with few words, all caps, or ending with colon might be headers
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if (len(line.split()) <= 3 and len(line) > 3) or line.isupper() or line.endswith(':'):
                # This could be a header - save previous section and start new one
                if current_section["content"].strip():
                    potential_sections.append(current_section)
                    
                current_section = {"title": line, "content": ""}
            else:
                # This is content
                current_section["content"] += line + "\n"
                
        # Don't forget to add the last section
        if current_section["content"].strip():
            potential_sections.append(current_section)
            
        print(f"Found {len(potential_sections)} potential sections using simple heuristics")
        
        # Classify the potential sections
        classifier = SectionClassifier()
        for i, section in enumerate(potential_sections):
            section_type, confidence = classifier.classify_section(section["title"], section["content"])
            print(f"  {i+1}. '{section['title']}' => {section_type} ({confidence:.2f})")
            print(f"     First 50 chars: {section['content'][:50].replace(chr(10), ' ')}...")
            
    except Exception as e:
        print(f"Error in section classifier: {e}")

def test_enhanced_fallback(pdf_path):
    """Test an enhanced fallback method for section detection."""
    print("\n=== Enhanced Fallback Section Detection ===")
    
    try:
        import fitz  # PyMuPDF
        
        # Extract text blocks using TextPage which preserves more formatting
        doc = fitz.open(pdf_path)
        print(f"Document has {len(doc)} pages")
        
        # Initialize a text classifier to help with section detection
        classifier = SectionClassifier()
        
        # Save the full text for debugging
        full_text = ""
        for page in doc:
            full_text += page.get_text("text") + "\n"
            
        print("\nFull text from document (first 500 chars):")
        print(f"{'=' * 40}\n{full_text[:500]}\n{'=' * 40}\n")
        
        for page_num, page in enumerate(doc):
            print(f"\nPage {page_num + 1}/{len(doc)}:")
            
            # Get text blocks using the TextPage object for better formatting detection
            blocks = page.get_text("blocks")
            print(f"  Found {len(blocks)} text blocks")
            
            # Analyze blocks to detect section headers
            for i, block in enumerate(blocks[:10]):  # Show first 10 blocks
                text = block[4].strip()
                if not text:
                    continue
                    
                first_line = text.split('\n', 1)[0].strip()
                
                # Show more content for debugging
                content_preview = text[:100].replace('\n', ' ')
                
                # Use classifier for section type prediction
                section_type, confidence = classifier.classify_section(first_line, text)
                
                # Print more detailed information
                print(f"  Block {i+1}: {first_line[:30]}... => {section_type} ({confidence:.2f})")
                print(f"      Content: {content_preview}...")
                print(f"      Word count: {len(text.split())}")
                
        # Try direct text extraction with position and formatting data
        print("\nDetailed text extraction with formatting:")
        first_page = doc[0]
        text_dict = first_page.get_text("dict")
        
        # Count lines and spans
        total_blocks = len(text_dict.get("blocks", []))
        total_lines = sum(len(block.get("lines", [])) for block in text_dict.get("blocks", []))
        total_spans = sum(sum(len(line.get("spans", [])) for line in block.get("lines", []))
                         for block in text_dict.get("blocks", []))
        
        print(f"  Text structure: {total_blocks} blocks, {total_lines} lines, {total_spans} spans")
        
        # Look for formatting clues
        formatted_pieces = []
        for block in text_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                        
                    size = span.get("size", 0)
                    flags = span.get("flags", 0)
                    is_bold = bool(flags & 1)
                    
                    formatted_pieces.append({
                        "text": text,
                        "size": size,
                        "bold": is_bold,
                        "flags": flags
                    })
        
        # Find potential headers by looking at formatting
        potential_headers = []
        for piece in formatted_pieces:
            text = piece["text"]
            size = piece["size"]
            is_bold = piece["bold"]
            
            # Headers are often bigger, bolder, or ALL CAPS
            if ((size > 11 and len(text) < 50) or 
                (is_bold and len(text) < 50) or 
                (text.upper() == text and len(text) > 3 and len(text) < 50)):
                potential_headers.append(piece)
        
        print(f"\nFound {len(potential_headers)} potential headers based on formatting")
        for i, header in enumerate(potential_headers[:10]):  # Show first 10
            print(f"  {i+1}. '{header['text']}' (size: {header['size']}, bold: {header['bold']})")
            
    except ImportError:
        print("PyMuPDF (fitz) not available for enhanced analysis")
    except Exception as e:
        print(f"Error in enhanced fallback: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test PDF extraction and section detection')
    parser.add_argument('pdf_path', help='Path to the PDF file to test')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"File not found: {args.pdf_path}")
        return 1
        
    print(f"Testing PDF extraction on: {args.pdf_path}")
    
    # Run the tests
    test_text_extraction(args.pdf_path)
    test_direct_replacer(args.pdf_path)
    test_content_replacer(args.pdf_path)
    test_classifier(args.pdf_path)
    test_enhanced_fallback(args.pdf_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
