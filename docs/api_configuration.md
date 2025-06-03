# API Configuration Guide

This guide explains how to configure and use API keys for the Resume Rebuilder application.

## Environment Variables

The Resume Rebuilder uses environment variables stored in `.env` files to securely manage API keys and configuration settings. This approach keeps sensitive information out of your code and version control.

## Available API Integrations

The application can integrate with the following services:

### Job Search APIs
- **LinkedIn** - Search for jobs on LinkedIn
- **Indeed** - Search for jobs on Indeed
- **Glassdoor** - Search for jobs on Glassdoor
- **Monster** - Search for jobs on Monster

### Applicant Tracking System (ATS) APIs
- **Lever** - Submit applications through Lever ATS
- **Greenhouse** - Submit applications through Greenhouse ATS
- **Workday** - Submit applications through Workday ATS

### Resume Processing APIs
- **ManageAI Resume API** - Local API for resume processing

### LLM Integration
- **LLM Studio** - Local large language model integration

## Setting Up Your API Keys

1. Locate the `.env` file in the project root directory (`/Users/kj/ResumeRebuild/.env`)
2. Edit the file to add your actual API keys (replace the placeholder values)
3. Save the file and restart the application

Example `.env` file:
```
# ManageAI Resume API Configuration
RESUME_API_KEY=abc123def456
RESUME_API_URL=http://localhost:8080

# Job Search APIs
LINKEDIN_API_KEY=your_linkedin_api_key
INDEED_API_KEY=your_indeed_api_key
GLASSDOOR_API_KEY=your_glassdoor_api_key
MONSTER_API_KEY=your_monster_api_key

# ATS System APIs
LEVER_API_KEY=your_lever_api_key
GREENHOUSE_API_KEY=your_greenhouse_api_key
WORKDAY_API_KEY=your_workday_api_key

# LLM Configuration
LLM_STUDIO_HOST=localhost
LLM_STUDIO_PORT=5000
LLM_STUDIO_MODEL=qwen-14b
```

## Checking API Status

You can check the status of your API configurations using the included utility:

```bash
python check_api_status.py
```

This will show you which APIs are properly configured and provide guidance for setting up missing keys.

## Using the Job Search CLI

The Job Search CLI allows you to search for jobs across multiple platforms using a simple command:

```bash
# Basic search
python job_search_cli.py "Python Developer"

# Search with location
python job_search_cli.py "Data Scientist" -l "San Francisco"

# Search specific sources
python job_search_cli.py "Software Engineer" -s linkedin,indeed

# Output to file
python job_search_cli.py "UX Designer" -o jobs.txt

# Output as JSON
python job_search_cli.py "Product Manager" -f json -o jobs.json
```

## Security Notes

1. **Never commit your `.env` file** to version control
2. Keep your API keys secure and don't share them
3. Regularly rotate your API keys for better security
4. The `.env` file is already added to `.gitignore` to prevent accidental commits

## Obtaining API Keys

For information on obtaining API keys for the various services:

- **LinkedIn API**: Visit the [LinkedIn Developer Portal](https://developer.linkedin.com/)
- **Indeed API**: Visit the [Indeed Publisher Portal](https://developers.indeed.com/)
- **Glassdoor API**: Visit the [Glassdoor Developer Portal](https://www.glassdoor.com/developer/)
- **Monster API**: Contact Monster for API access
- **Lever API**: Contact your Lever administrator
- **Greenhouse API**: Contact your Greenhouse administrator
- **Workday API**: Contact your Workday administrator
