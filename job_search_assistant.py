#!/usr/bin/env python3
"""
Job Search Assistant

This assistant helps you:
1. Process your resume for job applications using our optimized OCR
2. Prepare your resume text for various application platforms
3. Extract key skills and experience for job application forms
"""

import os
import sys
import re
import argparse
from datetime import datetime

from resume_for_job_apps import process_resume_for_job_application

def highlight_skills(resume_text):
    """
    Extract and highlight potential skills from the resume text
    
    Args:
        resume_text: Processed resume text
        
    Returns:
        dict: Categories of extracted skills
    """
    print("\n===== SKILL EXTRACTION =====")
    print("These skills might be useful to highlight in your applications:")
    
    # Define skill categories and patterns
    skill_categories = {
        "Programming Languages": [
            r"\b(Python|Java|C\+\+|JavaScript|TypeScript|C#|Ruby|PHP|Swift|Kotlin|Go|Rust)\b"
        ],
        "Frameworks & Libraries": [
            r"\b(React|Angular|Vue|Django|Flask|Spring|Express|TensorFlow|PyTorch|Pandas|NumPy|scikit-learn)\b"
        ],
        "Tools & Technologies": [
            r"\b(Docker|Kubernetes|AWS|Azure|GCP|Git|GitHub|GitLab|CI/CD|Jenkins|Linux|Windows|macOS)\b"
        ],
        "Soft Skills": [
            r"\b(leadership|teamwork|communication|problem.solving|project management|organization|time management)\b",
            r"\b(collaboration|initiative|adaptability|creativity|critical thinking)\b"
        ]
    }
    
    extracted_skills = {}
    
    # Extract skills by category
    for category, patterns in skill_categories.items():
        skills = set()
        for pattern in patterns:
            matches = re.finditer(pattern, resume_text, re.IGNORECASE)
            for match in matches:
                # Add the skill with original capitalization
                skills.add(match.group(0))
        
        if skills:
            extracted_skills[category] = sorted(list(skills))
            
            # Print the skills in this category
            print(f"\n{category}:")
            print("  " + ", ".join(extracted_skills[category]))
    
    return extracted_skills

def extract_sections(resume_text):
    """
    Attempt to extract common resume sections
    
    Args:
        resume_text: Processed resume text
        
    Returns:
        dict: Extracted sections
    """
    # Common section headers in resumes
    section_patterns = {
        "summary": r"(?:PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE)(.*?)(?=\b[A-Z\s]{2,}:|$)",
        "experience": r"(?:EXPERIENCE|WORK\s+EXPERIENCE|EMPLOYMENT)(.*?)(?=\b[A-Z\s]{2,}:|$)", 
        "education": r"(?:EDUCATION|ACADEMIC|QUALIFICATIONS)(.*?)(?=\b[A-Z\s]{2,}:|$)",
        "skills": r"(?:SKILLS|TECHNICAL\s+SKILLS|CORE\s+COMPETENCIES)(.*?)(?=\b[A-Z\s]{2,}:|$)",
    }
    
    sections = {}
    
    for section_name, pattern in section_patterns.items():
        matches = re.search(pattern, resume_text, re.IGNORECASE | re.DOTALL)
        if matches:
            # Clean up the section content
            content = matches.group(1).strip()
            sections[section_name] = content
    
    return sections

def prepare_ats_friendly_text(resume_text):
    """
    Prepare ATS-friendly version of the resume text
    
    Args:
        resume_text: Processed resume text
        
    Returns:
        str: ATS-friendly resume text
    """
    # Replace special characters
    ats_text = resume_text
    
    # Replace bullets and special characters
    ats_text = re.sub(r'[•◦⦿⁃◘◙■►▷➢▪◾◽⬤]', '-', ats_text)
    
    # Replace non-standard whitespace
    ats_text = re.sub(r'\s+', ' ', ats_text)
    
    # Clean up excessive spacing
    ats_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', ats_text)
    
    return ats_text

def job_search_assistant(resume_pdf_path, output_dir="."):
    """
    Run the job search assistant
    
    Args:
        resume_pdf_path: Path to the resume PDF
        output_dir: Directory for output files
    """
    print("\n" + "="*70)
    print("✨ JOB SEARCH ASSISTANT ✨".center(70))
    print("="*70)
    
    # 1. Process the resume with our optimized OCR
    output_file = process_resume_for_job_application(resume_pdf_path, output_dir)
    
    # Read the processed resume text
    with open(output_file, 'r', encoding='utf-8') as f:
        resume_text = f.read()
    
    # 2. Extract skills
    extracted_skills = highlight_skills(resume_text)
    
    # 3. Prepare ATS-friendly version
    ats_friendly_text = prepare_ats_friendly_text(resume_text)
    ats_file = output_file.replace('.txt', '_ATS.txt')
    with open(ats_file, 'w', encoding='utf-8') as f:
        f.write(ats_friendly_text)
    
    print(f"\n✅ ATS-friendly version saved to: {ats_file}")
    
    # 4. Provide guidance
    print("\n===== JOB APPLICATION TIPS =====")
    print("1. Copy specific skills from above when asked in application forms")
    print("2. Use the ATS-friendly version for online application systems")
    print("3. For free-form applications, tailor your resume to match job keywords")
    print("4. Always proofread before submitting (our OCR isn't perfect!)")
    
    print("\n" + "="*70)
    print("Good luck with your job search!".center(70))
    print("="*70)
    
    return ats_file

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Job Search Assistant")
    parser.add_argument("resume_pdf", help="Path to your resume PDF file")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    
    args = parser.parse_args()
    
    # Validate PDF path
    if not os.path.exists(args.resume_pdf):
        print(f"Error: Resume PDF not found at {args.resume_pdf}")
        return 1
    
    try:
        job_search_assistant(args.resume_pdf, args.output)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
