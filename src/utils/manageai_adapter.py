"""
ManageAI Resume API adapter for the Resume Rebuilder application.

This module provides an adapter to connect the Resume Rebuilder application
with the existing ManageAI Resume API.
"""

import os
import logging
import json
import requests
from typing import Dict, Any, Optional, List

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ManageAIResumeAdapter:
    """
    Adapter for connecting to the ManageAI Resume API.
    
    This class provides methods to interact with the ManageAI Resume API
    endpoints and handles authentication, error handling, and data formatting.
    """
    
    def __init__(
        self,
        api_url: str = "http://localhost:8080",
        api_key: Optional[str] = None
    ):
        """
        Initialize the adapter with connection settings.
        
        Args:
            api_url: URL of the ManageAI Resume API
            api_key: Optional API key for authentication
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        logger.info(f"ManageAI Resume API adapter initialized with URL: {self.api_url}")
    
    def _make_request(self, endpoint: str, method: str = "POST", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the ManageAI Resume API.
        
        Args:
            endpoint: API endpoint to call
            method: HTTP method (GET, POST)
            data: Data to send in the request body
            
        Returns:
            Response data as dictionary
            
        Raises:
            ConnectionError: If the connection fails
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        headers["Content-Type"] = "application/json"
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check for errors
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Failed to connect to ManageAI Resume API: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
            raise TimeoutError(f"Request to ManageAI Resume API timed out: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            # Try to get error details from response
            error_msg = f"HTTP error {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_msg += f": {error_data['error']}"
            except:
                error_msg += f": {e.response.text}"
            raise RuntimeError(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the connection to the ManageAI Resume API.
        
        Returns:
            bool: True if the connection is successful, False otherwise
        """
        try:
            # Try to access the API root or health endpoint
            url = f"{self.api_url}/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                logger.info("Successfully connected to ManageAI Resume API")
                return True
            else:
                # If health endpoint doesn't exist, try the root endpoint
                url = self.api_url
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    logger.info("Successfully connected to ManageAI Resume API")
                    return True
                else:
                    logger.warning(f"Failed to connect to ManageAI Resume API, status code: {response.status_code}")
                    return False
                
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error to ManageAI Resume API: {e}")
            return False
        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout connecting to ManageAI Resume API: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error connecting to ManageAI Resume API: {e}")
            return False
    
    def set_api_url(self, api_url: str) -> None:
        """
        Set or update the API URL.
        
        Args:
            api_url: New API URL
        """
        self.api_url = api_url.rstrip('/')
        logger.info(f"API URL updated to: {self.api_url}")
    
    def set_api_key(self, api_key: str) -> None:
        """
        Set or update the API key.
        
        Args:
            api_key: New API key
        """
        self.api_key = api_key
        logger.info("API key updated")
    
    def analyze_resume(self, resume_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a resume using the ManageAI Resume API.
        
        Args:
            resume_content: Dictionary containing resume content
            
        Returns:
            Dictionary with analysis results
        """
        data = {"resume": resume_content}
        return self._make_request("analyze/resume", data=data)
    
    def analyze_job(self, job_description: str) -> Dict[str, Any]:
        """
        Analyze a job description using the ManageAI Resume API.
        
        Args:
            job_description: Job description text
            
        Returns:
            Dictionary with analysis results
        """
        data = {"job_description": job_description}
        return self._make_request("analyze/job", data=data)
    
    def match_resume_to_job(
        self, 
        resume_content: Dict[str, Any], 
        job_description: str,
        resume_analysis: Optional[Dict[str, Any]] = None,
        job_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Match a resume to a job description using the ManageAI Resume API.
        
        Args:
            resume_content: Dictionary containing resume content
            job_description: Job description text
            resume_analysis: Optional pre-computed resume analysis
            job_analysis: Optional pre-computed job description analysis
            
        Returns:
            Dictionary with match results
        """
        data = {
            "resume": resume_content,
            "job_description": job_description
        }
        
        if resume_analysis:
            data["resume_analysis"] = resume_analysis
            
        if job_analysis:
            data["job_analysis"] = job_analysis
            
        return self._make_request("match", data=data)
    
    def improve_resume(
        self, 
        resume_content: Dict[str, Any], 
        job_description: str,
        match_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Improve a resume for a specific job using the ManageAI Resume API.
        
        Args:
            resume_content: Dictionary containing resume content
            job_description: Job description text
            match_result: Optional pre-computed match results
            
        Returns:
            Dictionary with improved resume content
        """
        data = {
            "resume": resume_content,
            "job_description": job_description
        }
        
        if match_result:
            data["match_result"] = match_result
            
        return self._make_request("improve", data=data)


# Example usage
if __name__ == "__main__":
    # Simple test to verify adapter functionality
    adapter = ManageAIResumeAdapter()
    
    if adapter.test_connection():
        print("Successfully connected to ManageAI Resume API")
        
        # Example resume and job description
        resume = {
            "contact": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890"
            },
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "ABC Corp",
                    "start_date": "2020-01",
                    "end_date": "Present",
                    "description": "Developed web applications using Python and JavaScript."
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science",
                    "institution": "University of Technology",
                    "field": "Computer Science",
                    "graduation_date": "2019-05"
                }
            ]
        }
        
        job_description = """
        Senior Software Engineer position requiring 3+ years of experience with
        Python development, web frameworks, and cloud infrastructure. Must have
        strong problem-solving skills and ability to work in a team.
        """
        
        try:
            # Analyze resume
            resume_analysis = adapter.analyze_resume(resume)
            print("Resume analysis complete")
            
            # Analyze job
            job_analysis = adapter.analyze_job(job_description)
            print("Job analysis complete")
            
            # Match resume to job
            match_result = adapter.match_resume_to_job(
                resume, 
                job_description, 
                resume_analysis, 
                job_analysis
            )
            print(f"Match score: {match_result.get('score', 'N/A')}")
            
            # Improve resume
            improved = adapter.improve_resume(resume, job_description, match_result)
            print("Resume improvement complete")
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Failed to connect to ManageAI Resume API")
