"""
Glassdoor job search using Agent-S.

This module provides an alternative approach to Glassdoor job search
by using Agent-S, which interacts with the GUI in a way similar to how humans would.
Agent-S is a specialized automation framework designed for GUI interaction.
"""

import os
import time
import logging
import io
import pyautogui
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
import platform

from src.utils.env_loader import get_api_key, get_setting

# Configure logger
logger = logging.getLogger(__name__)

# Import Agent-S components
try:
    from gui_agents.s2.agents.agent_s import AgentS2
    from gui_agents.s2.agents.grounding import OSWorldACI
    from gui_agents.utils import download_kb_data
    AGENT_S_AVAILABLE = True
except ImportError:
    logger.warning("Agent-S (gui_agents) package not installed. Please install it with: pip install gui_agents")
    AgentS2 = None
    OSWorldACI = None
    download_kb_data = None
    AGENT_S_AVAILABLE = False

class GlassdoorAgentS:
    """Agent-S implementation for Glassdoor job search."""
    
    BASE_URL = "https://www.glassdoor.com"
    SEARCH_URL = f"{BASE_URL}/Job/jobs.htm"
    
    def __init__(self):
        """Initialize the Glassdoor Agent-S."""
        self.agent = None
        self.grounding_agent = None
        self.initialized = False
        
        # Load credentials and settings
        self.openai_api_key = get_setting("OPENAI_API_KEY", "")
        self.anthropic_api_key = get_setting("ANTHROPIC_API_KEY", "")
        self.model_provider = get_setting("AGENTS_MODEL_PROVIDER", "anthropic").lower()
        self.model_name = get_setting("AGENTS_MODEL_NAME", "claude-3-7-sonnet-20250219")
        self.grounding_model_provider = get_setting("AGENTS_GROUNDING_MODEL_PROVIDER", "anthropic").lower()
        self.grounding_model_name = get_setting("AGENTS_GROUNDING_MODEL_NAME", "claude-3-7-sonnet-20250219")
        self.grounding_model_resize_width = int(get_setting("AGENTS_GROUNDING_MODEL_RESIZE_WIDTH", "1366"))
        
        # Check if we have the required API keys
        if self.model_provider == "openai" and not self.openai_api_key:
            logger.warning("OpenAI API key not configured for Agent-S. Set OPENAI_API_KEY in your .env file.")
        
        if self.model_provider == "anthropic" and not self.anthropic_api_key:
            logger.warning("Anthropic API key not configured for Agent-S grounding. Set ANTHROPIC_API_KEY in your .env file.")
    
    def _initialize_agent(self):
        """Initialize the Agent-S instance if not already done."""
        if self.initialized:
            return True
            
        try:
            # Ensure we have the required API keys
            if self.model_provider == "openai" and not self.openai_api_key:
                logger.error("OpenAI API key required for Agent-S")
                return False
            elif self.model_provider == "anthropic" and not self.anthropic_api_key:
                logger.error("Anthropic API key required for Agent-S")
                return False
                
            # Get platform information
            current_platform = platform.system().lower()
            
            # Download knowledge base data if needed
            download_kb_data(
                version="s2",
                release_tag="v0.2.2",
                download_dir="kb_data",
                platform=current_platform
            )
            
            # Set up engine parameters for main agent
            engine_params = {
                "engine_type": self.model_provider,
                "model": self.model_name,
            }
            
            # Set up engine parameters for grounding agent
            screen_width, screen_height = pyautogui.size()
            grounding_height = screen_height * self.grounding_model_resize_width / screen_width
            
            engine_params_for_grounding = {
                "engine_type": self.grounding_model_provider,
                "model": self.grounding_model_name,
                "grounding_width": self.grounding_model_resize_width,
                "grounding_height": grounding_height,
            }
            
            # Initialize grounding agent
            self.grounding_agent = OSWorldACI(
                platform=current_platform,
                engine_params_for_generation=engine_params,
                engine_params_for_grounding=engine_params_for_grounding
            )
            
            # Initialize Agent-S2
            self.agent = AgentS2(
                engine_params,
                self.grounding_agent,
                platform=current_platform,
                action_space="pyautogui",
                observation_type="screenshot"
            )
            
            self.initialized = True
            logger.info("Agent-S initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Agent-S: {e}")
            return False
    
    def search_jobs(self, query: str, location: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on Glassdoor using Agent-S.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        if not self._initialize_agent():
            logger.error("Failed to initialize Agent-S")
            return []
            
        try:
            # Build search URL
            search_url = f"{self.SEARCH_URL}?sc.keyword={quote_plus(query)}"
            if location:
                search_url += f"&locT=C&locId=1347&locKeyword={quote_plus(location)}"
            
            logger.info(f"Searching Glassdoor with Agent-S for '{query}' in '{location or 'any location'}'")
            
            # Take a screenshot of current state
            screenshot = pyautogui.screenshot()
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            screenshot_bytes = buffered.getvalue()
            
            # Prepare observation
            obs = {
                "screenshot": screenshot_bytes,
            }
            
            # Create instruction for Agent-S
            instruction = f"Open a web browser and go to {search_url}. Search for {query} jobs"
            if location:
                instruction += f" in {location}"
            instruction += ". Extract information about the first few job postings including job title, company, location, and if possible, a brief description or URL."
            
            # Use Agent-S to perform the search
            info, action = self.agent.predict(instruction=instruction, observation=obs)
            logger.debug(f"Agent-S info: {info}")
            logger.debug(f"Agent-S action: {action}")
            
            # Execute the action (Agent-S will control the browser)
            if action:
                exec(action[0])
            
            # Allow time for navigation and interaction
            time.sleep(5)
            
            # Take another screenshot to analyze results
            screenshot = pyautogui.screenshot()
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            screenshot_bytes = buffered.getvalue()
            
            # Update observation
            obs = {
                "screenshot": screenshot_bytes,
            }
            
            # Ask Agent-S to extract job listings
            extraction_instruction = f"Extract details of the top {min(limit, 10)} job listings from the current Glassdoor search results page. For each job, include the job title, company name, location, and any other visible information."
            
            info, _ = self.agent.predict(instruction=extraction_instruction, observation=obs)
            
            # Parse job listings from the agent's response
            job_listings = self._parse_jobs_from_response(info, query, limit)
            
            logger.info(f"Found {len(job_listings)} jobs on Glassdoor using Agent-S for query '{query}'")
            return job_listings
            
        except Exception as e:
            logger.error(f"Error searching Glassdoor with Agent-S: {e}")
            return []
    
    def _parse_jobs_from_response(self, response: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Parse job listings from Agent-S response.
        
        Args:
            response: Text response from Agent-S
            query: Original search query
            limit: Maximum number of results
            
        Returns:
            List of job postings
        """
        job_listings = []
        
        try:
            # Extract job information from the response
            lines = response.strip().split('\n')
            current_job = {}
            
            # Simple parsing of the text response - can be improved
            for line in lines:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Look for titles, typically with position prefixes
                if line.startswith("Job") or line.startswith("Title:") or "Position:" in line:
                    # If we have a current job with title, save it and start new one
                    if current_job and "title" in current_job:
                        job_listings.append(current_job)
                        if len(job_listings) >= limit:
                            break
                        current_job = {}
                    
                    # Extract title
                    title_parts = line.split(":", 1)
                    if len(title_parts) > 1:
                        current_job["title"] = title_parts[1].strip()
                    else:
                        current_job["title"] = line
                
                # Look for company information
                elif line.startswith("Company:") or "Company:" in line:
                    parts = line.split("Company:", 1)
                    if len(parts) > 1:
                        current_job["company"] = parts[1].strip()
                    else:
                        current_job["company"] = "Unknown Company"
                        
                # Look for location information
                elif line.startswith("Location:") or "Location:" in line:
                    parts = line.split("Location:", 1)
                    if len(parts) > 1:
                        current_job["location"] = parts[1].strip()
                    else:
                        current_job["location"] = "Unknown Location"
                        
                # Look for description or additional details
                elif line.startswith("Description:") or "Description:" in line:
                    parts = line.split("Description:", 1)
                    if len(parts) > 1:
                        current_job["description"] = parts[1].strip()
                        
                # If there's a URL mentioned
                elif "http" in line.lower() or "www." in line.lower():
                    # Extract URL-like string
                    import re
                    url_match = re.search(r'https?://\S+|www\.\S+', line)
                    if url_match:
                        current_job["url"] = url_match.group(0)
            
            # Don't forget the last job if we have one
            if current_job and "title" in current_job:
                job_listings.append(current_job)
            
            # If we couldn't parse properly, create some basic entries
            if not job_listings:
                for i in range(min(3, limit)):
                    job_listings.append({
                        "id": f"glassdoor-agents-{i}",
                        "title": f"{query} Position",
                        "company": "Company information unavailable",
                        "location": location or "Location unavailable",
                        "description": "Description unavailable - Agent-S encountered parsing difficulties",
                        "source": "Glassdoor (Agent-S)"
                    })
            else:
                # Add missing fields and source
                for i, job in enumerate(job_listings):
                    job["id"] = f"glassdoor-agents-{i}"
                    job["source"] = "Glassdoor (Agent-S)"
                    
                    # Add default values for missing fields
                    job.setdefault("title", f"{query} Position")
                    job.setdefault("company", "Unknown Company")
                    job.setdefault("location", "Unknown Location")
                    job.setdefault("description", "No description available")
                    job.setdefault("url", "https://www.glassdoor.com")
            
            return job_listings[:limit]
            
        except Exception as e:
            logger.error(f"Error parsing Agent-S response: {e}")
            return []

# Singleton instance
glassdoor_agent_s = GlassdoorAgentS()
