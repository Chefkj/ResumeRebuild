#!/usr/bin/env python3
"""
Flask web server for Resume Rebuilder web interface
"""

import os
import sys
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Try to import real classes, fall back to mocks if not available
try:
    from utils.pdf_extractor import PDFExtractor
    pdf_extractor_available = True
except ImportError as e:
    logger.warning(f"PDFExtractor import failed: {e}")
    from utils.mock_classes import MockPDFExtractor as PDFExtractor
    pdf_extractor_available = False

try:
    from utils.resume_generator import ResumeGenerator
except ImportError:
    from utils.mock_classes import MockResumeGenerator as ResumeGenerator

try:
    from utils.job_analyzer import JobAnalyzer
except ImportError:
    from utils.mock_classes import MockJobAnalyzer as JobAnalyzer

try:
    from utils.api_client import APIClient
except ImportError:
    from utils.mock_classes import MockAPIClient as APIClient

try:
    from utils.manageai_api_manager import ManageAIAPIManager
except ImportError:
    from utils.mock_classes import MockManageAIAPIManager as ManageAIAPIManager

try:
    from utils.resume_api_integration import ResumeAPIIntegration, ConnectionType
except ImportError:
    from utils.mock_classes import MockResumeAPIIntegration as ResumeAPIIntegration, MockConnectionType as ConnectionType

try:
    from utils.pdf_content_replacer import PDFContentReplacer
except ImportError:
    from utils.mock_classes import MockPDFContentReplacer as PDFContentReplacer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'resume_rebuilder_web_interface_secret_key_change_in_production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variables for session state
current_session = {
    'resume_content': None,
    'job_description': '',
    'chat_history': [],
    'file_name': '',
    'session_name': 'Default Session'
}

class WebResumeHandler:
    """Handler for resume processing operations in web interface."""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.resume_generator = ResumeGenerator()
        self.job_analyzer = JobAnalyzer()
        
        # Initialize API components with better error handling
        try:
            self.api_manager = ManageAIAPIManager()
            # Try to get API client if the method exists
            if hasattr(self.api_manager, 'get_api_client'):
                self.api_client = self.api_manager.get_api_client()
            else:
                self.api_client = APIClient()
            
            # Create ResumeAPIIntegration with proper connection type
            if hasattr(ConnectionType, 'MANAGEAI'):
                connection_type = ConnectionType.MANAGEAI
            else:
                connection_type = 'mock'
                
            self.resume_api = ResumeAPIIntegration(
                api_client=self.api_client,
                connection_type=connection_type
            )
        except Exception as e:
            logger.warning(f"Failed to initialize API components: {e}")
            # Use mock implementations
            self.api_manager = ManageAIAPIManager()
            self.api_client = APIClient()
            self.resume_api = ResumeAPIIntegration(
                api_client=self.api_client,
                connection_type='mock'
            )
    
    def extract_text_from_file(self, file_path):
        """Extract text from uploaded file."""
        try:
            if file_path.lower().endswith('.pdf'):
                # Use the correct method for PDFExtractor
                resume_content = self.pdf_extractor.extract(file_path)
                return resume_content.raw_text
            elif file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "Unsupported file format. Please upload PDF or TXT files."
        except Exception as e:
            logger.error(f"Error extracting text from file: {e}")
            return f"Error reading file: {str(e)}"
    
    def process_chat_message(self, message, resume_content=None, job_description=None):
        """Process chat message with LLM integration."""
        try:
            # Build context for the LLM
            context = f"Resume Content:\n{resume_content or 'No resume loaded'}\n\n"
            if job_description:
                context += f"Job Description:\n{job_description}\n\n"
            context += f"User Question: {message}"
            
            # Use ResumeAPIIntegration for chat processing
            response = self.resume_api.process_with_context(
                user_input=message,
                resume_content=resume_content or "",
                job_description=job_description or ""
            )
            
            return response
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return f"I apologize, but I encountered an error processing your request: {str(e)}"
    
    def improve_resume(self, resume_content):
        """Improve resume content using AI."""
        try:
            prompt = f"Please improve this resume by enhancing the content, making it more professional, and optimizing it for ATS systems:\n\n{resume_content}"
            return self.resume_api.process_with_context(
                user_input=prompt,
                resume_content=resume_content,
                job_description=""
            )
        except Exception as e:
            logger.error(f"Error improving resume: {e}")
            return f"Error improving resume: {str(e)}"
    
    def tailor_for_job(self, resume_content, job_description):
        """Tailor resume for specific job."""
        try:
            prompt = f"Please tailor this resume for the following job posting. Focus on relevant skills and experience:\n\nJob Posting:\n{job_description}\n\nResume:\n{resume_content}"
            return self.resume_api.process_with_context(
                user_input=prompt,
                resume_content=resume_content,
                job_description=job_description
            )
        except Exception as e:
            logger.error(f"Error tailoring resume: {e}")
            return f"Error tailoring resume: {str(e)}"

# Initialize the resume handler
resume_handler = WebResumeHandler()

# Routes
@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    global current_session
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.lower().endswith(('.pdf', '.txt')):
        try:
            filename = secure_filename(file.filename)
            upload_path = os.path.join('/tmp', filename)
            file.save(upload_path)
            
            # Extract text from the file
            text_content = resume_handler.extract_text_from_file(upload_path)
            
            # Update session
            current_session['resume_content'] = text_content
            current_session['file_name'] = filename
            
            # Clean up uploaded file
            os.remove(upload_path)
            
            return jsonify({
                'success': True,
                'content': text_content,
                'filename': filename
            })
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Please upload PDF or TXT files.'}), 400

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    global current_session
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    message = data['message']
    
    try:
        # Process the message
        response = resume_handler.process_chat_message(
            message=message,
            resume_content=current_session.get('resume_content'),
            job_description=current_session.get('job_description')
        )
        
        # Add to chat history
        current_session['chat_history'].append({
            'type': 'user',
            'message': message,
            'timestamp': data.get('timestamp', '')
        })
        current_session['chat_history'].append({
            'type': 'assistant',
            'message': response,
            'timestamp': data.get('timestamp', '')
        })
        
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return jsonify({'error': f'Error processing message: {str(e)}'}), 500

@app.route('/api/quick-action', methods=['POST'])
def quick_action():
    """Handle quick action requests."""
    global current_session
    
    data = request.get_json()
    if not data or 'action' not in data:
        return jsonify({'error': 'No action specified'}), 400
    
    action = data['action']
    resume_content = current_session.get('resume_content')
    
    if not resume_content:
        return jsonify({'error': 'No resume content available'}), 400
    
    try:
        if action == 'improve':
            result = resume_handler.improve_resume(resume_content)
        elif action == 'tailor':
            job_description = data.get('job_description', current_session.get('job_description', ''))
            if not job_description:
                return jsonify({'error': 'Job description required for tailoring'}), 400
            result = resume_handler.tailor_for_job(resume_content, job_description)
        elif action == 'format':
            result = "Resume formatting functionality will be implemented in a future update."
        elif action == 'keywords':
            result = "Keyword optimization functionality will be implemented in a future update."
        else:
            return jsonify({'error': 'Unknown action'}), 400
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"Error processing quick action: {e}")
        return jsonify({'error': f'Error processing action: {str(e)}'}), 500

@app.route('/api/update-content', methods=['POST'])
def update_content():
    """Update resume content."""
    global current_session
    
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'No content provided'}), 400
    
    current_session['resume_content'] = data['content']
    
    return jsonify({'success': True})

@app.route('/api/session', methods=['GET', 'POST'])
def session_management():
    """Handle session export/import."""
    global current_session
    
    if request.method == 'GET':
        # Export current session
        return jsonify(current_session)
    
    elif request.method == 'POST':
        # Import session
        data = request.get_json()
        if data:
            current_session.update(data)
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Invalid session data'}), 400

@app.route('/api/job-description', methods=['POST'])
def update_job_description():
    """Update job description."""
    global current_session
    
    data = request.get_json()
    if not data or 'job_description' not in data:
        return jsonify({'error': 'No job description provided'}), 400
    
    current_session['job_description'] = data['job_description']
    
    return jsonify({'success': True})

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return jsonify({'error': 'File too large. Please upload files smaller than 16MB.'}), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Create static directory if it doesn't exist
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    print("Starting Resume Rebuilder Web Server...")
    print("Access the application at: http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)