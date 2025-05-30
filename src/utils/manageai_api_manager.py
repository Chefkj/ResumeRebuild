"""
ManageAI API Server Manager for Resume Rebuilder.

This module manages the lifecycle of the ManageAI Resume API server process.
It provides functionality to start and stop the server as needed.
"""

import os
import sys
import time
import logging
import threading
import importlib.util
import importlib
import requests
import atexit
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Callable

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ManageAIAPIManager:
    """Manager for the ManageAI Resume API server."""
    
    def __init__(self, api_path: Optional[str] = None, host: str = "localhost", 
                 port: int = 8080, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the API manager.
        
        Args:
            api_path: Path to the ManageAI resume_api.py file
            host: Host to bind the API server to
            port: Port for the API server to listen on
            config: Configuration dictionary for the Resume API
        """
        self.host = host
        self.port = port
        self.config = config or {}
        
        # Find the API path if not provided
        if not api_path:
            # Try to find it at expected locations
            possible_paths = [
                "/Users/kj/managerai/resume_api.py",
                str(Path.home() / "managerai" / "resume_api.py"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    api_path = path
                    break
        
        self.api_path = api_path
        self.api_instance = None
        self._api_process = None
        self._server_started = False
        self._health_check_thread = None
        self._stop_health_check = threading.Event()
        
        # Register shutdown handler to ensure server is stopped on exit
        atexit.register(self.stop_server)
        
        logger.info(f"ManageAI API Manager initialized with path: {self.api_path}")
    
    def start_server(self, wait_for_startup: bool = True, timeout: int = 10, retries: int = 3) -> bool:
        """
        Start the ManageAI Resume API server.
        
        Args:
            wait_for_startup: Whether to wait for the server to be ready
            timeout: Maximum time to wait for server startup (in seconds)
            retries: Number of retry attempts if startup fails
            
        Returns:
            bool: True if the server was started successfully, False otherwise
        """
        if self._server_started and self.api_instance:
            logger.info("ManageAI API server is already running.")
            return True
            
        if not self.api_path or not os.path.exists(self.api_path):
            logger.error(f"Cannot start ManageAI API: API file not found at {self.api_path}")
            return False
        
        # Try starting the server with retries
        for attempt in range(retries):
            try:
                # Import the API module dynamically
                logger.info(f"Attempting to start ManageAI Resume API server (attempt {attempt+1}/{retries})...")
                
                # Add the ManageAI directory to sys.path for imports to work
                manageai_dir = os.path.dirname(self.api_path)
                if manageai_dir not in sys.path:
                    sys.path.insert(0, manageai_dir)
                    logger.info(f"Added {manageai_dir} to Python path for imports")
                
                # Use importlib to load the resume_api.py module
                spec = importlib.util.spec_from_file_location("resume_api", self.api_path)
                resume_api_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(resume_api_module)
                
                # Create an instance of the ResumeAPI class
                self.api_instance = resume_api_module.ResumeAPI(
                    host=self.host,
                    port=self.port,
                    config=self.config
                )
                
                # Start the server in a threaded mode
                self.api_instance.start(threaded=True)
                self._server_started = True
                
                logger.info(f"ManageAI Resume API server started on {self.host}:{self.port}")
                
                # Start health check thread
                self._start_health_check()
                
                # Wait for the server to be ready if requested
                if wait_for_startup:
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        if self.is_server_running():
                            logger.info("ManageAI Resume API server is ready")
                            return True
                        time.sleep(0.5)
                    
                    logger.warning(f"ManageAI Resume API server didn't respond within {timeout} seconds")
                    # Don't return False here, as the server might still become available
                
                return True
                
            except ModuleNotFoundError as e:
                # If a dependency like Flask is missing, try to install it
                if "No module named 'flask'" in str(e) or "No module named" in str(e):
                    logger.warning(f"Module not found: {str(e)}. Attempting to install dependencies...")
                    try:
                        # Install Flask and dependencies
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "werkzeug", "redis", "python-dotenv"])
                        
                        # Try importing again
                        spec = importlib.util.spec_from_file_location("resume_api", self.api_path)
                        resume_api_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(resume_api_module)
                        
                        # Create an instance of the ResumeAPI class
                        self.api_instance = resume_api_module.ResumeAPI(
                            host=self.host,
                            port=self.port,
                            config=self.config
                        )
                        
                        # Start the server in a threaded mode
                        self.api_instance.start(threaded=True)
                        self._server_started = True
                        
                        logger.info(f"ManageAI Resume API server started on {self.host}:{self.port}")
                        
                        # Start health check thread
                        self._start_health_check()
                        
                        return True
                        
                    except Exception as inner_e:
                        logger.error(f"Failed to install or import dependencies: {inner_e}")
                        
                        # Try alternative approach: run the resume_api.py directly using subprocess
                        logger.info("Trying to run resume_api.py as a separate process...")
                        try:
                            self._run_resume_api_as_process()
                            # No need to set self.api_instance since we're managing it as a subprocess
                            self._server_started = True
                            return True  # Skip the rest of the function
                        except Exception as proc_e:
                            logger.error(f"Failed to run resume_api.py as a separate process: {proc_e}")
                            raise RuntimeError(f"Failed to start ManageAI Resume API: {proc_e}") from e
                else:
                    raise
            except Exception as e:
                logger.error(f"Error starting ManageAI API server (attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    logger.info(f"Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    self._server_started = False
                    return False
        
        return False  # If we get here, all attempts failed
    
    def _start_health_check(self, interval: int = 30):
        """
        Start a background thread to periodically check if the server is still running.
        
        Args:
            interval: Time between health checks in seconds
        """
        if self._health_check_thread and self._health_check_thread.is_alive():
            return  # Already running
            
        self._stop_health_check.clear()
        
        def health_check_worker():
            while not self._stop_health_check.is_set():
                if not self.is_server_running() and self._server_started:
                    logger.warning("ManageAI API server not responding, attempting to restart...")
                    self.restart_server()
                time.sleep(interval)
        
        self._health_check_thread = threading.Thread(
            target=health_check_worker, 
            daemon=True,
            name="ManageAI-API-HealthCheck"
        )
        self._health_check_thread.start()
    
    def _stop_health_check_thread(self):
        """Stop the health check thread."""
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._stop_health_check.set()
            self._health_check_thread.join(timeout=1.0)
    
    def _run_resume_api_as_process(self):
        """
        Run the resume_api.py as a separate process.
        
        This method is used as a fallback when direct import fails.
        """
        if not self.api_path or not os.path.exists(self.api_path):
            raise FileNotFoundError(f"Resume API file not found at {self.api_path}")
        
        # First, try to install any missing dependencies that might be needed
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "flask", "werkzeug", "redis", "python-dotenv"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("Installed required dependencies for resume_api.py")
        except subprocess.CalledProcessError:
            logger.warning("Failed to install some dependencies, but continuing anyway")
        
        # Prepare the command to run the resume_api.py
        cmd = [
            sys.executable,  # Use the current Python interpreter
            self.api_path,
            "--host", self.host,
            "--port", str(self.port)
        ]
        
        # Add any config parameters
        if self.config:
            for key, value in self.config.items():
                cmd.extend([f"--{key}", str(value)])
        
        # Add PYTHONPATH to ensure imports work correctly
        env = os.environ.copy()
        manageai_dir = os.path.dirname(self.api_path)
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{manageai_dir}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = manageai_dir
        
        # Run the process in the background
        logger.info(f"Starting resume_api.py as a subprocess: {' '.join(cmd)}")
        self._api_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Check if the process started successfully
        if self._api_process.poll() is not None:
            stdout, stderr = self._api_process.communicate()
            raise RuntimeError(f"Failed to start resume_api.py process. "
                             f"Exit code: {self._api_process.returncode}, "
                             f"Stdout: {stdout}, Stderr: {stderr}")
        
        # Start a thread to monitor the process output
        def monitor_output():
            while self._api_process and self._api_process.poll() is None:
                try:
                    line = self._api_process.stderr.readline()
                    if line:
                        logger.info(f"Resume API [stderr]: {line.strip()}")
                    
                    line = self._api_process.stdout.readline()
                    if line:
                        logger.info(f"Resume API [stdout]: {line.strip()}")
                except:
                    break
        
        threading.Thread(
            target=monitor_output, 
            daemon=True,
            name="ManageAI-API-OutputMonitor"
        ).start()
        
        # Register a cleanup function to terminate the process on exit
        atexit.register(lambda: self._api_process.terminate() if hasattr(self, '_api_process') else None)
        
        logger.info(f"Resume API process started with PID {self._api_process.pid}")
        
        # Wait briefly and check if the process is still running
        time.sleep(1)
        if self._api_process.poll() is not None:
            stdout, stderr = self._api_process.communicate()
            logger.error(f"Resume API process terminated immediately after starting!")
            logger.error(f"Exit code: {self._api_process.returncode}")
            logger.error(f"Stdout: {stdout}")
            logger.error(f"Stderr: {stderr}")
            raise RuntimeError(f"Resume API process failed to start and terminated with code {self._api_process.returncode}")
    
    def restart_server(self) -> bool:
        """
        Restart the ManageAI Resume API server.
        
        Returns:
            bool: True if the server was restarted successfully, False otherwise
        """
        logger.info("Restarting ManageAI Resume API server...")
        self.stop_server()
        time.sleep(1)  # Give it a moment to fully shut down
        return self.start_server()
    
    def stop_server(self) -> bool:
        """
        Stop the ManageAI Resume API server.
        
        Returns:
            bool: True if the server was stopped successfully, False otherwise
        """
        # Stop health check first
        self._stop_health_check_thread()
        
        if not self._server_started:
            logger.info("ManageAI API server is not running.")
            return True
        
        # Case 1: Server was started as a subprocess
        if hasattr(self, '_api_process') and self._api_process is not None:
            try:
                logger.info(f"Stopping Resume API process with PID {self._api_process.pid}")
                self._api_process.terminate()
                # Give it some time to shut down gracefully
                for _ in range(5):
                    if self._api_process.poll() is not None:
                        break
                    time.sleep(0.5)
                
                # If it's still running, force kill it
                if self._api_process.poll() is None:
                    logger.warning("Process didn't terminate gracefully, forcing kill...")
                    self._api_process.kill()
                    self._api_process.wait(timeout=5)
                
                self._server_started = False
                self._api_process = None
                logger.info("ManageAI Resume API server process stopped")
                return True
            except Exception as e:
                logger.error(f"Error stopping ManageAI API server process: {e}")
                return False
        
        # Case 2: Server was started via direct import
        elif self.api_instance:
            try:
                self.api_instance.stop()
                self._server_started = False
                self.api_instance = None
                logger.info("ManageAI Resume API server stopped")
                return True
            except Exception as e:
                logger.error(f"Error stopping ManageAI API server: {e}")
                return False
        
        # Shouldn't reach here, but just in case
        logger.warning("Inconsistent server state detected")
        self._server_started = False
        return True
    
    def is_server_running(self) -> bool:
        """
        Check if the ManageAI Resume API server is running.
        
        Returns:
            bool: True if the server is running, False otherwise
        """
        if not self._server_started:
            return False
            
        # Try the health endpoint first
        try:
            response = requests.get(f"http://{self.host}:{self.port}/health", timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
            
        # If health endpoint failed, try the test endpoint as fallback
        try:
            response = requests.post(
                f"http://{self.host}:{self.port}/test", 
                json={"check": "connectivity"}, 
                timeout=2
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
