#!/usr/bin/env python3
"""
Test script for raw OCR text extraction

This script tests only the raw OCR text extraction from PDF resumes without any header processing.
It uses the RawOCRTextExtractor which avoids all header processing and sequential text ordering.

This is now just a wrapper around test_raw_ocr_extraction_new.py for compatibility.
"""

import sys
import argparse

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test raw OCR text extraction")
    parser.add_argument("pdf_path", nargs="?", default="improved_resume.pdf", 
                        help="Path to the PDF file to test (default: improved_resume.pdf)")
    parser.add_argument("--output", "-o", default=".", 
                        help="Output folder for extracted text files (default: current directory)")
    parser.add_argument("--dpi", "-d", type=int, default=1400,
                        help="DPI value for PDF to image conversion (default: 1400)")
    parser.add_argument("--mode", "-m", choices=["psm3", "psm4", "all"], default="all",
                        help="OCR mode to use (psm3, psm4, or all) (default: all)")
    args = parser.parse_args()
    
    # Use the new implementation which skips header processing
    print("NOTE: Using raw OCR extraction without any header processing or sequential text ordering")
    print("      to show the raw text output directly from Tesseract OCR.")
    print(f"Using DPI: {args.dpi}, OCR Mode: {args.mode}")
    
    # Import and use the new test function
    from test_raw_ocr_extraction_new import test_raw_ocr_extraction
    test_raw_ocr_extraction(args.pdf_path, args.output, args.dpi, args.mode)
