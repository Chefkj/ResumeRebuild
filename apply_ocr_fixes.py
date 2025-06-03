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

def apply_fixes_to_ocr_extraction():
    """Apply fixes to the OCR extraction code to address test failures."""
    logger.info("Applying fixes to OCR text extraction...")
    
    # Path to the OCR text extraction file
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           'src/utils/ocr_text_extraction.py')
    
    # Read the current file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Fix embedded header handling (make the pattern more robust)
    # Original pattern uses simple matching but might miss cases with unexpected spacing or word breaking
    logger.info("1. Enhancing embedded header detection and formatting...")
    
    # Look for header pattern code
    embed_header_pattern = r'# Pattern 1: header immediately followed by text with no space\n.*?text = re\.sub\(fr\'({header})([A-Za-z])\', r\'\\1\\n\\n\\2\', text, flags=re\.IGNORECASE\)'
    
    improved_header_replacement = """# Pattern 1: header immediately followed by text with no space
            # Example: "EXPERIENCECompany Name" -> "EXPERIENCE\\n\\nCompany Name"
            text = re.sub(fr'({header})([A-Za-z0-9])', r'\\1\\n\\n\\2', text, flags=re.IGNORECASE)
            
            # Additional handling for period or other punctuation followed by header without space
            # Example: "details.SKILLS" -> "details.\\n\\nSKILLS"
            text = re.sub(fr'([.!?:;])({header})([A-Za-z0-9])?', r'\\1\\n\\n\\2\\n\\n\\3' if '\\3' else r'\\1\\n\\n\\2', text, flags=re.IGNORECASE)"""
    
    content = re.sub(embed_header_pattern, improved_header_replacement, content)
    
    # 2. Improve date format handling
    logger.info("2. Improving date format handling...")
    
    # Look for date format handling code
    date_format_pattern = r'# Fix for commonly broken date formats like "February 2018 - January\\n2020".*?r\'\1 \2 - \3 \4\', text\)'
    
    improved_date_replacement = """# Fix for commonly broken date formats like "February 2018 - January\\n2020"
        # Normalize full month names and abbreviations
        month_mapping = {'January': 'Jan', 'February': 'Feb', 'March': 'Mar', 'April': 'Apr',
                          'May': 'May', 'June': 'Jun', 'July': 'Jul', 'August': 'Aug',
                          'September': 'Sep', 'October': 'Oct', 'November': 'Nov', 'December': 'Dec'}
        
        # First pass - fix abbreviations consistently
        for full_name, abbr in month_mapping.items():
            text = re.sub(fr'\\b{full_name}\\b', abbr, text, flags=re.IGNORECASE)
        
        # Fix date format patterns more comprehensively
        text = re.sub(r'([A-Z][a-z]+)\\s+(\\d{4})\\s*-\\s*([A-Z][a-z]+)\\s*\\n(\\d{4})', 
                      r'\\1 \\2 - \\3 \\4', text)
                      
        # Also handle cases with spaces before the linebreak
        text = re.sub(r'([A-Z][a-z]+)\\s+(\\d{4})\\s*-\\s*([A-Z][a-z]+)\\s+\\n(\\d{4})', 
                      r'\\1 \\2 - \\3 \\4', text)
                      
        # Handle date with dash prefix comprehensively
        text = re.sub(r'-\\s*([A-Z][a-z]+)\\s+(\\d{4})\\s*-\\s*([A-Z][a-z]+)\\s*\\n(\\d{4})', 
                      r' - \\1 \\2 - \\3 \\4', text)
                      
        # Additional pattern for dates split across lines without dash
        text = re.sub(r'([A-Z][a-z]+)\\s+(\\d{4})\\n([A-Z][a-z]+)\\s+(\\d{4})', 
                      r'\\1 \\2 - \\3 \\4', text)"""
    
    content = re.sub(date_format_pattern, improved_date_replacement, content)
    
    # 3. Fix email space handling
    logger.info("3. Fixing email space pattern handling...")
    
    # Look for email space pattern
    email_pattern = r'# Fix email spaces.*?text = re\.sub\(r\'\(\S\)@\s+\(\S\)\', r\'\1@\2\', text\)'
    
    improved_email_replacement = """# Fix email spaces - comprehensive patterns
        # Fix spaces before @ symbol
        text = re.sub(r'(\\S)\\s+@\\s*(\\S)', r'\\1@\\2', text)
        # Fix spaces after @ symbol 
        text = re.sub(r'(\\S)@\\s+(\\S)', r'\\1@\\2', text)
        # Fix email space but preserve surrounding text
        text = re.sub(r'([a-zA-Z0-9._%+-]+)\\s*@\\s*([a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})', r'\\1@\\2', text)"""
    
    if email_pattern in content:
        content = content.replace(email_pattern, improved_email_replacement)
    else:
        # Add the improved email pattern in the final cleanup section
        final_cleanup_end = content.find("return text", content.find("def _final_cleanup"))
        if final_cleanup_end > 0:
            content = content[:final_cleanup_end] + improved_email_replacement + "\n        \n        " + content[final_cleanup_end:]
    
    # 4. Improve multiple SKILLS section handling
    logger.info("4. Enhancing multiple SKILLS section handling...")
    
    # Look for SKILLS handling code
    skills_pattern = r'# Pattern 5: Handle repeated section headers \(like multiple SKILLS sections\).*?next_section_pos = next_header_pos'
    
    improved_skills_replacement = """# Pattern 5: Handle repeated section headers (like multiple SKILLS sections)
                # Count occurrences of this header
                header_occurrences = len(re.findall(fr'\\b{header}\\b', text, re.IGNORECASE))
                if header_occurrences > 1:
                    # Process each occurrence to ensure proper separation
                    positions = [m.start() for m in re.finditer(fr'\\b{header}\\b', text, re.IGNORECASE)]
                    
                    # Keep track of the primary section (the one with most content)
                    primary_pos = positions[0]
                    primary_content_length = 0
                    
                    # Find the section with most content
                    for pos in positions:
                        # Find the end of the content for this section (next section or end of text)
                        next_section_pos = len(text)
                        for header_kw in self.section_headers:
                            # Skip the current header
                            if header_kw == header:
                                continue
                            next_header_pos = text.find(header_kw, pos + len(header))
                            if next_header_pos > pos and next_header_pos < next_section_pos:
                                next_section_pos = next_header_pos"""
    
    content = re.sub(skills_pattern, improved_skills_replacement, content)
    
    # 5. Fix the formatting for skills sections with improved sub-section handling
    skills_pattern2 = r'# Format as a subheader rather than removing.*?text = text\[:pos\] \+ text\[pos:line_end\]\.replace\(header, f"• {header}:"\) \+ text\[line_end:\]'
    
    improved_skills_replacement2 = """# Format as a subheader rather than removing
                                text = text[:pos] + "\\n• " + header + ":\\n" + text[line_end:]"""
    
    content = re.sub(skills_pattern2, improved_skills_replacement2, content)
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("Successfully applied fixes to OCR text extraction code.")

def run_tests_after_fixes():
    """Run test cases to verify the fixes."""
    logger.info("\nRunning tests to verify fixes...")
    
    # Test embedded header cases
    test_cases = [
        # Test embedded headers
        {
            'desc': 'Embedded header after period',
            'text': 'Completed all required tasks.SKILLSCreated a new system.',
            'expected_pattern': r'Completed all required tasks\.\s+SKILLS\s+Created'
        },
        # Test email spaces
        {
            'desc': 'Email with space before @',
            'text': 'Contact: user @gmail.com',
            'expected_pattern': r'Contact: user@gmail.com'
        },
        # Test date formats
        {
            'desc': 'Broken date with newline',
            'text': 'May 2020 - October\n2022',
            'expected_pattern': r'May 2020 - October 2022'
        },
        # Test multiple SKILLS sections
        {
            'desc': 'Multiple SKILLS sections',
            'text': 'SKILLS\n\nPython, Java\n\nSome text\n\nSKILLS\n\nSQL, C++',
            'expected_pattern': r'SKILLS\s+Python, Java\s+Some text\s+•\s+SKILLS:'
        }
    ]
    
    # Create OCR extractor
    extractor = OCRTextExtractor()
    
    # Run tests
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases):
        logger.info(f"\nTest {i+1}: {test['desc']}")
        logger.info(f"Input: {test['text'].replace(chr(10), '\\n')}")
        
        # Process text
        processed = extractor._process_page_text(test['text'])
        result = extractor._final_cleanup(processed)
        
        logger.info(f"Result: {result.replace(chr(10), '\\n')}")
        
        # Check if result matches expected pattern
        if re.search(test['expected_pattern'], result):
            logger.info("✓ PASSED")
            passed += 1
        else:
            logger.info("✗ FAILED")
            failed += 1
    
    # Show summary
    logger.info(f"\nTest summary: {passed} passed, {failed} failed")
    if failed == 0:
        logger.info("✅ All tests passed! Fixes were successful.")
    else:
        logger.info("⚠️ Some tests failed. Further improvements may be needed.")

if __name__ == "__main__":
    # Apply fixes
    apply_fixes_to_ocr_extraction()
    
    # Run tests to verify fixes
    run_tests_after_fixes()
