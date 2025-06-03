"""
API Client module for communicating with resume-related web services.
"""

import os
import json
import requests
from urllib.parse import urljoin
import logging
from src.utils.env_loader import get_api_key, get_setting

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIClient:
    """Client for interacting with resume API endpoints."""
    
    def __init__(self, base_url=None, api_key=None):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API endpoints
            api_key: API key for authentication
        """
        self.base_url = base_url or get_setting("RESUME_API_URL", "http://localhost:8080/")
        self.api_key = api_key or get_api_key("RESUME_API_KEY", "")
        
        # Ensure base_url ends with a slash
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        
        logger.info(f"Initialized API client with base URL: {self.base_url}")
        if not self.api_key:
            logger.warning("No API key provided. Some endpoints may require authentication.")
    
    def _make_request(self, method, endpoint, data=None, params=None, files=None, timeout=30):
        """
        Make a request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint to call
            data: Data to send in the request body
            params: Query parameters to include
            files: Files to upload
            timeout: Request timeout in seconds
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If the request fails
        """
        url = urljoin(self.base_url, endpoint)
        headers = {
            'Authorization': f'Bearer {self.api_key}' if self.api_key else None,
            'Accept': 'application/json',
        }
        
        # Remove None values from headers
        headers = {k: v for k, v in headers.items() if v is not None}
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                if files:
                    # Don't include Content-Type header when using files
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == 'PUT':
                headers['Content-Type'] = 'application/json'
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Raise exception for HTTP errors
            response.raise_for_status()
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    logger.error(f"Error response: {error_data}")
                except ValueError:
                    logger.error(f"Error status code: {e.response.status_code}")
                    logger.error(f"Error content: {e.response.content}")
            raise Exception(f"API request failed: {str(e)}")
    
    def analyze_resume(self, resume_content, job_description=None):
        """
        Analyze a resume against an optional job description.
        
        Args:
            resume_content: Dictionary containing resume content
            job_description: Optional job description text
            
        Returns:
            Dictionary with analysis results
        """
        data = {
            'resume': resume_content,
        }
        
        if job_description:
            data['job_description'] = job_description
        
        return self._make_request('POST', 'analyze', data=data)
    
    def upload_resume_pdf(self, file_path):
        """
        Upload a resume PDF file for analysis.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with the extracted resume content
        """
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            return self._make_request('POST', 'upload', files=files)
    
    def get_resume_templates(self):
        """
        Get available resume templates.
        
        Returns:
            List of available templates
        """
        return self._make_request('GET', 'templates')
    
    def generate_resume_pdf(self, resume_content, template_id):
        """
        Generate a resume PDF from content and template.
        
        Args:
            resume_content: Dictionary containing resume content
            template_id: ID of the template to use
            
        Returns:
            Dictionary with URL to the generated PDF
        """
        data = {
            'resume': resume_content,
            'template_id': template_id
        }
        
        return self._make_request('POST', 'generate', data=data)
    
    def keyword_optimization(self, resume_content, job_description):
        """
        Get keyword optimization suggestions.
        
        Args:
            resume_content: Dictionary containing resume content
            job_description: Job description text
            
        Returns:
            Dictionary with optimization suggestions
        """
        data = {
            'resume': resume_content,
            'job_description': job_description
        }
        
        return self._make_request('POST', 'optimize', data=data)
    
    def ats_compatibility_check(self, resume_content):
        """
        Check if resume is compatible with Applicant Tracking Systems.
        
        Args:
            resume_content: Dictionary containing resume content
            
        Returns:
            Dictionary with compatibility score and suggestions
        """
        return self._make_request('POST', 'ats-check', data={'resume': resume_content})
    
    def set_api_credentials(self, base_url=None, api_key=None):
        """
        Update API credentials.
        
        Args:
            base_url: New base URL for the API
            api_key: New API key
        """
        if base_url:
            self.base_url = base_url
            if not self.base_url.endswith('/'):
                self.base_url += '/'
        
        if api_key:
            self.api_key = api_key
            
    def set_api_key(self, api_key):
        """
        Set or update the API key.
        
        Args:
            api_key: The API key to use for authentication
        """
        self.api_key = api_key

    def iterate_resume(self, resume_content, feedback, focus_area="general"):
        """
        Submit feedback for resume iteration to further refine a resume.
        
        Args:
            resume_content: Dictionary or string containing the current resume content
            feedback: Specific feedback for improvement
            focus_area: Area to focus improvements on (e.g., skills, experience, summary)
            
        Returns:
            Dictionary with the improved resume content
        """
        data = {
            'resume': resume_content,
            'feedback': feedback,
            'focus_area': focus_area
        }
        
        return self._make_request('POST', 'iterate', data=data)
        
    def test_connection(self):
        """
        Test the connection to the API endpoint.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Make a simple GET request to test the connection
            endpoint = "health"  # Typically APIs have a health endpoint
            url = urljoin(self.base_url, endpoint)
            headers = {
                'Authorization': f'Bearer {self.api_key}' if self.api_key else None,
                'Accept': 'application/json',
            }
            
            # Remove None values from headers
            headers = {k: v for k, v in headers.items() if v is not None}
            
            logger.info(f"Testing connection to {url}")
            response = requests.get(url, headers=headers, timeout=10)
            
            # Return True if the status code is 2xx (success)
            return 200 <= response.status_code < 300
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection test failed: {e}")
            return False
