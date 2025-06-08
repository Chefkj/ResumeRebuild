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
from src.utils.manageai_web_automation import manageai_web_client

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
        # Get job search API keys (used as fallbacks)
        self.linkedin_api_key = self.settings.settings.get('job_search', {}).get('linkedin_api_key', '')
        self.indeed_api_key = self.settings.settings.get('job_search', {}).get('indeed_api_key', '')
        self.ziprecruiter_api_key = self.settings.settings.get('job_search', {}).get('ziprecruiter_api_key', '')
        self.monster_api_key = self.settings.settings.get('job_search', {}).get('monster_api_key', '')
        
        # Get web scraping credentials (fallback for Glassdoor)
        self.glassdoor_username = get_setting("GLASSDOOR_USERNAME", "")
        self.glassdoor_password = get_setting("GLASSDOOR_PASSWORD", "")
        
        # Log available methods
        available_methods = []
        
        # Web automation is always available through ManageAI
        available_methods.append('LinkedIn (Web Automation)')
        available_methods.append('Indeed (Web Automation)')
        available_methods.append('Glassdoor (Web Automation)')
        
        # API fallbacks
        if self.linkedin_api_key:
            available_methods.append('LinkedIn (API Fallback)')
        if self.indeed_api_key:
            available_methods.append('Indeed (API Fallback)')
        if self.ziprecruiter_api_key:
            available_methods.append('ZipRecruiter (API)')
        if self.monster_api_key:
            available_methods.append('Monster (API)')
        if self.glassdoor_username and self.glassdoor_password:
            available_methods.append('Glassdoor (Scraper Fallback)')
            
        logger.info(f"Job search methods available: {', '.join(available_methods)}")
        logger.info("Primary method: Web automation using browser OAuth (no API keys required)")
        
        if not any([self.linkedin_api_key, self.indeed_api_key, self.ziprecruiter_api_key, self.monster_api_key]):
            logger.info("No API keys configured - relying entirely on web automation")
        else:
            logger.info("API keys configured as fallback options")
    
    def search_linkedin(self, 
                       query: str, 
                       location: Optional[str] = None,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on LinkedIn using web automation.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        try:
            logger.info(f"Searching LinkedIn for '{query}' in '{location or 'any location'}' using web automation")
            
            # Use ManageAI web automation for LinkedIn job search
            results = manageai_web_client.search_linkedin_jobs(query, location, limit)
            
            if results:
                logger.info(f"Found {len(results)} LinkedIn jobs via web automation")
                return results
            else:
                logger.warning("No LinkedIn jobs found via web automation")
                return []
                
        except Exception as e:
            logger.error(f"Error searching LinkedIn via web automation: {e}")
            
            # Fallback to API if web automation fails and API key is available
            if self.linkedin_api_key:
                logger.info("Falling back to LinkedIn API...")
                try:
                    # This is a placeholder - actual implementation would use the official LinkedIn API
                    logger.warning("LinkedIn API integration is a placeholder - implement actual API calls")
                    return []
                except Exception as api_error:
                    logger.error(f"LinkedIn API fallback also failed: {api_error}")
            
            return []
    
    def search_indeed(self, 
                     query: str, 
                     location: Optional[str] = None,
                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on Indeed using web automation.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        try:
            logger.info(f"Searching Indeed for '{query}' in '{location or 'any location'}' using web automation")
            
            # Use ManageAI web automation for Indeed job search
            results = manageai_web_client.search_indeed_jobs(query, location, limit)
            
            if results:
                logger.info(f"Found {len(results)} Indeed jobs via web automation")
                return results
            else:
                logger.warning("No Indeed jobs found via web automation")
                return []
                
        except Exception as e:
            logger.error(f"Error searching Indeed via web automation: {e}")
            
            # Fallback to API if web automation fails and API key is available
            if self.indeed_api_key:
                logger.info("Falling back to Indeed API...")
                try:
                    # This is a placeholder - actual implementation would use the official Indeed API
                    logger.warning("Indeed API integration is a placeholder - implement actual API calls")
                    return []
                except Exception as api_error:
                    logger.error(f"Indeed API fallback also failed: {api_error}")
            
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
        Search for jobs on Glassdoor using web automation.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        try:
            logger.info(f"Searching Glassdoor for '{query}' in '{location or 'any location'}' using web automation")
            
            # Use ManageAI web automation for Glassdoor job search
            results = manageai_web_client.search_glassdoor_jobs(query, location, limit)
            
            if results:
                logger.info(f"Found {len(results)} Glassdoor jobs via web automation")
                return results
            else:
                logger.warning("No Glassdoor jobs found via web automation")
                
                # Fallback to Selenium scraper if available
                if self.glassdoor_username and self.glassdoor_password:
                    logger.info("Falling back to Selenium scraper...")
                    return glassdoor_scraper.search_jobs(query, location, limit)
                    
                return []
                
        except Exception as e:
            logger.error(f"Error searching Glassdoor via web automation: {e}")
            
            # Fallback to Selenium scraper if web automation fails
            if self.glassdoor_username and self.glassdoor_password:
                logger.info("Falling back to Selenium scraper...")
                try:
                    return glassdoor_scraper.search_jobs(query, location, limit)
                except Exception as scraper_error:
                    logger.error(f"Glassdoor scraper fallback also failed: {scraper_error}")
            else:
                logger.warning("Glassdoor credentials not configured. Set GLASSDOOR_USERNAME and GLASSDOOR_PASSWORD in your .env file for fallback scraping.")
            
            return []
    
    def search_all_apis(self, 
                       query: str, 
                       location: Optional[str] = None,
                       limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for jobs across all available sources (web automation prioritized).
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return per source
            
        Returns:
            List of job postings from all available sources
        """
        all_results = []
        search_summary = []
        
        # LinkedIn search (web automation first)
        try:
            linkedin_results = self.search_linkedin(query, location, limit)
            all_results.extend(linkedin_results)
            search_summary.append(f"LinkedIn: {len(linkedin_results)} jobs")
        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")
            search_summary.append("LinkedIn: failed")
            
        # Indeed search (web automation first)
        try:
            indeed_results = self.search_indeed(query, location, limit)
            all_results.extend(indeed_results)
            search_summary.append(f"Indeed: {len(indeed_results)} jobs")
        except Exception as e:
            logger.error(f"Indeed search failed: {e}")
            search_summary.append("Indeed: failed")
            
        # Glassdoor search (web automation first)
        try:
            glassdoor_results = self.search_glassdoor(query, location, limit)
            all_results.extend(glassdoor_results)
            search_summary.append(f"Glassdoor: {len(glassdoor_results)} jobs")
        except Exception as e:
            logger.error(f"Glassdoor search failed: {e}")
            search_summary.append("Glassdoor: failed")
            
        # ZipRecruiter search (API only for now)
        if self.ziprecruiter_api_key:
            try:
                ziprecruiter_results = self.search_ziprecruiter(query, location, limit)
                all_results.extend(ziprecruiter_results)
                search_summary.append(f"ZipRecruiter: {len(ziprecruiter_results)} jobs")
            except Exception as e:
                logger.error(f"ZipRecruiter search failed: {e}")
                search_summary.append("ZipRecruiter: failed")
        else:
            search_summary.append("ZipRecruiter: no API key")
            
        # Monster search (API only for now)
        if self.monster_api_key:
            try:
                monster_results = self.search_monster(query, location, limit)
                all_results.extend(monster_results)
                search_summary.append(f"Monster: {len(monster_results)} jobs")
            except Exception as e:
                logger.error(f"Monster search failed: {e}")
                search_summary.append("Monster: failed")
        else:
            search_summary.append("Monster: no API key")
            
        logger.info(f"Job search completed: {' | '.join(search_summary)}")
        logger.info(f"Total: {len(all_results)} jobs found across all sources")
        return all_results

# Create a singleton instance
job_search_client = JobSearchAPIClient()
