#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test for Sequential Text Ordering Integration with OCR Text Extractor
"""

import os
import sys
import unittest
import logging
from src.utils.ocr_text_extraction import OCRTextExtractor
from src.utils.sequential_text_ordering import apply_sequential_ordering, SequentialTextOrderer

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestSequentialTextOrdering(unittest.TestCase):
    """Tests for the sequential text ordering functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.ocr_extractor = OCRTextExtractor()
        self.text_orderer = SequentialTextOrderer()
        
        # Sample unordered resume text with common ordering issues
        self.unordered_text = """
JOHN DOE
john.doe@example.com | 555-123-4567 | New York, NY

TECHNICAL SKILLS
Programming: Python, JavaScript, Java, C++
Database: SQL, MongoDB, Redis
Web: HTML, CSS, React, Vue.js
Tools: Git, Docker, Kubernetes, Jenkins

WORK HISTORY
Software Engineer II
ABC Corporation | New York, NY | 2019 - Present
• Developed and maintained RESTful APIs using Python Django
• Implemented CI/CD pipeline using Jenkins and Docker
• Reduced API response time by 30% through code optimization

EDUCATION
Bachelor of Science in Computer Science
University of Technology | Boston, MA | 2015 - 2019
• GPA: 3.8/4.0
• Relevant Coursework: Data Structures, Algorithms, Database Systems

Frontend Developer
XYZ Company | Boston, MA | 2018 - 2019
• Designed and implemented responsive UI using React
• Collaborated with UX team to improve user experience
• Maintained code quality through unit and integration tests

SUMMARY
Software engineer with 5 years of experience in full-stack development.
Skilled in Python, JavaScript, and cloud technologies. Passionate about
building scalable and maintainable applications.

Project Lead
DEF Startup | Remote | 2017 - 2018
• Led a team of 3 developers in building a mobile application
• Coordinated with stakeholders to define project requirements
• Delivered the project on time and within budget

CERTIFICATIONS
AWS Certified Developer - Associate
Google Cloud Professional Developer
Microsoft Certified: Azure Developer Associate
"""

    def test_sequential_text_ordering(self):
        """Test that sequential text ordering works correctly."""
        # Apply sequential ordering directly
        ordered_text = apply_sequential_ordering(self.unordered_text)
        
        # Verify sections appear in logical order
        self.assertLess(ordered_text.find("SUMMARY"), ordered_text.find("WORK HISTORY"),
                        "Summary should appear before Work History")
        self.assertLess(ordered_text.find("SUMMARY"), ordered_text.find("EDUCATION"),
                        "Summary should appear before Education")
        self.assertLess(ordered_text.find("WORK HISTORY"), ordered_text.find("EDUCATION"),
                        "Work History should appear before Education")
        self.assertLess(ordered_text.find("EDUCATION"), ordered_text.find("CERTIFICATIONS"),
                        "Education should appear before Certifications")

    def test_integration_with_ocr_extractor(self):
        """Test that OCR extractor integrates sequential text ordering correctly."""
        # Apply the full OCR pipeline's final cleanup to the text
        processed_text = self.ocr_extractor._final_cleanup(self.unordered_text)
        
        # Verify the same ordering expectations after final cleanup
        self.assertLess(processed_text.find("SUMMARY"), processed_text.find("WORK HISTORY"),
                        "Summary should appear before Work History")
        self.assertLess(processed_text.find("SUMMARY"), processed_text.find("EDUCATION"),
                        "Summary should appear before Education")
        self.assertLess(processed_text.find("WORK HISTORY"), processed_text.find("EDUCATION"),
                        "Work History should appear before Education")
        self.assertLess(processed_text.find("EDUCATION"), processed_text.find("CERTIFICATIONS"),
                        "Education should appear before Certifications")

    def test_text_blocks_ordering(self):
        """Test that text blocks within sections are properly ordered."""
        # Create a sample text with out-of-order work history entries
        work_history_test = """
WORK HISTORY

Software Engineer II
ABC Corporation | New York, NY | 2019 - Present
• Developed and maintained RESTful APIs using Python Django

Frontend Developer
XYZ Company | Boston, MA | 2018 - 2019
• Designed and implemented responsive UI using React

Project Lead
DEF Startup | Remote | 2017 - 2018
• Led a team of 3 developers in building a mobile application
"""
        
        # Apply sequential ordering
        ordered_text = apply_sequential_ordering(work_history_test)
        
        # Check that entries are in reverse chronological order (most recent first)
        self.assertLess(ordered_text.find("2019 - Present"), ordered_text.find("2018 - 2019"),
                        "Most recent job should appear first")
        self.assertLess(ordered_text.find("2018 - 2019"), ordered_text.find("2017 - 2018"),
                        "Jobs should be in reverse chronological order")


if __name__ == "__main__":
    unittest.main()
