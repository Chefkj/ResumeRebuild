#!/usr/bin/env python3
"""
Job Application Assistant

This tool helps you apply for jobs by:
1. Tailoring your resume for specific job listings
2. Generating cover letters
3. Tracking your job applications
4. Preparing for interviews
"""

import os
import sys
import re
import json
import argparse
import logging
import platform
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import shutil

# Try to import JobFinder and JobListing
try:
    from job_finder import JobListing, JobFinder, JobFinderException
    JOB_FINDER_AVAILABLE = True
except ImportError:
    JOB_FINDER_AVAILABLE = False
    # Create stub classes for type hints if not available
    class JobListing:
        def __init__(self, **kwargs): pass
        def to_dict(self): return {}
        @classmethod
        def from_dict(cls, data): return cls()
    class JobFinder:
        def __init__(self, **kwargs): pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
APPLICATION_TRACKING_DIR = "job_applications"
COVER_LETTER_TEMPLATES_DIR = "cover_letter_templates"
TAILORED_RESUMES_DIR = "tailored_resumes"
SKILLS_KEYWORD_FILE = "skills_keywords.json"

class JobApplicationException(Exception):
    """Exception raised for errors in the JobApplication module."""
    pass

class ApplicationStatus:
    """Enum-like class for application status values."""
    PREPARING = "preparing"
    APPLIED = "applied"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    REJECTED = "rejected"
    OFFER = "offer"
    WITHDRAWN = "withdrawn"

class JobApplication:
    """Class representing a job application."""
    
    def __init__(self, job: JobListing, status: str = ApplicationStatus.PREPARING,
                 applied_date: Optional[str] = None, app_id: Optional[str] = None,
                 notes: Optional[str] = None):
        """
        Initialize a job application.
        
        Args:
            job: JobListing object
            status: Application status
            applied_date: Date when applied (if applicable)
            app_id: Application ID (generated if not provided)
            notes: Additional notes about the application
        """
        self.job = job
        self.status = status
        self.applied_date = applied_date
        self.app_id = app_id or self._generate_id()
        self.notes = notes or ""
        self.tailored_resume_path = None
        self.cover_letter_path = None
        self.interviews = []
    
    def _generate_id(self) -> str:
        """Generate a unique ID for the application."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_string = f"{self.job.title}_{self.job.company}_{timestamp}"
        return f"app_{hash(unique_string) & 0xFFFFFFFF:08x}"
    
    def update_status(self, status: str, notes: Optional[str] = None):
        """
        Update the application status.
        
        Args:
            status: New application status
            notes: Optional notes about the status update
        """
        self.status = status
        if notes:
            self.add_note(notes)
        
        if status == ApplicationStatus.APPLIED and not self.applied_date:
            self.applied_date = datetime.now().strftime("%Y-%m-%d")
    
    def add_note(self, note: str):
        """
        Add a note to the application.
        
        Args:
            note: Note text to add
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.notes += f"\n[{timestamp}] {note}"
        self.notes = self.notes.strip()
    
    def add_interview(self, interview_date: str, interview_type: str, notes: Optional[str] = None):
        """
        Add an interview to the application.
        
        Args:
            interview_date: Date of the interview
            interview_type: Type of interview (phone, video, onsite, etc.)
            notes: Optional notes about the interview
        """
        self.interviews.append({
            "date": interview_date,
            "type": interview_type,
            "notes": notes or ""
        })
        self.update_status(ApplicationStatus.INTERVIEW_SCHEDULED)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "app_id": self.app_id,
            "job": self.job.to_dict(),
            "status": self.status,
            "applied_date": self.applied_date,
            "notes": self.notes,
            "tailored_resume_path": self.tailored_resume_path,
            "cover_letter_path": self.cover_letter_path,
            "interviews": self.interviews
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobApplication':
        """Create a JobApplication object from a dictionary."""
        job = JobListing.from_dict(data["job"])
        app = cls(
            job=job,
            status=data["status"],
            applied_date=data.get("applied_date"),
            app_id=data.get("app_id"),
            notes=data.get("notes")
        )
        app.tailored_resume_path = data.get("tailored_resume_path")
        app.cover_letter_path = data.get("cover_letter_path")
        app.interviews = data.get("interviews", [])
        return app
    
    def __str__(self) -> str:
        """String representation of the job application."""
        status_display = {
            ApplicationStatus.PREPARING: "🔄 Preparing",
            ApplicationStatus.APPLIED: "📨 Applied",
            ApplicationStatus.INTERVIEW_SCHEDULED: "📅 Interview Scheduled",
            ApplicationStatus.REJECTED: "❌ Rejected",
            ApplicationStatus.OFFER: "🎉 Offer Received",
            ApplicationStatus.WITHDRAWN: "⏹️ Withdrawn"
        }.get(self.status, self.status)
        
        header = f"{self.job.title} - {self.job.company} ({status_display})"
        
        details = []
        if self.applied_date:
            details.append(f"Applied: {self.applied_date}")
        
        if self.interviews:
            next_interview = sorted(self.interviews, key=lambda i: i["date"])[0]
            details.append(f"Next Interview: {next_interview['date']} ({next_interview['type']})")
        
        if self.job.url:
            details.append(f"Job URL: {self.job.url}")
        
        if self.tailored_resume_path:
            details.append(f"Tailored Resume: {os.path.basename(self.tailored_resume_path)}")
        
        if self.cover_letter_path:
            details.append(f"Cover Letter: {os.path.basename(self.cover_letter_path)}")
        
        result = [header, "-" * len(header)] + details
        
        # Add notes preview if available
        if self.notes:
            notes_preview = self.notes.split('\n')[0]
            result.append(f"\nNotes: {notes_preview}")
        
        return "\n".join(result)


class JobApplicationAssistant:
    """Class for assisting with job applications."""
    
    def __init__(self, resume_path: Optional[str] = None, output_dir: str = "."):
        """
        Initialize a job application assistant.
        
        Args:
            resume_path: Path to your resume file
            output_dir: Directory for output files
        """
        self.resume_path = resume_path
        self.resume_text = None
        self.output_dir = output_dir
        self.app_tracking_dir = os.path.join(output_dir, APPLICATION_TRACKING_DIR)
        self.tailored_resumes_dir = os.path.join(output_dir, TAILORED_RESUMES_DIR)
        self.cover_letter_dir = os.path.join(output_dir, COVER_LETTER_TEMPLATES_DIR)
        
        # Ensure directories exist
        os.makedirs(self.app_tracking_dir, exist_ok=True)
        os.makedirs(self.tailored_resumes_dir, exist_ok=True)
        os.makedirs(self.cover_letter_dir, exist_ok=True)
        
        # Load resume text if provided
        if resume_path and os.path.exists(resume_path):
            with open(resume_path, 'r', encoding='utf-8') as f:
                self.resume_text = f.read()
        
        # Initialize JobFinder if available
        self.job_finder = None
        if JOB_FINDER_AVAILABLE:
            self.job_finder = JobFinder(resume_path, output_dir)
    
    def create_application(self, job: JobListing) -> JobApplication:
        """
        Create a new job application.
        
        Args:
            job: JobListing object
            
        Returns:
            JobApplication object
        """
        app = JobApplication(job)
        self._save_application(app)
        return app
    
    def update_application(self, app: JobApplication):
        """
        Update an existing job application.
        
        Args:
            app: JobApplication object to update
        """
        self._save_application(app)
    
    def get_application(self, app_id: str) -> JobApplication:
        """
        Retrieve a job application by ID.
        
        Args:
            app_id: Application ID
            
        Returns:
            JobApplication object
        """
        app_path = os.path.join(self.app_tracking_dir, f"{app_id}.json")
        if not os.path.exists(app_path):
            raise JobApplicationException(f"Application not found: {app_id}")
        
        with open(app_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return JobApplication.from_dict(data)
    
    def list_applications(self, status: Optional[str] = None) -> List[JobApplication]:
        """
        List all job applications, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of JobApplication objects
        """
        if not os.path.exists(self.app_tracking_dir):
            return []
        
        app_files = [f for f in os.listdir(self.app_tracking_dir) if f.endswith(".json")]
        
        applications = []
        for app_file in app_files:
            try:
                app_path = os.path.join(self.app_tracking_dir, app_file)
                with open(app_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Skip if status filter is set and doesn't match
                if status and data.get("status") != status:
                    continue
                
                app = JobApplication.from_dict(data)
                applications.append(app)
            except Exception as e:
                logger.error(f"Error reading application file {app_file}: {str(e)}")
        
        # Sort by status and applied date
        def sort_key(app):
            # Define status priority order
            status_priority = {
                ApplicationStatus.OFFER: 0,
                ApplicationStatus.INTERVIEW_SCHEDULED: 1,
                ApplicationStatus.APPLIED: 2,
                ApplicationStatus.PREPARING: 3,
                ApplicationStatus.REJECTED: 4,
                ApplicationStatus.WITHDRAWN: 5
            }
            # Use applied date as secondary sort key, or current date if not applied
            date_str = app.applied_date or datetime.now().strftime("%Y-%m-%d")
            return (status_priority.get(app.status, 99), date_str)
        
        applications.sort(key=sort_key)
        
        return applications
    
    def _save_application(self, app: JobApplication):
        """
        Save a job application to disk.
        
        Args:
            app: JobApplication object to save
        """
        app_path = os.path.join(self.app_tracking_dir, f"{app.app_id}.json")
        
        with open(app_path, 'w', encoding='utf-8') as f:
            json.dump(app.to_dict(), f, indent=2)
        
        logger.info(f"Saved application to {app_path}")
    
    def delete_application(self, app_id: str) -> bool:
        """
        Delete a job application.
        
        Args:
            app_id: Application ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        app_path = os.path.join(self.app_tracking_dir, f"{app_id}.json")
        if os.path.exists(app_path):
            os.remove(app_path)
            logger.info(f"Deleted application: {app_id}")
            return True
        return False
    
    def create_tailored_resume(self, app: JobApplication) -> Tuple[str, str]:
        """
        Create a tailored resume for a job application.
        
        Args:
            app: JobApplication object
            
        Returns:
            Tuple of (file_path, tailored_resume_text)
        """
        if not self.resume_text:
            raise JobApplicationException("Resume text not available")
        
        # Create a tailored resume based on job description
        resume_text = self.resume_text
        
        # 1. Extract skills from job description to highlight
        job_skills = []
        if hasattr(app.job, 'missing_skills') and app.job.missing_skills:
            job_skills = app.job.missing_skills
        else:
            # Basic keyword extraction if we don't have missing skills
            common_skills = self._load_skills_keywords()
            for skill in common_skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', app.job.description, re.IGNORECASE):
                    job_skills.append(skill)
        
        # 2. Create job-specific tailoring
        tailored_text = f"# Tailored Resume for {app.job.title} at {app.job.company}\n\n"
        
        # Add original resume text
        tailored_text += resume_text
        
        # Add skills section if missing in the original
        if "SKILLS" not in resume_text.upper() and job_skills:
            tailored_text += "\n\nSKILLS\n"
            tailored_text += ", ".join(job_skills)
        
        # Generate filename based on job info
        safe_company = re.sub(r'[^\w\-\.]', '_', app.job.company)
        safe_title = re.sub(r'[^\w\-\.]', '_', app.job.title)
        filename = f"resume_{safe_company}_{safe_title}_{datetime.now().strftime('%Y%m%d')}.txt"
        file_path = os.path.join(self.tailored_resumes_dir, filename)
        
        # Save tailored resume
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(tailored_text)
        
        # Update application with tailored resume path
        app.tailored_resume_path = file_path
        self._save_application(app)
        
        logger.info(f"Created tailored resume at {file_path}")
        return file_path, tailored_text
    
    def create_cover_letter(self, app: JobApplication) -> Tuple[str, str]:
        """
        Create a cover letter for a job application.
        
        Args:
            app: JobApplication object
            
        Returns:
            Tuple of (file_path, cover_letter_text)
        """
        # Try to find a cover letter template
        template_path = os.path.join(self.cover_letter_dir, "template.txt")
        template_text = ""
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template_text = f.read()
        else:
            # Default template if none exists
            template_text = """[Your Name]
[Your Address]
[City, State ZIP]
[Your Email]
[Your Phone]

[Date]

[Hiring Manager's Name]
[Company Name]
[Company Address]
[City, State ZIP]

Dear [Hiring Manager's Name or "Hiring Manager"],

I am writing to express my interest in the [Job Title] position at [Company Name]. With my background in [relevant experience/skills], I am excited about the opportunity to contribute to your team.

[Paragraph about your relevant experience and how it relates to the job]

[Paragraph about why you're interested in the company specifically]

Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experiences align with your needs.

Sincerely,

[Your Name]
"""
        
        # Replace placeholders in the template
        cover_text = template_text
        cover_text = cover_text.replace("[Job Title]", app.job.title)
        cover_text = cover_text.replace("[Company Name]", app.job.company)
        cover_text = cover_text.replace("[Date]", datetime.now().strftime("%B %d, %Y"))
        
        # Generate filename based on job info
        safe_company = re.sub(r'[^\w\-\.]', '_', app.job.company)
        safe_title = re.sub(r'[^\w\-\.]', '_', app.job.title)
        filename = f"cover_letter_{safe_company}_{safe_title}_{datetime.now().strftime('%Y%m%d')}.txt"
        file_path = os.path.join(self.cover_letter_dir, filename)
        
        # Save cover letter
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cover_text)
        
        # Update application with cover letter path
        app.cover_letter_path = file_path
        self._save_application(app)
        
        logger.info(f"Created cover letter at {file_path}")
        return file_path, cover_text
    
    def generate_interview_prep(self, app: JobApplication) -> str:
        """
        Generate interview preparation materials.
        
        Args:
            app: JobApplication object
            
        Returns:
            Path to the generated prep file
        """
        # Create interview prep document
        prep_text = f"# Interview Preparation for {app.job.title} at {app.job.company}\n\n"
        
        # Add job details
        prep_text += "## JOB DETAILS\n\n"
        prep_text += f"Title: {app.job.title}\n"
        prep_text += f"Company: {app.job.company}\n"
        prep_text += f"Location: {app.job.location}\n\n"
        
        # Add job description
        prep_text += "## JOB DESCRIPTION\n\n"
        prep_text += app.job.description
        prep_text += "\n\n"
        
        # Add skills matching
        if hasattr(app.job, 'matching_skills') and app.job.matching_skills:
            prep_text += "## YOUR MATCHING SKILLS\n\n"
            for skill in app.job.matching_skills:
                prep_text += f"- {skill}\n"
            prep_text += "\n"
        
        if hasattr(app.job, 'missing_skills') and app.job.missing_skills:
            prep_text += "## SKILLS TO PREPARE FOR\n\n"
            for skill in app.job.missing_skills:
                prep_text += f"- {skill}\n"
            prep_text += "\n"
        
        # Add interview question templates
        prep_text += "## COMMON INTERVIEW QUESTIONS\n\n"
        prep_text += "1. Tell me about yourself.\n"
        prep_text += "2. Why are you interested in this position?\n"
        prep_text += "3. Why do you want to work for our company?\n"
        prep_text += "4. What are your strengths and weaknesses?\n"
        prep_text += "5. Describe a challenging situation at work and how you handled it.\n"
        prep_text += "6. Where do you see yourself in five years?\n"
        prep_text += "7. What questions do you have for us?\n\n"
        
        # Generate filename
        safe_company = re.sub(r'[^\w\-\.]', '_', app.job.company)
        filename = f"interview_prep_{safe_company}_{datetime.now().strftime('%Y%m%d')}.txt"
        file_path = os.path.join(self.app_tracking_dir, filename)
        
        # Save prep file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(prep_text)
        
        logger.info(f"Created interview prep at {file_path}")
        return file_path
    
    def _load_skills_keywords(self) -> List[str]:
        """
        Load common skills keywords.
        
        Returns:
            List of skill keywords
        """
        skills_path = os.path.join(self.output_dir, SKILLS_KEYWORD_FILE)
        
        # If file exists, load from it
        if os.path.exists(skills_path):
            try:
                with open(skills_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading skills file: {str(e)}")
        
        # Otherwise, return default skills
        return [
            "Python", "Java", "JavaScript", "TypeScript", "React", "Vue", "Angular",
            "Node.js", "Express", "Django", "Flask", "Spring", "SQL", "NoSQL",
            "MongoDB", "PostgreSQL", "MySQL", "Oracle", "AWS", "Azure", "GCP",
            "Docker", "Kubernetes", "CI/CD", "DevOps", "Agile", "Scrum",
            "Machine Learning", "AI", "Data Science", "Big Data", "Hadoop", "Spark",
            "ETL", "Data Warehouse", "Business Intelligence", "Power BI", "Tableau",
            "Product Management", "Project Management", "Leadership", "Team Management"
        ]
    
    def open_file(self, file_path: str) -> bool:
        """
        Open a file with the system's default application.
        
        Args:
            file_path: Path to the file to open
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path], check=True)
            else:  # Linux and other Unix-like
                subprocess.run(["xdg-open", file_path], check=True)
            return True
        except Exception as e:
            logger.error(f"Error opening file: {str(e)}")
            return False


def display_application_details(app: JobApplication):
    """Display detailed information about a job application."""
    print("\n" + "="*70)
    print(f"APPLICATION DETAILS: {app.job.title} at {app.job.company}".center(70))
    print("="*70)
    
    # Status information
    status_display = {
        ApplicationStatus.PREPARING: "🔄 Preparing",
        ApplicationStatus.APPLIED: "📨 Applied",
        ApplicationStatus.INTERVIEW_SCHEDULED: "📅 Interview Scheduled",
        ApplicationStatus.REJECTED: "❌ Rejected",
        ApplicationStatus.OFFER: "🎉 Offer Received",
        ApplicationStatus.WITHDRAWN: "⏹️ Withdrawn"
    }.get(app.status, app.status)
    
    print(f"Status: {status_display}")
    
    if app.applied_date:
        print(f"Applied Date: {app.applied_date}")
    
    # Job details
    print("\nJOB DETAILS:")
    print("-" * 70)
    print(f"Title: {app.job.title}")
    print(f"Company: {app.job.company}")
    print(f"Location: {app.job.location}")
    
    if hasattr(app.job, 'salary') and app.job.salary:
        print(f"Salary: {app.job.salary}")
    
    print(f"Source: {app.job.source}")
    print(f"URL: {app.job.url}")
    
    # Application materials
    print("\nAPPLICATION MATERIALS:")
    print("-" * 70)
    
    if app.tailored_resume_path:
        print(f"Tailored Resume: {app.tailored_resume_path}")
    else:
        print("Tailored Resume: Not created yet")
    
    if app.cover_letter_path:
        print(f"Cover Letter: {app.cover_letter_path}")
    else:
        print("Cover Letter: Not created yet")
    
    # Interviews
    if app.interviews:
        print("\nINTERVIEWS:")
        print("-" * 70)
        for i, interview in enumerate(app.interviews, 1):
            print(f"{i}. Date: {interview['date']}, Type: {interview['type']}")
            if interview['notes']:
                print(f"   Notes: {interview['notes']}")
    
    # Notes
    if app.notes:
        print("\nNOTES:")
        print("-" * 70)
        print(app.notes)


def main():
    """Main entry point for the job application assistant."""
    parser = argparse.ArgumentParser(description="Job Application Assistant")
    parser.add_argument("--resume", "-r", help="Path to your resume text file")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    
    # Application commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List applications
    list_parser = subparsers.add_parser("list", help="List job applications")
    list_parser.add_argument("--status", "-s", help="Filter by status")
    
    # View application details
    view_parser = subparsers.add_parser("view", help="View job application details")
    view_parser.add_argument("app_id", help="Application ID to view")
    
    # Create application from job listing
    create_parser = subparsers.add_parser("create", help="Create a job application")
    create_parser.add_argument("--job-file", "-j", help="Path to job listing JSON file")
    create_parser.add_argument("--title", help="Job title")
    create_parser.add_argument("--company", help="Company name")
    create_parser.add_argument("--location", help="Job location")
    create_parser.add_argument("--description", help="Job description")
    create_parser.add_argument("--url", help="Job URL")
    create_parser.add_argument("--source", default="manual", help="Job source")
    
    # Update application status
    update_parser = subparsers.add_parser("update", help="Update job application status")
    update_parser.add_argument("app_id", help="Application ID to update")
    update_parser.add_argument("--status", "-s", required=True, 
                               choices=["preparing", "applied", "interview_scheduled", "rejected", "offer", "withdrawn"],
                               help="New application status")
    update_parser.add_argument("--notes", "-n", help="Notes for the status update")
    
    # Add notes to application
    note_parser = subparsers.add_parser("note", help="Add notes to job application")
    note_parser.add_argument("app_id", help="Application ID to add notes to")
    note_parser.add_argument("note", help="Note text to add")
    
    # Add interview to application
    interview_parser = subparsers.add_parser("interview", help="Add interview to job application")
    interview_parser.add_argument("app_id", help="Application ID to add interview to")
    interview_parser.add_argument("--date", "-d", required=True, help="Interview date (YYYY-MM-DD)")
    interview_parser.add_argument("--type", "-t", required=True, 
                                 choices=["phone", "video", "onsite", "technical", "other"],
                                 help="Interview type")
    interview_parser.add_argument("--notes", "-n", help="Notes about the interview")
    
    # Create tailored resume for application
    resume_parser = subparsers.add_parser("tailor", help="Create tailored resume for job application")
    resume_parser.add_argument("app_id", help="Application ID to create resume for")
    
    # Create cover letter for application
    cover_parser = subparsers.add_parser("cover", help="Create cover letter for job application")
    cover_parser.add_argument("app_id", help="Application ID to create cover letter for")
    
    # Generate interview prep for application
    prep_parser = subparsers.add_parser("prep", help="Generate interview prep for job application")
    prep_parser.add_argument("app_id", help="Application ID to create prep for")
    
    # Delete application
    delete_parser = subparsers.add_parser("delete", help="Delete job application")
    delete_parser.add_argument("app_id", help="Application ID to delete")
    delete_parser.add_argument("--confirm", "-c", action="store_true", 
                               help="Confirm deletion without prompting")
    
    args = parser.parse_args()
    
    try:
        # Initialize application assistant
        assistant = JobApplicationAssistant(args.resume, args.output)
        
        # List applications
        if args.command == "list":
            applications = assistant.list_applications(args.status)
            if not applications:
                print(f"No applications found{' with status: ' + args.status if args.status else ''}")
                return 0
            
            print("\n" + "="*70)
            print("JOB APPLICATIONS".center(70))
            print("="*70)
            
            for i, app in enumerate(applications, 1):
                status_display = {
                    ApplicationStatus.PREPARING: "🔄 Preparing",
                    ApplicationStatus.APPLIED: "📨 Applied",
                    ApplicationStatus.INTERVIEW_SCHEDULED: "📅 Interview Scheduled",
                    ApplicationStatus.REJECTED: "❌ Rejected",
                    ApplicationStatus.OFFER: "🎉 Offer Received",
                    ApplicationStatus.WITHDRAWN: "⏹️ Withdrawn"
                }.get(app.status, app.status)
                
                print(f"{i}. [{app.app_id}] {app.job.title} - {app.job.company} ({status_display})")
                
                if app.applied_date:
                    print(f"   Applied: {app.applied_date}")
                
                print()
        
        # View application details
        elif args.command == "view":
            app = assistant.get_application(args.app_id)
            display_application_details(app)
        
        # Create application
        elif args.command == "create":
            # Create from job file
            if args.job_file:
                if not JOB_FINDER_AVAILABLE:
                    print("Error: JobFinder module not available")
                    return 1
                
                with open(args.job_file, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                
                job = JobListing.from_dict(job_data)
            
            # Create manually
            elif args.title and args.company:
                if not JOB_FINDER_AVAILABLE:
                    # Create a basic JobListing class implementation
                    from job_finder import JobListing
                
                job = JobListing(
                    title=args.title,
                    company=args.company,
                    location=args.location or "Unknown",
                    description=args.description or "",
                    url=args.url or "",
                    source=args.source
                )
            
            else:
                print("Error: Either provide a job file or specify title and company")
                parser.print_help()
                return 1
            
            # Create application
            app = assistant.create_application(job)
            print(f"Created application with ID: {app.app_id}")
            display_application_details(app)
        
        # Update application status
        elif args.command == "update":
            app = assistant.get_application(args.app_id)
            app.update_status(args.status, args.notes)
            assistant.update_application(app)
            print(f"Updated status to '{args.status}'")
        
        # Add notes to application
        elif args.command == "note":
            app = assistant.get_application(args.app_id)
            app.add_note(args.note)
            assistant.update_application(app)
            print("Added note to application")
        
        # Add interview to application
        elif args.command == "interview":
            app = assistant.get_application(args.app_id)
            app.add_interview(args.date, args.type, args.notes)
            assistant.update_application(app)
            print(f"Added {args.type} interview on {args.date}")
        
        # Create tailored resume
        elif args.command == "tailor":
            app = assistant.get_application(args.app_id)
            resume_path, _ = assistant.create_tailored_resume(app)
            print(f"Created tailored resume: {resume_path}")
            
            # Ask if user wants to open the file
            if input("Open the resume file? (y/n): ").lower().startswith('y'):
                assistant.open_file(resume_path)
        
        # Create cover letter
        elif args.command == "cover":
            app = assistant.get_application(args.app_id)
            cover_path, _ = assistant.create_cover_letter(app)
            print(f"Created cover letter: {cover_path}")
            
            # Ask if user wants to open the file
            if input("Open the cover letter file? (y/n): ").lower().startswith('y'):
                assistant.open_file(cover_path)
        
        # Generate interview prep
        elif args.command == "prep":
            app = assistant.get_application(args.app_id)
            prep_path = assistant.generate_interview_prep(app)
            print(f"Created interview prep document: {prep_path}")
            
            # Ask if user wants to open the file
            if input("Open the interview prep file? (y/n): ").lower().startswith('y'):
                assistant.open_file(prep_path)
        
        # Delete application
        elif args.command == "delete":
            if args.confirm or input(f"Are you sure you want to delete application {args.app_id}? (y/n): ").lower().startswith('y'):
                if assistant.delete_application(args.app_id):
                    print(f"Deleted application: {args.app_id}")
                else:
                    print(f"Application not found: {args.app_id}")
        
        # No command or invalid command
        else:
            parser.print_help()
        
        return 0
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
