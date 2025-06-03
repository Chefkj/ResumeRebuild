"""
PDF Text Preprocessor

This module provides functions to preprocess text extracted from PDFs,
particularly for fixing common extraction issues like embedded section headers.
"""

import re
import logging

logger = logging.getLogger(__name__)

def split_embedded_headers(text, header_keywords=None):
    """
    Process text with embedded section headers and split them into proper sections.
    
    Args:
        text (str): The raw text extracted from a PDF
        header_keywords (list): List of header keywords to look for
        
    Returns:
        str: Processed text with section headers properly separated
    """
    if not header_keywords:
        header_keywords = [
            'SUMMARY', 'PROFILE', 'OBJECTIVE', 
            'EXPERIENCE', 'EMPLOYMENT', 'WORK HISTORY',
            'EDUCATION', 'ACADEMIC', 'QUALIFICATIONS',
            'SKILLS', 'COMPETENCIES', 'EXPERTISE',
            'PROJECTS', 'ACCOMPLISHMENTS', 'ACHIEVEMENTS',
            'CERTIFICATIONS', 'LANGUAGES', 'INTERESTS',
            'PROFESSIONAL', 'VOLUNTEER', 'REFERENCES'
        ]
    
    # Words that should NOT be treated as section headers
    non_section_words = ['RESUME', 'CV', 'CURRICULUM VITAE', 'NAME', 'PAGE', 'EMAIL']
    
    # Filter out non-section words from header keywords
    filtered_keywords = [kw for kw in header_keywords if kw not in non_section_words]
    
    # Convert the text to lines
    lines = text.split('\n')
    processed_lines = []
    
    # Keep track of the current section to handle hierarchical content
    current_section = None
    in_experience_section = False
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            processed_lines.append(line)
            continue
        
        # Check if we're entering an experience section
        if any(keyword.upper() in line.upper() for keyword in ['EXPERIENCE', 'EMPLOYMENT', 'WORK HISTORY']):
            in_experience_section = True
            current_section = "EXPERIENCE"
        # Check if we're leaving an experience section
        elif any(keyword.upper() in line.upper() for keyword in ['EDUCATION', 'SKILLS', 'PROJECTS']) and in_experience_section:
            in_experience_section = False
            current_section = None
            
        # Process each line to look for embedded headers
        modified_line = line
        
        # Check for main section headers first
        for keyword in filtered_keywords:
            # Skip short keywords that might cause false positives
            if len(keyword) < 5:
                continue
                
            # Check if keyword exists as a standalone word in the line (with non-alphanumeric chars before/after)
            pattern = r'([^a-zA-Z0-9])(' + re.escape(keyword) + r')([^a-zA-Z0-9]|$)'
            matches = list(re.finditer(pattern, modified_line, re.IGNORECASE))
            
            if matches:
                for match in reversed(matches):  # Process from right to left to maintain indices
                    # Get the surrounding characters to check context
                    start_idx = max(0, match.start(2) - 15)
                    end_idx = min(len(modified_line), match.end(2) + 15)
                    context = modified_line[start_idx:end_idx]
                    
                    # Only split if it's likely a true section header and not part of a phrase
                    # For example, don't split "Professional Development" into a section
                    if not any(word in context.lower() for word in ['professional development', 'with', 'and']):
                        # Insert newline before the section header
                        start_pos = match.start(2)
                        modified_line = modified_line[:start_pos] + '\n\n' + keyword + '\n' + modified_line[match.end(2):]
            
            # Also check for special cases of headers directly attached to text
            # Pattern for headers with text immediately attached (e.g., "SUMMARYEnthusiastic")
            pattern = r'(' + re.escape(keyword) + r')([A-Z][a-z]+)'
            if re.search(pattern, modified_line, re.IGNORECASE):
                modified_line = re.sub(pattern, r'\n\n\1\n\2', modified_line, flags=re.IGNORECASE)
        
        # Special handling for job titles in experience sections
        if in_experience_section:
            # Check for job title patterns (position at company)
            job_pattern = r'([A-Z][a-z]+(?: [A-Z][a-z]+)*) (at|for|with) ([A-Z][a-zA-Z\s,\.]+)'
            if re.search(job_pattern, modified_line):
                # Format as a sub-section rather than a main section
                if i > 0 and lines[i-1].strip():  # If previous line isn't empty
                    modified_line = '\n• ' + modified_line
                else:
                    modified_line = '• ' + modified_line
                
            # Check for date patterns that usually indicate job entries
            date_pattern = r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4})\s*(-|to|–|—)\s*'
            if re.search(date_pattern, modified_line, re.IGNORECASE):
                # Format as a sub-entry if it's not already
                if not modified_line.strip().startswith('•') and i > 0 and lines[i-1].strip():
                    modified_line = '\n  ' + modified_line  # Indent to indicate it's part of a job entry
        
        # Check for lines that end with bullets/periods followed by uppercase text
        # This often indicates an embedded header
        bullet_pattern = r'(•|\.)([A-Z]{2,})'
        if re.search(bullet_pattern, modified_line):
            # Only apply if this looks like a genuine section header, not just capitalized text
            match = re.search(bullet_pattern, modified_line)
            potential_header = match.group(2)
            
            if potential_header in filtered_keywords:
                modified_line = re.sub(bullet_pattern, r'\1\n\n\2', modified_line)
            
        processed_lines.append(modified_line)
    
    # Join the lines back into text
    processed_text = '\n'.join(processed_lines)
    
    # Remove excessive newlines
    processed_text = re.sub(r'\n{3,}', '\n\n', processed_text)
    
    # Add special handling for the common format where bullet points are used
    # and text flows without proper line breaks, but avoid creating too many breaks
    processed_text = re.sub(r'([^\n])•', r'\1\n• ', processed_text)
    
    # Remove "RESUME" header if it appears at the top of the document
    processed_text = re.sub(r'^RESUME\s*\n+', '', processed_text)
    
    return processed_text


def preprocess_pdf_text(text, is_ocr_extracted=False):
    """
    Apply all preprocessing techniques to the PDF text.
    
    Args:
        text (str): Raw text extracted from PDF
        is_ocr_extracted (bool): Whether the text was extracted using OCR
        
    Returns:
        str: Preprocessed text
    """
    # First split embedded headers
    text = split_embedded_headers(text)
    
    # Fix common spacing issues
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between lowercase and uppercase
    
    # Fix issues with joined words
    text = re.sub(r'([a-z])(\d)', r'\1 \2', text)  # Space between letters and numbers
    
    # Special handling for OCR-extracted text
    if is_ocr_extracted:
        # Fix common OCR errors in resumes
        text = re.sub(r'([A-Za-z])\.([A-Z])', r'\1. \2', text)  # Add space after periods
        text = re.sub(r'(\d{4})\s*-\s*(\d{4}|\w+)', r'\1 - \2', text)  # Fix date ranges
        text = re.sub(r'(\w+),(\w+)', r'\1, \2', text)  # Add space after commas
    
    # Clean up excessive whitespace
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n +', '\n', text)
    
    return text
