# Resume Rebuilder with ManageAI and LLM Studio Integration

This application provides tools to improve resumes using both direct LLM Studio integration and the ManageAI Resume API.

## Features

- **Direct LLM Studio Integration**: Connect directly to a locally running LLM Studio instance
- **ManageAI API Integration**: Connect to the ManageAI Resume API for advanced resume processing
- **Resume Analysis**: Get detailed analysis of your resume
- **Job Matching**: Match your resume against specific job descriptions
- **Resume Tailoring**: Generate tailored versions of your resume for specific jobs
- **ATS Compatibility Check**: Ensure your resume is compatible with Applicant Tracking Systems
- **Automatic Server Management**: The ManageAI Resume API server is automatically started and stopped with the application

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure you have either:
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
