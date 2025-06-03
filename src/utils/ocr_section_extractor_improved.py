"""
Improved OCR-based Section Extractor for Resume PDFs

This module provides an enhanced section extraction approach that uses
Tesseract OCR to better extract text from PDFs, with improved handling
of embedded sections and hierarchical content.
"""

import os
import re
import logging
import fitz  # PyMuPDF
from src.utils.simple_section_extractor import SimpleSectionExtractor
from src.utils.pdf_extractor import PDFExtractor
from src.utils.ocr_text_extraction import OCRTextExtractor

logger = logging.getLogger(__name__)

class OCRSectionExtractorImproved(SimpleSectionExtractor):
    """
    Enhanced section extractor that uses OCR for better text extraction from PDFs,
    particularly when section headers are embedded in text. Handles hierarchical
    content better and avoids incorrect section detection.
    """
    
    def __init__(self):
        """Initialize the improved OCR-based section extractor."""
        super().__init__()  # Initialize the parent SimpleSectionExtractor
        self.pdf_extractor = PDFExtractor()  # Initialize PDF extractor for OCR
        self.ocr_extractor = OCRTextExtractor()  # Initialize the specialized OCR text extractor
        self._format_info = None  # Initialize format info to avoid attribute error
        
        # Words that should not be treated as separate sections, even if they look like headers
        self.non_section_words = [
            'RESUME', 'CV', 'CURRICULUM VITAE', 'NAME', 'PAGE', 'EMAIL',
            'PHONE', 'ADDRESS', 'STREET', 'CITY', 'STATE', 'ZIP'
        ]
        
        # Words that likely indicate a job title in experience section (hierarchical content)
        self.job_title_indicators = [
            'MANAGER', 'DIRECTOR', 'ENGINEER', 'SPECIALIST', 'ANALYST', 
            'DEVELOPER', 'ASSISTANT', 'COORDINATOR', 'CONSULTANT',
            'BENEFITS', 'CUSTOMER', 'SERVICE', 'REPRESENTATIVE', 'AGENT',
            'SUPERVISOR', 'LEAD', 'HEAD', 'CHIEF', 'OFFICER'
        ]
    
    def extract_sections(self, pdf_path):
        """
        Extract sections using OCR for better text extraction,
        then apply an enhanced probabilistic approach to identify sections.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            dict: Dictionary of extracted sections
        """
        try:
            # First, extract text using specialized OCR extractor for better section header recognition
            logger.info(f"Extracting text from {pdf_path} using OCR")
            ocr_text = self.ocr_extractor.extract_text(pdf_path)
            
            if not ocr_text or len(ocr_text.strip()) < 100:
                logger.warning("OCR extraction failed or returned minimal text, falling back to regular extraction")
                return super().extract_sections(pdf_path)
            
            # Temporary file path for the OCR text (for debugging)
            tmp_txt_path = f"{os.path.splitext(pdf_path)[0]}_ocr.txt"
            
            # Save the OCR text to a temporary file for debugging
            with open(tmp_txt_path, 'w', encoding='utf-8') as f:
                f.write(ocr_text)
                
            logger.info(f"OCR text saved to {tmp_txt_path}")
            
            # Open the original PDF to extract any available formatting information
            doc = fitz.open(pdf_path)
            self._format_info = self._extract_format_info(doc)
            
            # Split the OCR text into lines
            lines = ocr_text.split('\n')
            
            # Pre-process lines to avoid common OCR issues
            lines = self._preprocess_lines(lines)
            
            # Score each line for being a potential section header
            line_scores = self._score_lines_improved(lines)
            
            # Find section boundaries with improved logic
            section_boundaries = self._find_section_boundaries_improved(lines, line_scores)
            
            # Extract sections with enhanced content organization
            sections = self._extract_sections_from_boundaries_improved(lines, section_boundaries)
            
            # Clean up temporary file
            try:
                os.remove(tmp_txt_path)
            except:
                pass
                
            return sections
            
        except Exception as e:
            logger.error(f"Error in OCR-based section extraction: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to regular section extraction
            logger.info("Falling back to regular section extraction")
            return super().extract_sections(pdf_path)
    
    def _preprocess_lines(self, lines):
        """
        Pre-process OCR-extracted lines to fix common OCR issues.
        
        Args:
            lines: List of text lines
            
        Returns:
            list: Processed lines
        """
        processed_lines = []
        current_section = None
        in_experience_section = False
        
        # First pass - Look for merged lines where a location is merged with the next line
        # (Example: UtahActed as first point of contact...)
        fixed_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                fixed_lines.append(line)
                continue
                
            # Check for merged location and text patterns
            # Common pattern: StateName followed immediately by a verb or action
            # Look for state names or city/state combinations merged with text
            location_merge_pattern = r'([A-Z][a-z]+(?:,\s*[A-Z]{2})?)((?:[A-Z][a-z]+ed|[A-Z][a-z]+ing|[A-Z]ct)\b)'
            match = re.search(location_merge_pattern, line)
            
            if match:
                # Split the merged content
                location = match.group(1)
                action = match.group(2)
                
                # Replace with properly separated text
                new_line = line.replace(match.group(0), f"{location}\n{action}")
                
                # Split into separate lines and add to fixed_lines
                split_lines = new_line.split('\n')
                fixed_lines.extend(split_lines)
            else:
                # Look for other capitalized words merged together without spaces
                # Pattern: CapitalizedWord immediately followed by another CapitalizedWord
                cap_words_pattern = r'([A-Z][a-z]+)([A-Z][a-z]+)'
                match = re.search(cap_words_pattern, line)
                
                if match:
                    # Split the merged capitalized words
                    word1 = match.group(1)
                    word2 = match.group(2)
                    
                    # Check if this is likely a proper segmentation point
                    # (avoid splitting names like "McDonald" or "VanDyke")
                    if not any(compound in match.group(0) for compound in ['Mc', 'Mac', 'Van', 'De', 'La']):
                        # Replace with properly spaced or separated text
                        new_line = line.replace(match.group(0), f"{word1}\n{word2}")
                        split_lines = new_line.split('\n')
                        fixed_lines.extend(split_lines)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
        
        # Second pass - Apply other preprocessing
        for i, line in enumerate(fixed_lines):
            line = line.strip()
            
            # Skip empty lines, but preserve them for formatting
            if not line:
                processed_lines.append(line)
                continue
            
            # Check if this line might be a section header
            if line.upper() == line and len(line) <= 30:
                line_upper = line.upper()
                
                # Detect if we're entering an Experience section
                if any(keyword in line_upper for keyword in ['EXPERIENCE', 'EMPLOYMENT', 'WORK HISTORY']):
                    in_experience_section = True
                # Detect if we're leaving an Experience section
                elif any(keyword in line_upper for keyword in ['EDUCATION', 'SKILLS', 'PROJECTS']):
                    in_experience_section = False
                
                # Check if it's a non-section word like "RESUME"
                if any(word in line_upper for word in self.non_section_words):
                    # Don't treat as a section header
                    processed_lines.append(line)
                    continue
            
            # Special handling for job titles in experience sections
            if in_experience_section and i > 0:
                # Check if this could be a job title (often followed by company or dates)
                is_likely_job_title = (
                    any(word in line.upper() for word in self.job_title_indicators) or
                    re.search(r'(?:\b(?:at|for)\s+[A-Z][a-zA-Z\s,\.]+)', line) or  # "at Company Name"
                    re.search(r'(?:[A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+,\s*[A-Z]{2})', line)  # "City Name, ST"
                )
                
                # Fix lines that look like a date range
                date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b.*?(?:Present|Current|\d{4})'
                has_date = re.search(date_pattern, line, re.IGNORECASE)
                
                if is_likely_job_title or has_date:
                    # Ensure job titles and dates are properly separated 
                    # but not treated as new sections
                    if fixed_lines[i-1].strip():  # If previous line is not empty
                        processed_lines.append("")  # Add some spacing
            
            processed_lines.append(line)
        
        return processed_lines
    
    def _score_lines_improved(self, lines):
        """
        Improved scoring function for identifying potential section headers.
        
        Args:
            lines: List of text lines
            
        Returns:
            list: Scores for each line
        """
        scores = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            score = 0.0
            
            if not line:  # Skip empty lines
                scores.append(0.0)
                continue
            
            # Check if this is likely a non-section word (like "RESUME")
            if any(word == line.upper() for word in self.non_section_words):
                scores.append(0.0)  # Zero score to ensure it's not treated as a section
                continue
            
            # Feature 1: Contains keywords from section types (highest weight)
            section_type_match = False
            for section_type, keywords in self.section_types.items():
                if any(keyword.lower() == line.lower() for keyword in keywords):
                    # Exact match gets highest score
                    section_type_match = True
                    score += 5.0  # Higher weight for exact match in OCR text
                    break
                elif any(re.search(rf'\b{re.escape(keyword.lower())}\b', line.lower()) for keyword in keywords):
                    # Word boundary match (surrounded by spaces/punctuation)
                    section_type_match = True
                    score += 4.0  # Higher weight for word boundary match in OCR text
                    break
                elif any(keyword.lower() in line.lower() for keyword in keywords):
                    # Partial match (substring)
                    section_type_match = True
                    score += 2.5
                    break
            
            # Feature 2: Formatting suggests a header (all caps, short, etc.)
            if line == line.upper() and len(line) > 3 and len(line.split()) <= 4:
                score += 3.0  # Increased weight for ALL CAPS headers in OCR text
            elif line.title() == line and len(line) > 3 and len(line.split()) <= 4:
                # Title Case Headers Are Common
                score += 2.0
            
            # Feature 3: Line ends with colon (common for headers)
            if line.endswith(':'):
                score += 1.5
            
            # Feature 4: Short line length (headers tend to be short)
            if len(line) < 20:
                score += 1.5
            elif len(line) < 30:
                score += 0.75
            
            # Feature 5: Position in document (headers often at top or after space)
            if i == 0 or (i > 0 and not lines[i-1].strip()):
                score += 1.0
                
            # Feature 6: Preceding line is empty and next line is also empty - strong header indicator
            if i > 0 and i < len(lines) - 1 and not lines[i-1].strip() and not lines[i+1].strip():
                score += 2.0
            
            # Feature 7: Next line suggests content (e.g., bullet points or date ranges)
            if i < len(lines) - 1:
                next_line = lines[i+1].strip()
                if next_line.startswith('•') or next_line.startswith('-') or next_line.startswith('*'):
                    score += 1.5  # Bullet points are strong indicators of content after a header
                    
                # Check for date ranges commonly found in experience/education sections
                date_pattern = r'\d{4}\s*(-|to)\s*\d{4}|\d{4}\s*(-|to)\s*(Present|Current)'
                if re.search(date_pattern, next_line, re.IGNORECASE):
                    score += 1.5  # Date ranges are strong indicators for sections like Experience
            
            # Reduce score if the line looks like part of content rather than a header
            if re.search(r'^\d+\s*\.', line) or re.search(r'^\(\d+\)', line):  # Numbered items
                score -= 2.0
                
            # Reduce score for lines that are likely contact information
            if re.search(r'@|http|www|\+\d|\(\d{3}\)|\d{3}-\d{3}-\d{4}', line):
                score -= 2.0
            
            # Strongly reduce score for job titles within experience sections
            # Only if they appear to be part of a job description (context is important)
            if i > 0 and i < len(lines) - 1:
                prev_context = lines[max(0, i-3):i]
                next_context = lines[i+1:min(len(lines), i+4)]
                
                # If we see content patterns typical of a job description (dates, bullets, responsibilities)
                has_date_before = any(re.search(r'\b\d{4}\b', line) for line in prev_context)
                has_bullet_after = any(line.strip().startswith('•') for line in next_context)
                
                # Check for job title indicators
                is_job_title = any(title in line.upper() for title in self.job_title_indicators)
                
                # If the context suggests this is a job title within a section, reduce its score
                if (has_date_before or has_bullet_after) and is_job_title:
                    score -= 3.0  # Strongly discourage treating job titles as section headers
                
            scores.append(score)
        
        return scores
    
    def _find_section_boundaries_improved(self, lines, scores):
        """
        Improved method to identify section boundaries using the scores with better
        handling of hierarchical content like job titles within experience sections.
        
        Args:
            lines: List of text lines
            scores: Line scores
            
        Returns:
            list: Indices of section boundaries
        """
        boundaries = []
        threshold = 3.0  # Higher minimum score to consider as potential header
        window_size = 5   # Look at local context to find peaks
        
        # Make sure the first line is always a boundary (contact section)
        if len(lines) > 0:
            boundaries.append(0)
        
        # First pass: find high-scoring local maxima (peaks)
        for i in range(len(scores)):
            # Skip lines with low scores
            if scores[i] < threshold:
                continue
                
            # Check if this is a local maximum within window_size
            start_idx = max(0, i - window_size)
            end_idx = min(len(scores), i + window_size + 1)
            local_scores = scores[start_idx:end_idx]
            
            if scores[i] == max(local_scores):
                # This is a local maximum - likely a section header
                
                # Only add if not too close to an existing boundary
                # This helps avoid treating job titles as section headers
                if not any(abs(b - i) < 3 for b in boundaries):
                    boundaries.append(i)
        
        # If we have too few sections, look for other clues
        if len(boundaries) <= 2:
            # Look for content pattern changes - focus on major sections
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                # Check for standard resume section headers
                major_sections = ['EXPERIENCE', 'EDUCATION', 'SKILLS', 'SUMMARY', 'PROJECTS']
                if any(section in line.upper() for section in major_sections):
                    # Only add if not too close to an existing boundary
                    if not any(abs(b - i) < 3 for b in boundaries):
                        boundaries.append(i)
        
        # Sort boundaries
        boundaries.sort()
        
        # Post-process boundaries to handle missed hierarchical content
        processed_boundaries = self._post_process_boundaries(lines, boundaries)
        
        return processed_boundaries
    
    def _post_process_boundaries(self, lines, boundaries):
        """
        Post-process section boundaries to fix issues with hierarchical content
        and other common OCR section detection problems.
        
        Args:
            lines: List of text lines
            boundaries: Initial section boundaries
            
        Returns:
            list: Improved section boundaries
        """
        # No boundaries or only one boundary (the start) - nothing to post-process
        if len(boundaries) <= 1:
            return boundaries
            
        result = [boundaries[0]]  # Always keep the first boundary
        
        for i in range(1, len(boundaries)):
            curr_boundary = boundaries[i]
            prev_boundary = boundaries[i-1]
            
            # Get the header line for this potential section
            if curr_boundary < len(lines):
                header_line = lines[curr_boundary].strip().upper()
            else:
                continue  # Skip invalid boundary
                
            # Skip "RESUME" header - it shouldn't be a section
            if header_line == "RESUME":
                continue
                
            # Check if this looks like a job title that should be part of Experience
            # Get some context from surrounding lines
            context_start = max(0, curr_boundary - 3)
            context_end = min(len(lines), curr_boundary + 4)
            context = " ".join([lines[j].strip() for j in range(context_start, context_end)])
            
            # Check if this is within an experience section
            in_experience = False
            for j in range(len(result)):
                if j < len(result) and result[j] < curr_boundary and result[j] < len(lines):
                    section_header = lines[result[j]].strip().upper()
                    if any(keyword in section_header for keyword in ['EXPERIENCE', 'EMPLOYMENT', 'WORK']):
                        in_experience = True
                        break
                        
            # Check if header has job title indicators
            is_job_title = False
            if any(title in header_line for title in self.job_title_indicators):
                is_job_title = True
                
            # Check for date patterns that often appear with job titles
            has_date_pattern = re.search(r'\d{4}.*?(?:present|current|\d{4})', context, re.IGNORECASE)
            
            # Skip job titles within experience sections
            if in_experience and is_job_title and has_date_pattern:
                continue
                
            # Skip lines that don't look like real section headers
            if len(header_line) > 30 and not any(keyword in header_line for keyword in self.section_types.keys()):
                continue
                
            # This looks like a valid section boundary
            result.append(curr_boundary)
        
        return result
    
    def _extract_sections_from_boundaries_improved(self, lines, boundaries):
        """
        Extract and classify sections with improved handling of content organization.
        
        Args:
            lines: List of text lines
            boundaries: Section boundaries
            
        Returns:
            dict: Dictionary of extracted sections
        """
        sections = {}
        
        # Map of common resume section headers to their standard types
        standard_section_types = {
            'SUMMARY': 'summary',
            'PROFILE': 'summary',
            'PROFESSIONAL': 'summary',  # Added "PROFESSIONAL" as a summary type
            'OBJECTIVE': 'summary',
            'EXPERIENCE': 'experience',
            'EMPLOYMENT': 'experience',
            'WORK HISTORY': 'experience',
            'EDUCATION': 'education',
            'ACADEMIC': 'education',
            'SKILLS': 'skills',
            'TECHNICAL SKILLS': 'skills',
            'COMPETENCIES': 'skills',
            'PROJECTS': 'projects',
            'ACCOMPLISHMENTS': 'achievements',
            'ACHIEVEMENTS': 'achievements',
            'CERTIFICATIONS': 'certifications',
            'LANGUAGES': 'languages',
            'INTERESTS': 'interests',
            'VOLUNTEER': 'volunteer',
            'REFERENCES': 'references'
        }
        
        # For each boundary pair, extract and classify the section
        for i in range(len(boundaries)):
            start = boundaries[i]
            end = boundaries[i+1] if i < len(boundaries) - 1 else len(lines)
            
            # Get section content
            section_lines = lines[start:end]
            if not section_lines:
                continue
            
            # Get the header line
            header_line = section_lines[0].strip()
            
            # Special handling for the first section - usually contact info
            if i == 0:
                # For the first section, keep the first line as part of the content
                # since contact sections often don't have an explicit header
                content = "\n".join(section_lines).strip()
                section_type = "contact"
                confidence = 0.9
            else:
                # For other sections, first line is likely header, rest is content
                content = "\n".join(section_lines[1:]).strip()
                
                # Try to classify based on the header
                header_upper = header_line.upper()
                section_type = None
                
                # Check for standard section headers
                for key, val in standard_section_types.items():
                    if key in header_upper or header_upper in key:
                        section_type = val
                        confidence = 0.9
                        break
                
                # If no match, use more sophisticated classification
                if not section_type:
                    section_type, confidence = self._classify_section(header_line, content, i == 0)
            
            # Normalize the header display name
            display_name = header_line
            for standard_header, type_name in standard_section_types.items():
                if standard_header in header_line.upper():
                    display_name = standard_header.title()
                    break
            
            # Create section key
            if section_type != "unknown":
                section_key = section_type.upper()
            else:
                section_key = header_line[:20] if header_line else f"Section {i+1}"
            
            # Make sure we don't overwrite existing sections
            suffix = ""
            while section_key + suffix in sections:
                suffix = "_" + str(len(suffix) + 1) if suffix else "_1"
            
            section_key = section_key + suffix
            
            # Create section entry
            sections[section_key] = {
                'type': section_type,
                'confidence': confidence,
                'content': content,
                'original_header': header_line,
                'display_name': display_name
            }
        
        return sections
