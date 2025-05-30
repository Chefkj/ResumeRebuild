"""
Resume API Integration module for connecting to different backend services.

This module provides a unified interface for connecting to either a direct
LLM Studio connection, the local server, or the ManageAI Resume API.
"""

import os
import logging
import json
from enum import Enum
from typing import Dict, Any, Optional, List, Union

from .local_llm_adapter import LocalLLMAdapter
from .api_client import APIClient
from .manageai_adapter import ManageAIResumeAdapter

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConnectionType(Enum):
    """Enum for available connection types."""
    LOCAL_SERVER = "local_server"
    MANAGE_AI = "manageai"
    LLM_DIRECT = "llm_direct"

class ResumeAPIIntegration:
    """
    Unified integration class for different resume API backends.
    
    This class provides a unified interface to interact with different backends:
    - Local server (via APIClient)
    - ManageAI Resume API (via ManageAIResumeAdapter)
    - Direct LLM Studio connection (via LocalLLMAdapter)
    
    It automatically handles switching between backends and provides consistent
    error handling.
    """
    
    def __init__(
        self,
        connection_type: Union[ConnectionType, str] = ConnectionType.LOCAL_SERVER,
        local_url: str = "http://localhost:8080",
        manageai_url: str = "http://localhost:8080",
        llm_host: str = "localhost",
        llm_port: int = 1234,
        llm_model: str = "qwen-14b",
        api_key: Optional[str] = None
    ):
        """
        Initialize the integration with connection settings.
        
        Args:
            connection_type: Type of connection to use
            local_url: URL for the local server
            manageai_url: URL for the ManageAI Resume API
            llm_host: Host for direct LLM Studio connection
            llm_port: Port for direct LLM Studio connection
            llm_model: Model name for direct LLM Studio connection
            api_key: API key for authentication (used with local server and ManageAI API)
        """
        if isinstance(connection_type, str):
            try:
                connection_type = ConnectionType(connection_type)
            except ValueError:
                logger.warning(f"Invalid connection type: {connection_type}. Using LOCAL_SERVER.")
                connection_type = ConnectionType.LOCAL_SERVER
                
        self.connection_type = connection_type
        self.local_url = local_url
        self.manageai_url = manageai_url
        self.llm_host = llm_host
        self.llm_port = llm_port
        self.llm_model = llm_model
        self.api_key = api_key
        
        # Initialize the appropriate client based on connection type
        self._init_client()
        
    def _init_client(self):
        """Initialize the client based on the connection type."""
        if self.connection_type == ConnectionType.LOCAL_SERVER:
            logger.info(f"Initializing connection to local server at {self.local_url}")
            self.client = APIClient(base_url=self.local_url, api_key=self.api_key)
            self._connection_active = self.client.test_connection()
            
        elif self.connection_type == ConnectionType.MANAGE_AI:
            logger.info(f"Initializing connection to ManageAI Resume API at {self.manageai_url}")
            self.client = ManageAIResumeAdapter(api_url=self.manageai_url, api_key=self.api_key)
            self._connection_active = self.client.test_connection()
            
        elif self.connection_type == ConnectionType.LLM_DIRECT:
            logger.info(f"Initializing direct connection to LLM Studio at {self.llm_host}:{self.llm_port}")
            self.client = LocalLLMAdapter(
                host=self.llm_host,
                port=self.llm_port,
                model_name=self.llm_model
            )
            self._connection_active = self.client.test_connection()
            
        else:
            raise ValueError(f"Unsupported connection type: {self.connection_type}")
            
        if not self._connection_active:
            logger.warning(f"Failed to connect to {self.connection_type.value}")
    
    def switch_connection(self, connection_type: Union[ConnectionType, str]):
        """
        Switch to a different connection type.
        
        Args:
            connection_type: New connection type to use
            
        Returns:
            bool: True if the switch was successful, False otherwise
        """
        if isinstance(connection_type, str):
            try:
                connection_type = ConnectionType(connection_type)
            except ValueError:
                logger.error(f"Invalid connection type: {connection_type}")
                return False
                
        # No need to switch if already using this connection
        if connection_type == self.connection_type and self._connection_active:
            return True
            
        # Save current connection type to restore if switch fails
        old_connection_type = self.connection_type
        
        # Switch to new connection type
        self.connection_type = connection_type
        
        try:
            self._init_client()
            return self._connection_active
        except Exception as e:
            logger.error(f"Failed to switch connection: {e}")
            # Restore old connection type if switch fails
            self.connection_type = old_connection_type
            self._init_client()
            return False
    
    def set_api_key(self, api_key: str):
        """
        Set or update the API key.
        
        Args:
            api_key: New API key
        """
        self.api_key = api_key
        
        # Update the key in the current client
        if self.connection_type == ConnectionType.LOCAL_SERVER:
            self.client.set_api_key(api_key)
        elif self.connection_type == ConnectionType.MANAGE_AI:
            self.client.set_api_key(api_key)
    
    def test_connection(self) -> bool:
        """
        Test the current connection.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            if self.connection_type == ConnectionType.LOCAL_SERVER:
                return self.client.test_connection()
            elif self.connection_type == ConnectionType.MANAGE_AI:
                return self.client.test_connection()
            elif self.connection_type == ConnectionType.LLM_DIRECT:
                return self.client.test_connection()
            else:
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def analyze_resume(self, resume_content, job_description=None):
        """
        Analyze a resume against a job description, using the current client.
        
        Args:
            resume_content: Dictionary or string with resume content
            job_description: Optional job description to compare against
            
        Returns:
            Dictionary with analysis results
            
        Raises:
            RuntimeError: If the connection is not active
            ValueError: If resume content is invalid
        """
        if not self._connection_active:
            raise RuntimeError(f"No active connection to {self.connection_type.value}")
            
        if not resume_content:
            raise ValueError("Resume content cannot be empty")
            
        # Handle different client types
        if self.connection_type == ConnectionType.LOCAL_SERVER:
            return self.client.analyze_resume(resume_content, job_description)
        
        elif self.connection_type == ConnectionType.MANAGE_AI:
            # Format resume content if needed
            structured_resume = self._ensure_structured_resume(resume_content)
            
            if job_description:
                job_analysis = self.client.analyze_job(job_description)
                return self.client.match_resume_to_job(structured_resume, job_description)
            else:
                return self.client.analyze_resume(structured_resume)
                
        elif self.connection_type == ConnectionType.LLM_DIRECT:
            # For direct LLM, use the prompt template for resume analysis
            prompt = f"Analyze the following resume and provide feedback for improvement:\n\n"
            
            if isinstance(resume_content, dict):
                prompt += json.dumps(resume_content, indent=2)
            else:
                prompt += str(resume_content)
                
            if job_description:
                prompt += f"\n\nFor the following job description:\n\n{job_description}"
                
            prompt += "\n\nPlease provide a detailed analysis with the following sections:\n"
            prompt += "1. Overall assessment\n2. Key strengths\n3. Areas for improvement\n"
            prompt += "4. Keyword relevance (if job description is provided)\n"
            prompt += "5. Specific recommendations"
            
            # Call the LLM and format the response
            response = self.client.generate_text(prompt)
            
            # Return a structured response
            return {
                "analysis": response,
                "score": None,  # LLM doesn't provide a numeric score
                "generated_at": None
            }
    
    def improve_resume(self, resume_content, job_description=None, feedback=None):
        """
        Get suggestions for improving a resume.
        
        Args:
            resume_content: Dictionary or string with resume content
            job_description: Optional job description to tailor for
            feedback: Optional specific feedback to incorporate
            
        Returns:
            Dictionary with improvement suggestions
        """
        if not self._connection_active:
            raise RuntimeError(f"No active connection to {self.connection_type.value}")
            
        if not resume_content:
            raise ValueError("Resume content cannot be empty")
            
        # Handle different client types
        if self.connection_type == ConnectionType.LOCAL_SERVER:
            if feedback:
                return self.client.iterate_resume(resume_content, feedback)
            else:
                return self.client.keyword_optimization(resume_content, job_description)
        
        elif self.connection_type == ConnectionType.MANAGE_AI:
            # Format resume content if needed
            structured_resume = self._ensure_structured_resume(resume_content)
            
            if not job_description:
                # Without job description, just analyze the resume
                return self.client.analyze_resume(structured_resume)
            
            # With job description, get improvement suggestions
            match_result = self.client.match_resume_to_job(structured_resume, job_description)
            return self.client.improve_resume(structured_resume, job_description, match_result)
                
        elif self.connection_type == ConnectionType.LLM_DIRECT:
            # For direct LLM, use the prompt template for resume improvement
            prompt = f"Improve the following resume"
            
            if job_description:
                prompt += f" based on this job description:\n\n{job_description}\n\n"
            else:
                prompt += ":\n\n"
                
            if isinstance(resume_content, dict):
                prompt += json.dumps(resume_content, indent=2)
            else:
                prompt += str(resume_content)
                
            if feedback:
                prompt += f"\n\nIncorporate this feedback: {feedback}"
                
            # Call the LLM and format the response
            response = self.client.generate_text(prompt)
            
            # Return a structured response
            return {
                "improved_resume": response,
                "generated_at": None
            }
    
    def _ensure_structured_resume(self, resume_content):
        """
        Ensure resume content is in the structured format expected by the ManageAI API.
        
        Args:
            resume_content: Dictionary or string with resume content
            
        Returns:
            Dictionary with structured resume data
        """
        if isinstance(resume_content, dict):
            return resume_content
            
        # Parse plain text resume into structured format
        sections = []
        current_section = ""
        current_content = []
        
        # Split resume into lines and identify sections
        for line in str(resume_content).split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a new section header (all caps or ends with :)
            if line.isupper() or line.endswith(':'):
                # Save previous section if it exists
                if current_section and current_content:
                    sections.append({
                        "name": current_section,
                        "content": '\n'.join(current_content)
                    })
                current_section = line.rstrip(':')
                current_content = []
            else:
                current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            sections.append({
                "name": current_section,
                "content": '\n'.join(current_content)
            })
        
        # Try to extract contact info from the first section
        name = ""
        email = ""
        phone = ""
        
        if sections and sections[0]["name"].upper() in ("CONTACT", "PERSONAL INFORMATION"):
            contact_text = sections[0]["content"]
            # Simple extraction logic
            for line in contact_text.split('\n'):
                if '@' in line:
                    email = line
                elif any(c.isdigit() for c in line) and ('-' in line or '.' in line or ' ' in line):
                    phone = line
                elif not name and line and line != email and line != phone:
                    name = line
        
        # Create the structured resume
        structured_resume = {
            "contact": {
                "name": name,
                "email": email,
                "phone": phone
            },
            "sections": sections
        }
        
        return structured_resume
    
    def ensure_server_running(self, max_attempts: int = 3) -> bool:
        """
        Ensure the required API server is running.
        
        This method attempts to start or reconnect to the appropriate server
        based on the current connection type.
        
        Args:
            max_attempts: Maximum number of restart attempts
            
        Returns:
            bool: True if the server is running, False otherwise
        """
        # For local ManageAI API, make sure the server is running
        if self.connection_type == ConnectionType.MANAGE_AI:
            from .manageai_api_manager import ManageAIAPIManager
            
            try:
                # Get the appropriate host/port from the ManageAI URL
                import re
                match = re.match(r'http://([\w.-]+):(\d+)', self.manageai_url)
                if match:
                    host, port = match.groups()
                    port = int(port)
                else:
                    host, port = "localhost", 8080
                    
                # Create and start API manager if needed
                api_manager = ManageAIAPIManager(host=host, port=port)
                
                # Try to start the server if it's not running
                if not api_manager.is_server_running():
                    logger.info("ManageAI API server not running, attempting to start...")
                    success = api_manager.start_server(wait_for_startup=True, retries=max_attempts)
                    if not success:
                        logger.error("Failed to start ManageAI API server")
                        return False
                
                # Server is running at this point
                logger.info("ManageAI API server is running")
                return True
                
            except Exception as e:
                logger.error(f"Error ensuring ManageAI API server is running: {e}")
                return False
                
        # For LLM Studio connection, just test if it's accessible
        elif self.connection_type == ConnectionType.LLM_DIRECT:
            # Just verify the connection works
            adapter = LocalLLMAdapter(
                host=self.llm_host,
                port=self.llm_port,
                model_name=self.llm_model
            )
            if adapter.test_connection():
                logger.info(f"LLM Studio is accessible at {self.llm_host}:{self.llm_port}")
                return True
            else:
                logger.error(f"LLM Studio not accessible at {self.llm_host}:{self.llm_port}")
                return False
                
        return self._connection_active
    
    def ensure_server_running(self) -> bool:
        """
        Ensure that the ManageAI Resume API server is running.
        This method will attempt to start the server if it's not already running.
        Only applies to ManageAI connection type.
        
        Returns:
            bool: True if the server is running or was successfully started, False otherwise
        """
        if self.connection_type != ConnectionType.MANAGE_AI:
            return True  # Only applies to ManageAI
        
        # Check if connection is active
        if not self._connection_active:
            # Try to start the ManageAI Resume API server
            try:
                # Import the API manager here to avoid circular imports
                from .manageai_api_manager import ManageAIAPIManager
                
                # Create an API manager and start the server
                logger.info("Connection to ManageAI Resume API failed, attempting to start the server...")
                api_manager = ManageAIAPIManager(
                    host=self.manageai_url.split('://')[1].split(':')[0] if '://' in self.manageai_url else 'localhost',
                    port=int(self.manageai_url.split(':')[-1].split('/')[0]) if ':' in self.manageai_url else 8080
                )
                
                if api_manager.start_server(wait_for_startup=True, timeout=30, retries=2):
                    logger.info("ManageAI Resume API server started successfully")
                    # Re-initialize the client
                    self.client = ManageAIResumeAdapter(api_url=self.manageai_url, api_key=self.api_key)
                    self._connection_active = self.client.test_connection()
                    return self._connection_active
                else:
                    logger.error("Failed to start ManageAI Resume API server")
                    return False
            except Exception as e:
                logger.error(f"Error starting ManageAI Resume API server: {e}")
                return False
        
        return True
