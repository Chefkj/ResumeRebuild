#!/usr/bin/env python3
"""
Job Finder

This tool helps you search for job listings from various sources and
analyze them for compatibility with your resume and skills.
"""

import os
import sys
import re
import json
import argparse
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from bs4 import BeautifulSoup
import time
import urllib.parse
import hashlib
import hmac
import base64
import uuid
from abc import ABC, abstractmethod

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API configuration
API_CONFIG_FILE = "job_api_config.json"

# Import job analyzer if available
try:
    from src.utils.job_analyzer import JobAnalyzer
    JOB_ANALYZER_AVAILABLE = True
except ImportError:
    JOB_ANALYZER_AVAILABLE = False
    logger.warning("JobAnalyzer not available. Some features will be limited.")

# Constants
DEFAULT_JOB_SEARCH_SITES = ["linkedin", "indeed", "glassdoor"]
JOB_SEARCH_LIMIT = 10
JOB_SEARCH_CACHE_DIR = "job_search_cache"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

class JobFinderException(Exception):
    """Exception raised for errors in the JobFinder module."""
    pass

class JobAPIClient(ABC):
    """Abstract base class for job API clients."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def search_jobs(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """
        Search for jobs using the API.
        
        Args:
            query: Search query string
            location: Location to search in
            limit: Maximum number of results to return
            
        Returns:
            List of job data dictionaries
        """
        pass
    
    @staticmethod
    def format_description(description: str) -> str:
        """Format job description for display."""
        # Remove HTML tags
        if description:
            soup = BeautifulSoup(description, "html.parser")
            return soup.get_text().strip()
        return ""

class LinkedInAPIClient(JobAPIClient):
    """LinkedIn Jobs API client."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.access_token = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with LinkedIn API."""
        if not self.config.get("client_id") or not self.config.get("client_secret"):
            logger.warning("LinkedIn API credentials not configured. Using simulation mode.")
            return
            
        try:
            # LinkedIn uses OAuth 2.0
            auth_url = "https://www.linkedin.com/oauth/v2/accessToken"
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.config["client_id"],
                "client_secret": self.config["client_secret"]
            }
            
            response = requests.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            auth_result = response.json()
            self.access_token = auth_result.get("access_token")
            
            logger.info("Successfully authenticated with LinkedIn API")
        except Exception as e:
            logger.error(f"LinkedIn authentication error: {str(e)}")
            self.access_token = None
    
    def search_jobs(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Search for jobs on LinkedIn."""
        if not self.access_token:
            logger.warning("LinkedIn API not authenticated, using simulation mode")
            return self._simulated_search(query, location, limit)
        
        try:
            # LinkedIn Jobs Search API v2
            search_url = "https://api.linkedin.com/v2/jobSearch"
            
            # Prepare parameters
            params = {
                "keywords": query,
                "count": min(limit, 50),  # API limit
            }
            
            if location:
                params["location"] = location
            
            # Set up headers with access token
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json"
            }
            
            response = requests.get(search_url, params=params, headers=headers)
            response.raise_for_status()
            
            job_data = response.json()
            return self._parse_linkedin_jobs(job_data)
        except Exception as e:
            logger.error(f"LinkedIn API error: {str(e)}")
            logger.info("Falling back to simulation mode")
            return self._simulated_search(query, location, limit)
    
    def _parse_linkedin_jobs(self, job_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse LinkedIn API response into job dictionaries."""
        jobs = []
        
        # Extract job elements from the response
        elements = job_data.get("elements", [])
        
        for element in elements:
            try:
                job_view = element.get("jobView", {})
                
                job = {
                    "title": job_view.get("title", "Unknown Title"),
                    "company": job_view.get("company", {}).get("name", "Unknown Company"),
                    "location": job_view.get("location", "Unknown Location"),
                    "description": self.format_description(job_view.get("description", "")),
                    "url": job_view.get("jobApplyUrl", ""),
                    "source": "linkedin",
                    "date_posted": job_view.get("listedAt", ""),
                    "job_id": job_view.get("jobUrn", "")
                }
                
                # Add salary if available
                compensation = job_view.get("compensationDetails", {})
                if compensation:
                    min_salary = compensation.get("minCompensation", {}).get("amount")
                    max_salary = compensation.get("maxCompensation", {}).get("amount")
                    currency = compensation.get("currency", "USD")
                    
                    if min_salary and max_salary:
                        job["salary"] = f"{currency} {min_salary:,} - {currency} {max_salary:,}"
                    elif min_salary:
                        job["salary"] = f"{currency} {min_salary:,}+"
                
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing LinkedIn job: {str(e)}")
        
        return jobs
    
    def _simulated_search(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Simulated LinkedIn job search for testing."""
        logger.info("Using simulated LinkedIn job data")
        
        dummy_jobs = [
            {
                "title": "Software Engineer",
                "company": "LinkedIn",
                "location": location or "Remote",
                "description": (
                    "Software Engineer position requiring 3+ years of experience with "
                    "Python development, web frameworks, and cloud infrastructure. Must have "
                    "strong problem-solving skills and ability to work in a team."
                ),
                "url": "https://linkedin.com/jobs/view/software-engineer",
                "source": "linkedin",
                "salary": "$120,000 - $150,000",
                "date_posted": "3 days ago",
                "job_id": f"linkedin_{uuid.uuid4().hex[:8]}"
            },
            {
                "title": "Full Stack Developer",
                "company": "Tech Innovations Inc.",
                "location": location or "San Francisco, CA",
                "description": (
                    "Full Stack Developer role working with React, Node.js, and Python. "
                    "Building modern web applications with cloud infrastructure on AWS. "
                    "Must have experience with CI/CD pipelines and automated testing."
                ),
                "url": "https://linkedin.com/jobs/view/full-stack-developer",
                "source": "linkedin",
                "salary": "$130,000 - $160,000",
                "date_posted": "1 week ago",
                "job_id": f"linkedin_{uuid.uuid4().hex[:8]}"
            },
            {
                "title": f"{query} Specialist",
                "company": "Dynamic Solutions",
                "location": location or "Chicago, IL",
                "description": (
                    f"As a {query} Specialist, you will be responsible for developing "
                    "innovative solutions to complex problems. Requires experience with "
                    "latest technologies and a passion for learning."
                ),
                "url": f"https://linkedin.com/jobs/view/{query.lower().replace(' ', '-')}-specialist",
                "source": "linkedin",
                "salary": "$115,000 - $145,000",
                "date_posted": "2 days ago",
                "job_id": f"linkedin_{uuid.uuid4().hex[:8]}"
            }
        ]
        
        # Add query-specific jobs
        keywords = query.lower().split()
        for keyword in keywords[:2]:  # Limit to first two keywords
            dummy_jobs.append({
                "title": f"Senior {keyword.title()} Developer",
                "company": f"{keyword.title()} Technologies",
                "location": location or "New York, NY",
                "description": (
                    f"Senior {keyword.title()} Developer role for an experienced professional. "
                    f"Deep expertise in {keyword} required, along with 5+ years of professional "
                    "development experience. You will lead projects and mentor junior developers."
                ),
                "url": f"https://linkedin.com/jobs/view/senior-{keyword.lower()}-developer",
                "source": "linkedin",
                "salary": "$140,000 - $180,000",
                "date_posted": "Just posted",
                "job_id": f"linkedin_{uuid.uuid4().hex[:8]}"
            })
        
        return dummy_jobs[:limit]

class IndeedAPIClient(JobAPIClient):
    """Indeed Jobs API client."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.publisher_id = self.config.get("publisher_id")
        self.api_key = self.config.get("api_key")
    
    def search_jobs(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Search for jobs on Indeed."""
        if not self.publisher_id or not self.api_key:
            logger.warning("Indeed API credentials not configured. Using simulation mode.")
            return self._simulated_search(query, location, limit)
        
        try:
            # Indeed Job Search API
            search_url = "https://api.indeed.com/ads/apisearch"
            
            # Prepare parameters
            params = {
                "publisher": self.publisher_id,
                "v": "2",  # API version
                "format": "json",
                "q": query,
                "limit": min(limit, 25),  # API limit
                "userip": "1.2.3.4",  # Required parameter (dummy IP)
                "useragent": USER_AGENT
            }
            
            if location:
                params["l"] = location
            
            # Add API key in header or as parameter based on Indeed's requirements
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(search_url, params=params, headers=headers)
            response.raise_for_status()
            
            job_data = response.json()
            return self._parse_indeed_jobs(job_data)
        except Exception as e:
            logger.error(f"Indeed API error: {str(e)}")
            logger.info("Falling back to simulation mode")
            return self._simulated_search(query, location, limit)
    
    def _parse_indeed_jobs(self, job_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Indeed API response into job dictionaries."""
        jobs = []
        
        # Extract job results from the response
        results = job_data.get("results", [])
        
        for result in results:
            try:
                job = {
                    "title": result.get("jobtitle", "Unknown Title"),
                    "company": result.get("company", "Unknown Company"),
                    "location": result.get("formattedLocation", result.get("city", "")),
                    "description": self.format_description(result.get("snippet", "")),
                    "url": result.get("url", ""),
                    "source": "indeed",
                    "date_posted": result.get("formattedRelativeTime", ""),
                    "job_id": result.get("jobkey", f"indeed_{uuid.uuid4().hex[:8]}")
                }
                
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing Indeed job: {str(e)}")
        
        return jobs
    
    def _simulated_search(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Simulated Indeed job search for testing."""
        logger.info("Using simulated Indeed job data")
        
        dummy_jobs = [
            {
                "title": "Data Scientist",
                "company": "DataCorp",
                "location": location or "Boston, MA",
                "description": (
                    "Data Scientist role requiring experience with machine learning, "
                    "Python, and data visualization tools. You'll work on complex data "
                    "problems and develop models to drive business decisions."
                ),
                "url": "https://indeed.com/jobs/view/data-scientist",
                "source": "indeed",
                "salary": "$140,000 - $160,000",
                "date_posted": "2 days ago",
                "job_id": f"indeed_{uuid.uuid4().hex[:8]}"
            },
            {
                "title": "Frontend Developer",
                "company": "WebSolutions LLC",
                "location": location or "Austin, TX",
                "description": (
                    "Frontend Developer position focused on React and modern JavaScript. "
                    "Working on user interfaces for enterprise applications with a focus "
                    "on accessibility and performance optimization."
                ),
                "url": "https://indeed.com/jobs/view/frontend-developer",
                "source": "indeed",
                "salary": "$110,000 - $130,000",
                "date_posted": "5 days ago",
                "job_id": f"indeed_{uuid.uuid4().hex[:8]}"
            },
            {
                "title": f"{query} Engineer",
                "company": "Innovative Technologies",
                "location": location or "Denver, CO",
                "description": (
                    f"Looking for a skilled {query} Engineer to join our growing team. "
                    "You'll be working with cutting-edge technologies to solve complex "
                    "problems and deliver high-quality solutions to our clients."
                ),
                "url": f"https://indeed.com/jobs/view/{query.lower().replace(' ', '-')}-engineer",
                "source": "indeed",
                "salary": "$125,000 - $155,000",
                "date_posted": "1 day ago",
                "job_id": f"indeed_{uuid.uuid4().hex[:8]}"
            }
        ]
        
        # Add query-specific jobs
        keywords = query.lower().split()
        for keyword in keywords[:2]:  # Limit to first two keywords
            dummy_jobs.append({
                "title": f"{keyword.title()} Developer",
                "company": f"Best {keyword.title()} Solutions",
                "location": location or "Remote",
                "description": (
                    f"We're looking for a talented {keyword.title()} Developer to join our team. "
                    f"You'll be responsible for developing and maintaining {keyword}-based applications "
                    "and collaborating with cross-functional teams to deliver high-quality software."
                ),
                "url": f"https://indeed.com/jobs/view/{keyword.lower()}-developer",
                "source": "indeed",
                "salary": "$120,000 - $150,000",
                "date_posted": "3 days ago",
                "job_id": f"indeed_{uuid.uuid4().hex[:8]}"
            })
        
        return dummy_jobs[:limit]

class GlassdoorAPIClient(JobAPIClient):
    """Glassdoor Jobs API client."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.partner_id = self.config.get("partner_id")
        self.api_key = self.config.get("api_key")
    
    def search_jobs(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Search for jobs on Glassdoor."""
        if not self.partner_id or not self.api_key:
            logger.warning("Glassdoor API credentials not configured. Using simulation mode.")
            return self._simulated_search(query, location, limit)
        
        try:
            # Glassdoor Job Search API
            search_url = "https://api.glassdoor.com/api/api.htm"
            
            # Prepare parameters
            params = {
                "v": "1",
                "format": "json",
                "t.p": self.partner_id,
                "t.k": self.api_key,
                "action": "jobs-prog",
                "countryId": "1",  # US
                "jobTitle": query,
                "returnJobResults": "true",
                "limit": min(limit, 20)  # API limit
            }
            
            if location:
                params["location"] = location
            
            # Make request
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            job_data = response.json()
            return self._parse_glassdoor_jobs(job_data)
        except Exception as e:
            logger.error(f"Glassdoor API error: {str(e)}")
            logger.info("Falling back to simulation mode")
            return self._simulated_search(query, location, limit)
    
    def _parse_glassdoor_jobs(self, job_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Glassdoor API response into job dictionaries."""
        jobs = []
        
        # Extract job listings from response
        response = job_data.get("response", {})
        job_listings = response.get("jobListings", [])
        
        for listing in job_listings:
            try:
                job = {
                    "title": listing.get("jobTitle", "Unknown Title"),
                    "company": listing.get("employer", {}).get("name", "Unknown Company"),
                    "location": listing.get("location", ""),
                    "description": self.format_description(listing.get("jobDescription", "")),
                    "url": listing.get("applyUrl", ""),
                    "source": "glassdoor",
                    "date_posted": listing.get("postingDate", ""),
                    "job_id": str(listing.get("jobListingId", f"glassdoor_{uuid.uuid4().hex[:8]}"))
                }
                
                # Add salary if available
                pay_info = listing.get("salarySourceAndRange", {})
                if pay_info:
                    min_pay = pay_info.get("min")
                    max_pay = pay_info.get("max")
                    pay_period = pay_info.get("payPeriod", "")
                    
                    if min_pay and max_pay:
                        job["salary"] = f"${min_pay:,} - ${max_pay:,} {pay_period}"
                    elif min_pay:
                        job["salary"] = f"${min_pay:,}+ {pay_period}"
                
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing Glassdoor job: {str(e)}")
        
        return jobs
    
    def _simulated_search(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Simulated Glassdoor job search for testing."""
        logger.info("Using simulated Glassdoor job data")
        
        dummy_jobs = [
            {
                "title": "Backend Engineer",
                "company": "ServerTech",
                "location": location or "Seattle, WA",
                "description": (
                    "Backend Engineer position working with microservices architecture "
                    "on AWS. Experience with Python, Java, or Go required. Must have "
                    "experience with database design and API development."
                ),
                "url": "https://glassdoor.com/jobs/view/backend-engineer",
                "source": "glassdoor",
                "salary": "$125,000 - $155,000",
                "date_posted": "1 day ago",
                "job_id": f"glassdoor_{uuid.uuid4().hex[:8]}"
            },
            {
                "title": "DevOps Engineer",
                "company": "CloudOps",
                "location": location or "New York, NY",
                "description": (
                    "DevOps Engineer role focusing on Kubernetes, Docker, and CI/CD "
                    "pipelines. You'll be responsible for maintaining cloud infrastructure "
                    "and improving deployment processes."
                ),
                "url": "https://glassdoor.com/jobs/view/devops-engineer",
                "source": "glassdoor",
                "salary": "$130,000 - $170,000",
                "date_posted": "3 days ago",
                "job_id": f"glassdoor_{uuid.uuid4().hex[:8]}"
            },
            {
                "title": f"Senior {query} Architect",
                "company": "Enterprise Solutions",
                "location": location or "Miami, FL",
                "description": (
                    f"Senior {query} Architect role for an experienced professional. "
                    "You will be responsible for designing and implementing large-scale "
                    "systems, mentoring team members, and setting technical direction."
                ),
                "url": f"https://glassdoor.com/jobs/view/senior-{query.lower().replace(' ', '-')}-architect",
                "source": "glassdoor",
                "salary": "$150,000 - $190,000",
                "date_posted": "6 days ago",
                "job_id": f"glassdoor_{uuid.uuid4().hex[:8]}"
            }
        ]
        
        # Add query-specific jobs
        keywords = query.lower().split()
        for keyword in keywords[:2]:  # Limit to first two keywords
            dummy_jobs.append({
                "title": f"{keyword.title()} Solutions Architect",
                "company": f"{keyword.title()} Enterprises",
                "location": location or "Chicago, IL",
                "description": (
                    f"We're seeking an experienced {keyword.title()} Solutions Architect to "
                    f"lead our {keyword} initiatives. You'll work with stakeholders to understand "
                    "requirements and translate them into technical solutions."
                ),
                "url": f"https://glassdoor.com/jobs/view/{keyword.lower()}-solutions-architect",
                "source": "glassdoor",
                "salary": "$135,000 - $175,000",
                "date_posted": "1 week ago",
                "job_id": f"glassdoor_{uuid.uuid4().hex[:8]}"
            })
        
        return dummy_jobs[:limit]

class JobListing:
    """Class representing a job listing."""
    
    def __init__(self, title: str, company: str, location: str, 
                 description: str, url: str, source: str,
                 salary: Optional[str] = None, 
                 date_posted: Optional[str] = None,
                 job_id: Optional[str] = None):
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.url = url
        self.source = source
        self.salary = salary
        self.date_posted = date_posted
        self.job_id = job_id or self._generate_id()
        self.match_score = None
        self.matching_skills = []
        self.missing_skills = []
    
    def _generate_id(self) -> str:
        """Generate a unique ID for the job."""
        # Create a unique ID based on title, company, and some content
        unique_string = f"{self.title}_{self.company}_{self.description[:50]}"
        # Use the first 16 characters of the hash for brevity
        return f"{hash(unique_string) & 0xFFFFFFFF:08x}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "url": self.url,
            "source": self.source,
            "salary": self.salary,
            "date_posted": self.date_posted,
            "match_score": self.match_score,
            "matching_skills": self.matching_skills,
            "missing_skills": self.missing_skills
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobListing':
        """Create a JobListing object from a dictionary."""
        job = cls(
            title=data["title"],
            company=data["company"],
            location=data["location"],
            description=data["description"],
            url=data["url"],
            source=data["source"],
            salary=data.get("salary"),
            date_posted=data.get("date_posted"),
            job_id=data.get("job_id")
        )
        job.match_score = data.get("match_score")
        job.matching_skills = data.get("matching_skills", [])
        job.missing_skills = data.get("missing_skills", [])
        return job
    
    def __str__(self) -> str:
        """String representation of the job listing."""
        header = f"{self.title} - {self.company}"
        if self.match_score is not None:
            header += f" (Match: {self.match_score}%)"
        
        details = [
            f"Location: {self.location}",
            f"Source: {self.source}"
        ]
        
        if self.salary:
            details.append(f"Salary: {self.salary}")
        
        if self.date_posted:
            details.append(f"Posted: {self.date_posted}")
        
        result = [header, "-" * len(header)] + details
        
        # Add description preview
        desc_preview = self.description.strip()[:300]
        result.append(f"\nDescription: {desc_preview}...")
        
        # Add URL
        result.append(f"\nURL: {self.url}")
        
        return "\n".join(result)


class JobFinder:
    """Class for finding job listings from various sources."""
    
    def __init__(self, resume_path: Optional[str] = None, output_dir: str = "."):
        self.resume_path = resume_path
        self.resume_text = None
        self.output_dir = output_dir
        self.cache_dir = os.path.join(output_dir, JOB_SEARCH_CACHE_DIR)
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load resume text if provided
        if resume_path and os.path.exists(resume_path):
            with open(resume_path, 'r', encoding='utf-8') as f:
                self.resume_text = f.read()
        
        # Create job analyzer if available
        self.job_analyzer = JobAnalyzer() if JOB_ANALYZER_AVAILABLE else None
    
    def search_jobs(self, keywords: List[str], location: str = "", 
                  sources: List[str] = DEFAULT_JOB_SEARCH_SITES,
                  limit: int = JOB_SEARCH_LIMIT) -> List[JobListing]:
        """
        Search for job listings based on keywords and location.
        
        Args:
            keywords: List of job keywords to search for
            location: Job location to search in
            sources: List of job sources to search
            limit: Maximum number of results to return per source
            
        Returns:
            List of JobListing objects
        """
        all_results = []
        
        # Format keywords for search
        search_query = " ".join(keywords)
        
        # Search each source
        for source in sources:
            try:
                logger.info(f"Searching for jobs on {source}...")
                source_method = getattr(self, f"_search_{source}", None)
                if source_method:
                    results = source_method(search_query, location, limit)
                    all_results.extend(results)
                    logger.info(f"Found {len(results)} jobs on {source}")
                else:
                    logger.warning(f"No search method available for {source}")
            except Exception as e:
                logger.error(f"Error searching {source}: {str(e)}")
        
        # Sort results by relevance/match score if available
        all_results = sorted(all_results, key=lambda job: job.match_score or 0, reverse=True)
        
        # Cache the results
        self._cache_job_results(keywords, location, all_results)
        
        return all_results
    
    def _search_linkedin(self, query: str, location: str, limit: int) -> List[JobListing]:
        """Search for jobs on LinkedIn."""
        # Simulate search with basic data (replace with actual API calls in production)
        logger.info("Simulating LinkedIn search (replace with actual API call)")
        results = []
        
        # For testing, create some dummy jobs
        dummy_jobs = [
            JobListing(
                title="Software Engineer",
                company="LinkedIn",
                location="Remote" if not location else location,
                description=(
                    "Software Engineer position requiring 3+ years of experience with "
                    "Python development, web frameworks, and cloud infrastructure. Must have "
                    "strong problem-solving skills and ability to work in a team."
                ),
                url="https://linkedin.com/jobs/view/software-engineer",
                source="linkedin",
                salary="$120,000 - $150,000",
                date_posted="3 days ago"
            ),
            JobListing(
                title="Full Stack Developer",
                company="Tech Innovations Inc.",
                location="San Francisco, CA" if not location else location,
                description=(
                    "Full Stack Developer role working with React, Node.js, and Python. "
                    "Building modern web applications with cloud infrastructure on AWS. "
                    "Must have experience with CI/CD pipelines and automated testing."
                ),
                url="https://linkedin.com/jobs/view/full-stack-developer",
                source="linkedin",
                salary="$130,000 - $160,000",
                date_posted="1 week ago"
            )
        ]
        results.extend(dummy_jobs[:limit])
        
        return results
    
    def _search_indeed(self, query: str, location: str, limit: int) -> List[JobListing]:
        """Search for jobs on Indeed."""
        # Simulate search with basic data (replace with actual API calls in production)
        logger.info("Simulating Indeed search (replace with actual API call)")
        results = []
        
        # For testing, create some dummy jobs
        dummy_jobs = [
            JobListing(
                title="Data Scientist",
                company="DataCorp",
                location="Boston, MA" if not location else location,
                description=(
                    "Data Scientist role requiring experience with machine learning, "
                    "Python, and data visualization tools. You'll work on complex data "
                    "problems and develop models to drive business decisions."
                ),
                url="https://indeed.com/jobs/view/data-scientist",
                source="indeed",
                salary="$140,000 - $160,000",
                date_posted="2 days ago"
            ),
            JobListing(
                title="Frontend Developer",
                company="WebSolutions LLC",
                location="Austin, TX" if not location else location,
                description=(
                    "Frontend Developer position focused on React and modern JavaScript. "
                    "Working on user interfaces for enterprise applications with a focus "
                    "on accessibility and performance optimization."
                ),
                url="https://indeed.com/jobs/view/frontend-developer",
                source="indeed",
                salary="$110,000 - $130,000",
                date_posted="5 days ago"
            )
        ]
        results.extend(dummy_jobs[:limit])
        
        return results
    
    def _search_glassdoor(self, query: str, location: str, limit: int) -> List[JobListing]:
        """Search for jobs on Glassdoor."""
        # Simulate search with basic data (replace with actual API calls in production)
        logger.info("Simulating Glassdoor search (replace with actual API call)")
        results = []
        
        # For testing, create some dummy jobs
        dummy_jobs = [
            JobListing(
                title="Backend Engineer",
                company="ServerTech",
                location="Seattle, WA" if not location else location,
                description=(
                    "Backend Engineer position working with microservices architecture "
                    "on AWS. Experience with Python, Java, or Go required. Must have "
                    "experience with database design and API development."
                ),
                url="https://glassdoor.com/jobs/view/backend-engineer",
                source="glassdoor",
                salary="$125,000 - $155,000",
                date_posted="1 day ago"
            ),
            JobListing(
                title="DevOps Engineer",
                company="CloudOps",
                location="New York, NY" if not location else location,
                description=(
                    "DevOps Engineer role focusing on Kubernetes, Docker, and CI/CD "
                    "pipelines. You'll be responsible for maintaining cloud infrastructure "
                    "and improving deployment processes."
                ),
                url="https://glassdoor.com/jobs/view/devops-engineer",
                source="glassdoor",
                salary="$130,000 - $170,000",
                date_posted="3 days ago"
            )
        ]
        results.extend(dummy_jobs[:limit])
        
        return results
    
    def analyze_job_match(self, job: JobListing) -> Dict[str, Any]:
        """
        Analyze how well a job matches the user's resume.
        
        Args:
            job: JobListing object to analyze
            
        Returns:
            Dict with match information
        """
        if not self.job_analyzer or not self.resume_text:
            raise JobFinderException("Job analyzer or resume text not available")
        
        # Extract keywords from job description
        job_keywords = self.job_analyzer._extract_keywords(job.description)
        
        # Check which keywords from job are present in resume
        missing_keywords = []
        present_keywords = []
        
        for keyword in job_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', self.resume_text, re.IGNORECASE):
                present_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        # Calculate match score as percentage of present keywords
        if job_keywords:
            match_score = round((len(present_keywords) / len(job_keywords)) * 100)
        else:
            match_score = 0
        
        # Update the job listing with match information
        job.match_score = match_score
        job.matching_skills = present_keywords
        job.missing_skills = missing_keywords
        
        return {
            "match_score": match_score,
            "matching_skills": present_keywords,
            "missing_skills": missing_keywords
        }
    
    def _cache_job_results(self, keywords: List[str], location: str, results: List[JobListing]):
        """Cache job search results to a file."""
        # Create a unique filename based on search parameters
        search_id = f"{'-'.join(keywords)}_{location}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cache_file = os.path.join(self.cache_dir, f"job_search_{search_id}.json")
        
        # Convert results to dictionaries
        results_dict = [job.to_dict() for job in results]
        
        # Save to file
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                "search_params": {
                    "keywords": keywords,
                    "location": location,
                    "timestamp": datetime.now().isoformat()
                },
                "results": results_dict
            }, f, indent=2)
        
        logger.info(f"Cached {len(results)} job results to {cache_file}")
    
    def load_cached_results(self, cache_file: str) -> List[JobListing]:
        """Load job results from cache file."""
        cache_path = os.path.join(self.cache_dir, cache_file)
        
        if not os.path.exists(cache_path):
            raise JobFinderException(f"Cache file not found: {cache_path}")
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = [JobListing.from_dict(job_data) for job_data in data["results"]]
        return results
    
    def list_cached_searches(self) -> List[Dict[str, Any]]:
        """List all cached search results."""
        if not os.path.exists(self.cache_dir):
            return []
        
        cache_files = [f for f in os.listdir(self.cache_dir) if f.startswith("job_search_") and f.endswith(".json")]
        
        results = []
        for cache_file in cache_files:
            try:
                cache_path = os.path.join(self.cache_dir, cache_file)
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                results.append({
                    "file": cache_file,
                    "keywords": data["search_params"]["keywords"],
                    "location": data["search_params"]["location"],
                    "timestamp": data["search_params"]["timestamp"],
                    "result_count": len(data["results"])
                })
            except Exception as e:
                logger.error(f"Error reading cache file {cache_file}: {str(e)}")
        
        # Sort by timestamp, newest first
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return results


def display_job_details(job: JobListing):
    """Display detailed information about a job listing."""
    print("\n" + "="*70)
    print(f"JOB DETAILS: {job.title}".center(70))
    print("="*70)
    
    print(f"Company: {job.company}")
    print(f"Location: {job.location}")
    
    if job.salary:
        print(f"Salary: {job.salary}")
    
    if job.date_posted:
        print(f"Posted: {job.date_posted}")
    
    print(f"Source: {job.source}")
    print(f"URL: {job.url}")
    
    print("\nDESCRIPTION:")
    print("-" * 70)
    # Print description with proper wrapping
    for i in range(0, len(job.description), 70):
        print(job.description[i:i+70])
    
    # Display match information if available
    if job.match_score is not None:
        print("\nMATCH ANALYSIS:")
        print("-" * 70)
        print(f"Match Score: {job.match_score}%")
        
        if job.matching_skills:
            print("\nMatching Skills:")
            print(", ".join(job.matching_skills))
        
        if job.missing_skills:
            print("\nMissing Skills:")
            print(", ".join(job.missing_skills))


def main():
    """Main entry point for the job finder tool."""
    parser = argparse.ArgumentParser(description="Find and analyze job listings")
    parser.add_argument("--resume", "-r", help="Path to your resume text file")
    parser.add_argument("--keywords", "-k", nargs="+", help="Keywords to search for")
    parser.add_argument("--location", "-l", default="", help="Location to search in")
    parser.add_argument("--sources", "-s", nargs="+", default=DEFAULT_JOB_SEARCH_SITES, 
                        help=f"Job sources to search (default: {', '.join(DEFAULT_JOB_SEARCH_SITES)})")
    parser.add_argument("--limit", type=int, default=JOB_SEARCH_LIMIT, 
                        help=f"Maximum results per source (default: {JOB_SEARCH_LIMIT})")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    parser.add_argument("--cached", "-c", help="Use cached search results file")
    parser.add_argument("--list-cache", action="store_true", help="List cached search results")
    
    args = parser.parse_args()
    
    try:
        # Initialize job finder
        job_finder = JobFinder(args.resume, args.output)
        
        # List cached searches if requested
        if args.list_cache:
            cached_searches = job_finder.list_cached_searches()
            if not cached_searches:
                print("No cached searches found.")
                return 0
            
            print("\n" + "="*70)
            print("CACHED JOB SEARCHES".center(70))
            print("="*70)
            
            for i, search in enumerate(cached_searches, 1):
                timestamp = datetime.fromisoformat(search["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                print(f"{i}. {search['file']}")
                print(f"   Keywords: {', '.join(search['keywords'])}")
                print(f"   Location: {search['location']}")
                print(f"   Date: {timestamp}")
                print(f"   Results: {search['result_count']}")
                print()
            
            return 0
        
        # Load cached results if specified
        if args.cached:
            jobs = job_finder.load_cached_results(args.cached)
            print(f"\nLoaded {len(jobs)} jobs from cache file: {args.cached}")
        
        # Otherwise, search for jobs if keywords are provided
        elif args.keywords:
            jobs = job_finder.search_jobs(
                keywords=args.keywords,
                location=args.location,
                sources=args.sources,
                limit=args.limit
            )
            print(f"\nFound {len(jobs)} matching jobs")
        
        else:
            parser.print_help()
            return 1
        
        # Display job results
        if jobs:
            print("\n" + "="*70)
            print("JOB SEARCH RESULTS".center(70))
            print("="*70)
            
            for i, job in enumerate(jobs, 1):
                match_info = ""
                if job.match_score is not None:
                    match_info = f" (Match: {job.match_score}%)"
                
                print(f"{i}. {job.title} - {job.company}{match_info}")
                print(f"   {job.location} | {job.source}")
                if job.salary:
                    print(f"   Salary: {job.salary}")
                print()
            
            # Interactive job selection
            while True:
                try:
                    selection = input("\nEnter job number to view details (or 'q' to quit): ")
                    if selection.lower() == 'q':
                        break
                    
                    job_index = int(selection) - 1
                    if 0 <= job_index < len(jobs):
                        selected_job = jobs[job_index]
                        
                        # If resume is available, analyze match
                        if args.resume and job_finder.resume_text and not selected_job.match_score:
                            job_finder.analyze_job_match(selected_job)
                        
                        display_job_details(selected_job)
                    else:
                        print("Invalid job number. Please try again.")
                except ValueError:
                    print("Please enter a valid job number or 'q' to quit.")
                except KeyboardInterrupt:
                    break
        
        return 0
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
