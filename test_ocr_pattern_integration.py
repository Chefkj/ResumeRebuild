#!/usr/bin/env python3
"""
Test script for the integrated OCR pattern library.

This script tests the integration of the pattern library with the OCR text extraction
module to ensure that patterns are applied correctly and efficiently.
"""

import os
import sys
import logging
import time
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import test patterns
from src.utils.ocr_text_extraction import OCRTextExtractor
from src.utils.pattern_library import initialize_standard_library

def test_integrated_pattern_library():
    """Test the integration of the pattern library with OCR text extraction."""
    logger.info("Testing OCR Pattern Library Integration...")
    
    # Initialize OCR text extractor
    ocr = OCRTextExtractor()
    
    # Test cases for different pattern categories
    test_cases = {
        "dates": [
            "May 2020 - October\n2022",
            "-May 2020 - October 2022",
            "May2020-October2022",
            "January2019-March\n2023",
            "June 2018 - Present"
        ],
        "locations": [
            "UtahDeveloped new software solutions.",
            "CaliforniaManaging large teams.",
            "Salt Lake CityDeveloped software.",
            "New YorkCreated marketing campaigns for Los AngelesClients."
        ],
        "contact": [
            "Contact: user @gmail.com",
            "Contact: user@ gmail.com",
            "Contact: user @ gmail.com",
            "Contact: first.last @ company.com or another.user@ example.com"
        ],
        "headers": [
            "Completed tasksSKILLS section follows.",
            "Previous workEXPERIENCE section follows.",
            "Completed tasks.SKILLS section follows.",
            "Previous work.EXPERIENCE section follows."
        ],
        "special_cases": [
            "JOHN DOE KUPortland",
            "COWENJRKUMillcreek, UT 84106"
        ]
    }
    
    logger.info("Testing OCR text cleanup with pattern library integration...")
    
    # Test all categories together
    combined_test = """JOHN DOE KUPortland, OR
SUMMARY
Enthusiastic Computer Scientist with experience in software development.

EXPERIENCE
May2020-October2022
Software DeveloperActed as first point of contact for customer support.
• Managed client issues and escalated technical problems.

UtahDeveloped many projects, including:
• System monitoring applications
• Database integration APIs
CaliforniaManaging technical debt.

SKILLS
• Python, Java, SQL
tasks.SKILLS for cloud platforms:
• AWS, Azure, GCP

Contact: user @ gmail.com | 555-123-4567 | linkedin.com/in/ johnsmith"""

    start_time = time.time()
    processed = ocr._final_cleanup(combined_test)
    end_time = time.time()
    
    logger.info("\nOriginal Text:")
    logger.info("-" * 60)
    logger.info(combined_test.replace('\n', '\\n'))
    
    logger.info("\nProcessed Text:")
    logger.info("-" * 60)
    logger.info(processed.replace('\n', '\\n'))
    
    logger.info(f"\nProcessing time: {(end_time - start_time)*1000:.2f}ms")
    
    # Check performance stats
    logger.info("\nPattern Library Performance Report:")
    ocr.pattern_library.print_performance_report()
    
    # Test individual categories
    logger.info("\nTesting individual pattern categories...")
    
    for category, cases in test_cases.items():
        logger.info(f"\n=== Testing Category: {category} ===")
        
        for i, test_input in enumerate(cases):
            # Apply the _final_cleanup method which uses the pattern library
            result = ocr._final_cleanup(test_input)
            
            logger.info(f"Test {i+1}:")
            logger.info(f"Input:  {test_input.replace(chr(10), '\\n')}")
            logger.info(f"Output: {result.replace(chr(10), '\\n')}")
            logger.info("-" * 40)

if __name__ == "__main__":
    test_integrated_pattern_library()
