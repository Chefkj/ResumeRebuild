#!/usr/bin/env python3
"""
Resume Rebuilder - PDF to PDF
A tool for extracting content from PDF resumes, allowing modifications, and creating a new formatted PDF.

This script supports both GUI mode and command line interface for rebuilding resumes.
"""

import os
import sys
import argparse

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Resume Rebuilder - Extract, modify, and rebuild PDF resumes"
    )
    parser.add_argument(
        "--gui", 
        action="store_true",
        help="Launch in GUI mode (default)"
    )
    parser.add_argument(
        "--pdf", 
        help="Path to input PDF resume"
    )
    parser.add_argument(
        "--job", 
        help="Path to job description file"
    )
    parser.add_argument(
        "--output", 
        help="Path for output PDF (default: new_resume.pdf)"
    )
    parser.add_argument(
        "--use-ocr",
        action="store_true", 
        help="Use OCR for text extraction (requires tesseract)"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM content refinement"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_args()
    
    # If GUI mode or no arguments specified, launch GUI
    if args.gui or (not args.pdf and len(sys.argv) == 1):
        from src.gui import main as gui_main
        gui_main()
        return
    
    # Command line mode
    if args.pdf:
        if not os.path.exists(args.pdf):
            print(f"Error: PDF file not found: {args.pdf}")
            sys.exit(1)
            
        job_description = None
        if args.job:
            if not os.path.exists(args.job):
                print(f"Error: Job description file not found: {args.job}")
                sys.exit(1)
            with open(args.job, 'r', encoding='utf-8') as f:
                job_description = f.read()
        
        # Import the PDF content replacer
        from src.utils.pdf_content_replacer import PDFContentReplacer
        
        # Initialize the replacer
        replacer = PDFContentReplacer(
            use_enhanced=True,
            use_llm=not args.no_llm,
            use_ocr=args.use_ocr
        )
        
        # Process the resume
        try:
            print(f"Processing resume: {args.pdf}")
            output_path = args.output or 'new_resume.pdf'
            
            # Improve the resume
            result_path = replacer.improve_resume(
                args.pdf,
                job_description,
                output_path
            )
            
            print(f"Resume successfully processed and saved to: {result_path}")
            
        except Exception as e:
            print(f"Error processing resume: {e}")
            sys.exit(1)
    else:
        print("Error: No PDF file specified. Use --pdf or --gui")
        sys.exit(1)

if __name__ == "__main__":
    main()