"""
Resume Section Classifier module.

This module provides functionality to classify different sections of a resume 
based on content, formatting, and machine learning techniques.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SectionClassifier:
    """
    Class for classifying resume sections based on content and formatting.
    
    Provides methods to identify and classify different parts of a resume,
    such as contact information, education, experience, skills, etc.
    """
    
    def __init__(self):
        """Initialize the section classifier with patterns for different sections."""
        # Patterns for different section types
        self.patterns = {
            'contact': [
                r'email|phone|address|contact|linkedin|github'
            ],
            'education': [
                r'education|academic|degree|university|college|school|GPA'
            ],
            'experience': [
                r'experience|employment|work history|professional|career'
            ],
            'skills': [
                r'skills|expertise|proficiencies|competencies|technologies'
            ],
            'projects': [
                r'projects|portfolio|implementations|developments'
            ],
            'certifications': [
                r'certifications|certificates|credentials|licenses'
            ],
            'awards': [
                r'awards|honors|achievements|recognitions'
            ],
            'publications': [
                r'publications|papers|research|articles|journals'
            ],
            'summary': [
                r'summary|profile|objective|about me|professional summary'
            ],
            'languages': [
                r'languages|language proficiency|fluent in'
            ],
            'interests': [
                r'interests|hobbies|activities|passions'
            ],
            'references': [
                r'references|referees|recommendations'
            ],
            'volunteer': [
                r'volunteer|community service|non-profit'
            ]
        }
        
        # Compile patterns for faster matching
        self.compiled_patterns = {}
        for section_type, patterns in self.patterns.items():
            self.compiled_patterns[section_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Additional formatting clues
        self.formatting_clues = {
            'education': [
                'bachelor', 'master', 'ph.d', 'diploma', 'certificate',
                'university of', 'college', 'gpa', 'dean\'s list', 'honors'
            ],
            'experience': [
                'manager', 'developer', 'engineer', 'analyst', 'consultant',
                'intern', 'specialist', 'coordinator', 'responsible for'
            ],
            'skills': [
                'proficient', 'experienced', 'familiar with', 'expert in',
                'knowledge of', 'skilled in', 'mastery of'
            ]
        }
    
    def classify_section(self, section_title, section_content) -> Tuple[str, float]:
        """
        Classify a resume section based on title and content.
        
        Args:
            section_title: The title or heading of the section
            section_content: The text content of the section
            
        Returns:
            Tuple of (section_type, confidence_score)
        """
        # First, try to match by section title
        best_match = self._match_by_title(section_title)
        if best_match[1] > 0.8:  # High confidence threshold
            return best_match
        
        # If title matching isn't confident, try content-based classification
        content_match = self._match_by_content(section_content)
        
        # If content matching is stronger, use it, otherwise stick with title match
        if content_match[1] > best_match[1]:
            return content_match
        
        # If neither method is confident, use a combination
        if best_match[1] < 0.6 and content_match[1] < 0.6:
            combined_score = (best_match[1] + content_match[1]) / 2
            # If they agree on the type, boost the confidence
            if best_match[0] == content_match[0]:
                combined_score = min(0.8, combined_score * 1.5)
                return (best_match[0], combined_score)
            
            # Otherwise, return the stronger match
            return best_match if best_match[1] > content_match[1] else content_match
        
        return best_match
    
    def _match_by_title(self, title) -> Tuple[str, float]:
        """
        Match a section based on its title.
        
        Args:
            title: The section title or heading
            
        Returns:
            Tuple of (section_type, confidence_score)
        """
        title = title.strip().lower()
        best_match = ('unknown', 0.0)
        
        # Check exact title matches first
        for section_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(title):
                    # Direct match in the section title is very reliable
                    return (section_type, 0.9)
        
        # If no exact match, check for partial matches
        for section_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                # Extract the core pattern without regex symbols
                core_pattern = pattern.pattern.replace(r'|', ' ').replace(r'^', '').replace(r'$', '')
                words = core_pattern.split()
                
                # Check each word in the pattern
                for word in words:
                    if len(word) > 3 and word.lower() in title.lower():
                        # Partial match, calculate confidence based on word similarity
                        confidence = 0.7  # Base confidence for partial matches
                        return (section_type, confidence)
        
        return best_match
    
    def _match_by_content(self, content) -> Tuple[str, float]:
        """
        Match a section based on its content.
        
        Args:
            content: The section content text
            
        Returns:
            Tuple of (section_type, confidence_score)
        """
        content = content.strip().lower()
        scores = defaultdict(float)
        
        # Count pattern matches in the content
        for section_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                scores[section_type] += len(matches) * 0.1  # Each match adds 0.1 to score
        
        # Look for formatting clues
        for section_type, clues in self.formatting_clues.items():
            for clue in clues:
                if clue.lower() in content:
                    scores[section_type] += 0.05  # Each clue adds 0.05 to score
        
        # Additional content-based heuristics
        # Education sections often contain years and degrees
        if re.search(r'\b(20\d{2}|19\d{2})\b.*\b(20\d{2}|19\d{2}|present)\b', content) and \
           re.search(r'\b(bachelor|master|phd|diploma|degree|gpa)\b', content, re.IGNORECASE):
            scores['education'] += 0.2
        
        # Experience sections often contain job titles and responsibilities
        if re.search(r'\b(20\d{2}|19\d{2})\b.*\b(20\d{2}|19\d{2}|present)\b', content) and \
           re.search(r'\b(manage|develop|lead|responsible|project|team)\b', content, re.IGNORECASE):
            scores['experience'] += 0.2
        
        # Skills sections often contain lists and technical terms
        if len(re.findall(r'[•\-\*]', content)) > 3 or \
           re.search(r'\b(proficient|experienced|knowledge|skills)\b', content, re.IGNORECASE):
            scores['skills'] += 0.2
        
        # Find the section type with the highest score
        best_section = max(scores.items(), key=lambda x: x[1], default=('unknown', 0.0))
        
        return best_section
    
    def classify_sections_in_document(self, sections):
        """
        Classify all sections in a document.
        
        Args:
            sections: List of section objects with name and content attributes
            
        Returns:
            Dictionary mapping section objects to classification results
        """
        results = {}
        
        for section in sections:
            if hasattr(section, 'name') and hasattr(section, 'content'):
                section_type, confidence = self.classify_section(
                    section.name, section.get_text() if hasattr(section, 'get_text') else section.content
                )
                
                results[section] = {
                    'type': section_type,
                    'confidence': confidence
                }
        
        return results
    
    def analyze_resume_structure(self, sections):
        """
        Analyze the overall structure of a resume.
        
        Args:
            sections: List of section objects with name and content attributes
            
        Returns:
            Dictionary with analysis results
        """
        # Classify sections
        classifications = self.classify_sections_in_document(sections)
        
        # Count section types
        section_types = {}
        for section, result in classifications.items():
            section_type = result['type']
            if section_type not in section_types:
                section_types[section_type] = 0
            section_types[section_type] += 1
        
        # Check for missing important sections
        important_sections = {'contact', 'education', 'experience', 'skills'}
        missing_sections = important_sections - set(section_types.keys())
        
        # Check section order
        section_order = [result['type'] for section, result in sorted(
            classifications.items(),
            key=lambda x: sections.index(x[0])
        )]
        
        # Ideal section order (simplified)
        ideal_order = ['summary', 'experience', 'education', 'skills', 'projects', 
                       'certifications', 'awards', 'publications', 'languages', 
                       'volunteer', 'interests', 'references']
        
        # Calculate order score (how close the order is to ideal)
        order_score = 0.0
        for i, section_type in enumerate(section_order):
            if section_type in ideal_order:
                ideal_pos = ideal_order.index(section_type)
                # Normalized position difference (0 = perfect order, 1 = worst order)
                pos_diff = abs(i - ideal_pos) / max(len(ideal_order), len(section_order))
                order_score += 1.0 - pos_diff
        
        # Normalize order score
        if section_order:
            order_score /= len(section_order)
        
        return {
            'classifications': classifications,
            'section_types': section_types,
            'missing_sections': list(missing_sections),
            'section_order': section_order,
            'order_score': order_score
        }
