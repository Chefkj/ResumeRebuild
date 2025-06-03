#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Pattern Library

This script tests the pattern library functionality and performance.
"""

import logging
import sys
import time
from src.utils.pattern_library import PatternLibrary, initialize_standard_library

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_pattern_library():
    """
    Test the pattern library functionality with standard patterns.
    """
    logger.info("Testing Pattern Library...")
    
    # Initialize library with standard patterns
    library = initialize_standard_library()
    logger.info(f"Initialized library with {len(library.patterns)} patterns in {len(library.categories)} categories")
    
    # Test cases for each category
    test_cases = {
        "dates": [
            {
                "name": "Date with newline",
                "input": "May 2020 - October\n2022",
                "expected": "May 2020 - October 2022"
            },
            {
                "name": "Date with dash prefix",
                "input": "-May 2020 - October 2022",
                "expected": " - May 2020 - October 2022"
            },
            {
                "name": "Date with no spaces",
                "input": "May2020-October2022",
                "expected": "May 2020 - October 2022"
            },
            {
                "name": "Complex date range with multiple patterns",
                "input": "January2019-March\n2023",
                "expected": "January 2019 - March 2023"
            },
            {
                "name": "Present dates",
                "input": "June 2018 - Present",
                "expected": "June 2018 - Present"
            }
        ],
        "locations": [
            {
                "name": "State + verb past tense",
                "input": "UtahDeveloped new software solutions.",
                "expected": "Utah\nDeveloped new software solutions."
            },
            {
                "name": "State + verb present participle",
                "input": "CaliforniaManaging large teams.",
                "expected": "California\nManaging large teams."
            },
            {
                "name": "City + verb",
                "input": "Salt Lake CityDeveloped software.",
                "expected": "Salt Lake City\nDeveloped software."
            },
            {
                "name": "Complex location pattern",
                "input": "New YorkCreated marketing campaigns for Los AngelesClients.",
                "expected": "New York\nCreated marketing campaigns for Los Angeles\nClients."
            }
        ],
        "contact": [
            {
                "name": "Email with space before @",
                "input": "Contact: user @gmail.com",
                "expected": "Contact: user@gmail.com"
            },
            {
                "name": "Email with space after @",
                "input": "Contact: user@ gmail.com",
                "expected": "Contact: user@gmail.com"
            },
            {
                "name": "Email with spaces around @",
                "input": "Contact: user @ gmail.com",
                "expected": "Contact: user@gmail.com"
            },
            {
                "name": "Multiple email patterns",
                "input": "Contact: first.last @ company.com or another.user@ example.com",
                "expected": "Contact: first.last@company.com or another.user@example.com"
            }
        ],
        "headers": [
            {
                "name": "Embedded SKILLS header",
                "input": "Completed tasks.SKILLS section follows.",
                "expected": "Completed tasks.\n\nSKILLS section follows."
            },
            {
                "name": "Embedded EXPERIENCE header",
                "input": "Previous work.EXPERIENCE section follows.",
                "expected": "Previous work.\n\nEXPERIENCE section follows."
            }
        ],
        "special_cases": [
            {
                "name": "Name with KU prefix",
                "input": "JOHN DOE KUPortland",
                "expected": "JOHN DOE\nPortland"
            },
            {
                "name": "COWEN JR pattern",
                "input": "COWENJRKUMillcreek, UT 84106",
                "expected": "COWEN JR\nMillcreek, UT 84106"
            }
        ]
    }
    
    # Test each category
    total_passed = 0
    total_tests = 0
    
    for category, cases in test_cases.items():
        logger.info(f"\n=== Testing Category: {category} ===")
        
        for test in cases:
            total_tests += 1
            name = test["name"]
            input_text = test["input"]
            expected = test["expected"]
            
            logger.info(f"\nTest: {name}")
            logger.info(f"Input: {input_text.replace(chr(10), '\\n')}")
            
            # Apply patterns from this category
            start_time = time.time()
            result = library.apply_category(input_text, category)
            end_time = time.time()
            
            logger.info(f"Output: {result.replace(chr(10), '\\n')}")
            logger.info(f"Processing time: {(end_time - start_time)*1000:.2f}ms")
            
            # Check if result matches expected
            if expected in result:
                logger.info(f"✅ PASS: Found expected pattern '{expected.replace(chr(10), '\\n')}'")
                total_passed += 1
            else:
                logger.info(f"❌ FAIL: Expected '{expected.replace(chr(10), '\\n')}' not found in '{result.replace(chr(10), '\\n')}'")
    
    # Show performance report
    logger.info("\n=== Pattern Library Performance Report ===")
    library.print_performance_report()
    
    # Show summary
    logger.info(f"\n=== TEST SUMMARY ===")
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {total_passed}")
    logger.info(f"Failed: {total_tests - total_passed}")
    success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    logger.info(f"Success Rate: {success_rate:.2f}%")

if __name__ == "__main__":
    test_pattern_library()
