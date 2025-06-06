"""
Job Search API Integration.

This module provides utilities for interacting with various job search APIs.
"""

import os
import logging
import requests
import json
from typing import Dict, List, Any, Optional, Union
from src.utils.env_loader import get_api_key, get_setting
from src.utils.settings import Settings
from src.utils.glassdoor_scraper import glassdoor_scraper
from src.utils.agents_glassdoor import glassdoor_agent_s

# Configure logger
logger = logging.getLogger(__name__)

class JobSearchAPIClient:
    """Client for interacting with job search APIs."""
    
    def __init__(self):
        """Initialize the job search API client."""
        self.settings = Settings()
        self._load_api_keys()
        
    def _load_api_keys(self):
        """Load API keys from settings or environment variables."""
        # Get job search API keys
        self.linkedin_api_key = self.settings.settings.get('job_search', {}).get('linkedin_api_key', '')
        self.indeed_api_key = self.settings.settings.get('job_search', {}).get('indeed_api_key', '')
        self.ziprecruiter_api_key = self.settings.settings.get('job_search', {}).get('ziprecruiter_api_key', '')
        self.monster_api_key = self.settings.settings.get('job_search', {}).get('monster_api_key', '')
        
        # Get web scraping credentials
        self.glassdoor_username = get_setting("GLASSDOOR_USERNAME", "")
        self.glassdoor_password = get_setting("GLASSDOOR_PASSWORD", "")
        
        # Log available APIs
        available_apis = []
        if self.linkedin_api_key:
            available_apis.append('LinkedIn')
        if self.indeed_api_key:
            available_apis.append('Indeed')
        if self.ziprecruiter_api_key:
            available_apis.append('ZipRecruiter')
        if self.monster_api_key:
            available_apis.append('Monster')
        if self.glassdoor_username and self.glassdoor_password:
            available_apis.append('Glassdoor (Scraper)')
            
        if available_apis:
            logger.info(f"Available job search APIs: {', '.join(available_apis)}")
        else:
            logger.warning("No job search API keys configured. Add them to your .env file or settings.")
    
    def search_linkedin(self, 
                       query: str, 
                       location: Optional[str] = None,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on LinkedIn.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        if not self.linkedin_api_key:
            logger.error("LinkedIn API key not configured")
            return []
            
        try:
            # Example implementation - replace with actual LinkedIn API endpoints
            url = "https://api.linkedin.com/v2/jobs"
            headers = {
                "Authorization": f"Bearer {self.linkedin_api_key}",
                "Content-Type": "application/json"
            }
            params = {
                "keywords": query,
                "location": location or "",
                "limit": limit
            }
            
            # This is a placeholder - actual implementation would use the official LinkedIn API
            logger.info(f"Searching LinkedIn for '{query}' in '{location or 'any location'}'")
            logger.warning("LinkedIn API integration is a placeholder - implement actual API calls")
            
            # Mocked response for development/testing
            return [
                {
                    "id": "linkedin-job-1",
                    "title": f"Senior {query} Developer",
                    "company": "Example Corp",
                    "location": location or "Remote",
                    "url": "https://linkedin.com/jobs/view/123456",
                    "description": f"We're looking for an experienced {query} developer...",
                    "source": "LinkedIn"
                }
            ]
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")
            return []
    
    def search_indeed(self, 
                     query: str, 
                     location: Optional[str] = None,
                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on Indeed.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        if not self.indeed_api_key:
            logger.error("Indeed API key not configured")
            return []
            
        try:
            # Example implementation - replace with actual Indeed API endpoints
            url = "https://api.indeed.com/ads/apisearch"
            params = {
                "publisher": self.indeed_api_key,
                "q": query,
                "l": location or "",
                "limit": limit,
                "format": "json",
                "v": "2"
            }
            
            # This is a placeholder - actual implementation would use the official Indeed API
            logger.info(f"Searching Indeed for '{query}' in '{location or 'any location'}'")
            logger.warning("Indeed API integration is a placeholder - implement actual API calls")
            
            # Mocked response for development/testing
            return [
                {
                    "id": "indeed-job-1",
                    "title": f"{query} Engineer",
                    "company": "Sample Inc",
                    "location": location or "Remote",
                    "url": "https://indeed.com/viewjob?jk=123456",
                    "description": f"Looking for a {query} developer with 3+ years experience...",
                    "source": "Indeed"
                }
            ]
        except Exception as e:
            logger.error(f"Error searching Indeed: {e}")
            return []
            
    def search_ziprecruiter(self, 
                        query: str, 
                        location: Optional[str] = None,
                        limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on ZipRecruiter.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        if not self.ziprecruiter_api_key:
            logger.error("ZipRecruiter API key not configured")
            return []
            
        try:
            # Example implementation - replace with actual ZipRecruiter API endpoints
            # ZipRecruiter API documentation: https://www.ziprecruiter.com/developers
            url = "https://api.ziprecruiter.com/jobs/v1"
            headers = {
                "Authorization": f"Bearer {self.ziprecruiter_api_key}",
                "Content-Type": "application/json"
            }
            params = {
                "search": query,
                "location": location or "",
                "page": 1,
                "jobs_per_page": limit
            }
            
            logger.info(f"Searching ZipRecruiter for '{query}' in '{location or 'any location'}'")
            logger.warning("ZipRecruiter API integration is a placeholder - implement actual API calls")
            
            # Mocked response for development/testing
            return [
                {
                    "id": "ziprecruiter-job-1",
                    "title": f"{query} Specialist",
                    "company": "Test Company",
                    "location": location or "Remote",
                    "url": "https://ziprecruiter.com/job/123456",
                    "description": f"Join our team as a {query} specialist...",
                    "source": "ZipRecruiter"
                }
            ]
        except Exception as e:
            logger.error(f"Error searching ZipRecruiter: {e}")
            return []
    
    def search_monster(self, 
                      query: str, 
                      location: Optional[str] = None,
                      limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on Monster.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        if not self.monster_api_key:
            logger.error("Monster API key not configured")
            return []
            
        try:
            # Example implementation - replace with actual Monster API endpoints
            logger.info(f"Searching Monster for '{query}' in '{location or 'any location'}'")
            logger.warning("Monster API integration is a placeholder - implement actual API calls")
            
            # Mocked response for development/testing
            return [
                {
                    "id": "monster-job-1",
                    "title": f"Junior {query} Developer",
                    "company": "Demo Organization",
                    "location": location or "Remote",
                    "url": "https://monster.com/jobs/123456",
                    "description": f"Entry-level position for {query} development...",
                    "source": "Monster"
                }
            ]
        except Exception as e:
            logger.error(f"Error searching Monster: {e}")
            return []
    
    def search_glassdoor(self, 
                        query: str, 
                        location: Optional[str] = None,
                        limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on Glassdoor using web scraping.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        if not self.glassdoor_username or not self.glassdoor_password:
            logger.warning("Glassdoor credentials not configured. Set GLASSDOOR_USERNAME and GLASSDOOR_PASSWORD in your .env file.")
            return []
            
        try:
            logger.info(f"Searching Glassdoor for '{query}' in '{location or 'any location'}'")
            return glassdoor_scraper.search_jobs(query, location, limit)
        except Exception as e:
            logger.error(f"Error searching Glassdoor: {e}")
            return []
    
    def search_all_apis(self, 
                       query: str, 
                       location: Optional[str] = None,
                       limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for jobs across all configured APIs.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return per API
            
        Returns:
            List of job postings from all available sources
        """
        all_results = []
        
        # LinkedIn search
        if self.linkedin_api_key:
            linkedin_results = self.search_linkedin(query, location, limit)
            all_results.extend(linkedin_results)
            
        # Indeed search
        if self.indeed_api_key:
            indeed_results = self.search_indeed(query, location, limit)
            all_results.extend(indeed_results)
            
        # ZipRecruiter search
        if self.ziprecruiter_api_key:
            ziprecruiter_results = self.search_ziprecruiter(query, location, limit)
            all_results.extend(ziprecruiter_results)
            
        # Glassdoor search (web scraping)
        if self.glassdoor_username and self.glassdoor_password:
            glassdoor_results = self.search_glassdoor(query, location, limit)
            all_results.extend(glassdoor_results)
            
        # Monster search
        if self.monster_api_key:
            monster_results = self.search_monster(query, location, limit)
            all_results.extend(monster_results)
            
        logger.info(f"Found {len(all_results)} jobs across all configured job search APIs")
        return all_results

# Create a singleton instance
job_search_client = JobSearchAPIClient()
