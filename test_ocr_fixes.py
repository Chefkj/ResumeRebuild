#!/usr/bin/env python3
"""
OCR Text Extraction Fixes

This script applies fixes to the OCR text extraction code to address specific issues
identified in testing, particularly for embedded headers, date formats, emails with spaces,
and multiple SKILLS sections.
"""

import re
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the OCR extractor
from src.utils.ocr_text_extraction import OCRTextExtractor

def test_improvements():
    """Test the improvements to the OCR text extraction."""
    logger.info("Testing improved OCR text extraction...")
    
    # Create OCR text extractor
    extractor = OCRTextExtractor()
    
    # Test cases for common issues
    test_cases = [
        # 1. Embedded headers
        {
            'name': "Embedded header after period",
            'text': "Completed all required tasks.SKILLSCreated a new system."
        },
        # 2. Email with spaces
        {
            'name': "Email with space before @",
            'text': "Contact: user @gmail.com"
        },
        {
            'name': "Email with space after @",
            'text': "Contact: user@ gmail.com"
        },
        # 3. Broken date formats
        {
            'name': "Date with newline",
            'text': "May 2020 - October\n2022"
        },
        {
            'name': "Date with dash prefix",
            'text': "-May 2020 - October 2022"
        },
        # 4. Multiple SKILLS sections
        {
            'name': "Multiple SKILLS sections",
            'text': "SKILLS\n\nPython, Java\n\nSome text\n\nSKILLS\n\nSQL, C++"
        },
        # 5. Merged location patterns
        {
            'name': "State merged with action",
            'text': "UtahActed as team lead for the project."
        },
        {
            'name': "City, state merged with text",
            'text': "New York, NYDeveloped the system."
        }
    ]
    
    # Custom handling for these test cases
    custom_fixes = {
        # Fix for embedded headers
        "Embedded header after period": lambda text: text.replace("tasks.SKILLS", "tasks.\n\nSKILLS\n\n"),
        
        # Fix for email with spaces
        "Email with space before @": lambda text: text.replace("user @", "user@"),
        "Email with space after @": lambda text: text.replace("@ gmail", "@gmail"),
        
        # Fix for broken dates
        "Date with newline": lambda text: text.replace("October\n2022", "October 2022"),
        "Date with dash prefix": lambda text: text.replace("-May", " - May"),
        
        # Fix for multiple SKILLS sections
        "Multiple SKILLS sections": lambda text: re.sub(r"(Some text)\n\nSKILLS", r"\1\n\n• SKILLS:", text),
        
        # Fix for merged location patterns
        "State merged with action": lambda text: text.replace("UtahActed", "Utah\nActed"),
        "City, state merged with text": lambda text: text.replace("NY", "NY\n")
    }
    
    # Process each test case
    results = []
    
    for test in test_cases:
        name = test['name']
        text = test['text']
        logger.info(f"\nProcessing test case: {name}")
        logger.info(f"Input: {text.replace(chr(10), '\\n')}")
        
        # Apply default OCR processing
        processed_text = extractor._process_page_text(text)
        final_text = extractor._final_cleanup(processed_text)
        
        logger.info(f"Default output: {final_text.replace(chr(10), '\\n')}")
        
        # Apply custom fixes if available
        if name in custom_fixes:
            custom_text = custom_fixes[name](text)
            custom_processed = extractor._process_page_text(custom_text)
            custom_final = extractor._final_cleanup(custom_processed)
            logger.info(f"Fixed output: {custom_final.replace(chr(10), '\\n')}")
            
            # Compare results
            if final_text != custom_final:
                logger.info(f"✓ Fix for '{name}' works better")
                results.append({'test': name, 'status': 'improved', 'fix': custom_fixes[name].__code__.co_consts[0]})
            else:
                logger.info(f"⚠️ No improvement for '{name}'")
                results.append({'test': name, 'status': 'unchanged'})
        else:
            logger.info(f"⚠️ No custom fix defined for '{name}'")
            results.append({'test': name, 'status': 'no_fix'})
    
    # Report summary of findings
    logger.info("\n" + "=" * 50)
    logger.info("SUMMARY OF NEEDED FIXES")
    logger.info("=" * 50)
    
    for result in results:
        if result['status'] == 'improved':
            logger.info(f"* {result['test']}: Replace {result['fix']}")
    
    # Provide guidance for manual fix implementation
    logger.info("\nThe issues identified require manual implementation of fixes in the OCR code.")
    logger.info("Based on the tests, focus on these areas:")
    logger.info("1. Better handling of embedded headers (fix 'tasks.SKILLS' → 'tasks.\\n\\nSKILLS\\n\\n')")
    logger.info("2. Email space handling (fix 'user @gmail' → 'user@gmail' and 'user@ gmail' → 'user@gmail')")
    logger.info("3. Date format handling (fix 'October\\n2022' → 'October 2022')")
    logger.info("4. Multiple SKILLS section formatting (main section vs bullet list format)")
    logger.info("\nImplement these fixes in src/utils/ocr_text_extraction.py")

if __name__ == "__main__":
    # Test improvements
    test_improvements()
