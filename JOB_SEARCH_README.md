# Resume OCR Job Search Toolkit

This toolkit provides optimized OCR and job search tools to help you extract high-quality text from your resume PDF for job applications.

## Quick Start

The simplest way to get started is to use the job search assistant:

```bash
./job_search_assistant.py improved_resume.pdf
```

This will:
1. Process your resume with our optimized OCR
2. Extract skills that might be useful in job applications
3. Create an ATS-friendly version of your resume text
4. Provide tips for using the extracted text in job applications

## Available Tools

### 1. Job Search Assistant

```bash
./job_search_assistant.py path/to/your/resume.pdf --output output_directory
```

A comprehensive tool that combines OCR processing with job application guidance.

### 2. Resume for Job Applications

```bash
./resume_for_job_apps.py path/to/your/resume.pdf --output output_directory
```

Focus solely on extracting high-quality text from your resume PDF using our optimized OCR pipeline.

### 3. Targeted OCR Improvement

```bash
./targeted_ocr_improvement.py path/to/your/resume.pdf --dpi 1500 --output output_directory
```

Advanced OCR tool that specifically addresses common recognition issues in resume PDFs.

### 4. OCR Workflow Script

```bash
./run_ocr_improvement.sh path/to/your/resume.pdf output_directory 1500
```

Runs a full OCR comparison and improves results using multiple methods.

## OCR Quality

Our OCR pipeline provides:

- Accurate recognition of problematic words like "diplomacy" (often misread as "Ciplomacy")
- Correct identification of location information like "millcreek" (often misread as "villereek")
- Better handling of special characters and formatting
- Enhanced consensus approach that combines multiple OCR methods for better accuracy

## Job Application Tips

1. **Tailor Your Resume**: Use the extracted text as a base, but customize it for each application to match job keywords.

2. **Check Formatting**: OCR may lose some formatting, so review for issues before submitting.

3. **Use ATS-Friendly Version**: For online application systems, use the ATS-friendly version which has cleaned up special characters.

4. **Extract Key Skills**: Copy specific skills and experiences from the extracted sections when filling out application forms.

5. **Always Proofread**: While our OCR is optimized, always review the text before submission to catch any remaining issues.

## How It Works

The OCR pipeline uses:

1. Multiple OCR processing methods (6 different approaches)
2. Enhanced consensus approach with case-sensitive voting
3. Character-level analysis and correction
4. Special handling of problematic words
5. Location pattern recognition
6. High-DPI image processing (1500 DPI for optimal results)

For more details, see [OCR_IMPROVEMENT_GUIDE.md](OCR_IMPROVEMENT_GUIDE.md).
