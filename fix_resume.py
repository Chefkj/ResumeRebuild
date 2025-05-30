#!/usr/bin/env python3
"""
PDF Resume Fix and Analyzer

This script directly analyzes and extracts sections from a PDF resume,
showing the results in a way that makes sense. It can be used to verify
the functionality of the PDF content replacer and direct replacer.
"""

import os
import re
import sys
import fitz  # PyMuPDF
from pprint import pprint

def analyze_pdf_resume(pdf_path):
    """Analyze a PDF resume and extract its content."""
    print(f"Analyzing PDF resume: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    print(f"Document has {len(doc)} pages")
    
    # Extract full text
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    
    # Show a preview of the full text
    print("\nFull text preview (first 300 characters):")
    print("=" * 40)
    print(full_text[:300])
    print("=" * 40)
    
    # Try to identify key sections
    print("\nDetected sections:")
    
    # Common resume section patterns - enhanced with more variations
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
            matches.append({
                'start': match.start(),
                'header': match.group().strip(),
                'type': section_name
            })
    
    # Sort by position in text
    matches.sort(key=lambda x: x['start'])
    
    # Extract section content
    sections = []
    for i, match in enumerate(matches):
        # Get content between this header and next header (or end of text)
        start = match['start'] + len(match['header'])
        end = matches[i+1]['start'] if i < len(matches) - 1 else len(full_text)
        content = full_text[start:end].strip()
        
        section = {
            'title': match['header'].strip(),
            'type': match['type'],
            'content': content,
            'word_count': len(content.split())
        }
        sections.append(section)
    
    # Print sections with word counts
    for i, section in enumerate(sections):
        print(f"  {i+1}. {section['title']}: {section['type']} ({section['word_count']} words)")
        print(f"     Sample: {section['content'][:50]}...")
        print()
    
    # Also extract using text blocks for comparison - with improved detection
    print("\nAlternative detection using text blocks:")
    headers = []
    
    for page_num, page in enumerate(doc):
        # Get blocks with dehyphenation for better text extraction
        blocks = page.get_text("dict", flags=fitz.TEXT_DEHYPHENATE)["blocks"]
        
        for block_num, block in enumerate(blocks):
            if "lines" not in block:
                continue
                
            # Check each line for potential headers
            for line in block["lines"]:
                line_text = ""
                line_is_bold = False
                line_font_size = 0
                line_is_all_caps = True
                
                # Process all spans in the line to get combined properties
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    
                    line_text += text + " "
                    
                    # Check formatting properties
                    font_size = span["size"]
                    font_flags = span.get("flags", 0)
                    is_bold = bool(font_flags & 2**0)
                    
                    # Track the maximum font size in the line
                    if font_size > line_font_size:
                        line_font_size = font_size
                    
                    # Track if any part of the line is bold
                    if is_bold:
                        line_is_bold = True
                    
                    # Check all caps status for the whole line
                    if text.upper() != text:
                        line_is_all_caps = False
                
                # Clean up the line text
                line_text = line_text.strip()
                if not line_text:
                    continue
                
                # Get section type hint based on common section names
                section_type = "unknown"
                common_sections = {
                    "education": ["education", "academic", "qualifications", "degrees"],
                    "experience": ["experience", "work", "employment", "history", "career"],
                    "skills": ["skills", "competencies", "proficiencies", "expertise"],
                    "summary": ["summary", "profile", "objective", "about"],
                    "certifications": ["certifications", "certificates", "credentials"],
                    "languages": ["languages", "language"],
                    "projects": ["projects", "portfolio"],
                    "achievements": ["accomplishments", "awards", "honors", "achievements"],
                    "publications": ["publications", "papers", "research"],
                    "volunteer": ["volunteer", "community", "service"],
                    "interests": ["interests", "hobbies", "activities"],
                    "references": ["references"]
                }
                
                # Check if the line text contains any common section names
                lower_text = line_text.lower()
                for sec_type, keywords in common_sections.items():
                    if any(keyword in lower_text for keyword in keywords):
                        section_type = sec_type
                        break
                
                # Enhanced header detection heuristics
                is_potential_header = False
                confidence = 0.0
                
                # Headers are often bold, larger font, all caps, etc.
                if line_font_size > 12 and (line_is_bold or line_is_all_caps):
                    is_potential_header = True
                    confidence = 0.8  # High confidence
                elif line_font_size >= 14:
                    is_potential_header = True
                    confidence = 0.9  # Higher confidence for larger font
                elif line_is_all_caps and len(line_text.split()) <= 3:
                    is_potential_header = True
                    confidence = 0.7  # Moderate confidence
                elif line_is_bold and len(line_text) < 30 and len(line_text.split()) <= 4:
                    is_potential_header = True
                    confidence = 0.7  # Moderate confidence
                
                # Additional factors that might indicate a header
                if line_text.endswith(':'):
                    confidence += 0.1
                    is_potential_header = True
                
                # Section type recognition boosts confidence
                if section_type != "unknown":
                    confidence += 0.2
                    is_potential_header = True
                
                # Only add confident header candidates
                if is_potential_header and confidence > 0.5:
                    headers.append({
                        'text': line_text,
                        'font_size': line_font_size,
                        'is_bold': line_is_bold,
                        'is_all_caps': line_is_all_caps,
                        'section_type': section_type,
                        'confidence': confidence,
                        'page': page_num + 1
                    })
    
    # Sort headers by confidence and group by page
    headers.sort(key=lambda x: (-x.get('confidence', 0), x['page']))
    
    # Print detected headers with improved information
    print("\nPotential section headers by confidence:")
    for i, header in enumerate(headers):
        conf_str = f"{header.get('confidence', 0)*100:.1f}%" if 'confidence' in header else "N/A"
        section_type = f"({header.get('section_type', 'unknown')})" if 'section_type' in header else ""
        print(f"  {i+1}. '{header['text']}' - Size: {header['font_size']}, " +
              f"Bold: {header['is_bold']}, Page: {header['page']}, Confidence: {conf_str} {section_type}")
    
    # Create a summary of the best section headers
    print("\nRecommended section structure:")
    used_sections = set()
    for header in sorted(headers, key=lambda x: (-x.get('confidence', 0))):
        section_type = header.get('section_type', 'unknown')
        if section_type != 'unknown' and section_type not in used_sections:
            used_sections.add(section_type)
            conf_str = f"{header.get('confidence', 0)*100:.1f}%" if 'confidence' in header else "N/A"
            print(f"  • {section_type.title()}: '{header['text']}' (Confidence: {conf_str})")
    
    # Return the full analysis
    return {
        'text': full_text,
        'sections': sections,
        'potential_headers': headers
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_resume.py /path/to/resume.pdf")
        return 1
        
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return 1
    
    analyze_pdf_resume(pdf_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
