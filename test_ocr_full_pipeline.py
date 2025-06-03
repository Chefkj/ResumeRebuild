#!/usr/bin/env python3
"""
Integration test for the complete OCR text extraction and section extraction pipeline.

This script tests the full resume parsing pipeline from PDF to structured sections,
focusing on the integration between OCR text extraction and section extraction with
proper handling of merged text patterns and embedded headers.
"""

import os
import sys
import logging
import time
import argparse
from pprint import pprint
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the required components
from src.utils.ocr_text_extraction import OCRTextExtractor
from src.utils.ocr_section_extractor_improved import OCRSectionExtractorImproved
from src.utils.text_utils import extract_contact_info, detect_broken_lines, fix_broken_lines

def test_full_pipeline(pdf_path):
    """
    Test the complete OCR text extraction and section extraction pipeline.
    
    Args:
        pdf_path: Path to the test PDF file
    """
    logger.info(f"Testing full OCR pipeline on PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"Test PDF not found at: {pdf_path}")
        return
    
    # Create extractors
    ocr_extractor = OCRTextExtractor()
    section_extractor = OCRSectionExtractorImproved()
    
    # 1. Extract raw OCR text
    logger.info("Step 1: Extracting raw text using OCR...")
    start_time = time.time()
    extracted_text = ocr_extractor.extract_text(pdf_path)
    ocr_time = time.time() - start_time
    logger.info(f"OCR extraction completed in {ocr_time:.2f} seconds")
    
    # Save raw OCR text for inspection
    raw_ocr_path = f"{os.path.splitext(pdf_path)[0]}_raw_ocr.txt"
    with open(raw_ocr_path, 'w', encoding='utf-8') as f:
        f.write(extracted_text)
    logger.info(f"Raw OCR text saved to: {raw_ocr_path}")
    
    # 2. Use OCR section extractor to get structured sections
    logger.info("\nStep 2: Extracting sections from OCR text...")
    start_time = time.time()
    sections = section_extractor.extract_sections(pdf_path)
    section_time = time.time() - start_time
    logger.info(f"Section extraction completed in {section_time:.2f} seconds")
    
    # 3. Validate sections
    logger.info("\nStep 3: Validating extracted sections...")
    
    # Check for expected sections
    expected_sections = [
        'SUMMARY', 'EXPERIENCE', 'EDUCATION', 'SKILLS', 
        'PROJECTS', 'CERTIFICATIONS', 'CONTACT'
    ]
    
    found_sections = []
    for section_key, section_data in sections.items():
        section_type = section_data['type'].upper()
        display_name = section_data['display_name'].upper()
        
        # Check if this section matches any expected section
        for expected in expected_sections:
            if expected in section_type or expected in display_name:
                found_sections.append(expected)
                break
    
    # Report on found sections
    logger.info("\nSection detection results:")
    logger.info("-" * 40)
    for section in expected_sections:
        status = "✓" if section in found_sections else "✗"
        logger.info(f"{status} {section}")
    
    # Calculate percentage of expected sections found
    found_pct = (len(found_sections) / len(expected_sections)) * 100
    logger.info(f"\nDetected {len(found_sections)} of {len(expected_sections)} expected sections ({found_pct:.1f}%)")
    
    # 4. Check for specific pattern fixes
    logger.info("\nStep 4: Checking for specific pattern fixes...")
    
    # Patterns to check in the extracted text
    patterns_to_check = {
        "Merged location patterns": r"(?:Utah|Texas|Florida|California)(?=[A-Z][a-z]+ed\b)",
        "Multiple SKILLS headers": r"SKILLS.*SKILLS",
        "Embedded headers": r"[a-z](EXPERIENCE|EDUCATION|SKILLS|SUMMARY)[a-zA-Z]",
        "Email formatting": r"\S@\s+\S",
        "Broken date formats": r"\d{4}\s*-\s*[A-Za-z]+\s*\n\d{4}",
    }
    
    # Check each pattern
    pattern_results = {}
    for description, pattern in patterns_to_check.items():
        matches = re.findall(pattern, extracted_text)
        pattern_results[description] = len(matches) == 0  # True if no matches (issue fixed)
    
    # Report pattern check results
    logger.info("\nPattern fix verification:")
    logger.info("-" * 40)
    all_patterns_fixed = True
    for description, is_fixed in pattern_results.items():
        status = "✓" if is_fixed else "✗"
        logger.info(f"{status} {description}")
        all_patterns_fixed = all_patterns_fixed and is_fixed
    
    # 5. Check contact information extraction
    logger.info("\nStep 5: Checking contact information extraction...")
    
    contact_info = extract_contact_info(extracted_text)
    logger.info("Extracted contact information:")
    for key, value in contact_info.items():
        status = "✓" if value is not None else "✗"
        logger.info(f"{status} {key}: {value}")
    
    # 6. Verify broken line detection and fixing
    logger.info("\nStep 6: Checking broken line detection and fixing...")
    
    # Insert a test case with known broken lines in the text
    test_text = "This is a broken\nline that should be joined. This is\nanother example."
    fixed_text = fix_broken_lines(test_text)
    broken_lines_fixed = "broken line" in fixed_text and "another example" in fixed_text
    
    logger.info(f"{'✓' if broken_lines_fixed else '✗'} Broken line detection and fixing")
    
    # 7. Report overall results
    logger.info("\n" + "=" * 50)
    logger.info("OVERALL PIPELINE TEST RESULTS")
    logger.info("=" * 50)
    
    # Calculate overall scores
    section_score = found_pct / 100
    pattern_score = sum(1 for fixed in pattern_results.values() if fixed) / len(pattern_results)
    contact_score = sum(1 for val in contact_info.values() if val is not None) / len(contact_info)
    
    # Show component scores
    logger.info(f"OCR Text Extraction:    {100 * pattern_score:.1f}%")
    logger.info(f"Section Extraction:     {found_pct:.1f}%")
    logger.info(f"Contact Info Detection: {100 * contact_score:.1f}%")
    
    # Calculate weighted overall score
    overall_score = (pattern_score * 0.4) + (section_score * 0.4) + (contact_score * 0.2)
    logger.info(f"\nOverall Pipeline Score: {100 * overall_score:.1f}%")
    
    # Final verdict
    if overall_score >= 0.8:
        logger.info("\n✅ Pipeline test PASSED - Good quality OCR extraction")
    elif overall_score >= 0.6:
        logger.info("\n⚠️ Pipeline test PARTIAL - Acceptable but needs improvement")
    else:
        logger.info("\n❌ Pipeline test FAILED - Poor quality OCR extraction")
    
    # Return sections for further inspection
    return sections

def display_section_details(sections):
    """
    Display detailed information about extracted sections.
    
    Args:
        sections: Dictionary of extracted sections
    """
    logger.info("\nDETAILED SECTION ANALYSIS")
    logger.info("=" * 50)
    
    for section_key, section_data in sections.items():
        logger.info(f"\nSECTION: {section_data['display_name']} ({section_data['type']})")
        logger.info(f"Confidence: {section_data['confidence']:.2f}")
        
        # For debugging, get content preview
        content = section_data['content']
        content_preview = content[:100] + "..." if len(content) > 100 else content
        content_preview = content_preview.replace("\n", "\\n ")
        
        logger.info(f"Content preview: {content_preview}")
        logger.info(f"Content length: {len(content)} characters")
        
        # Check for issues in each section's content
        issues = []
        
        # Check for merged text patterns in this section
        if any(re.search(r"(?:Utah|Texas|Florida|California)([A-Z][a-z]+ed\b)", content)):
            issues.append("Contains merged location patterns")
            
        # Check for embedded headers
        if any(re.search(rf"[a-z]({header})[a-zA-Z]", content) 
               for header in ['EXPERIENCE', 'EDUCATION', 'SKILLS', 'SUMMARY']):
            issues.append("Contains embedded headers")
            
        # Check for broken dates
        if re.search(r"\d{4}\s*-\s*[A-Za-z]+\s*\n\d{4}", content):
            issues.append("Contains broken date formats")
            
        if issues:
            logger.info(f"Issues detected: {', '.join(issues)}")
        else:
            logger.info("No issues detected in this section")
    
    logger.info("\n" + "=" * 50)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the full OCR pipeline")
    parser.add_argument("--pdf", default="/Users/kj/ResumeRebuild/sample_resume.pdf", 
                       help="Path to PDF for OCR testing")
    parser.add_argument("--detailed", action="store_true", 
                       help="Show detailed section analysis")
    args = parser.parse_args()
    
    # Run the pipeline test
    sections = test_full_pipeline(args.pdf)
    
    # Show detailed analysis if requested
    if args.detailed and sections:
        display_section_details(sections)
    
    logger.info("\nTest completed!")
