#!/usr/bin/env python3
"""
Test script for sequential ordering improvements

This script specifically tests the sequential ordering improvements
to ensure we don't mistakenly identify words like "objectives" as section headers.
"""

import sys
import os
from src.utils.sequential_text_ordering import apply_sequential_ordering

# The problematic text from the OCR extraction
problem_text = """SUMMARY

Enthusiastic Computer Scientist promotes excellent prioritization and organizational

OBJECTIVE

s with lower material and time requirements.

> Helped department stay on top of student and faculty needs with skilled clerical Support.

© Provided clerical Support services to staff.
"""

# The correct text - where "objectives" is part of a sentence
correct_text = """SUMMARY

Enthusiastic Computer Scientist promotes excellent prioritization and organizational skills.

EXPERIENCE

Work Study Intern
Western Governors University | Salt Lake City, Utah, United States 
• Boosted production with automation to achieve objectives with lower material and time requirements.
• Helped department stay on top of student and faculty needs with skilled clerical Support.
• Provided clerical Support services to staff.
"""

def test_sequential_ordering_fix():
    """Test our fix for the 'OBJECTIVE' section issue."""
    print("=== Testing Sequential Ordering Fix for OBJECTIVE ===\n")
    
    # Apply sequential ordering to the problem text
    print("Before Fix - Problem Text:")
    print(problem_text)
    print("\nAfter Sequential Ordering:")
    ordered_text = apply_sequential_ordering(problem_text)
    print(ordered_text)
    
    # Check if "OBJECTIVE" is still treated as a header
    if "OBJECTIVE\n\ns" in ordered_text or "OBJECTIVE\n\nS" in ordered_text:
        print("\nFAILED: 'OBJECTIVE' is still being treated as a header.")
    else:
        print("\nSUCCESSFUL: 'OBJECTIVE' is no longer treated as a header.")
    
    # Test with correct text to ensure we don't break valid headers
    print("\n=== Testing with Correct Text ===\n")
    correct_ordered_text = apply_sequential_ordering(correct_text)
    
    # Check if "SUMMARY" and "EXPERIENCE" are still properly identified as headers
    if "SUMMARY\n\n" in correct_ordered_text and "EXPERIENCE\n\n" in correct_ordered_text:
        print("SUCCESSFUL: Valid section headers are still correctly identified.")
    else:
        print("FAILED: Valid section headers are no longer being identified properly.")
    
    print("\nOrdered Correct Text:")
    print(correct_ordered_text)

if __name__ == "__main__":
    test_sequential_ordering_fix()
