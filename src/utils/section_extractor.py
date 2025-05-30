"""
Section Extractor for Resume PDFs

A specialized module for extracting sections from resume PDFs that have
challenging formatting, including handling special characters and embedded section headers.
"""

import re
import fitz  # PyMuPDF
import logging

# Set up logger
logger = logging.getLogger(__name__)

class SectionExtractor:
    """A specialized extractor for resume sections that works with challenging PDF formats."""
    
    def __init__(self):
        # Define standard section types and their variations
        self.section_types = {
            "summary": ["professional summary", "summary", "profile", "about me", "objective", 
                      "career objective", "professional profile"],
            "experience": ["work experience", "professional experience", "employment", 
                         "work history", "experience", "professional background", 
                         "career history", "job history"],
            "education": ["education", "academic background", "academic", "qualifications", 
                        "degrees", "schooling", "educational background", 
                        "academic qualifications"],
            "skills": ["skills", "technical skills", "expertise", "competencies", 
                     "proficiencies", "abilities", "core competencies", 
                     "professional skills", "skill set", "technical expertise"],
            "projects": ["projects", "personal projects", "project experience", 
                       "portfolio", "projects accomplished", "professional projects"],
            "certifications": ["certifications", "certificates", "professional certifications", 
                             "credentials", "licenses"],
            "languages": ["languages", "language proficiency", "language skills", 
                        "fluency", "foreign languages", "spoken languages"],
            "achievements": ["achievements", "accomplishments", "awards", "recognitions", 
                           "honors", "accolades"],
            "contact": ["contact", "personal information", "contact details", 
                       "contact information", "personal details"]
        }
    
    def extract_sections(self, pdf_path):
        """
        Extract sections from a PDF file with special handling for challenging formats.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary of sections with their content
        """
        try:
            # Open the document
            doc = fitz.open(pdf_path)
            
            # Extract full text
            full_text = ""
            for page in doc:
                full_text += page.get_text("text") + "\n"
            
            # First, try to find sections using various techniques
            sections = {}
            
            # 1. Try standard section pattern recognition
            sections = self._find_sections_by_patterns(full_text)
            if sections:
                logger.info(f"Found {len(sections)} sections using pattern matching")
            else:
                logger.info("No sections found using standard patterns")
            
            # 2. If no or few sections found, try format-based detection
            if len(sections) <= 1:
                format_sections = self._find_sections_by_formatting(doc)
                if format_sections:
                    logger.info(f"Found {len(format_sections)} sections using format detection")
                    sections = format_sections
            
            # 3. If still no luck, try contextual detection
            if len(sections) <= 1:
                context_sections = self._find_sections_by_context(full_text)
                if context_sections:
                    logger.info(f"Found {len(context_sections)} sections using contextual detection")
                    sections = context_sections
            
            # 4. Last resort: create default sections from the text
            if len(sections) <= 1:
                sections = self._create_default_sections(full_text)
                logger.info("Created default sections as fallback")
            
            # 5. Post-processing step: If we detected a large section (like Summary) that likely contains
            # subsections, try to split it into logical parts based on keywords
            if any(len(section['content'].split()) > 150 for section in sections.values()):
                subsections = self._extract_subsections_from_large_sections(sections)
                if len(subsections) > len(sections):
                    logger.info(f"Split large sections into {len(subsections)} subsections")
                    return subsections
            
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting sections: {e}")
            return {"error": str(e)}
    
    def _normalize_text(self, text):
        """Normalize text by removing special characters, lowercasing, etc."""
        # Remove (cid:XXX) patterns
        text = re.sub(r'\(cid:[0-9]+\)', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        # Convert to lowercase
        return text.lower()
    
    def _identify_section_type(self, header_text):
        """Identify the section type from header text."""
        normalized = self._normalize_text(header_text)
        
        for section_type, variations in self.section_types.items():
            # Check exact match
            if normalized in variations:
                return section_type, 1.0
            
            # Check if it contains a variation
            for variation in variations:
                if variation in normalized:
                    return section_type, 0.9
                    
            # Check if any words match (for multi-word sections)
            words = normalized.split()
            for variation in variations:
                variation_words = variation.split()
                for word in words:
                    if len(word) > 3 and word in variation_words:
                        return section_type, 0.7
        
        # Return unknown if no match
        return "unknown", 0.0
    
    def _find_sections_by_patterns(self, full_text):
        """Find sections using regex patterns."""
        # Enhanced section header patterns with flexible matching
        section_patterns = [
            # Format: (regex pattern, section_type)
            (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(?:EDUCATION|EDUCATIONAL|ACADEMIC|QUALIFICATIONS|DEGREES?|EDUCATIONAL\s+BACKGROUND|ACADEMIC\s+HISTORY)(?:\s|:|$|\n|\(cid:[0-9]+\))', "education"),
            (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(?:WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT|WORK\s*HISTORY|EXPERIENCE|PROFESSIONAL\s+BACKGROUND|CAREER\s+HISTORY|JOB\s+HISTORY)(?:\s|:|$|\n|\(cid:[0-9]+\))', "experience"),
            (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(?:SKILLS|TECHNICAL\s+SKILLS|PROFICIENCIES|EXPERTISE|CORE\s+COMPETENCIES|KEY\s+SKILLS|PROFESSIONAL\s+SKILLS|SKILL\s+SET)(?:\s|:|$|\n|\(cid:[0-9]+\))', "skills"),
            (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(?:PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE|CAREER\s+OBJECTIVE|PROFESSIONAL\s+PROFILE|ABOUT\s+ME|CAREER\s+SUMMARY)(?:\s|:|$|\n|\(cid:[0-9]+\))', "summary"),
        ]
        
        # Find all matches
        matches = []
        for pattern, section_type in section_patterns:
            for match in re.finditer(pattern, full_text):
                header_text = match.group().strip()
                matches.append((match.start(), header_text, section_type))
                logger.debug(f"Found section '{header_text}' of type '{section_type}' at position {match.start()}")
        
        # Sort by position in text
        matches.sort(key=lambda x: x[0])
        
        # Create sections based on matches
        sections = {}
        if matches:
            for i, (start_pos, header_text, section_type) in enumerate(matches):
                # Get section content (text between this header and next, or end)
                if i < len(matches) - 1:
                    content = full_text[start_pos + len(header_text):matches[i+1][0]]
                else:
                    content = full_text[start_pos + len(header_text):]
                
                # Clean up the content
                content = content.strip()
                
                # Clean up header
                clean_header = re.sub(r'\(cid:[0-9]+\)', '', header_text).strip()
                
                # Store the section
                sections[clean_header if clean_header else section_type] = {
                    'type': section_type,
                    'confidence': 0.9,  # High confidence for pattern-based detection
                    'content': content
                }
        
        return sections
    
    def _find_sections_by_formatting(self, doc):
        """Find sections based on text formatting clues."""
        sections = {}
        potential_headers = []
        
        # Look for potential headers based on formatting
        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        
                        # Get formatting information
                        font_size = span["size"]
                        font_name = span["font"]
                        is_bold = "bold" in font_name.lower() or bool(span.get("flags", 0) & 2**0)
                        is_all_caps = text.upper() == text and len(text) > 1
                        
                        # Score this text as potential header
                        header_score = 0
                        
                        if font_size > 12:
                            header_score += 3
                        elif font_size > 10:
                            header_score += 1
                            
                        if is_bold:
                            header_score += 2
                        if is_all_caps:
                            header_score += 2
                            
                        if text.endswith(':'):
                            header_score += 1
                            
                        # Check if it contains known section names
                        normalized = self._normalize_text(text)
                        for section_type, variations in self.section_types.items():
                            for variation in variations:
                                if variation in normalized:
                                    header_score += 3
                                    break
                        
                        # If good score, add to potential headers
                        if header_score >= 4:
                            # Also get position info for sorting
                            bbox = line["bbox"]  # (x0, y0, x1, y1)
                            potential_headers.append({
                                'text': text,
                                'score': header_score,
                                'position': (page_num, bbox[1])  # page number and y-position
                            })
        
        # Sort by position in document
        potential_headers.sort(key=lambda x: (x['position'][0], x['position'][1]))
        
        # Create sections from potential headers
        if potential_headers:
            # Extract full text to split by headers
            full_text = ""
            for page in doc:
                full_text += page.get_text("text") + "\n"
            
            for i, header in enumerate(potential_headers):
                header_text = header['text']
                section_type, confidence = self._identify_section_type(header_text)
                
                # Find the position of this header in the text
                # Need to handle special characters properly
                normalized_header = re.sub(r'\s+', ' ', header_text).strip()
                pattern = re.escape(normalized_header)
                matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
                
                if matches:
                    start_pos = matches[0].start()
                    
                    # Get section content
                    if i < len(potential_headers) - 1:
                        next_header = potential_headers[i+1]['text']
                        next_pattern = re.escape(re.sub(r'\s+', ' ', next_header).strip())
                        next_matches = list(re.finditer(next_pattern, full_text, re.IGNORECASE))
                        
                        if next_matches:
                            content = full_text[start_pos + len(normalized_header):next_matches[0].start()]
                        else:
                            content = full_text[start_pos + len(normalized_header):]
                    else:
                        content = full_text[start_pos + len(normalized_header):]
                    
                    # Clean up header and content
                    clean_header = re.sub(r'\(cid:[0-9]+\)', '', header_text).strip()
                    content = content.strip()
                    
                    # Store the section
                    sections[clean_header if clean_header else section_type] = {
                        'type': section_type,
                        'confidence': confidence * (header['score'] / 10.0),  # Adjust confidence by header score
                        'content': content
                    }
        
        return sections
    
    def _find_sections_by_context(self, full_text):
        """Find sections by analyzing the context and content patterns."""
        sections = {}
        lines = full_text.split('\n')
        
        # Look for potential section breaks based on contextual clues
        potential_sections = []
        
        # First check for keywords in the text that clearly indicate sections
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Search for common section headers that might be embedded in text
            # This helps with resumes that have section headers directly in paragraphs
            section_indicators = {
                "SKILLS": r'\b(?:SKILLS|TECHNICAL SKILLS|SKILL SET)\b',
                "EXPERIENCE": r'\b(?:EXPERIENCE|EMPLOYMENT|WORK HISTORY|PROFESSIONAL EXPERIENCE)\b',
                "EDUCATION": r'\b(?:EDUCATION|ACADEMIC|QUALIFICATIONS|DEGREE)\b',
                "SUMMARY": r'\b(?:SUMMARY|PROFILE|OBJECTIVE|CAREER SUMMARY)\b',
                "CERTIFICATIONS": r'\b(?:CERTIFICATIONS?|CERTIFICATES|CREDENTIALS)\b'
            }
            
            for section_name, pattern in section_indicators.items():
                if re.search(pattern, line, re.IGNORECASE):
                    # Found a section header embedded in text
                    header_type = section_name.lower()
                    
                    # Check if this is a standalone header or embedded in text
                    if line == line.upper() and len(line.split()) <= 3:
                        # It's likely a standalone header (higher confidence)
                        confidence = 0.9
                    else:
                        # Embedded in text (lower confidence)
                        confidence = 0.6
                        
                    potential_sections.append((i, section_name, header_type, confidence))
                    break
            
            # Check for contextual clues that might indicate a section header
            is_potential_header = False
            header_type = "unknown"
            confidence = 0.0
            
            # Check if this line is all uppercase (common for headers)
            if line == line.upper() and len(line) > 3 and len(line.split()) <= 3:
                is_potential_header = True
                
                # Try to classify it
                header_type, confidence = self._identify_section_type(line)
                
                # If it's a known type, higher confidence
                if header_type != "unknown":
                    confidence = max(confidence, 0.7)
                else:
                    # Look for other contextual clues
                    if i < len(lines) - 1:
                        next_line = lines[i+1].strip()
                        
                        # If next line has specific formatting like dates, probably experience section
                        if re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)\s+\d{4}\s*-\s*(?:Present|Current|\d{4})', next_line):
                            header_type = "experience"
                            confidence = 0.8
                            
                        # If next line has education-related terms, probably education section
                        elif re.search(r'(?:Bachelor|Master|PhD|B\.S\.|M\.S\.|M\.A\.|B\.A\.|Degree|University|College)', next_line):
                            header_type = "education"
                            confidence = 0.8
            
            # Check if it's a short line followed by bullet points
            elif len(line) < 20 and i < len(lines) - 2:
                next_line = lines[i+1].strip()
                if next_line.startswith('•') or next_line.startswith('-') or next_line.startswith('*'):
                    is_potential_header = True
                    header_type, confidence = self._identify_section_type(line)
                    if header_type == "unknown":
                        # Likely a skills section if it has bullet points
                        header_type = "skills"
                        confidence = 0.6
            
            if is_potential_header:
                potential_sections.append((i, line, header_type, confidence))
        
        # Create sections from the potential headers
        if potential_sections:
            for i, (line_index, header_text, section_type, confidence) in enumerate(potential_sections):
                # Get section content
                if i < len(potential_sections) - 1:
                    next_section_line = potential_sections[i+1][0]
                    content = "\n".join(lines[line_index+1:next_section_line])
                else:
                    content = "\n".join(lines[line_index+1:])
                
                # Clean up header and content
                clean_header = re.sub(r'\(cid:[0-9]+\)', '', header_text).strip()
                content = content.strip()
                
                # Store the section
                sections[clean_header if clean_header else section_type] = {
                    'type': section_type,
                    'confidence': confidence,
                    'content': content
                }
        
        return sections
    
    def _create_default_sections(self, full_text):
        """Create default sections from text as a last resort."""
        sections = {}
        
        # Split text roughly into thirds - a simple heuristic approach
        lines = full_text.split('\n')
        total_lines = len([l for l in lines if l.strip()])
        third = max(5, total_lines // 3)
        
        # First third is usually contact and summary
        summary_content = "\n".join(lines[:third]).strip()
        if summary_content:
            sections["SUMMARY"] = {
                'type': "summary",
                'confidence': 0.4,
                'content': summary_content
            }
        
        # Second third often has skills and experience
        experience_content = "\n".join(lines[third:2*third]).strip()
        if experience_content:
            sections["EXPERIENCE"] = {
                'type': "experience",
                'confidence': 0.4,
                'content': experience_content
            }
        
        # Last third usually has education and other info
        education_content = "\n".join(lines[2*third:]).strip()
        if education_content:
            sections["EDUCATION"] = {
                'type': "education",
                'confidence': 0.4,
                'content': education_content
            }
        
        # If we have one large section, try to split it into subsections
        # This helps with resumes that have merged all content into one block
        if len(sections) == 1 and any(len(section['content'].split()) > 150 for section in sections.values()):
            logger.info(f"Found one large section with {sum(len(section['content'].split()) for section in sections.values())} words, attempting to split into subsections")
            
            # Get the content of the large section
            large_section_name = list(sections.keys())[0]
            large_section_content = sections[large_section_name]['content']
            
            # Split into potential subsections using regex patterns
            subsections = {}
            
            # Common section headers within content
            section_patterns = [
                (r'(?i)(?:^|\n|\s)(EDUCATION|ACADEMIC|QUALIFICATIONS|DEGREES?)(?:\s|:|\n)', "EDUCATION"),
                (r'(?i)(?:^|\n|\s)(WORK\s+EXPERIENCE|EMPLOYMENT|WORK\s*HISTORY|EXPERIENCE|PROFESSIONAL\s+BACKGROUND)(?:\s|:|\n)', "EXPERIENCE"),
                (r'(?i)(?:^|\n|\s)(SKILLS|TECHNICAL\s+SKILLS|PROFICIENCIES|EXPERTISE|CORE\s+COMPETENCIES)(?:\s|:|\n)', "SKILLS"),
                (r'(?i)(?:^|\n|\s)(PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE|CAREER\s+OBJECTIVE)(?:\s|:|\n)', "SUMMARY"),
                (r'(?i)(?:^|\n|\s)(CERTIFICATIONS?|CERTIFICATES|CREDENTIALS|LICENSES)(?:\s|:|\n)', "CERTIFICATIONS"),
                (r'(?i)(?:^|\n|\s)(PROJECTS|PORTFOLIO|PERSONAL\s+PROJECTS|PROFESSIONAL\s+PROJECTS)(?:\s|:|\n)', "PROJECTS")
            ]
            
            # Find all matches within the large section
            matches = []
            for pattern, section_name in section_patterns:
                for match in re.finditer(pattern, large_section_content):
                    # Get the matched text and clean it up
                    header_text = match.group(1).strip()
                    matches.append((match.start(), header_text, section_name))
            
            # Sort by position in text
            matches.sort(key=lambda x: x[0])
            
            # Create subsections
            if matches:
                logger.info(f"Found {len(matches)} subsection matches within large section")
                for i, (start_pos, header_text, section_type) in enumerate(matches):
                    # Get section content (text between this header and next, or end)
                    if i < len(matches) - 1:
                        content = large_section_content[start_pos + len(header_text):matches[i+1][0]]
                    else:
                        content = large_section_content[start_pos + len(header_text):]
                    
                    # Clean up the content
                    content = content.strip()
                    
                    # Add the subsection if it has content
                    if content:
                        subsections[section_type] = {
                            'type': section_type.lower(),
                            'confidence': 0.7,  # Good confidence for subsections
                            'content': content
                        }
                
                # If we found subsections, replace the large section with these
                if len(subsections) > 1:
                    logger.info(f"Replacing large section with {len(subsections)} subsections")
                    return subsections
        
        return sections
    def _extract_subsections_from_large_sections(self, sections):
        """Extract subsections from large sections based on keywords."""
        result_sections = {}
        
        # Process each section looking for subsections
        for section_name, section_data in sections.items():
            content = section_data.get('content', '')
            word_count = len(content.split())
            
            # Only process large sections
            if word_count <= 150:
                result_sections[section_name] = section_data
                continue
                
            logger.info(f"Analyzing large section '{section_name}' ({word_count} words) for subsections")
            
            # Common section headers within content
            section_patterns = [
                (r'(?i)(?:^|\n|\s)(EDUCATION|ACADEMIC|QUALIFICATIONS|DEGREES?)(?:\s|:|\n)', "EDUCATION"),
                (r'(?i)(?:^|\n|\s)(WORK\s+EXPERIENCE|EMPLOYMENT|WORK\s*HISTORY|EXPERIENCE|PROFESSIONAL\s+BACKGROUND)(?:\s|:|\n)', "EXPERIENCE"),
                (r'(?i)(?:^|\n|\s)(SKILLS|TECHNICAL\s+SKILLS|PROFICIENCIES|EXPERTISE|CORE\s+COMPETENCIES)(?:\s|:|\n)', "SKILLS"),
                (r'(?i)(?:^|\n|\s)(SUMMARY|PROFILE|OBJECTIVE|CAREER\s+OBJECTIVE)(?:\s|:|\n)', "SUMMARY"),
                (r'(?i)(?:^|\n|\s)(CERTIFICATIONS?|CERTIFICATES|CREDENTIALS|LICENSES)(?:\s|:|\n)', "CERTIFICATIONS"),
                (r'(?i)(?:^|\n|\s)(PROJECTS|PORTFOLIO|PERSONAL\s+PROJECTS|PROFESSIONAL\s+PROJECTS)(?:\s|:|\n)', "PROJECTS")
            ]
            
            # Find all matches within the section
            matches = []
            for pattern, section_type in section_patterns:
                for match in re.finditer(pattern, content):
                    try:
                        # Try to get the matched header text
                        header_text = match.group(1).strip()
                    except IndexError:
                        # If there's no capture group, use the whole match
                        header_text = match.group(0).strip()
                    
                    # Get the entire line containing the header to preserve format
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    if line_start == 0:  # Header at beginning of content
                        line_start = 0
                    line_end = content.find('\n', match.start())
                    if line_end == -1:  # Header at end of content
                        line_end = len(content)
                    
                    full_header_line = content[line_start:line_end].strip()
                    matches.append((match.start(), header_text, section_type, full_header_line))
                    logger.debug(f"Found potential subsection '{header_text}' of type '{section_type}' at position {match.start()}")
            
            # Sort by position in text
            matches.sort(key=lambda x: x[0])
            
            # Create subsections
            if matches:
                logger.info(f"Found {len(matches)} subsection matches within large section '{section_name}'")
                for i, (start_pos, header_text, section_type, full_header_line) in enumerate(matches):
                    # Get section content (text between this header and next, or end)
                    if i < len(matches) - 1:
                        sub_content = content[start_pos:matches[i+1][0]]
                    else:
                        sub_content = content[start_pos:]
                    
                    # Clean up the content
                    sub_content = sub_content.strip()
                    
                    # Use the full header line we captured earlier
                    actual_section_name = full_header_line if full_header_line else section_type
                    
                    # Create a key that preserves the section type for matching but includes original text
                    section_key = f"{section_type}: {full_header_line}" if full_header_line else section_type
                    
                    # Add the subsection if it has content
                    if sub_content:
                        result_sections[section_key] = {
                            'type': section_type.lower(),
                            'confidence': 0.7,  # Good confidence for subsections
                            'content': sub_content,
                            'original_header': full_header_line,  # Preserve the original header
                            'display_name': actual_section_name,  # For display purposes
                            'section_type': section_type          # Standardized type for matching
                        }
            else:
                # Also try a content-based approach for resumes that don't explicitly label sections
                # Look for likely section starts based on content patterns
                
                # Split the content into lines for analysis
                lines = content.split('\n')
                
                # Initialize variables for detecting section boundaries
                current_position = 0
                current_section = None
                
                # Look for education-related content
                for i, line in enumerate(lines):
                    # Education section detection (degree information, university names)
                    if re.search(r'(?:Bachelor|Master|PhD|B\.S\.|M\.S\.|M\.A\.|B\.A\.|Degree|University|College)', line, re.IGNORECASE):
                        if current_section != "EDUCATION":
                            # Found start of education section
                            if current_section:
                                # Save the previous section content
                                result_sections[current_section] = {
                                    'type': current_section.lower(),
                                    'confidence': 0.6,
                                    'content': '\n'.join(lines[current_position:i])
                                }
                            
                            current_position = i
                            current_section = "EDUCATION"
                    
                    # Experience section detection (job titles, dates)
                    elif re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*-', line, re.IGNORECASE):
                        if current_section != "EXPERIENCE":
                            # Found start of experience section
                            if current_section:
                                # Save the previous section content
                                result_sections[current_section] = {
                                    'type': current_section.lower(),
                                    'confidence': 0.6,
                                    'content': '\n'.join(lines[current_position:i])
                                }
                            
                            current_position = i
                            current_section = "EXPERIENCE"
                    
                    # Skills section detection (bullet points or comma-separated lists)
                    elif re.search(r'(?:•|\*|-|,)\s*(?:Programming|Languages|Software|Tools|Frameworks|Java|Python|C\+\+)', line, re.IGNORECASE):
                        if current_section != "SKILLS":
                            # Found start of skills section
                            if current_section:
                                # Save the previous section content
                                result_sections[current_section] = {
                                    'type': current_section.lower(),
                                    'confidence': 0.6,
                                    'content': '\n'.join(lines[current_position:i])
                                }
                            
                            current_position = i
                            current_section = "SKILLS"
                
                # Save the last section
                if current_section and current_position < len(lines):
                    result_sections[current_section] = {
                        'type': current_section.lower(),
                        'confidence': 0.6,
                        'content': '\n'.join(lines[current_position:])
                    }
                
                # If we still didn't find subsections, add the original section
                if not result_sections:
                    result_sections[section_name] = section_data
        
        return result_sections
