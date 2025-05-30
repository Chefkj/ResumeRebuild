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
    
    # Convert the text to lines
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            processed_lines.append(line)
            continue
        
        # Process each line to look for embedded headers
        modified_line = line
        for keyword in header_keywords:
            # Check if keyword exists as a standalone word in the line (with non-alphanumeric chars before/after)
            pattern = r'([^a-zA-Z0-9])(' + re.escape(keyword) + r')([^a-zA-Z0-9]|$)'
            matches = list(re.finditer(pattern, modified_line))
            
            if matches:
                for match in reversed(matches):  # Process from right to left to maintain indices
                    # Get the surrounding characters to check context
                    start_idx = max(0, match.start(2) - 15)
                    end_idx = min(len(modified_line), match.end(2) + 15)
                    context = modified_line[start_idx:end_idx]
                    
                    # Only split if it's likely a true section header and not part of a phrase
                    # For example, don't split "Professional Development" into a section
                    if any(word in context for word in ['•', ':', 'with', 'and']):
                        # Insert newline before the section header
                        start_pos = match.start(2)
                        modified_line = modified_line[:start_pos] + '\n\n' + keyword + '\n' + modified_line[match.end(2):]
            
        # Also check for special cases of headers directly attached to text
        for keyword in header_keywords:
            # Pattern for headers with text immediately attached (e.g., "SUMMARYEnthusiastic")
            pattern = r'(' + re.escape(keyword) + r')([A-Z][a-z]+)'
            if re.search(pattern, modified_line):
                modified_line = re.sub(pattern, r'\n\n\1\n\2', modified_line)
        
        # Check for lines that end with bullets/periods followed by uppercase text
        bullet_pattern = r'(•|\.)([A-Z]{2,})'
        if re.search(bullet_pattern, modified_line):
            modified_line = re.sub(bullet_pattern, r'\1\n\n\2', modified_line)
            
        processed_lines.append(modified_line)
    
    # Join the lines back into text
    processed_text = '\n'.join(processed_lines)
    
    # Remove excessive newlines
    processed_text = re.sub(r'\n{3,}', '\n\n', processed_text)
    
    # Add special handling for the common format where bullet points are used
    # and text flows without proper line breaks
    processed_text = re.sub(r'•', '\n• ', processed_text)
    
    return processed_text


def preprocess_pdf_text(text):
    """
    Apply all preprocessing techniques to the PDF text.
    
    Args:
        text (str): Raw text extracted from PDF
        
    Returns:
        str: Preprocessed text
    """
    # First split embedded headers
    text = split_embedded_headers(text)
    
    # Fix common spacing issues
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between lowercase and uppercase
    
    # Fix issues with joined words
    text = re.sub(r'([a-z])(\d)', r'\1 \2', text)  # Space between letters and numbers
    
    # Clean up excessive whitespace
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n +', '\n', text)
    
    return text
