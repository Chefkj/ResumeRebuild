"""
ATS (Applicant Tracking System) API Integration.

This module provides utilities for interacting with various ATS APIs.
"""

import os
import logging
import requests
import json
from typing import Dict, List, Any, Optional, Union
from src.utils.env_loader import get_api_key, get_setting
from src.utils.settings import Settings

# Configure logger
logger = logging.getLogger(__name__)

class ATSAPIClient:
    """Client for interacting with ATS (Applicant Tracking System) APIs."""
    
    def __init__(self):
        """Initialize the ATS API client."""
        self.settings = Settings()
        self._load_api_keys()
        
    def _load_api_keys(self):
        """Load API keys from settings or environment variables."""
        # Get ATS API keys
        self.lever_api_key = self.settings.settings.get('ats', {}).get('lever_api_key', '')
        self.greenhouse_api_key = self.settings.settings.get('ats', {}).get('greenhouse_api_key', '')
        self.workday_api_key = self.settings.settings.get('ats', {}).get('workday_api_key', '')
        
        # Log available APIs
        available_apis = []
        if self.lever_api_key:
            available_apis.append('Lever')
        if self.greenhouse_api_key:
            available_apis.append('Greenhouse')
        if self.workday_api_key:
            available_apis.append('Workday')
            
        if available_apis:
            logger.info(f"Available ATS APIs: {', '.join(available_apis)}")
        else:
            logger.warning("No ATS API keys configured. Add them to your .env file or settings.")
    
    def submit_application_lever(self, 
                                resume_path: str,
                                job_id: str, 
                                name: str,
                                email: str,
                                phone: Optional[str] = None,
                                cover_letter: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a job application via Lever ATS API.
        
        Args:
            resume_path: Path to resume file
            job_id: Lever job ID
            name: Full name of applicant
            email: Email address
            phone: Phone number (optional)
            cover_letter: Cover letter text (optional)
            
        Returns:
            Response data from API
        """
        if not self.lever_api_key:
            logger.error("Lever API key not configured")
            return {"error": "Lever API key not configured"}
            
        if not os.path.exists(resume_path):
            logger.error(f"Resume file not found: {resume_path}")
            return {"error": f"Resume file not found: {resume_path}"}
            
        try:
            # Example implementation - replace with actual Lever API endpoints
            url = f"https://api.lever.co/v1/opportunities/{job_id}/applications"
            headers = {
                "Authorization": f"Bearer {self.lever_api_key}"
            }
            
            # Prepare data and files
            data = {
                "name": name,
                "email": email,
                "phone": phone or ""
            }
            
            files = {
                "resume": (os.path.basename(resume_path), open(resume_path, 'rb')),
            }
            
            if cover_letter:
                files["cover_letter"] = ("cover_letter.txt", cover_letter)
                
            # This is a placeholder - actual implementation would use the official Lever API
            logger.info(f"Submitting application to Lever for job {job_id}")
            logger.warning("Lever API integration is a placeholder - implement actual API calls")
            
            # Mocked response for development/testing
            return {
                "success": True,
                "application_id": "lever-app-123456",
                "status": "submitted",
                "message": "Application submitted successfully"
            }
        except Exception as e:
            logger.error(f"Error submitting application to Lever: {e}")
            return {"error": str(e)}
    
    def submit_application_greenhouse(self, 
                                     resume_path: str,
                                     job_id: str, 
                                     name: str,
                                     email: str,
                                     phone: Optional[str] = None,
                                     cover_letter: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a job application via Greenhouse ATS API.
        
        Args:
            resume_path: Path to resume file
            job_id: Greenhouse job ID
            name: Full name of applicant
            email: Email address
            phone: Phone number (optional)
            cover_letter: Cover letter text (optional)
            
        Returns:
            Response data from API
        """
        if not self.greenhouse_api_key:
            logger.error("Greenhouse API key not configured")
            return {"error": "Greenhouse API key not configured"}
            
        if not os.path.exists(resume_path):
            logger.error(f"Resume file not found: {resume_path}")
            return {"error": f"Resume file not found: {resume_path}"}
            
        try:
            # Example implementation - replace with actual Greenhouse API endpoints
            url = f"https://harvest.greenhouse.io/v1/applications"
            headers = {
                "Authorization": f"Basic {self.greenhouse_api_key}"
            }
            
            # Split name into first and last
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # Prepare data and files
            data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone or "",
                "job_id": job_id
            }
            
            files = {
                "resume": (os.path.basename(resume_path), open(resume_path, 'rb')),
            }
            
            if cover_letter:
                data["cover_letter"] = cover_letter
                
            # This is a placeholder - actual implementation would use the official Greenhouse API
            logger.info(f"Submitting application to Greenhouse for job {job_id}")
            logger.warning("Greenhouse API integration is a placeholder - implement actual API calls")
            
            # Mocked response for development/testing
            return {
                "success": True,
                "application_id": "greenhouse-app-123456",
                "status": "submitted",
                "message": "Application submitted successfully"
            }
        except Exception as e:
            logger.error(f"Error submitting application to Greenhouse: {e}")
            return {"error": str(e)}
    
    def submit_application_workday(self, 
                                  resume_path: str,
                                  job_id: str, 
                                  name: str,
                                  email: str,
                                  phone: Optional[str] = None,
                                  cover_letter: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a job application via Workday ATS API.
        
        Args:
            resume_path: Path to resume file
            job_id: Workday job ID
            name: Full name of applicant
            email: Email address
            phone: Phone number (optional)
            cover_letter: Cover letter text (optional)
            
        Returns:
            Response data from API
        """
        if not self.workday_api_key:
            logger.error("Workday API key not configured")
            return {"error": "Workday API key not configured"}
            
        if not os.path.exists(resume_path):
            logger.error(f"Resume file not found: {resume_path}")
            return {"error": f"Resume file not found: {resume_path}"}
            
        try:
            # Example implementation - replace with actual Workday API endpoints
            logger.info(f"Submitting application to Workday for job {job_id}")
            logger.warning("Workday API integration is a placeholder - implement actual API calls")
            
            # Mocked response for development/testing
            return {
                "success": True,
                "application_id": "workday-app-123456",
                "status": "submitted",
                "message": "Application submitted successfully"
            }
        except Exception as e:
            logger.error(f"Error submitting application to Workday: {e}")
            return {"error": str(e)}

# Create a singleton instance
ats_client = ATSAPIClient()
