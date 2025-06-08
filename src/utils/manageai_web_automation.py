"""
ManageAI Web Automation Client for Job Search.

This module provides integration with ManageAI's web automation capabilities
for automated job searching and application processes.
"""

import json
import logging
import requests
import time
from typing import Dict, List, Any, Optional

from src.utils.env_loader import get_setting

# Configure logger
logger = logging.getLogger(__name__)

class ManageAIWebAutomationClient:
    """Client for ManageAI web automation services."""
    
    def __init__(self):
        """Initialize the ManageAI web automation client."""
        self.api_url = get_setting("MANAGEAI_API_URL", "http://localhost:8080").rstrip('/')
        self.available = False
        self._check_availability()
    
    def _check_availability(self):
        """Check if ManageAI web automation is available."""
        try:
            # Check API health
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                
                # Check web automation status
                web_response = requests.get(f"{self.api_url}/web/status", timeout=5)
                if web_response.status_code == 200:
                    web_data = web_response.json()
                    self.available = web_data.get("available", False)
                    
                    if self.available:
                        logger.info("ManageAI web automation is available")
                    else:
                        logger.warning(f"ManageAI web automation not available: {web_data.get('error', 'Unknown reason')}")
                else:
                    logger.warning("ManageAI web automation status endpoint not available")
            else:
                logger.warning(f"ManageAI API not available: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"ManageAI web automation not available: {e}")
            self.available = False
    
    def search_glassdoor_jobs(self, query: str, location: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on Glassdoor using ManageAI web automation.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        if not self.available:
            logger.error("ManageAI web automation not available")
            return []
        
        try:
            logger.info(f"Searching Glassdoor with ManageAI for '{query}' in '{location or 'any location'}'")
            
            # Construct the search task
            task_description = f"Navigate to Glassdoor, search for '{query}'"
            if location:
                task_description += f" in '{location}'"
            task_description += f", and extract the top {limit} job listings with details like title, company, location, and description"
            
            payload = {
                "task": task_description,
                "url": "https://www.glassdoor.com",
                "job_title": query,
                "location": location or "",
                "extract_jobs": True,
                "limit": limit
            }
            
            response = requests.post(
                f"{self.api_url}/web/task",
                json=payload,
                timeout=120  # Job searches can take a while
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # Extract job listings from the result
                    jobs = self._parse_job_results(result, "Glassdoor (ManageAI)")
                    logger.info(f"Found {len(jobs)} jobs on Glassdoor using ManageAI")
                    return jobs
                else:
                    logger.error(f"Glassdoor search failed: {result.get('error', 'Unknown error')}")
                    return []
            else:
                logger.error(f"Glassdoor search request failed: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching Glassdoor with ManageAI: {e}")
            return []
    
    def search_indeed_jobs(self, query: str, location: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on Indeed using ManageAI web automation.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        if not self.available:
            logger.error("ManageAI web automation not available")
            return []
        
        try:
            logger.info(f"Searching Indeed with ManageAI for '{query}' in '{location or 'any location'}'")
            
            # Construct the search task
            task_description = f"Navigate to Indeed, search for '{query}'"
            if location:
                task_description += f" in '{location}'"
            task_description += f", and extract the top {limit} job listings with details like title, company, location, and description"
            
            payload = {
                "task": task_description,
                "url": "https://www.indeed.com",
                "job_title": query,
                "location": location or "",
                "extract_jobs": True,
                "limit": limit
            }
            
            response = requests.post(
                f"{self.api_url}/web/task",
                json=payload,
                timeout=120  # Job searches can take a while
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # Extract job listings from the result
                    jobs = self._parse_job_results(result, "Indeed (ManageAI)")
                    logger.info(f"Found {len(jobs)} jobs on Indeed using ManageAI")
                    return jobs
                else:
                    logger.error(f"Indeed search failed: {result.get('error', 'Unknown error')}")
                    return []
            else:
                logger.error(f"Indeed search request failed: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching Indeed with ManageAI: {e}")
            return []
    
    def search_linkedin_jobs(self, query: str, location: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on LinkedIn using ManageAI web automation.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        if not self.available:
            logger.error("ManageAI web automation not available")
            return []
        
        try:
            logger.info(f"Searching LinkedIn with ManageAI for '{query}' in '{location or 'any location'}'")
            
            # Construct the search task
            task_description = f"Navigate to LinkedIn Jobs, search for '{query}'"
            if location:
                task_description += f" in '{location}'"
            task_description += f", and extract the top {limit} job listings with details like title, company, location, and description"
            
            payload = {
                "task": task_description,
                "url": "https://www.linkedin.com/jobs",
                "job_title": query,
                "location": location or "",
                "extract_jobs": True,
                "limit": limit
            }
            
            response = requests.post(
                f"{self.api_url}/web/task",
                json=payload,
                timeout=120  # Job searches can take a while
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # Extract job listings from the result
                    jobs = self._parse_job_results(result, "LinkedIn (ManageAI)")
                    logger.info(f"Found {len(jobs)} jobs on LinkedIn using ManageAI")
                    return jobs
                else:
                    logger.error(f"LinkedIn search failed: {result.get('error', 'Unknown error')}")
                    return []
            else:
                logger.error(f"LinkedIn search request failed: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching LinkedIn with ManageAI: {e}")
            return []
    
    def extract_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Extract detailed information from a job posting.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Extracted job details
        """
        if not self.available:
            logger.error("ManageAI web automation not available")
            return {}
        
        try:
            logger.info(f"Extracting job details from: {job_url}")
            
            # Define selectors for common job posting elements
            selectors = {
                "title": "h1, .job-title, [data-testid='job-title']",
                "company": ".company-name, .employer, [data-testid='company-name']",
                "location": ".location, .job-location, [data-testid='job-location']",
                "salary": ".salary, .pay, [data-testid='salary']",
                "description": ".job-description, .description, [data-testid='job-description']",
                "requirements": ".requirements, .qualifications, [data-testid='requirements']",
                "posted_date": ".posted-date, .date-posted, [data-testid='posted-date']"
            }
            
            payload = {
                "url": job_url,
                "selectors": selectors
            }
            
            response = requests.post(
                f"{self.api_url}/web/extract",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info("Job details extracted successfully")
                    return result.get("extracted_data", {})
                else:
                    logger.error(f"Job details extraction failed: {result.get('error', 'Unknown error')}")
                    return {}
            else:
                logger.error(f"Job details extraction request failed: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error extracting job details: {e}")
            return {}
    
    def _parse_job_results(self, result: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
        """
        Parse job listings from ManageAI automation result.
        
        Args:
            result: Result from ManageAI web automation
            source: Source platform name
            
        Returns:
            List of formatted job postings
        """
        jobs = []
        
        try:
            # Extract job data from result
            job_data = result.get("data", {})
            extracted_jobs = job_data.get("jobs", [])
            
            if not extracted_jobs and "extracted_data" in result:
                # Alternative structure
                extracted_jobs = result["extracted_data"].get("jobs", [])
            
            # If we still don't have jobs, try to parse from text
            if not extracted_jobs and "text" in result:
                extracted_jobs = self._parse_jobs_from_text(result["text"])
            
            for i, job in enumerate(extracted_jobs):
                if isinstance(job, dict):
                    formatted_job = {
                        "id": f"{source.lower().replace(' ', '-')}-{i}",
                        "title": job.get("title", "Unknown Title"),
                        "company": job.get("company", "Unknown Company"),
                        "location": job.get("location", "Unknown Location"),
                        "description": job.get("description", "No description available"),
                        "url": job.get("url", ""),
                        "source": source
                    }
                    jobs.append(formatted_job)
            
            # If we still don't have any jobs, create placeholder entries
            if not jobs:
                logger.warning(f"No jobs could be parsed from {source} result")
                jobs = [{
                    "id": f"{source.lower().replace(' ', '-')}-placeholder",
                    "title": "Job search completed",
                    "company": "Multiple companies",
                    "location": "Various locations",
                    "description": "Job search was executed but results need manual review",
                    "url": "",
                    "source": source
                }]
            
        except Exception as e:
            logger.error(f"Error parsing job results from {source}: {e}")
            jobs = [{
                "id": f"{source.lower().replace(' ', '-')}-error",
                "title": "Error parsing results",
                "company": "Unknown",
                "location": "Unknown",
                "description": f"Error occurred while parsing job results: {str(e)}",
                "url": "",
                "source": source
            }]
        
        return jobs
    
    def _parse_jobs_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse job listings from text response.
        
        Args:
            text: Text response containing job information
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            # Simple text parsing - can be enhanced
            lines = text.split('\n')
            current_job = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for job indicators
                if any(keyword in line.lower() for keyword in ['job title:', 'position:', 'title:']):
                    if current_job and 'title' in current_job:
                        jobs.append(current_job)
                        current_job = {}
                    
                    title = line.split(':', 1)[1].strip() if ':' in line else line
                    current_job['title'] = title
                
                elif any(keyword in line.lower() for keyword in ['company:', 'employer:']):
                    company = line.split(':', 1)[1].strip() if ':' in line else line
                    current_job['company'] = company
                
                elif any(keyword in line.lower() for keyword in ['location:', 'city:']):
                    location = line.split(':', 1)[1].strip() if ':' in line else line
                    current_job['location'] = location
                
                elif any(keyword in line.lower() for keyword in ['description:', 'summary:']):
                    description = line.split(':', 1)[1].strip() if ':' in line else line
                    current_job['description'] = description
            
            # Don't forget the last job
            if current_job and 'title' in current_job:
                jobs.append(current_job)
            
        except Exception as e:
            logger.error(f"Error parsing jobs from text: {e}")
        
        return jobs

# Singleton instance
manageai_web_client = ManageAIWebAutomationClient()
