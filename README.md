# Resume Rebuilder with Enhanced OCR, ManageAI and LLM Studio Integration

This application provides tools to improve resumes using both direct LLM Studio integration and the ManageAI Resume API, with enhanced OCR text extraction for better resume parsing.

## Features

- **Enhanced OCR Text Extraction**: Robust extraction of text from PDF resumes with intelligent pattern correction
- **Direct LLM Studio Integration**: Connect directly to a locally running LLM Studio instance
- **ManageAI API Integration**: Connect to the ManageAI Resume API for advanced resume processing
- **Resume Analysis**: Get detailed analysis of your resume
- **Job Matching**: Match your resume against specific job descriptions
- **Resume Tailoring**: Generate tailored versions of your resume for specific jobs
- **ATS Compatibility Check**: Ensure your resume is compatible with Applicant Tracking Systems
- **Automatic Server Management**: The ManageAI Resume API server is automatically started and stopped with the application

## Advanced OCR Features

- **Merged Pattern Detection**: Fixes merged location-verb patterns (e.g., "UtahActed" → "Utah\nActed")
- **Section Header Handling**: Properly identifies and formats embedded section headers
- **Multiple SKILLS Section Handling**: Properly formats duplicate SKILLS sections
- **Broken Line Detection**: Identifies and fixes lines incorrectly broken during OCR extraction
- **Contact Information Enhancement**: Extracts and formats emails, phone numbers, and LinkedIn URLs
- **Date Format Correction**: Fixes broken date formats commonly found in resumes

## Setup

1. Install external dependencies:
   - **Tesseract OCR** (required for PDF text extraction):
     - macOS: `brew install tesseract`
     - Ubuntu: `sudo apt-get install tesseract-ocr`
     - Windows: Download from [UB-Mannheim's GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

   - **Poppler** (required for PDF to image conversion):
     - macOS: `brew install poppler`
     - Ubuntu: `sudo apt-get install poppler-utils`
     - Windows: Download from [poppler-windows](http://blog.alivate.com.au/poppler-windows/)

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make sure you have either:
   - LLM Studio running locally (for direct integration)
   - ManageAI Resume API installed at `/Users/kj/managerai/resume_api.py`

## Server Management

The Resume Rebuilder now automatically manages the ManageAI Resume API server:

- When the application starts, it will automatically start the server at localhost:8080
- When the application closes, it will automatically stop the server

You can also manually manage the server using the `manage_api_server.py` script:

```bash
# Start the server
./manage_api_server.py start

# Check server status
./manage_api_server.py status

# Restart the server
./manage_api_server.py restart

# Stop the server
./manage_api_server.py stop
```

## API Configuration

The application is configured to use the following default settings:

## OCR Text Extraction Improvements

The Resume Rebuilder includes enhanced OCR-based text extraction from PDF resumes, with the following improvements:

### OCR Text Extraction Module (`ocr_text_extraction.py`)

- **Advanced image preprocessing** for better text recognition
- **Multiple OCR configurations** to get the best possible text extraction
- **Smart result selection** algorithm to pick the most accurate OCR result
- **Automatic Tesseract environment detection** to locate language data files

### Text Utilities Module (`text_utils.py`)

- **Broken line detection** to identify and fix incorrectly broken lines
- **Contact information extraction** for emails, phones, LinkedIn URLs, and locations

### Section Extraction Module (`ocr_section_extractor_improved.py`)

- **Enhanced section boundary detection** for better section identification
- **Hierarchical content handling** to properly organize job titles and dates
- **Improved section classification** with confidence scores

### Testing

The OCR system can be tested using the provided test scripts:

1. **Test specific pattern fixes**:
   ```bash
   python test_merged_location_handling.py --test-patterns
   ```

2. **Test comprehensive OCR pipeline**:
   ```bash
   python test_ocr_full_pipeline.py --pdf path/to/resume.pdf
   ```

3. **Generate and validate test cases**:
   ```bash
   python generate_ocr_test_cases.py --run
   ```
- Server: `http://localhost:8080`
- API Key: Environment variable `RESUME_API_KEY` or default test key

You can change these settings in the application's settings panel or by setting environment variables.

## Usage

### Quick Demo

Run the demo script to see the full workflow in action:
```bash
./demo_with_managerai.sh
```

This will:
1. Check if ManageAI Resume API is running and start it if needed
2. Create sample resume and job description files if they don't exist
3. Run the resume improvement process using the ManageAI API

### Manual Usage

You can run the script manually with different options:

```bash
# Using ManageAI Resume API (recommended)
python use_llm_studio.py --use manageai --api-url http://localhost:8080 --resume my_resume.txt --job job_description.txt --action improve

# Using direct LLM Studio connection
python use_llm_studio.py --use direct --host localhost --port 5000 --resume my_resume.txt --job job_description.txt --action improve
```

### Available Actions

- `improve`: Get suggestions to improve your resume
- `tailor`: Generate a tailored version of your resume for a specific job
- `ats`: Check your resume's compatibility with Applicant Tracking Systems

### Command-line Options

- `--use`: Choose between "direct" (LLM Studio) or "manageai" (ManageAI API) integration
- `--host`: LLM Studio host (default: localhost)
- `--port`: LLM Studio port (default: 5000)
- `--api-url`: ManageAI Resume API URL (default: http://localhost:8080)
- `--api-key`: ManageAI Resume API key (if required)
- `--model`: Model name in LLM Studio (default: qwen-14b)
- `--resume`: Path to resume text file
- `--job`: Path to job description text file
- `--action`: Action to perform (improve, tailor, ats)
- `--output`: Output file path

## Integration Notes

### ManageAI Resume API

The application connects to the ManageAI Resume API at `/Users/kj/managerai/resume_api.py`, which provides enhanced resume processing capabilities. The API includes:

- Resume analysis
- Job description analysis
- Resume-job matching
- Optimization suggestions

### LLM Studio Integration

For direct LLM Studio integration, you need:
1. LLM Studio installed and running
2. A model like Qwen-14B loaded and available through the API
3. API access configured on the default port (5000)

## File Structure

- `src/utils/manageai_adapter.py`: Adapter for connecting to the ManageAI Resume API
- `src/utils/local_llm_adapter.py`: Adapter for connecting to LLM Studio directly
- `use_llm_studio.py`: Main script for resume improvement and LLM integration
- `demo_with_managerai.sh`: Demo script showing the complete workflow
- `src/local_server.py`: Simple local server for testing API connections
