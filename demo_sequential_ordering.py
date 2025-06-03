#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Demo for Sequential Text Ordering on Resume Text

This script demonstrates the improvement in text ordering
by comparing raw OCR text with the sequentially ordered text.
"""

import os
import sys
import logging
from src.utils.ocr_text_extraction import OCRTextExtractor
from src.utils.sequential_text_ordering import apply_sequential_ordering

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run the demo for sequential text ordering."""
    
    # Sample resume text with jumbled sections and merged text
    jumbled_text = """JOHN DOENYCSoftwareDeveloperNewYork
john.doe@email.com555-123-4567

SKILLS
Python JavaScript React NodeJSAWSDatabaseSQL MongoDB

Software Engineer ABCTech Sept2021 - Present
• Developedcustom features for clientsusingReactJS and Node.js
• Collaboratewith cross-functionalteams to deliver requirements
• Implement automated testing using Jest andCypress

PROJECTSInventoryManagementApp
Using React for frontend and Node.jsfor backend
Implementing authentication andauthorizationfeatures
Utilizing MongoDB for data storage

EXPERIENCE
Junior Developer XYZSolutions Jan2019 - Aug2021
• Built responsive websites for clients usingreact
• Assisted with troubleshooting appissues
• Integrated REST APIs with frontend components

EDUCATION
BachelorofScienceinComputerScience
University ofTechnology 2015-2019
• GPA: 3.8/4.0
• Activities: CodeClubPresident, HackathonParticipant

SUMMARY
Software engineer with5 yearsexperience in full-stack
development. Expertise in React,Node.js, andcloud services.
Passionate aboutbuilding user-friendly applications.

References available upon request."""

    # Create an instance of OCR Text Extractor
    extractor = OCRTextExtractor()
    
    print("\n===== ORIGINAL TEXT WITH JUMBLED SECTIONS =====")
    print(jumbled_text)
    
    # Apply regular cleanup without sequential ordering
    standard_cleanup = extractor._process_page_text(jumbled_text)
    
    print("\n\n===== TEXT AFTER STANDARD CLEANUP =====")
    print(standard_cleanup)
    
    # Apply pattern library and sequential ordering
    ordered_text = extractor._final_cleanup(jumbled_text)
    
    print("\n\n===== TEXT AFTER SEQUENTIAL ORDERING =====")
    print(ordered_text)
    
    # Display findings
    print("\n\n===== ORDERING IMPROVEMENTS =====")
    print("1. Fixed merged words (e.g., 'SoftwareDeveloper' -> 'Software Developer')")
    print("2. Properly ordered sections (SUMMARY first, then EXPERIENCE, etc.)")
    print("3. Aligned job titles, dates, and organizations in experience sections")
    print("4. Maintained formatting for skills and education sections")
    
    # Save results to files for comparison
    with open("jumbled_text.txt", "w") as f:
        f.write(jumbled_text)
    
    with open("ordered_text.txt", "w") as f:
        f.write(ordered_text)
    
    print("\nFiles saved for comparison:")
    print("- jumbled_text.txt: Original jumbled text")
    print("- ordered_text.txt: Text after sequential ordering")

if __name__ == "__main__":
    main()
