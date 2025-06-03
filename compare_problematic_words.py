#!/usr/bin/env python3
"""
Compare OCR Methods for Problematic Words

This script specifically compares how different OCR methods handle problematic words
that are consistently misrecognized, such as "diplomacy" being read as "Ciplomacy" 
and "millcreek" being read as "villereek".

It compares:
1. Traditional OCR
2. Raw OCR
3. The new targeted OCR approach
"""

import os
import sys
import time
import subprocess
import argparse
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_problematic_regions(pdf_path, output_dir="."):
    """
    Run traditional OCR and extract regions with problematic words
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save output files
    
    Returns:
        tuple: (output_file_path, list of problematic regions)
    """
    # Run traditional OCR and get output file
    ocr_output_file = run_traditional_ocr(pdf_path, output_dir)
    
    # Get the problematic words from file
    with open(ocr_output_file, "r", encoding="utf-8") as f:
        ocr_text = f.read()
    
    # Define known problematic words and their correct versions
    problematic_words = {
        "ciplomacy": "diplomacy",
        "Ciplomacy": "Diplomacy",
        "villereek": "millcreek",
        "Villereek": "Millcreek"
    }
    
    # Collect regions with problematic words (including surrounding context)
    problem_regions = []
    
    # Extract context around each problematic word
    for prob_word in problematic_words:
        # Find all occurrences
        for match in re.finditer(r'\b' + re.escape(prob_word) + r'\b', ocr_text):
            start = max(0, match.start() - 100)  # 100 chars before
            end = min(len(ocr_text), match.end() + 100)  # 100 chars after
            
            # Extract region with context
            region = ocr_text[start:end].strip()
            correct_word = problematic_words[prob_word]
            
            problem_regions.append({
                'region': region,
                'problem_word': prob_word,
                'correct_word': correct_word,
                'position': match.start()
            })
    
    return ocr_output_file, problem_regions

def run_targeted_ocr(pdf_path, output_dir="."):
    """
    Run the targeted OCR improvement script
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_targeted_ocr_{timestamp}.txt")
    
    cmd = ["python", "targeted_ocr_improvement.py", pdf_path, "--output", output_dir]
    try:
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(process.stdout)
        
        # Find the latest targeted OCR file
        files = [f for f in os.listdir(output_dir) if f.startswith(f"{base_name}_targeted_ocr_")]
        if files:
            latest_file = os.path.join(output_dir, max(files))
            return latest_file
        else:
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error running targeted OCR: {e}")
        return None

def run_traditional_ocr(pdf_path, output_dir="."):
    """
    Run traditional OCR and return the output file path
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_trad_ocr_{timestamp}.txt")
    
    cmd = ["python", "traditional_ocr.py", pdf_path, "--output", output_dir]
    try:
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(process.stdout)
        
        # Find the latest traditional OCR file
        files = [f for f in os.listdir(output_dir) if f.startswith(f"{base_name}_trad_ocr_")]
        if files:
            latest_file = os.path.join(output_dir, max(files))
            return latest_file
        else:
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error running traditional OCR: {e}")
        return None

def run_raw_ocr(pdf_path, output_dir="."):
    """
    Run raw OCR with PSM 4 and return the output file path
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_raw_ocr_{timestamp}.txt")
    
    cmd = ["python", "test_raw_ocr_extraction.py", pdf_path, "--output", output_dir, "--mode", "psm4"]
    try:
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(process.stdout)
        
        # Find the latest raw OCR file
        files = [f for f in os.listdir(output_dir) if f.startswith(f"{base_name}_raw_ocr_")]
        if files:
            latest_file = os.path.join(output_dir, max(files))
            return latest_file
        else:
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error running raw OCR: {e}")
        return None

def compare_results(problematic_regions, trad_file, raw_file, targeted_file):
    """
    Compare how each method handles the problematic regions
    
    Args:
        problematic_regions: List of problematic regions
        trad_file: Traditional OCR output file
        raw_file: Raw OCR output file
        targeted_file: Targeted OCR output file
    """
    # Read the output files
    try:
        with open(trad_file, "r", encoding="utf-8") as f:
            trad_text = f.read()
    except:
        trad_text = ""
        
    try:
        with open(raw_file, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except:
        raw_text = ""
    
    try:
        with open(targeted_file, "r", encoding="utf-8") as f:
            targeted_text = f.read()
    except:
        targeted_text = ""
    
    print("\n=== COMPARISON OF PROBLEMATIC WORDS ===\n")
    print(f"{'Problem Word':<15} {'Correct Word':<15} {'Trad OCR':<10} {'Raw OCR':<10} {'Targeted OCR':<12}")
    print("-" * 65)
    
    # Count overall successes
    trad_success = 0
    raw_success = 0
    targeted_success = 0
    total_problems = 0
    
    # Check for each problem word
    checked_words = set()
    for region in problematic_regions:
        prob_word = region['problem_word']
        corr_word = region['correct_word']
        
        # Skip words we've already checked
        if prob_word in checked_words:
            continue
            
        checked_words.add(prob_word)
        total_problems += 1
        
        # Count instances in each text
        trad_prob_count = len(re.findall(r'\b' + re.escape(prob_word) + r'\b', trad_text))
        trad_corr_count = len(re.findall(r'\b' + re.escape(corr_word) + r'\b', trad_text))
        
        raw_prob_count = len(re.findall(r'\b' + re.escape(prob_word) + r'\b', raw_text))
        raw_corr_count = len(re.findall(r'\b' + re.escape(corr_word) + r'\b', raw_text))
        
        targeted_prob_count = len(re.findall(r'\b' + re.escape(prob_word) + r'\b', targeted_text))
        targeted_corr_count = len(re.findall(r'\b' + re.escape(corr_word) + r'\b', targeted_text))
        
        # Determine success (if more correct than problematic, but also not zero)
        trad_status = "✓" if trad_corr_count > trad_prob_count and trad_corr_count > 0 else "✗"
        raw_status = "✓" if raw_corr_count > raw_prob_count and raw_corr_count > 0 else "✗"
        targeted_status = "✓" if targeted_corr_count > targeted_prob_count and targeted_corr_count > 0 else "✗"
        
        # Count successes
        if trad_status == "✓":
            trad_success += 1
        if raw_status == "✓":
            raw_success += 1
        if targeted_status == "✓":
            targeted_success += 1
            
        print(f"{prob_word:<15} {corr_word:<15} {trad_status:<10} {raw_status:<10} {targeted_status:<12}")
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Total problematic words checked: {total_problems}")
    print(f"Traditional OCR success rate: {trad_success}/{total_problems} ({trad_success/total_problems*100:.1f}%)")
    print(f"Raw OCR success rate: {raw_success}/{total_problems} ({raw_success/total_problems*100:.1f}%)")
    print(f"Targeted OCR success rate: {targeted_success}/{total_problems} ({targeted_success/total_problems*100:.1f}%)")
    
    # Print overall word counts
    trad_words = len(trad_text.split())
    raw_words = len(raw_text.split())
    targeted_words = len(targeted_text.split())
    
    print("\n=== OVERALL WORD COUNT ===")
    print(f"Traditional OCR: {trad_words} words")
    print(f"Raw OCR: {raw_words} words")
    print(f"Targeted OCR: {targeted_words} words")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Compare OCR methods for problematic words')
    parser.add_argument('pdf_path', help='Path to the PDF file to analyze')
    parser.add_argument('--output', '-o', default='.', help='Output directory for extracted text files')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"Error: File not found: {args.pdf_path}")
        return 1
    
    print(f"\n=== COMPARING OCR METHODS FOR PROBLEMATIC WORDS: {args.pdf_path} ===\n")
    
    # Make sure the output directory exists
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # First extract problematic regions using traditional OCR
    print("\n1. EXTRACTING PROBLEMATIC REGIONS")
    trad_file, problematic_regions = extract_problematic_regions(args.pdf_path, args.output)
    
    if not problematic_regions:
        print("No problematic words found in the text. Try running with a different PDF.")
        return 1
    
    print(f"Found {len(problematic_regions)} regions with problematic words.")
    
    # Run the raw OCR method
    print("\n2. RUNNING RAW OCR")
    raw_file = run_raw_ocr(args.pdf_path, args.output)
    
    # Run the targeted OCR improvement
    print("\n3. RUNNING TARGETED OCR IMPROVEMENT")
    targeted_file = run_targeted_ocr(args.pdf_path, args.output)
    
    # Compare results
    print("\n4. COMPARING RESULTS")
    compare_results(problematic_regions, trad_file, raw_file, targeted_file)
    
    print(f"\nAll output files are located in: {args.output}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
