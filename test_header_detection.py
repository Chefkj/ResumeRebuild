#!/usr/bin/env python3
"""
Test script specifically for header detection in sequential text ordering.

This script focuses on testing the proper identification of section headers,
particularly the case of "OBJECTIVE" vs "objectives".
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.sequential_text_ordering import apply_sequential_ordering, SequentialTextOrderer
from src.utils.sequential_text_ordering import TextBlock

def test_objective_detection():
    """Test specifically the detection of OBJECTIVE vs objectives."""
    print("\n=== Testing Header Detection for OBJECTIVE ===\n")
    
    # Case 1: "OBJECTIVE" as a proper header (wrapped in newlines)
    text1 = "\n\nSUMMARY\n\nExperienced software engineer.\n\nOBJECTIVE\n\nTo find a challenging position."
    
    # Case 2: "objectives" in a sentence (should not be treated as a header)
    text2 = "\n\nSUMMARY\n\nExperienced software engineer.\n\n• Boosted production with automation to achieve objectives with lower material requirements."
    
    # Case 3: The problematic case from OCR: "OBJECTIVE\ns with lower..."
    text3 = "\n\nSUMMARY\n\nEnthusiastic Computer Scientist promotes excellent prioritization and organizational\n\nOBJECTIVE\n\ns with lower material and time requirements."
    
    print("Case 1: Proper OBJECTIVE header")
    result1 = apply_sequential_ordering(text1)
    has_objective_header1 = "OBJECTIVE" in result1.split("SUMMARY")[1][:20]
    print(f"Header detected correctly: {'Yes' if has_objective_header1 else 'No'}")
    print(f"Result: {result1[:100]}...\n")
    
    print("Case 2: 'objectives' in a sentence")
    result2 = apply_sequential_ordering(text2)
    has_objective_header2 = "OBJECTIVE" in result2.split("SUMMARY")[1][:20]
    print(f"False header avoided correctly: {'Yes' if not has_objective_header2 else 'No'}")
    print(f"Result: {result2[:100]}...\n")
    
    print("Case 3: Problematic OCR split 'OBJECTIVE\\ns with lower...'")
    result3 = apply_sequential_ordering(text3)
    has_objective_header3 = "OBJECTIVE" in result3.split("SUMMARY")[1][:20]
    print(f"OCR split handled correctly: {'Yes' if not has_objective_header3 else 'No'}")
    print(f"Result: {result3[:100]}...\n")
    
    # Blocks test for more direct control
    print("Testing with direct TextBlock manipulation:")
    orderer = SequentialTextOrderer()
    
    # Create text blocks for the problematic case
    block1 = TextBlock("OBJECTIVE", 0, 100, 100, 20, 0)
    block2 = TextBlock("s with lower material and time requirements.", 0, 120, 300, 20, 0)
    
    # Process the blocks
    blocks = [block1, block2]
    orderer._identify_headers(blocks)
    
    # Check if block1 was identified as a header
    print(f"OBJECTIVE identified as header: {block1.is_header}")
    print(f"Expected: False (should not be a header when followed by 's with lower...')")

if __name__ == "__main__":
    test_objective_detection()
