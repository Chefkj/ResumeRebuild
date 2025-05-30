#!/usr/bin/env python3
"""
Simple local server for the Resume Rebuilder application that processes API requests
"""

import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import ssl
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default API key - in a production environment, use a more secure method
DEFAULT_API_KEY = "test-api-key-1234"

class ResumeAPIHandler(BaseHTTPRequestHandler):
    """Handler for the Resume API server."""
    
    def _set_response(self, status_code=200, content_type="application/json"):
        """Set the response headers."""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def _validate_auth(self):
        """Validate the Authorization header."""
        if 'Authorization' not in self.headers:
            return False
        
        auth_header = self.headers['Authorization']
        if not auth_header.startswith('Bearer '):
            return False
        
        api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        valid_api_key = os.environ.get("RESUME_API_KEY", DEFAULT_API_KEY)
        
        return api_key == valid_api_key
    
    def _read_request_data(self):
        """Read the request data."""
        content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
        request_data = self.rfile.read(content_length)
        return json.loads(request_data.decode('utf-8')) if request_data else {}
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        self._set_response()
        
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path.strip('/')
        
        if path == "health":
            # Health check endpoint
            self._set_response()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
        
        elif path == "templates":
            # Validate authentication
            if not self._validate_auth():
                self._set_response(401)
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode('utf-8'))
                return
            
            # Return mock templates
            templates = [
                {"id": "modern", "name": "Modern Resume", "description": "A clean, modern resume template"},
                {"id": "professional", "name": "Professional", "description": "A traditional professional resume layout"},
                {"id": "creative", "name": "Creative", "description": "Stand out with this creative resume design"}
            ]
            self._set_response()
            self.wfile.write(json.dumps(templates).encode('utf-8'))
        
        else:
            # Endpoint not found
            self._set_response(404)
            self.wfile.write(json.dumps({"error": f"Endpoint {path} not found"}).encode('utf-8'))
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path.strip('/')
        
        # Validate authentication for all POST endpoints
        if not self._validate_auth():
            self._set_response(401)
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode('utf-8'))
            return
        
        # Read request data
        try:
            request_data = self._read_request_data()
        except json.JSONDecodeError:
            self._set_response(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode('utf-8'))
            return
        
        # Handle different endpoints
        if path == "analyze":
            # Analyze resume endpoint
            if 'resume' not in request_data:
                self._set_response(400)
                self.wfile.write(json.dumps({"error": "Missing resume content"}).encode('utf-8'))
                return
            
            # Process the analysis (mock response)
            response_data = {
                "score": 85,
                "feedback": "Your resume looks good, but consider adding more keywords related to your industry."
            }
            
            self._set_response()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        
        elif path == "generate":
            # Generate resume PDF endpoint
            if 'resume' not in request_data or 'template_id' not in request_data:
                self._set_response(400)
                self.wfile.write(json.dumps({"error": "Missing required fields"}).encode('utf-8'))
                return
            
            # Generate PDF (mock response)
            response_data = {
                "pdf_url": "http://localhost:8080/download/resume_123456.pdf",
                "message": "Resume generated successfully"
            }
            
            self._set_response()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        
        elif path == "optimize":
            # Keyword optimization endpoint
            if 'resume' not in request_data or 'job_description' not in request_data:
                self._set_response(400)
                self.wfile.write(json.dumps({"error": "Missing required fields"}).encode('utf-8'))
                return
                
            # Process optimization (mock response)
            response_data = {
                "suggestions": [
                    {"keyword": "leadership", "context": "Consider adding examples of leadership roles"},
                    {"keyword": "python", "context": "Highlight your Python programming skills"}
                ]
            }
            
            self._set_response()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        
        elif path == "ats-check":
            # ATS compatibility check endpoint
            if 'resume' not in request_data:
                self._set_response(400)
                self.wfile.write(json.dumps({"error": "Missing resume content"}).encode('utf-8'))
                return
                
            # Process ATS check (mock response)
            response_data = {
                "compatibility_score": 92,
                "suggestions": [
                    "Use more industry-standard section headings",
                    "Ensure proper formatting of dates"
                ]
            }
            
            self._set_response()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        
        elif path == "iterate":
            # Resume iteration endpoint
            if 'resume' not in request_data or 'feedback' not in request_data:
                self._set_response(400)
                self.wfile.write(json.dumps({"error": "Missing required fields"}).encode('utf-8'))
                return
                
            # Process iteration (mock response)
            response_data = {
                "updated_resume": request_data['resume'],  # In a real implementation, this would be modified
                "message": "Resume updated based on feedback"
            }
            
            self._set_response()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        
        else:
            # Endpoint not found
            self._set_response(404)
            self.wfile.write(json.dumps({"error": f"Endpoint {path} not found"}).encode('utf-8'))

def run_server(server_class=HTTPServer, handler_class=ResumeAPIHandler, port=8080):
    """Run the server."""
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logger.info(f"Starting server on port {port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
    finally:
        httpd.server_close()
        logger.info("Server stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resume API local server")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Port to run the server on (default: 8080)")
    args = parser.parse_args()
    
    run_server(port=args.port)
