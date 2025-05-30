"""
LLM-based resume refinement module.

This module uses your local ManageAI API to refine and improve extracted resume content.
"""

import os
import json
import logging
import requests
import time
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default ManageAI API configuration
DEFAULT_API_URL = "http://localhost:8080"


class LLMRefiner:
    """
    Class for refining extracted resume content using LLM capabilities via ManageAI API.
    
    Uses the local ManageAI API to improve structure, fix formatting issues,
    and enhance the overall quality of extracted resume content.
    """
    
    def __init__(self, api_url=None):
        """
        Initialize the LLM refiner with API settings.
        
        Args:
            api_url: URL to the ManageAI API (default: http://localhost:8080)
        """
        self.api_url = api_url or os.environ.get("MANAGERAI_API_URL", DEFAULT_API_URL)
        
        # Ensure API URL doesn't have a trailing slash
        if self.api_url.endswith('/'):
            self.api_url = self.api_url[:-1]
            
        logger.info(f"Initialized LLM Refiner with API URL: {self.api_url}")
        self._check_api_connection()
    
    def _check_api_connection(self):
        """Check if the ManageAI API is accessible."""
        try:
            response = requests.get(f"{self.api_url}/", timeout=5)
            response.raise_for_status()
            logger.info("Successfully connected to ManageAI API")
            return True
        except requests.RequestException as e:
            logger.warning(f"Unable to connect to ManageAI API: {e}")
            logger.warning("Resume refinement will be limited without API access")
            return False
    
    def refine_resume(self, resume_content, job_description=None):
        """
        Refine the extracted resume content using LLM.
        
        Args:
            resume_content: Resume content object or text
            job_description: Optional job description to tailor the resume for
            
        Returns:
            Refined resume content
        """
        # Create a deep copy to avoid modifying the original
        from copy import deepcopy
        refined_content = deepcopy(resume_content)
        
        # Convert resume content to string if it's an object
        resume_text = self._extract_text(resume_content)
        
        if not resume_text:
            logger.error("No resume text could be extracted")
            return refined_content
        
        # If job description is provided, use the matching endpoint
        if job_description:
            improved_resume = self._improve_resume_for_job(resume_text, job_description)
        else:
            # Otherwise, just analyze and improve the resume
            improved_resume = self._analyze_and_improve_resume(resume_text)
        
        if improved_resume:
            # Update the resume content with the improved text
            self._update_resume_content(refined_content, improved_resume)
        else:
            logger.warning("Failed to get improved resume from API, returning original")
            
        return refined_content
    
    def _extract_text(self, resume_content) -> str:
        """Extract plain text from resume content object."""
        # If it's already a string, return it
        if isinstance(resume_content, str):
            return resume_content
        
        # If it's a ResumeContent object with sections
        if hasattr(resume_content, 'sections'):
            # Join all section contents
            sections_text = []
            
            # Add contact info if available
            if hasattr(resume_content, 'contact_info'):
                contact_text = self._dict_to_text(resume_content.contact_info)
                if contact_text:
                    sections_text.append(contact_text)
            
            # Add each section's content
            for section in resume_content.sections:
                if hasattr(section, 'title') and hasattr(section, 'content'):
                    sections_text.append(f"{section.title}\n{section.content}")
                    
            return "\n\n".join(sections_text)
        
        # Try to convert to string as a last resort
        try:
            return str(resume_content)
        except Exception as e:
            logger.error(f"Failed to convert resume content to text: {e}")
            return ""
    
    def _dict_to_text(self, data_dict) -> str:
        """Convert a dictionary to formatted text."""
        if not isinstance(data_dict, dict):
            return str(data_dict)
            
        lines = []
        for key, value in data_dict.items():
            if value:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _analyze_and_improve_resume(self, resume_text) -> Optional[str]:
        """
        Analyze and improve a resume without a specific job target.
        
        Args:
            resume_text: Plain text resume content
            
        Returns:
            Improved resume text or None if operation failed
        """
        # First, analyze the resume
        analyze_url = f"{self.api_url}/analyze/resume"
        
        try:
            # Try up to 3 times with exponential backoff
            for attempt in range(3):
                try:
                    analyze_response = requests.post(
                        analyze_url,
                        json={"resume": resume_text},
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    analyze_response.raise_for_status()
                    break
                except requests.RequestException as e:
                    wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                    if attempt < 2:  # Don't wait after the last attempt
                        logger.warning(f"API request failed, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        raise
            
            # Get analysis result
            analysis = analyze_response.json()
            if not analysis.get("success", False):
                logger.error(f"Resume analysis failed: {analysis.get('error', 'Unknown error')}")
                return None
            
            # Use the improve endpoint with a generic improvement request
            improve_url = f"{self.api_url}/improve"
            
            # Create a generic job description for general improvements
            generic_job = (
                "Seeking a professional with excellent communication skills, "
                "attention to detail, and strong organizational abilities. "
                "The ideal candidate will have demonstrated experience in their field, "
                "be able to work both independently and as part of a team, and "
                "show a track record of achieving results."
            )
            
            improve_response = requests.post(
                improve_url,
                json={
                    "resume": resume_text,
                    "job_description": generic_job,
                    "match_result": None
                },
                headers={"Content-Type": "application/json"},
                timeout=60  # Longer timeout for improvement
            )
            improve_response.raise_for_status()
            
            # Get improvement result
            improvement = improve_response.json()
            if not improvement.get("success", False):
                logger.error(f"Resume improvement failed: {improvement.get('error', 'Unknown error')}")
                return None
            
            return improvement.get("improved_resume")
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during resume analysis and improvement: {e}")
            return None
    
    def _improve_resume_for_job(self, resume_text, job_description) -> Optional[str]:
        """
        Improve a resume targeting a specific job description.
        
        Args:
            resume_text: Plain text resume content
            job_description: Job description to target
            
        Returns:
            Improved resume text or None if operation failed
        """
        try:
            # Use the match endpoint to get match analysis
            match_url = f"{self.api_url}/match"
            
            for attempt in range(3):
                try:
                    match_response = requests.post(
                        match_url,
                        json={
                            "resume": resume_text,
                            "job_description": job_description
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=45  # Matching can take longer
                    )
                    match_response.raise_for_status()
                    break
                except requests.RequestException as e:
                    wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                    if attempt < 2:  # Don't wait after the last attempt
                        logger.warning(f"API request failed, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        raise
                        
            # Get match result
            match_result = match_response.json()
            if not match_result.get("success", False):
                logger.error(f"Resume-job matching failed: {match_result.get('error', 'Unknown error')}")
                # Continue anyway, we can still try to improve without match results
            
            # Use the improve endpoint
            improve_url = f"{self.api_url}/improve"
            
            improve_response = requests.post(
                improve_url,
                json={
                    "resume": resume_text,
                    "job_description": job_description,
                    "match_result": match_result if match_result.get("success", False) else None
                },
                headers={"Content-Type": "application/json"},
                timeout=60  # Longer timeout for improvement
            )
            improve_response.raise_for_status()
            
            # Get improvement result
            improvement = improve_response.json()
            if not improvement.get("success", False):
                logger.error(f"Resume improvement failed: {improvement.get('error', 'Unknown error')}")
                return None
            
            return improvement.get("improved_resume")
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during resume improvement: {e}")
            return None
            
    def _update_resume_content(self, resume_content, improved_text):
        """Update the resume content object with improved text."""
        if isinstance(resume_content, str):
            # If it's a string, return the improved text directly
            return improved_text
        
        try:
            # Try to extract sections from the improved text
            import re
            
            # If we have sections in the original resume
            if hasattr(resume_content, 'sections'):
                # Get all section titles from the original
                section_titles = [section.title for section in resume_content.sections 
                                 if hasattr(section, 'title')]
                
                # Extract content for each section from the improved text
                for i, section in enumerate(resume_content.sections):
                    if not hasattr(section, 'title'):
                        continue
                        
                    title = section.title
                    
                    # Create a pattern to find this section in the improved text
                    pattern = rf"(?:{re.escape(title)}|{title.upper()})[:\s]*\n+(.*?)(?:\n\n|\Z)"
                    
                    # Find next section title to use as delimiter (if not the last section)
                    next_delimiter = r"\Z"  # End of string by default
                    if i < len(section_titles) - 1:
                        next_title = section_titles[i+1]
                        next_delimiter = rf"(?:{re.escape(next_title)}|{next_title.upper()})"
                    
                    # Complete pattern with next section delimiter
                    pattern = rf"(?:{re.escape(title)}|{title.upper()})[:\s]*\n+(.*?)(?:\n+{next_delimiter}|\Z)"
                    
                    # Try to find the section content
                    match = re.search(pattern, improved_text, re.DOTALL)
                    if match:
                        # Update the section content
                        new_content = match.group(1).strip()
                        if new_content:
                            section.content = new_content
            
            # Update contact info if available
            if hasattr(resume_content, 'contact_info'):
                # Try to extract contact info from the beginning of the text
                contact_match = re.search(r'\A(.*?)(?:\n\n|\Z)', improved_text, re.DOTALL)
                if contact_match:
                    contact_text = contact_match.group(1).strip()
                    
                    # Try to update individual fields
                    for field in resume_content.contact_info:
                        # Look for "Field: value" patterns
                        field_match = re.search(rf"{re.escape(field)}:?\s*([^\n]+)", 
                                              contact_text, re.IGNORECASE)
                        if field_match:
                            resume_content.contact_info[field] = field_match.group(1).strip()
                    
        except Exception as e:
            logger.error(f"Failed to update resume content with improved text: {e}")
            
        return resume_content


# Simple test function
def test_refiner():
    """Test the LLM refiner with a sample resume."""
    # Sample resume text
    sample_resume = """
    John Doe
    Software Developer
    email@example.com | (555) 123-4567
    
    EDUCATION
    Bachelor of Science in Computer Science, University of Technology
    2018-2022
    
    EXPERIENCE
    Software Developer, Tech Company Inc.
    June 2022 - Present
    - Developed REST APIs using Python and Flask
    - Implemented CI/CD pipelines using Jenkins
    - Optimized database queries resulting in 30% performance improvement
    """
    
    # Sample job description
    sample_job = """
    Senior Software Engineer
    
    Requirements:
    - 5+ years of experience in software development
    - Expert in Python and JavaScript
    - Experience with cloud platforms (AWS/Azure)
    """
    
    # Initialize refiner
    refiner = LLMRefiner()
    
    # Test refinement without job description
    print("Testing general resume refinement...")
    refined_general = refiner.refine_resume(sample_resume)
    
    # Test refinement with job description
    print("Testing job-specific resume refinement...")
    refined_targeted = refiner.refine_resume(sample_resume, sample_job)
    
    return {
        "original": sample_resume,
        "refined_general": refined_general,
        "refined_targeted": refined_targeted
    }


if __name__ == "__main__":
    test_results = test_refiner()
    print("\nTest complete.")