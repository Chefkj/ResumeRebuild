# Resume to Job Application Text Converter

## Quick Start

To extract text from your resume for job applications, simply run:

```bash
./get_job_ready.sh "/Users/kj/Downloads/KJ Cowen - Resume.pdf"
```

This will:
1. Process your resume with our optimized OCR
2. Extract key skills for job applications
3. Create an ATS-friendly version of your resume text
4. Open the output directory automatically

## Alternative Approaches

If you encounter any issues with the main script, you can use the direct OCR approach:

```bash
./direct_ocr_resume.py "/Users/kj/Downloads/KJ Cowen - Resume.pdf"
```

This script has minimal dependencies and focuses only on extracting high-quality text from your resume.

## What's Fixed

The scripts have been updated to:
- Fix the issues with the resume rebuilder's API dependency
- Better handle resume files with spaces in the filename
- Look for your resume in both the current directory and Downloads folder
- Provide a direct OCR approach that bypasses all complex dependencies
- Handle macOS-specific path commands for better compatibility

## Output Files

The scripts generate several files in the output directory:

1. `*_job_app_*.txt` - The full text of your resume from the job search assistant
2. `*_job_app_*_ATS.txt` - ATS-friendly version with special characters removed
3. `*_targeted_ocr_*.txt` - Direct OCR output from the targeted improvement
4. `*_job_ready.txt` - A simplified version ready for job applications

## Best Practices

1. Always review the extracted text before submitting to job applications
2. The ATS-friendly version is best for online application systems
3. Use the extracted skills when filling out specific skills fields
4. Customize the text for each job application to match relevant keywords
