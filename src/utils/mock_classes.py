"""
Mock classes for testing GUI without full dependencies
"""

class MockPDFExtractor:
    def extract_text(self, pdf_path):
        return f"Mock extracted text from {pdf_path}"
    
    def extract(self, pdf_path):
        """Mock extract method that returns a simple object with raw_text attribute"""
        class MockResumeContent:
            def __init__(self, text):
                self.raw_text = text
                self.contact_info = {}
                self.sections = []
        
        return MockResumeContent(f"Mock resume content extracted from {pdf_path}\n\nJOHN SAMPLE\nEmail: john@example.com\nPhone: (555) 123-4567\n\nPROFESSIONAL SUMMARY\nExperienced professional with expertise in various fields.\n\nEXPERIENCE\nSample Company - Sample Role (2020-Present)\n• Accomplished various tasks\n• Delivered results")

class MockResumeGenerator:
    def generate(self, content):
        return "Mock generated resume"

class MockJobAnalyzer:
    def analyze(self, text):
        return {"score": 85, "suggestions": ["Mock suggestion 1", "Mock suggestion 2"]}

class MockAPIClient:
    def __init__(self):
        self.connected = False
    
    def test_connection(self):
        return True

class MockManageAIAPIManager:
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port
        self.server_running = False
    
    def get_api_client(self):
        return MockAPIClient()
    
    def start_server(self):
        self.server_running = True
        return True
    
    def stop_server(self):
        self.server_running = False
        return True
    
    def is_server_running(self):
        return self.server_running

class MockConnectionType:
    LOCAL_SERVER = "local_server"
    MANAGE_AI = "manage_ai"
    LLM_DIRECT = "llm_direct"

class MockResumeAPIIntegration:
    def __init__(self, connection_type=None, local_url=None, manageai_url=None, api_key=None, api_client=None):
        self.connection_type = connection_type
        self._connection_active = True
        self.api_client = api_client
    
    def process_with_context(self, user_input, resume_content="", job_description=""):
        # Mock AI response based on input
        if "improve" in user_input.lower():
            return f"Here's an improved version of your resume:\n\n{resume_content[:200]}... [Mock improvements applied]"
        elif "tailor" in user_input.lower() and job_description:
            return f"I've tailored your resume for this job. Here are the key improvements:\n\n- Added relevant keywords from the job posting\n- Emphasized matching skills and experience\n- Reordered sections for better alignment"
        elif "format" in user_input.lower():
            return "I've reformatted your resume with better structure and professional styling."
        elif "keyword" in user_input.lower():
            return "I've optimized your resume with industry-relevant keywords for better ATS compatibility."
        else:
            return f"Based on your question '{user_input}', here's my advice for your resume: Consider focusing on quantifiable achievements and using action verbs to make your experience more impactful."
    
    def improve_resume(self, resume_content, job_description=None, feedback=None):
        return {
            "improved_resume": f"Mock improved content based on: {feedback or 'general improvements'}",
            "generated_at": None
        }
    
    def analyze_resume(self, resume_content, job_description=None):
        return {
            "analysis": "Mock analysis of the resume showing strengths and areas for improvement",
            "score": 78,
            "generated_at": None
        }

class MockPDFContentReplacer:
    def __init__(self, use_enhanced=True, use_llm=True, use_ocr=False, use_direct=True):
        self.use_enhanced = use_enhanced
        self.use_llm = use_llm
        self.use_ocr = use_ocr
        self.use_direct = use_direct
    
    def analyze_resume(self, pdf_path):
        return {
            'basic_resume': f"""JOHN SMITH
Email: john.smith@email.com | Phone: (555) 123-4567
LinkedIn: linkedin.com/in/johnsmith | Location: San Francisco, CA

PROFESSIONAL SUMMARY
Results-driven Software Engineer with 5+ years of experience developing scalable web applications and leading cross-functional teams. Proven track record of improving system performance and delivering high-quality solutions.

EXPERIENCE

Senior Software Engineer | Tech Corp | 2020 - Present
• Led development of microservices architecture serving 1M+ daily users
• Improved application performance by 40% through code optimization
• Mentored 3 junior developers and conducted technical interviews
• Technologies: React, Node.js, PostgreSQL, AWS, Docker

Software Engineer | StartupXYZ | 2018 - 2020
• Developed RESTful APIs and frontend components for e-commerce platform
• Implemented automated testing reducing production bugs by 60%
• Collaborated with product managers and designers on feature development
• Technologies: Python, Django, JavaScript, MySQL, Redis

EDUCATION
Bachelor of Science in Computer Science
University of Technology | 2018
GPA: 3.8/4.0, Magna Cum Laude

SKILLS
• Programming Languages: Python, JavaScript, Java, C++, TypeScript
• Frontend: React, Vue.js, HTML5, CSS3, Bootstrap
• Backend: Node.js, Django, Express.js, Flask
• Databases: PostgreSQL, MySQL, MongoDB, Redis
• Cloud & DevOps: AWS, Docker, Kubernetes, Jenkins, Git
• Other: Agile/Scrum, Test-Driven Development, System Design

PROJECTS
Personal Finance App | 2023
• Built full-stack application with React frontend and Node.js backend
• Implemented secure authentication and data encryption
• Deployed on AWS with CI/CD pipeline

CERTIFICATIONS
• AWS Certified Solutions Architect (2022)
• Certified Scrum Master (2021)""",
            'formatted_document': None
        }
    
    def improve_resume(self, pdf_path, job_description=None, output_path=None):
        return output_path or "mock_improved_resume.pdf"