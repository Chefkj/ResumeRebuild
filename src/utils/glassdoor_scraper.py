"""
Glassdoor Web Scraper.

This module provides a web scraping implementation for Glassdoor job search
since they no longer offer a public API.
"""

import os
import time
import logging
import re
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains

from bs4 import BeautifulSoup

from src.utils.env_loader import get_api_key, get_setting

# Configure logger
logger = logging.getLogger(__name__)

class GlassdoorScraper:
    """Web scraper for Glassdoor job search."""
    
    BASE_URL = "https://www.glassdoor.com"
    SEARCH_URL = f"{BASE_URL}/Job/jobs.htm"
    LOGIN_URL = f"{BASE_URL}/profile/login_input.htm"
    
    def __init__(self):
        """Initialize the Glassdoor scraper."""
        self.browser = None
        self.logged_in = False
        self.username = get_setting("GLASSDOOR_USERNAME", "")
        self.password = get_setting("GLASSDOOR_PASSWORD", "")
        self.headless = get_setting("HEADLESS_BROWSER", "true").lower() == "true"
        
        if not self.username or not self.password:
            logger.warning(
                "Glassdoor credentials not configured. Set GLASSDOOR_USERNAME and "
                "GLASSDOOR_PASSWORD in your .env file."
            )
    
    def _setup_browser(self):
        """Set up the browser for web scraping."""
        if self.browser:
            return
            
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
            
            # Initialize browser
            service = Service(ChromeDriverManager().install())
            self.browser = webdriver.Chrome(service=service, options=chrome_options)
            self.browser.implicitly_wait(10)
            
            logger.info("Browser initialized for Glassdoor web scraping")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    def _login(self):
        """Log in to Glassdoor."""
        if self.logged_in:
            return
        
        if not self.username or not self.password:
            logger.warning("Skipping Glassdoor login - credentials not configured")
            return
        
        try:
            self._setup_browser()
            
            # Navigate to login page
            self.browser.get(self.LOGIN_URL)
            time.sleep(2)  # Wait for page to load
            
            # Check for cookie banner and accept
            try:
                cookie_button = WebDriverWait(self.browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                cookie_button.click()
                time.sleep(1)
            except TimeoutException:
                logger.debug("No cookie banner found or already accepted")
            
            # Find the email input field and enter email
            email_input = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "modalUserEmail"))
            )
            email_input.send_keys(self.username)
            
            # Click continue button
            continue_button = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
            continue_button.click()
            
            # Wait for password field
            password_input = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "modalUserPassword"))
            )
            password_input.send_keys(self.password)
            
            # Click sign in button
            sign_in_button = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
            sign_in_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            if "Sign In" in self.browser.title:
                logger.error("Failed to log in to Glassdoor")
                return False
            
            logger.info("Successfully logged in to Glassdoor")
            self.logged_in = True
            return True
            
        except Exception as e:
            logger.error(f"Error during Glassdoor login: {e}")
            return False
    
    def search_jobs(self, query: str, location: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for jobs on Glassdoor.
        
        Args:
            query: Job search query
            location: Optional location filter
            limit: Maximum number of results to return
            
        Returns:
            List of job postings
        """
        try:
            self._setup_browser()
            
            # Build search URL
            search_url = f"{self.SEARCH_URL}?sc.keyword={quote_plus(query)}"
            if location:
                search_url += f"&locT=C&locId=1347&locKeyword={quote_plus(location)}"
            
            # Navigate to search page
            self.browser.get(search_url)
            time.sleep(3)  # Wait for page to load
            
            # Check for cookie banner and accept
            try:
                cookie_button = WebDriverWait(self.browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                cookie_button.click()
                time.sleep(1)
            except TimeoutException:
                logger.debug("No cookie banner found or already accepted")
            
            # Check for login popup and close
            try:
                close_button = WebDriverWait(self.browser, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Close']"))
                )
                close_button.click()
                time.sleep(1)
            except TimeoutException:
                logger.debug("No login popup found")
            
            # Wait for job listings
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobCard"))
            )
            
            # Extract job listings
            job_listings = []
            job_cards = self.browser.find_elements(By.CSS_SELECTOR, ".jobCard")[:limit]
            
            for job_card in job_cards:
                try:
                    # Extract job details
                    title_element = job_card.find_element(By.CSS_SELECTOR, ".jobTitle")
                    company_element = job_card.find_element(By.CSS_SELECTOR, ".companyName")
                    location_element = job_card.find_element(By.CSS_SELECTOR, ".location")
                    
                    title = title_element.text
                    company = company_element.text
                    job_location = location_element.text
                    
                    # Get job URL
                    job_link = title_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    # Get job description
                    description = "Click job link for full description"
                    try:
                        # Try to click on the job card to see description
                        job_card.click()
                        time.sleep(2)
                        
                        # Find description in the detail pane
                        desc_element = WebDriverWait(self.browser, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".jobDescriptionContent"))
                        )
                        description = desc_element.text[:500] + "..." if len(desc_element.text) > 500 else desc_element.text
                    except Exception as e:
                        logger.debug(f"Couldn't get full description: {e}")
                    
                    job_listings.append({
                        "id": f"glassdoor-{len(job_listings)}",
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "url": job_link,
                        "description": description,
                        "source": "Glassdoor (Web Scraper)"
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to extract job details: {e}")
            
            logger.info(f"Found {len(job_listings)} jobs on Glassdoor for query '{query}'")
            return job_listings
            
        except Exception as e:
            logger.error(f"Error searching Glassdoor: {e}")
            return []
        finally:
            if self.browser and not self.headless:
                # Keep browser open for headful mode
                pass
            elif self.browser:
                self.close()
    
    def close(self):
        """Close the browser."""
        if self.browser:
            try:
                self.browser.quit()
                self.browser = None
                self.logged_in = False
                logger.info("Closed Glassdoor browser session")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

# Singleton instance
glassdoor_scraper = GlassdoorScraper()
