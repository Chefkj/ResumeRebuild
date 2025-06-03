"""
Text Utilities for Resume Processing

This module provides helper functions for text processing in the context of resume parsing.
"""

import re
import logging

logger = logging.getLogger(__name__)

def detect_broken_lines(text):
    """
    Detect lines that were likely broken incorrectly during OCR.
    
    Args:
        text (str): The OCR extracted text
        
    Returns:
        list: List of (start_idx, end_idx) tuples indicating broken line spans
    """
    broken_lines = []
    lines = text.split('\n')
    
    # Patterns that indicate broken lines
    end_patterns = [
        r'with$', r'for$', r'and$', r'the$', r'to$', r'of$', r'in$', r'as$', r'by$',  # Prepositions/conjunctions
        r'[A-Za-z]{3,}$',  # Words at end without punctuation
        r'\d{4}$'  # Years at end
    ]
    
    start_patterns = [
        r'^[a-z]',  # Line starts with lowercase
        r'^the\s', r'^and\s', r'^to\s', r'^of\s', r'^in\s', r'^as\s', r'^by\s',  # Common continuation words
        r'^[0-9]',  # Line starts with number
    ]
    
    # Check each pair of adjacent lines
    current_pos = 0
    for i in range(len(lines) - 1):
        line1 = lines[i].strip()
        line2 = lines[i + 1].strip()
        
        # Skip empty lines
        if not line1 or not line2:
            current_pos += len(lines[i]) + 1  # +1 for newline
            continue
        
        # Check if line1 ends with a pattern that suggests it continues
        ends_with_pattern = any(re.search(pattern, line1) for pattern in end_patterns)
        
        # Check if line2 starts with a pattern that suggests it's a continuation
        starts_with_pattern = any(re.search(pattern, line2) for pattern in start_patterns)
        
        # Don't merge if line2 is a bullet point or part of a list
        is_bullet_point = line2.startswith('•') or line2.startswith('-') or line2.startswith('*')
        
        # Don't merge if line1 ends with a strong separator
        ends_with_separator = line1.endswith('.') or line1.endswith(':') or line1.endswith(';')
        
        # Check for date patterns that should not be merged
        date_pattern = r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\s*$'
        is_date_line = bool(re.search(date_pattern, line1, re.IGNORECASE))
        
        # Calculate line positions
        line1_start = current_pos
        line1_end = line1_start + len(line1)
        line2_start = line1_end + 1  # +1 to skip newline
        
        # If conditions suggest these lines should be joined
        if (ends_with_pattern or starts_with_pattern) and not is_bullet_point and not ends_with_separator and not is_date_line:
            broken_lines.append((line1_end, line2_start))
        
        # Update position for next iteration
        current_pos += len(lines[i]) + 1  # +1 for newline
    
    return broken_lines

def fix_broken_lines(text):
    """
    Fix broken lines in OCR text by joining lines that were likely broken incorrectly.
    
    Args:
        text (str): The OCR extracted text
        
    Returns:
        str: The text with broken lines fixed
    """
    # Detect broken lines
    broken_lines = detect_broken_lines(text)
    
    # No broken lines detected
    if not broken_lines:
        return text
    
    # Fix the broken lines by replacing newlines with spaces
    result = list(text)
    
    # Process from end to beginning to maintain indices
    for line_end, line_start in sorted(broken_lines, reverse=True):
        # Replace newline with space or nothing if already a space
        if result[line_end] == ' ':
            result[line_start-1:line_start] = ['']
        else:
            result[line_start-1:line_start] = [' ']
    
    return ''.join(result)

def extract_contact_info(text):
    """
    Extract contact information from resume text.
    
    Args:
        text (str): The resume text
        
    Returns:
        dict: Dictionary with contact information (email, phone, etc.)
    """
    contact_info = {
        'email': None,
        'phone': None,
        'linkedin': None,
        'location': None
    }
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        contact_info['email'] = email_match.group(0)
    
    # Extract phone
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 123-456-7890
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b'      # (123) 456-7890
    ]
    
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            contact_info['phone'] = phone_match.group(0)
            break
    
    # Extract LinkedIn URL
    linkedin_pattern = r'linkedin\.com/in/[A-Za-z0-9_-]+'
    linkedin_match = re.search(linkedin_pattern, text)
    if linkedin_match:
        contact_info['linkedin'] = 'https://www.' + linkedin_match.group(0)
    
    # Extract location (City, State format)
    location_pattern = r'[A-Z][a-z]+(?:[\s-][A-Z][a-z]+)*,\s*(?:[A-Z]{2}|[A-Za-z]+)'
    location_match = re.search(location_pattern, text)
    if location_match:
        contact_info['location'] = location_match.group(0)
    
    return contact_info
