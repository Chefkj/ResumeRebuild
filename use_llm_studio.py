#!/usr/bin/env python3
"""
Script to connect to LLM Studio via ManageAI integration for resume improvement

This script provides an integration with the ManageAI Resume API and LLM Studio
to leverage advanced AI capabilities for resume improvement.
"""

import sys
import os
import logging
import json
import time
import argparse

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from utils.local_llm_adapter import LocalLLMAdapter
from utils.manageai_adapter import ManageAIResumeAdapter

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResumeLLMHelper:
    """Helper class to use LLM Studio for resume generation and improvement"""
    
    def __init__(self, host="localhost", port=5000, model_name="qwen-14b"):
        """Initialize the helper with connection to LLM Studio"""
        self.llm_adapter = LocalLLMAdapter(
            host=host,
            port=port,
            model_name=model_name
        )
        
        # Verify connection
        if not self.llm_adapter.test_connection():
            logger.error("Could not connect to LLM Studio. Is it running?")
            raise ConnectionError("Failed to connect to LLM Studio")
        
        logger.info("Successfully connected to LLM Studio")


class ManageAIResumeHelper:
    """Helper class to use ManageAI API for resume enhancement"""
    
    def __init__(self, api_url="http://localhost:8080", api_key=None):
        """Initialize the helper with connection to ManageAI Resume API"""
        self.api = ManageAIResumeAdapter(api_url=api_url, api_key=api_key)
        
        # Verify connection
        if not self.api.test_connection():
            logger.error("Could not connect to ManageAI Resume API. Is it running?")
            raise ConnectionError("Failed to connect to ManageAI Resume API")
        
        logger.info("Successfully connected to ManageAI Resume API")
        
    def parse_resume_text(self, resume_text: str) -> dict:
        """
        Parse plain text resume into structured format for the API
        
        Args:
            resume_text: Plain text resume content
        
        Returns:
            Dictionary with structured resume data
        """
        # For simplicity, we'll use a basic structure that works with the API
        sections = []
        current_section = ""
        current_content = []
        
        # Split resume into lines and identify sections
        for line in resume_text.split('\n'):
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
        
        # Format resume data for API
        name = ""
        email = ""
        phone = ""
        
        # Try to extract contact info from the first section
        if sections and sections[0]["name"].upper() in ("CONTACT", "PERSONAL INFORMATION"):
            contact_text = sections[0]["content"]
            # Simple extraction logic - could be more sophisticated
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
    
    def improve_resume(self, resume_text, job_description=None):
        """
        Get suggestions to improve a resume based on a job description
        using the ManageAI Resume API
        
        Args:
            resume_text: The current resume content as text
            job_description: Optional job description to tailor the resume for
        
        Returns:
            Suggestions for improving the resume
        """
        # Parse the resume text into a structured format
        structured_resume = self.parse_resume_text(resume_text)
        
        if not job_description:
            # Just analyze the resume if no job description
            result = self.api.analyze_resume(structured_resume)
            return self._format_analysis_result(result)
        
        # If we have a job description, do a match and get improvement suggestions
        job_analysis = self.api.analyze_job(job_description)
        match_result = self.api.match_resume_to_job(structured_resume, job_description)
        
        improvement = self.api.improve_resume(structured_resume, job_description, match_result)
        
        return self._format_improvement_result(improvement, match_result)
    
    def tailor_resume(self, resume_text, job_description):
        """
        Generate a tailored version of the resume for a specific job
        
        Args:
            resume_text: The current resume content
            job_description: Job description to tailor the resume for
        
        Returns:
            Tailored version of the resume
        """
        # Parse the resume text into a structured format
        structured_resume = self.parse_resume_text(resume_text)
        
        # Go through the full analysis and improvement workflow
        resume_analysis = self.api.analyze_resume(structured_resume)
        job_analysis = self.api.analyze_job(job_description)
        match_result = self.api.match_resume_to_job(
            structured_resume, 
            job_description,
            resume_analysis,
            job_analysis
        )
        
        improvement = self.api.improve_resume(structured_resume, job_description, match_result)
        
        # Return the improved resume content
        if "improved_resume" in improvement:
            return self._format_improved_resume(improvement["improved_resume"])
        else:
            return f"## IMPROVEMENT SUGGESTIONS\n\n{self._format_improvement_result(improvement, match_result)}"
    
    def get_ats_compatibility(self, resume_text):
        """
        Check if the resume is compatible with Applicant Tracking Systems
        using ManageAI Resume API
        
        Args:
            resume_text: The resume content to check
        
        Returns:
            ATS compatibility analysis
        """
        # Parse the resume text into a structured format
        structured_resume = self.parse_resume_text(resume_text)
        
        # Analyze the resume
        analysis = self.api.analyze_resume(structured_resume)
        
        # Extract ATS compatibility information
        if "ats_compatibility" in analysis:
            return self._format_ats_result(analysis["ats_compatibility"])
        else:
            return self._format_analysis_result(analysis)
    
    def _format_analysis_result(self, analysis):
        """Format analysis result into readable text"""
        result = "# RESUME ANALYSIS\n\n"
        
        if "skills" in analysis:
            result += "## Skills Identified\n"
            for skill in analysis["skills"]:
                result += f"- {skill}\n"
            result += "\n"
            
        if "experience_summary" in analysis:
            result += "## Experience Summary\n"
            result += f"{analysis['experience_summary']}\n\n"
            
        if "suggestions" in analysis:
            result += "## Suggestions for Improvement\n"
            for suggestion in analysis["suggestions"]:
                result += f"- {suggestion}\n"
                
        return result
    
    def _format_improvement_result(self, improvement, match_result):
        """Format improvement result into readable text"""
        result = "# RESUME IMPROVEMENT SUGGESTIONS\n\n"
        
        if match_result and "score" in match_result:
            result += f"## Match Score: {match_result['score']}/100\n\n"
            
        if "gap_analysis" in improvement:
            result += "## Skills Gap Analysis\n"
            for gap in improvement["gap_analysis"]:
                result += f"- **{gap['skill']}**: {gap['recommendation']}\n"
            result += "\n"
            
        if "improvements" in improvement:
            result += "## Suggested Improvements\n"
            for section, suggestions in improvement["improvements"].items():
                result += f"### {section}\n"
                for suggestion in suggestions:
                    result += f"- {suggestion}\n"
                result += "\n"
                
        return result
    
    def _format_ats_result(self, ats_info):
        """Format ATS compatibility info into readable text"""
        result = "# ATS COMPATIBILITY ANALYSIS\n\n"
        
        if "score" in ats_info:
            result += f"## Overall Score: {ats_info['score']}/100\n\n"
            
        if "issues" in ats_info:
            result += "## Issues Detected\n"
            for issue in ats_info["issues"]:
                result += f"- **{issue['severity']}**: {issue['description']}\n"
            result += "\n"
            
        if "recommendations" in ats_info:
            result += "## Recommendations\n"
            for rec in ats_info["recommendations"]:
                result += f"- {rec}\n"
                
        return result
    
    def _format_improved_resume(self, improved_resume):
        """Format improved resume into a readable format"""
        result = "# IMPROVED RESUME\n\n"
        
        # Format contact information
        if "contact" in improved_resume:
            contact = improved_resume["contact"]
            result += f"## {contact.get('name', 'Contact Information')}\n"
            if "email" in contact and contact["email"]:
                result += f"Email: {contact['email']}\n"
            if "phone" in contact and contact["phone"]:
                result += f"Phone: {contact['phone']}\n"
            if "address" in contact and contact["address"]:
                result += f"Address: {contact['address']}\n"
            if "linkedin" in contact and contact["linkedin"]:
                result += f"LinkedIn: {contact['linkedin']}\n"
            result += "\n"
        
        # Format other sections
        if "sections" in improved_resume:
            for section in improved_resume["sections"]:
                result += f"## {section['name']}\n"
                result += f"{section['content']}\n\n"
        
        return result

def main():
    """Main function to demonstrate LLM Studio integration with resumes"""
    parser = argparse.ArgumentParser(description="Use LLM Studio and ManageAI Resume API to improve resumes")
    parser.add_argument("--host", default="localhost", help="LLM Studio host")
    parser.add_argument("--port", type=int, default=1234, help="LLM Studio port")
    parser.add_argument("--model", default="qwen-14b", help="Model name in LLM Studio")
    parser.add_argument("--api-url", default="http://localhost:8080", help="ManageAI Resume API URL")
    parser.add_argument("--api-key", help="ManageAI Resume API key")
    parser.add_argument("--use", choices=["direct", "manageai"], default="manageai", 
                        help="Use direct LLM Studio connection or ManageAI API")
    parser.add_argument("--resume", help="Path to resume text file")
    parser.add_argument("--job", help="Path to job description text file")
    parser.add_argument("--action", choices=["improve", "tailor", "ats"], 
                        default="improve", help="Action to perform")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    # Check if resume file is provided
    if not args.resume:
        logger.error("Please provide a resume file with --resume")
        return 1
    
    # Read resume content
    try:
        with open(args.resume, 'r') as f:
            resume_text = f.read()
    except Exception as e:
        logger.error(f"Error reading resume file: {e}")
        return 1
    
    # Read job description if provided
    job_description = None
    if args.job:
        try:
            with open(args.job, 'r') as f:
                job_description = f.read()
        except Exception as e:
            logger.error(f"Error reading job description file: {e}")
            return 1
    
    try:
        # Initialize the appropriate helper based on user choice
        if args.use == "direct":
            logger.info("Using direct connection to LLM Studio...")
            helper = ResumeLLMHelper(
                host=args.host,
                port=args.port,
                model_name=args.model
            )
        else:
            logger.info("Using ManageAI Resume API...")
            helper = ManageAIResumeHelper(
                api_url=args.api_url,
                api_key=args.api_key
            )
        
        # Perform the requested action
        if args.action == "improve":
            logger.info("Getting suggestions to improve the resume...")
            result = helper.improve_resume(resume_text, job_description)
            logger.info("\nImprovement suggestions:")
            print("\n" + result)
            
        elif args.action == "tailor":
            if not job_description:
                logger.error("Job description is required for tailoring")
                return 1
                
            logger.info("Tailoring resume for the job description...")
            result = helper.tailor_resume(resume_text, job_description)
            logger.info("\nTailored resume:")
            print("\n" + result)
            
        elif args.action == "ats":
            logger.info("Checking ATS compatibility...")
            result = helper.get_ats_compatibility(resume_text)
            logger.info("\nATS compatibility analysis:")
            print("\n" + result)
        
        # Save output if requested
        if args.output and result:
            try:
                with open(args.output, 'w') as f:
                    f.write(result)
                logger.info(f"Result saved to {args.output}")
            except Exception as e:
                logger.error(f"Error saving output: {e}")
                
        return 0
            
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
