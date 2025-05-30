#!/usr/bin/env python3
"""
Resume Section Detection Test

This script tests the improved PDF section detection for resume rebuilding.
It integrates the enhanced algorithms from fix_resume.py and pdf_content_replacer.py.
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
    from src.utils.pdf_content_replacer import PDFContentReplacer
    from src.utils.pdf_extractor import PDFExtractor
except ImportError:
    from utils.pdf_content_replacer import PDFContentReplacer
    from utils.pdf_extractor import PDFExtractor

def test_pdf_sections(pdf_path):
    """Test PDF section detection with all available methods."""
    print(f"Testing section detection on: {pdf_path}")
    
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return False
    
    print("\n" + "="*50)
    print("METHOD 1: Using PDFContentReplacer")
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
            
            print(f"  • {section_name} ({section_type}) - {word_count} words, " +
                 f"confidence: {confidence:.2f}")
            
            # Print a small preview of the content
            content_preview = section_data.get('content', '')[:50].replace('\n', ' ')
            if content_preview:
                print(f"    Preview: {content_preview}...")
    except Exception as e:
        print(f"Error using PDFContentReplacer: {e}")
    
    print("\n" + "="*50)
    print("METHOD 2: Using fix_resume.py Pattern Detection")
    print("="*50)
    
    try:
        # Open the PDF with PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Extract full text
        full_text = ""
        for page in doc:
            full_text += page.get_text("text") + "\n"
        
        # Try to identify sections based on common section headers
        section_patterns = [
            (r'(?i)(?:^|\n)(?:EDUCATION|ACADEMIC|QUALIFICATIONS|DEGREES?|EDUCATIONAL\s+BACKGROUND|ACADEMIC\s+HISTORY)(?:\s|:|\n)', "Education"),
            (r'(?i)(?:^|\n)(?:WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT|WORK\s*HISTORY|EXPERIENCE|PROFESSIONAL\s+BACKGROUND|CAREER\s+HISTORY|JOB\s+HISTORY)(?:\s|:|\n)', "Experience"),
            (r'(?i)(?:^|\n)(?:SKILLS|TECHNICAL\s+SKILLS|PROFICIENCIES|EXPERTISE|CORE\s+COMPETENCIES|KEY\s+SKILLS|PROFESSIONAL\s+SKILLS|SKILL\s+SET)(?:\s|:|\n)', "Skills"),
            (r'(?i)(?:^|\n)(?:PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE|CAREER\s+OBJECTIVE|PROFESSIONAL\s+PROFILE|ABOUT\s+ME|CAREER\s+SUMMARY)(?:\s|:|\n)', "Summary"),
            (r'(?i)(?:^|\n)(?:CERTIFICATIONS?|CERTIFICATES|CREDENTIALS|LICENSES|PROFESSIONAL\s+CERTIFICATIONS)(?:\s|:|\n)', "Certifications"),
            (r'(?i)(?:^|\n)(?:LANGUAGES?|LANGUAGE\s+PROFICIENCY|LANGUAGE\s+SKILLS|FLUENCY|FOREIGN\s+LANGUAGES)(?:\s|:|\n)', "Languages"),
            (r'(?i)(?:^|\n)(?:PROJECTS|PROJECT\s+EXPERIENCE|PORTFOLIO|PERSONAL\s+PROJECTS|PROFESSIONAL\s+PROJECTS|KEY\s+PROJECTS)(?:\s|:|\n)', "Projects"),
            (r'(?i)(?:^|\n)(?:ACCOMPLISHMENTS|AWARDS|HONORS|ACHIEVEMENTS|ACCOLADES|RECOGNITIONS)(?:\s|:|\n)', "Accomplishments"),
            (r'(?i)(?:^|\n)(?:PUBLICATIONS|PAPERS|RESEARCH|RESEARCH\s+EXPERIENCE|PUBLISHED\s+WORKS)(?:\s|:|\n)', "Publications"),
            (r'(?i)(?:^|\n)(?:VOLUNTEER|COMMUNITY\s+SERVICE|VOLUNTEERING|CIVIC\s+ACTIVITIES|COMMUNITY\s+INVOLVEMENT)(?:\s|:|\n)', "Volunteer"),
            (r'(?i)(?:^|\n)(?:INTERESTS|HOBBIES|ACTIVITIES|PERSONAL\s+INTERESTS)(?:\s|:|\n)', "Interests"),
            (r'(?i)(?:^|\n)(?:REFERENCES|PROFESSIONAL\s+REFERENCES)(?:\s|:|\n)', "References"),
            (r'(?i)(?:^|\n)(?:ADDITIONAL\s+INFORMATION|OTHER\s+INFORMATION|MISCELLANEOUS)(?:\s|:|\n)', "Additional")
        ]
        
        # Find all matches
        matches = []
        for pattern, section_name in section_patterns:
            for match in re.finditer(pattern, full_text):
                matches.append((match.start(), match.group().strip(), section_name))
        
        # Sort by position in text
        matches.sort(key=lambda x: x[0])
        
        # Extract sections
        sections = []
        for i, (start_pos, header_text, section_type) in enumerate(matches):
            # Get section content (text between this header and next, or end)
            if i < len(matches) - 1:
                content = full_text[start_pos + len(header_text):matches[i+1][0]]
            else:
                content = full_text[start_pos + len(header_text):]
                
            # Clean up the content
            content = content.strip()
            word_count = len(content.split())
            
            sections.append({
                'header': header_text,
                'type': section_type,
                'content': content,
                'word_count': word_count
            })
        
        # Print sections
        print(f"\nDetected {len(sections)} sections using pattern matching:")
        for i, section in enumerate(sections):
            print(f"  {i+1}. {section['header']} ({section['type']}) - {section['word_count']} words")
            
            # Print a small preview of the content
            content_preview = section['content'][:50].replace('\n', ' ')
            print(f"     Preview: {content_preview}...")
            
    except Exception as e:
        print(f"Error in pattern detection: {e}")
    
    print("\n" + "="*50)
    print("METHOD 3: Using PDFExtractor")
    print("="*50)
    
    try:
        # Use the PDFExtractor directly
        extractor = PDFExtractor()
        resume = extractor.extract(pdf_path)
        
        print(f"\nExtracted {len(resume.sections)} sections:")
        for i, section in enumerate(resume.sections):
            word_count = len(section.content.split())
            print(f"  {i+1}. {section.title} - {word_count} words")
            
            # Print a small preview of the content
            content_preview = section.content[:50].replace('\n', ' ')
            print(f"     Preview: {content_preview}...")
    except Exception as e:
        print(f"Error using PDFExtractor: {e}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Test improved PDF section detection")
    parser.add_argument("pdf_path", help="Path to the PDF resume to analyze")
    
    args = parser.parse_args()
    
    test_pdf_sections(args.pdf_path)
    
if __name__ == "__main__":
    main()
