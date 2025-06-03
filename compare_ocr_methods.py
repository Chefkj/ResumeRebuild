#!/usr/bin/env python3
"""
Compare OCR Methods

This script compares different OCR methods and settings to help determine
the best approach for a particular PDF.
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime

def compare_methods(pdf_path, output_dir="."):
    """
    Compare different OCR methods on the same PDF
    """
    results = []
    
    print(f"\n=== COMPARING OCR METHODS FOR: {pdf_path} ===\n")
    
    # Method 1: Traditional OCR with DPI=1200
    print("\n1. TRADITIONAL OCR (DPI=1200)")
    start_time = time.time()
    output_file = run_traditional_ocr(pdf_path, output_dir, 1200)
    elapsed = time.time() - start_time
    word_count = count_words(output_file)
    results.append({
        'method': 'Traditional OCR (DPI=1200)',
        'time': elapsed,
        'word_count': word_count,
        'output_file': output_file
    })
    
    # Method 2: Traditional OCR with DPI=1500
    print("\n2. TRADITIONAL OCR (DPI=1500)")
    start_time = time.time()
    output_file = run_traditional_ocr(pdf_path, output_dir, 1500)
    elapsed = time.time() - start_time
    word_count = count_words(output_file)
    results.append({
        'method': 'Traditional OCR (DPI=1500)',
        'time': elapsed,
        'word_count': word_count,
        'output_file': output_file
    })
    
    # Method 3: Raw OCR with PSM=3
    print("\n3. RAW OCR (PSM=3, DPI=1400)")
    start_time = time.time()
    output_file = run_raw_ocr(pdf_path, output_dir, "psm3")
    elapsed = time.time() - start_time
    word_count = count_words(output_file)
    results.append({
        'method': 'Raw OCR (PSM=3, DPI=1400)',
        'time': elapsed,
        'word_count': word_count,
        'output_file': output_file
    })
    
    # Method 4: Raw OCR with PSM=4
    print("\n4. RAW OCR (PSM=4, DPI=1400)")
    start_time = time.time()
    output_file = run_raw_ocr(pdf_path, output_dir, "psm4")
    elapsed = time.time() - start_time
    word_count = count_words(output_file)
    results.append({
        'method': 'Raw OCR (PSM=4, DPI=1400)',
        'time': elapsed,
        'word_count': word_count,
        'output_file': output_file
    })
    
    # Print comparison table
    print("\n=== OCR METHOD COMPARISON ===\n")
    print(f"{'METHOD':<30} {'TIME (s)':<10} {'WORD COUNT':<12} {'OUTPUT FILE':<40}")
    print("-" * 90)
    
    for result in results:
        print(f"{result['method']:<30} {result['time']:<10.2f} {result['word_count']:<12} {os.path.basename(result['output_file'])}")
    
    # Find best method based on word count
    best_method = max(results, key=lambda r: r['word_count'])
    print(f"\nBest method based on word count: {best_method['method']} with {best_method['word_count']} words")
    print(f"Best output file: {best_method['output_file']}")
    
    return results

def run_traditional_ocr(pdf_path, output_dir, dpi):
    """
    Run traditional OCR and return the output file path
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_trad_ocr_dpi{dpi}_{timestamp}.txt")
    
    cmd = ["python", "traditional_ocr.py", pdf_path, "--dpi", str(dpi), "--output", output_dir]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        # Rename the output file to include the DPI
        latest_file = get_latest_file(output_dir, f"{base_name}_trad_ocr_")
        if latest_file:
            os.rename(latest_file, output_file)
            return output_file
        else:
            return "unknown"
    except subprocess.CalledProcessError as e:
        print(f"Error running traditional OCR: {e}")
        return "error"

def run_raw_ocr(pdf_path, output_dir, mode):
    """
    Run raw OCR and return the output file path
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_raw_ocr_{mode}_{timestamp}.txt")
    
    cmd = ["python", "test_raw_ocr_extraction.py", pdf_path, "--mode", mode, "--output", output_dir]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        # Rename the output file to include the mode
        latest_file = get_latest_file(output_dir, f"{base_name}_raw_ocr_")
        if latest_file:
            os.rename(latest_file, output_file)
            return output_file
        else:
            return "unknown"
    except subprocess.CalledProcessError as e:
        print(f"Error running raw OCR: {e}")
        return "error"

def get_latest_file(directory, prefix):
    """
    Get the latest file matching the prefix in the directory
    """
    matching_files = [f for f in os.listdir(directory) if f.startswith(prefix)]
    if not matching_files:
        return None
    
    return os.path.join(directory, max(matching_files, key=lambda f: os.path.getmtime(os.path.join(directory, f))))

def count_words(file_path):
    """
    Count words in a text file
    """
    if not os.path.exists(file_path) or file_path in ["unknown", "error"]:
        return 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return len(content.split())
    except Exception as e:
        print(f"Error counting words in {file_path}: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Compare different OCR methods on a PDF')
    parser.add_argument('pdf_path', help='Path to the PDF file to analyze')
    parser.add_argument('--output', '-o', default='.', help='Output directory for extracted text files')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"Error: File not found: {args.pdf_path}")
        return 1
    
    compare_methods(args.pdf_path, args.output)
    return 0

if __name__ == '__main__':
    sys.exit(main())
