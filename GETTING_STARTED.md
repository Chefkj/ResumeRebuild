# Getting Started with Your Job Search

Hi Keith! We've created a set of tools to help you get your resume ready for job applications. These tools address the OCR issues with "diplomacy" and "millcreek" and make it easy to extract high-quality text from your resume.

## Quick Start Guide

### One-Command Solution (Recommended)

Just run this command in the terminal:

```bash
cd /Users/kj/ResumeRebuild
./get_job_ready.sh improved_resume.pdf
```

This will:
1. Process your resume with our optimized OCR
2. Extract key skills that you can use in job applications
3. Create an ATS-friendly version of your resume text
4. Open the output directory automatically

### Other Available Commands

For more specific needs, you can use:

```bash
# Run the full job search assistant
./job_search_assistant.py improved_resume.pdf

# Just extract high-quality text from your resume
./resume_for_job_apps.py improved_resume.pdf

# Try different OCR settings for better results
./targeted_ocr_improvement.py improved_resume.pdf --dpi 1500
```

## What To Do With The Output

Once your resume is processed, you'll have two main files:

1. `improved_resume_job_app_[timestamp].txt` - The full text of your resume
2. `improved_resume_job_app_[timestamp]_ATS.txt` - ATS-friendly version with special characters removed

### Using These Files

1. **Online Application Forms**: Copy from the ATS-friendly version when filling out online job applications.

2. **LinkedIn & Job Sites**: Use the extracted text to update your profile or create a plain text version of your resume.

3. **Custom Applications**: Use the extracted skills to highlight relevant qualifications in cover letters or custom resume versions.

## Getting Help

If you encounter any issues or have questions:

1. Check the `JOB_SEARCH_README.md` for detailed documentation
2. Review the `OCR_IMPROVEMENT_GUIDE.md` for technical details on the OCR improvements
3. The code has extensive comments to help you understand and modify if needed

Good luck with your job search! 🎉
