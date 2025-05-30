"""
Job Analyzer module for comparing resumes against job descriptions.
"""

import re
from collections import Counter

class JobAnalyzer:
    """Class for analyzing job descriptions and comparing them to resumes."""
    
    def __init__(self):
        self.skill_patterns = [
            r'Python', r'Java', r'JavaScript', r'TypeScript', r'React', r'Vue', r'Angular',
            r'Node\.js', r'Express', r'Django', r'Flask', r'Spring', r'SQL', r'NoSQL',
            r'MongoDB', r'PostgreSQL', r'MySQL', r'Oracle', r'AWS', r'Azure', r'GCP',
            r'Docker', r'Kubernetes', r'CI/CD', r'DevOps', r'Agile', r'Scrum',
            r'Machine Learning', r'AI', r'Data Science', r'Big Data', r'Hadoop', r'Spark',
            r'ETL', r'Data Warehouse', r'Business Intelligence', r'Power BI', r'Tableau',
            r'Product Management', r'Project Management', r'Leadership', r'Team Management',
            r'Strategic Planning', r'Marketing', r'SEO', r'SEM', r'Content Marketing',
            r'Social Media', r'Digital Marketing', r'Sales', r'Customer Success',
            r'Customer Service', r'Technical Support', r'UX', r'UI', r'User Research',
            r'Wireframing', r'Prototyping', r'Figma', r'Sketch', r'Adobe XD', r'Photoshop',
            r'Illustrator', r'InDesign', r'After Effects', r'Video Editing', r'Animation',
            r'3D Modeling', r'Game Development', r'Unity', r'Unreal Engine',
            r'C\+\+', r'C#', r'Swift', r'Objective-C', r'Kotlin', r'Go', r'Rust',
            r'PHP', r'Ruby', r'Rails', r'Perl', r'Scala', r'Haskell', r'Clojure',
            r'Linux', r'Unix', r'Bash', r'Shell Scripting', r'Networking', r'Security',
            r'Cybersecurity', r'Penetration Testing', r'Ethical Hacking', r'Cryptography',
            r'Blockchain', r'Smart Contracts', r'Cryptocurrency', r'Solidity',
            r'AR', r'VR', r'IoT', r'Embedded Systems', r'Robotics', r'Automation',
            r'Communication', r'Presentation', r'Public Speaking', r'Writing',
            r'Technical Writing', r'Documentation', r'Research', r'Analysis',
            r'Problem Solving', r'Critical Thinking', r'Creativity', r'Innovation'
        ]
        self.stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
            'when', 'where', 'how', 'who', 'which', 'this', 'that', 'these', 'those',
            'then', 'than', 'such', 'both', 'through', 'about', 'for', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
            'do', 'does', 'did', 'doing', 'at', 'by', 'with', 'from', 'to', 'in',
            'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
            'here', 'there', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now'
        }
    
    def analyze(self, job_description, resume_content):
        """
        Analyze a job description against a resume and provide recommendations.
        
        Args:
            job_description: String containing the job description
            resume_content: ResumeContent object containing the resume
            
        Returns:
            (keywords, suggestions) tuple containing:
                - list of relevant keywords found in the job description
                - list of suggestions for improving the resume
        """
        # Extract relevant keywords from job description
        job_keywords = self._extract_keywords(job_description)
        
        # Convert resume content to string for analysis
        resume_text = str(resume_content)
        
        # Check which keywords from job are present in resume
        missing_keywords = []
        present_keywords = []
        
        for keyword in job_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', resume_text, re.IGNORECASE):
                present_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        # Generate suggestions based on analysis
        suggestions = self._generate_suggestions(job_keywords, present_keywords, missing_keywords, job_description, resume_text)
        
        return (job_keywords, suggestions)
    
    def _extract_keywords(self, text):
        """Extract important keywords from text."""
        # Find all skill matches
        skill_matches = []
        for pattern in self.skill_patterns:
            matches = re.findall(r'\b' + pattern + r'\b', text, re.IGNORECASE)
            skill_matches.extend([match for match in matches])
        
        # Count word frequency in text (excluding stop words)
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#-.]+\b', text.lower())
        word_counts = Counter([word for word in words if word not in self.stop_words and len(word) > 2])
        
        # Get most frequent words (likely to be important)
        common_words = [word for word, count in word_counts.most_common(20) if count > 1]
        
        # Combine skill matches with common words for final keywords list
        keywords = list(set([s.strip() for s in skill_matches]))
        keywords.extend([word for word in common_words if word not in [k.lower() for k in keywords]])
        
        return keywords
    
    def _generate_suggestions(self, job_keywords, present_keywords, missing_keywords, job_description, resume_text):
        """Generate suggestions for improving the resume."""
        suggestions = []
        
        # Suggestion for missing keywords
        if missing_keywords:
            if len(missing_keywords) > 5:
                # If many keywords are missing, suggest focusing on top ones
                top_missing = missing_keywords[:5]
                suggestions.append(f"Consider adding these key skills that appear in the job description: {', '.join(top_missing)}.")
                suggestions.append(f"There are {len(missing_keywords) - 5} more keywords from the job description that aren't in your resume.")
            else:
                suggestions.append(f"Consider adding these keywords that appear in the job description: {', '.join(missing_keywords)}.")
        
        # Suggestion for experience match
        exp_match = re.search(r'(\d+)\+?\s*(?:years|yrs)(?:\s+of)?\s+experience', job_description, re.IGNORECASE)
        if exp_match:
            years_required = int(exp_match.group(1))
            suggestions.append(f"The job requests {years_required}+ years of experience. Make sure your work history clearly demonstrates this experience level.")
        
        # Suggestion for education match
        edu_patterns = [
            r'bachelor(?:\'s)?\s+degree', r'master(?:\'s)?\s+degree', 
            r'phd', r'doctorate', r'mba'
        ]
        
        for pattern in edu_patterns:
            if re.search(pattern, job_description, re.IGNORECASE) and not re.search(pattern, resume_text, re.IGNORECASE):
                match = re.search(pattern, job_description, re.IGNORECASE).group(0)
                suggestions.append(f"The job mentions '{match}' as a requirement. Ensure your education section clearly lists your relevant degrees.")
        
        # Suggestion for resume length
        word_count = len(resume_text.split())
        if word_count < 300:
            suggestions.append("Your resume appears to be quite brief. Consider adding more details about your experiences and achievements.")
        elif word_count > 700:
            suggestions.append("Your resume may be too verbose. Consider condensing it to focus on the most relevant experiences for this position.")
        
        # General suggestions if we don't have many specific ones
        if len(suggestions) < 2:
            suggestions.append("Tailor your resume to use similar language and terminology as the job description.")
            suggestions.append("Quantify your achievements with specific metrics and results when possible.")
        
        return suggestions