#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Pattern Library on Real Resume

This script demonstrates the pattern library on a real resume PDF file.
It uses the OCR text extractor to convert the PDF to text and then shows
how the pattern library cleans up the OCR text.
"""

import os
import sys
import logging
from src.utils.ocr_text_extraction import OCRTextExtractor
from src.utils.pattern_library import initialize_standard_library

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_on_real_resume(pdf_path):
    """
    Extract text from a real resume PDF and apply pattern library fixes.
    
    Args:
        pdf_path: Path to the PDF resume file
    """
    logger.info(f"=== Testing Pattern Library on Real Resume: {os.path.basename(pdf_path)} ===")
    
    # Initialize OCR text extractor
    extractor = OCRTextExtractor()
    
    # Extract raw text from PDF
    logger.info("\nExtracting text from PDF...")
    try:
        raw_ocr_text = extractor.extract_text(pdf_path)
        
        # Show the first 500 characters of raw text to get a sense of it
        logger.info("\nRaw OCR Text (first 500 chars):")
        logger.info("=" * 50)
        logger.info(raw_ocr_text[:500].replace('\n', '\\n'))
        
        # Apply pattern fixes by category to show the transformation
        logger.info("\nApplying patterns category by category...")
        
        # Apply the patterns category by category
        processed_text = raw_ocr_text
        
        # Start with headers
        logger.info("\nAfter applying HEADERS patterns:")
        processed_text = extractor.pattern_library.apply_category(processed_text, "headers")
        logger.info(f"First 500 chars: {processed_text[:500].replace('\n', '\\n')}")
        
        # Then dates
        logger.info("\nAfter applying DATES patterns:")
        processed_text = extractor.pattern_library.apply_category(processed_text, "dates")
        logger.info(f"First 500 chars: {processed_text[:500].replace('\n', '\\n')}")
        
        # Then locations
        logger.info("\nAfter applying LOCATIONS patterns:")
        processed_text = extractor.pattern_library.apply_category(processed_text, "locations")
        logger.info(f"First 500 chars: {processed_text[:500].replace('\n', '\\n')}")
        
        # Then contact info
        logger.info("\nAfter applying CONTACT patterns:")
        processed_text = extractor.pattern_library.apply_category(processed_text, "contact")
        logger.info(f"First 500 chars: {processed_text[:500].replace('\n', '\\n')}")
        
        # Finally special cases
        logger.info("\nAfter applying SPECIAL CASES patterns:")
        processed_text = extractor.pattern_library.apply_category(processed_text, "special_cases")
        logger.info(f"First 500 chars: {processed_text[:500].replace('\n', '\\n')}")
        
        # Generate and show the performance report
        logger.info("\nPattern Library Performance Report:")
        extractor.pattern_library.print_performance_report()
        
        # Find examples of pattern fixes in the text
        find_example_fixes(raw_ocr_text, processed_text)
        
    except Exception as e:
        logger.error(f"Error processing resume: {e}")
        import traceback
        traceback.print_exc()

def find_example_fixes(raw_text, processed_text):
    """
    Find examples of patterns that were applied to the text.
    
    Args:
        raw_text: Original OCR text
        processed_text: Text after pattern fixes applied
    """
    import re
    
    logger.info("\nExamples of Fixes Applied:")
    logger.info("=" * 50)
    
    # Check for email formatting fixes
    email_pattern = r'\b\w+[\s@]+\w+\.\w+\b'
    raw_emails = re.findall(email_pattern, raw_text)
    if raw_emails:
        logger.info("1. Email formatting fixes:")
        for raw_email in raw_emails[:3]:  # Show up to 3 examples
            # Find corresponding fixed email
            clean_email = raw_email.replace(' ', '')
            if clean_email in processed_text:
                logger.info(f"   Before: '{raw_email}'")
                logger.info(f"   After:  '{clean_email}'")
    
    # Check for date formatting fixes
    date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)[\s\n]*\d{4}'
    raw_dates = re.findall(date_pattern, raw_text)
    if raw_dates:
        logger.info("\n2. Date formatting fixes:")
        for raw_date in raw_dates[:3]:  # Show up to 3 examples
            # Check for spaces between month and year
            if ' ' not in raw_date:
                month = re.match(r'([A-Za-z]+)', raw_date).group(1)
                year = raw_date[len(month):]
                fixed_date = f"{month} {year}"
                if fixed_date in processed_text:
                    logger.info(f"   Before: '{raw_date}'")
                    logger.info(f"   After:  '{fixed_date}'")
    
    # Check for location pattern fixes
    state_names = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 
                  'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 
                  'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 
                  'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 
                  'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 
                  'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 
                  'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 
                  'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 
                  'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 
                  'West Virginia', 'Wisconsin', 'Wyoming']
    
    for state in state_names:
        pattern = fr'{state}([A-Z][a-z]+(?:ed|ing)\b)'
        match = re.search(pattern, raw_text)
        if match:
            verb = match.group(1)
            before = f"{state}{verb}"
            after = f"{state}\n{verb}"
            if after in processed_text:
                logger.info("\n3. Location pattern fixes:")
                logger.info(f"   Before: '{before}'")
                logger.info(f"   After:  '{after}'")
                break
    
    # Check for embedded header fixes
    header_pattern = r'([a-z])(SKILLS|EXPERIENCE)'
    matches = re.findall(header_pattern, raw_text)
    if matches:
        logger.info("\n4. Embedded header fixes:")
        for match in matches[:2]:
            char, header = match
            before = f"{char}{header}"
            after = f"{char}\n\n{header}"
            if after in processed_text:
                logger.info(f"   Before: '{before}'")
                logger.info(f"   After:  '{after}'")
    
    # Check for special case fixes like KU pattern
    ku_pattern = r'([A-Z]+\s+[A-Z]+)\s*KU([A-Z][a-z]+)'
    matches = re.findall(ku_pattern, raw_text)
    if matches:
        logger.info("\n5. Special case fixes (KU pattern):")
        for match in matches[:2]:
            name, location = match
            before = f"{name} KU{location}"
            after = f"{name}\n{location}"
            if after in processed_text:
                logger.info(f"   Before: '{before}'")
                logger.info(f"   After:  '{after}'")

if __name__ == "__main__":
    # Use the new_resume.pdf as the test file
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "new_resume.pdf")
    test_on_real_resume(pdf_path)
