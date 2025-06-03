#!/usr/bin/env python3
"""
Complete Job Hunting Tool

This tool brings together all the functionality needed for a complete
job hunting workflow:

1. Process your resume with optimized OCR
2. Search for relevant job listings
3. Analyze job listings against your resume
4. Create tailored resumes and cover letters
5. Track your job applications
6. Prepare for interviews

It provides a simple command-line interface to access all these features.
"""

import os
import sys
import argparse
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_OUTPUT_DIR = "job_hunt_data"

def find_resume_file():
    """
    Find the most recent resume file in common locations.
    
    Returns:
        Path to resume file if found, None otherwise
    """
    # Common locations to check
    common_paths = [
        ".",  # Current directory
        "./job_applications_*",  # Job applications directories
        "./job_search_output",   # Job search output
        "./resume_output",       # Resume output
    ]
    
    import glob
    
    # Look for resume files in common locations
    resume_files = []
    for path in common_paths:
        for ext in ["*.txt", "*.pdf"]:
            pattern = os.path.join(path, ext)
            resume_files.extend(glob.glob(pattern))
    
    if not resume_files:
        return None
    
    # Sort by modification time, newest first
    resume_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Try to find the most likely resume file
    for file in resume_files:
        filename = os.path.basename(file)
        if re.search(r"resume|cv", filename, re.IGNORECASE):
            return file
    
    # Return the most recent file if no obvious resume file found
    return resume_files[0]

def ensure_output_dir(output_dir):
    """
    Ensure the output directory exists.
    
    Args:
        output_dir: Directory path
        
    Returns:
        Absolute path to the output directory
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Return absolute path
    return os.path.abspath(output_dir)

def process_resume(args):
    """
    Process the resume with optimized OCR.
    """
    try:
        from resume_for_job_apps import process_resume_for_job_application
        
        # Process resume
        output_file = process_resume_for_job_application(args.resume, args.output)
        
        print(f"\n✅ Resume processed successfully: {output_file}")
        print("\nUse this text when applying for jobs online.")
        
        # Return the processed file path
        return output_file
    except ImportError:
        print("Error: Could not import resume processor.")
        print("Please make sure resume_for_job_apps.py is available.")
        return None
    except Exception as e:
        print(f"Error processing resume: {str(e)}")
        return None

def search_jobs(args):
    """
    Search for job listings.
    """
    try:
        from job_finder import JobFinder
        
        # Initialize job finder
        job_finder = JobFinder(args.resume, args.output)
        
        # Search for jobs
        jobs = job_finder.search_jobs(
            keywords=args.keywords,
            location=args.location,
            sources=args.sources,
            limit=args.limit
        )
        
        print(f"\n✅ Found {len(jobs)} matching jobs")
        
        # Display job listings
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job.title} - {job.company}")
            print(f"   {job.location} | {job.source}")
            if hasattr(job, 'salary') and job.salary:
                print(f"   Salary: {job.salary}")
        
        return jobs
    except ImportError:
        print("Error: Could not import job finder.")
        print("Please make sure job_finder.py is available.")
        return []
    except Exception as e:
        print(f"Error searching jobs: {str(e)}")
        return []

def analyze_jobs(args, jobs=None):
    """
    Analyze job listings against resume.
    """
    try:
        from job_finder import JobFinder
        
        # Initialize job finder
        job_finder = JobFinder(args.resume, args.output)
        
        # Load resume text
        if not job_finder.resume_text:
            print("Error: Could not load resume text.")
            return []
        
        # Use provided jobs or load from cache
        if jobs is None:
            if args.job_file:
                import json
                with open(args.job_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                jobs = [job_finder.JobListing.from_dict(job_data) for job_data in data["results"]]
            else:
                print("Error: No jobs to analyze.")
                return []
        
        # Analyze each job
        for job in jobs:
            print(f"\nAnalyzing: {job.title} - {job.company}")
            match_info = job_finder.analyze_job_match(job)
            
            print(f"Match Score: {match_info['match_score']}%")
            print("\nMatching Skills:")
            print(", ".join(match_info['matching_skills']) or "None found")
            
            print("\nMissing Skills:")
            print(", ".join(match_info['missing_skills']) or "None found")
        
        return jobs
    except ImportError:
        print("Error: Could not import job finder.")
        print("Please make sure job_finder.py is available.")
        return []
    except Exception as e:
        print(f"Error analyzing jobs: {str(e)}")
        return []

def track_applications(args):
    """
    Track job applications.
    """
    try:
        from job_application_assistant import JobApplicationAssistant
        
        # Initialize application assistant
        assistant = JobApplicationAssistant(args.resume, args.output)
        
        # List all applications by default
        applications = assistant.list_applications()
        
        if not applications:
            print("No job applications found.")
            print("\nTo create an application:")
            print("job_hunter.py apply --resume your_resume.txt --title \"Job Title\" --company \"Company Name\"")
            return
        
        print("\n" + "="*70)
        print("JOB APPLICATIONS".center(70))
        print("="*70)
        
        # Group applications by status
        status_groups = {}
        for app in applications:
            if app.status not in status_groups:
                status_groups[app.status] = []
            status_groups[app.status].append(app)
        
        # Display applications by status group
        for status, apps in status_groups.items():
            status_display = {
                "preparing": "🔄 PREPARING",
                "applied": "📨 APPLIED",
                "interview_scheduled": "📅 INTERVIEWS SCHEDULED",
                "offer": "🎉 OFFERS",
                "rejected": "❌ REJECTED",
                "withdrawn": "⏹️ WITHDRAWN"
            }.get(status, status.upper())
            
            print(f"\n{status_display} ({len(apps)})")
            print("-" * len(status_display))
            
            for i, app in enumerate(apps, 1):
                print(f"{i}. [{app.app_id}] {app.job.title} - {app.job.company}")
                if app.applied_date:
                    print(f"   Applied: {app.applied_date}")
                if hasattr(app, 'interviews') and app.interviews:
                    next_interview = app.interviews[0]
                    print(f"   Next Interview: {next_interview['date']} ({next_interview['type']})")
        
        print("\nTo view application details:")
        print(f"job_hunter.py application view --app-id <APP_ID>")
        
    except ImportError:
        print("Error: Could not import job application assistant.")
        print("Please make sure job_application_assistant.py is available.")
    except Exception as e:
        print(f"Error tracking applications: {str(e)}")

def apply_for_job(args):
    """
    Create or update a job application.
    """
    try:
        from job_application_assistant import JobApplicationAssistant, JobApplication, ApplicationStatus
        
        if args.job_finder_available:
            from job_finder import JobListing
        else:
            # Create a minimal JobListing class if job_finder is not available
            class JobListing:
                def __init__(self, title, company, location, description, url, source, **kwargs):
                    self.title = title
                    self.company = company
                    self.location = location
                    self.description = description
                    self.url = url
                    self.source = source
                
                def to_dict(self):
                    return {
                        "title": self.title,
                        "company": self.company,
                        "location": self.location,
                        "description": self.description,
                        "url": self.url,
                        "source": self.source
                    }
        
        # Initialize application assistant
        assistant = JobApplicationAssistant(args.resume, args.output)
        
        # Get or create job application
        if args.app_id:
            # Update existing application
            app = assistant.get_application(args.app_id)
            print(f"Updating application for {app.job.title} at {app.job.company}")
            
            # Update status if provided
            if args.status:
                app.update_status(args.status, args.notes)
                assistant.update_application(app)
                print(f"Updated status to '{args.status}'")
            
            # Add note if provided
            elif args.notes:
                app.add_note(args.notes)
                assistant.update_application(app)
                print("Added note to application")
            
            # Add interview if provided
            elif args.interview_date and args.interview_type:
                app.add_interview(args.interview_date, args.interview_type, args.notes)
                assistant.update_application(app)
                print(f"Added {args.interview_type} interview on {args.interview_date}")
        
        # Create new application
        elif args.title and args.company:
            # Create job listing
            job = JobListing(
                title=args.title,
                company=args.company,
                location=args.location or "Unknown",
                description=args.description or "",
                url=args.url or "",
                source=args.source or "manual"
            )
            
            # Create application
            app = assistant.create_application(job)
            print(f"Created application with ID: {app.app_id}")
            
            # Set initial status if provided
            if args.status:
                app.update_status(args.status, args.notes)
                assistant.update_application(app)
        
        # Create application from job file
        elif args.job_file:
            import json
            with open(args.job_file, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            
            job = JobListing.from_dict(job_data)
            app = assistant.create_application(job)
            print(f"Created application with ID: {app.app_id} for {job.title} at {job.company}")
        
        else:
            print("Error: Not enough information to create or update application")
            return
        
        # Create tailored resume and cover letter if requested
        if args.create_materials:
            # Create tailored resume
            print("\nCreating tailored resume...")
            resume_path, _ = assistant.create_tailored_resume(app)
            print(f"Created tailored resume: {resume_path}")
            
            # Create cover letter
            print("\nCreating cover letter...")
            cover_path, _ = assistant.create_cover_letter(app)
            print(f"Created cover letter: {cover_path}")
        
        # Show application details
        from job_application_assistant import display_application_details
        display_application_details(app)
        
    except ImportError as e:
        print(f"Error importing required modules: {str(e)}")
        print("Please make sure job_application_assistant.py is available.")
    except Exception as e:
        print(f"Error applying for job: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main entry point."""
    # Define argument parser
    parser = argparse.ArgumentParser(description="Complete Job Hunting Tool")
    
    # Common arguments
    parser.add_argument("--resume", "-r", help="Path to your resume file (PDF or text)")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process resume command
    process_parser = subparsers.add_parser("process", help="Process resume with optimized OCR")
    
    # Search for jobs command
    search_parser = subparsers.add_parser("search", help="Search for job listings")
    search_parser.add_argument("--keywords", "-k", nargs="+", required=True, help="Keywords to search for")
    search_parser.add_argument("--location", "-l", default="", help="Location to search in")
    search_parser.add_argument("--sources", "-s", nargs="+", default=["linkedin", "indeed", "glassdoor"], 
                                help="Job sources to search")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum results per source")
    
    # Analyze jobs command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze job listings against resume")
    analyze_parser.add_argument("--job-file", "-j", help="Path to job listings file (from search)")
    
    # Track applications command
    track_parser = subparsers.add_parser("track", help="Track job applications")
    
    # Apply for job command
    apply_parser = subparsers.add_parser("apply", help="Create or update a job application")
    apply_parser.add_argument("--app-id", help="Application ID to update (if updating)")
    apply_parser.add_argument("--title", help="Job title (if creating)")
    apply_parser.add_argument("--company", help="Company name (if creating)")
    apply_parser.add_argument("--location", help="Job location")
    apply_parser.add_argument("--description", help="Job description")
    apply_parser.add_argument("--url", help="Job URL")
    apply_parser.add_argument("--source", default="manual", help="Job source")
    apply_parser.add_argument("--job-file", help="Path to job listing file")
    apply_parser.add_argument("--status", choices=["preparing", "applied", "interview_scheduled", "rejected", "offer", "withdrawn"],
                               help="Application status")
    apply_parser.add_argument("--notes", help="Notes for the application")
    apply_parser.add_argument("--interview-date", help="Interview date (YYYY-MM-DD)")
    apply_parser.add_argument("--interview-type", choices=["phone", "video", "onsite", "technical", "other"],
                               help="Interview type")
    apply_parser.add_argument("--create-materials", "-m", action="store_true", 
                               help="Create tailored resume and cover letter")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if job_finder is available
    try:
        import job_finder
        args.job_finder_available = True
    except ImportError:
        args.job_finder_available = False
    
    # Try to find resume if not specified
    if not args.resume:
        resume_file = find_resume_file()
        if resume_file:
            print(f"Using resume file: {resume_file}")
            args.resume = resume_file
        else:
            print("No resume file specified or found automatically.")
            if args.command not in ["track"]:  # Commands that don't strictly need a resume
                parser.print_help()
                return 1
    
    # Ensure output directory exists
    args.output = ensure_output_dir(args.output)
    
    # Execute command
    if args.command == "process":
        process_resume(args)
    elif args.command == "search":
        search_jobs(args)
    elif args.command == "analyze":
        analyze_jobs(args)
    elif args.command == "track":
        track_applications(args)
    elif args.command == "apply":
        apply_for_job(args)
    else:
        # No command, show help
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
