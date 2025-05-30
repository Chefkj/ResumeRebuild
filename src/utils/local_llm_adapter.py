"""
Local LLM adapter for using LLM Studio models with our resume rebuilder.

This module provides parameters for connecting to locally running LLM models
like Qwen 14B running in LLM Studio.
"""

import json
import requests
import logging
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalLLMAdapter:
    """
    Adapter for connecting to locally hosted LLM models.
    
    Supports connecting to models running in LLM Studio or other
    local inference servers that provide compatible APIs.
    """
    
    def __init__(
        self, 
        model_name: str = "qwen-14b", 
        host: str = "localhost", 
        port: int = 1234,
        api_path: str = "/v1/chat/completions"
    ):
        """
        Initialize the local LLM adapter.
        
        Args:
            model_name: Name of the model to use
            host: Hostname where LLM Studio is running
            port: Port number for LLM Studio API
            api_path: API endpoint path
        """
        self.model_name = model_name
        self.api_url = f"http://{host}:{port}{api_path}"
        logger.info(f"Initialized LocalLLMAdapter with API URL: {self.api_url}")
    
    def generate(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4000
    ) -> Optional[str]:
        """
        Generate a response from the local LLM.
        
        Args:
            system_prompt: System instructions for the model
            user_prompt: User query or input for the model
            temperature: Controls randomness (lower = more deterministic)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text response or None if there was an error
        """
        try:
            # Format the request based on LLM Studio's API
            data = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Send request to local LLM Studio API
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=120  # Local inference might take longer
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract content from LLM Studio response
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    logger.info("Response received from LLM Studio")
                    return content
                else:
                    logger.warning("Invalid response format from LLM Studio")
                    return None
            else:
                logger.error(f"LLM Studio API error: {response.status_code}, {response.text}")
                return None
                
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error to local LLM: {str(e)}"
            logger.error(error_msg)
            return None
        except requests.exceptions.Timeout as e:
            error_msg = f"Timeout while calling local LLM: {str(e)}"
            logger.error(error_msg)
            return None
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error to local LLM: {str(e)}"
            logger.error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error calling local LLM: {str(e)}"
            logger.exception(error_msg)
            return None
    
    def test_connection(self) -> bool:
        """
        Test the connection to the local LLM.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            data = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": "Hello, are you online?"}
                ],
                "max_tokens": 10
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Connection test to local LLM successful")
                return True
            else:
                logger.warning(f"Connection test failed with status code: {response.status_code}")
                return False
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error to local LLM: {str(e)}"
            logger.error(error_msg)
            return False
        except requests.exceptions.Timeout as e:
            error_msg = f"Timeout while calling local LLM: {str(e)}"
            logger.error(error_msg)
            return False
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error to local LLM: {str(e)}"
            logger.error(error_msg)
            return False
        except Exception as e:
            error_msg = f"Unexpected error calling local LLM: {str(e)}"
            logger.exception(error_msg)
            return False