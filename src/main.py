#!/usr/bin/env python3
"""
Resume Rebuilder - PDF to PDF 
A tool for extracting content from PDF resumes, allowing modifications, and creating a new formatted PDF.
"""

import os
import sys
import argparse
from utils.pdf_extractor import PDFExtractor
from utils.resume_generator import ResumeGenerator
from utils.job_analyzer import JobAnalyzer

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Resume Rebuilder - Extract, Modify, and Rebuild Resumes')
    parser.add_argument('input_pdf', help='Path to the input resume PDF file')
    parser.add_argument('-o', '--output', help='Path for the output PDF file', default='new_resume.pdf')
    parser.add_argument('-j', '--job-description', help='Path to job description file or text', default=None)
    parser.add_argument('-t', '--template', help='Resume template to use', default='modern')
    return parser.parse_args()

def main():
    """Main function to run the resume rebuilder."""
    args = parse_arguments()
    
    # Check if input file exists
    if not os.path.exists(args.input_pdf):
        print(f"Error: Input file '{args.input_pdf}' does not exist.")
        sys.exit(1)
    
    print(f"Processing resume: {args.input_pdf}")
    
    # Extract content from the PDF
    extractor = PDFExtractor()
    resume_content = extractor.extract(args.input_pdf)
    
    # Analyze job description if provided
    if args.job_description:
        analyzer = JobAnalyzer()
        if os.path.exists(args.job_description):
            with open(args.job_description, 'r') as f:
                job_text = f.read()
        else:
            job_text = args.job_description
            
        keywords, suggestions = analyzer.analyze(job_text, resume_content)
        print("\nJob Analysis Results:")
        print(f"Keywords found: {', '.join(keywords)}")
        print("\nSuggestions:")
        for suggestion in suggestions:
            print(f"- {suggestion}")
    
    # Allow user to edit the extracted content
    print("\nExtracted resume content. You can edit this content before generating the new resume.")
    print("Press Enter to continue to the editing phase...")
    input()
    
    # In a real application, you might open an editor or GUI here
    # For this example, we'll just use the extracted content directly
    
    # Generate the new resume
    generator = ResumeGenerator()
    output_path = generator.generate(resume_content, template=args.template, output_path=args.output)
    
    print(f"\nNew resume created successfully: {output_path}")

if __name__ == "__main__":
    main()