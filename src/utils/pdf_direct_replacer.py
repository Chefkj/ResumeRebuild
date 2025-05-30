"""
Direct PDF Content Replacement module for the Resume Rebuilder application.

This module improves upon the existing PDF replacer by directly manipulating PDFs
rather than recreating them, preserving all visual elements while updating content.
"""

import os
import re
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from collections import defaultdict

# PDF manipulation libraries
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from pdfminer.high_level import extract_text

# Import with fallback for different contexts (module vs. package)
try:
    from src.utils.section_classifier import SectionClassifier
    from src.utils.pdf_replacer import PDFDocument, PDFSection, FormattedText
except ImportError:
    from utils.section_classifier import SectionClassifier
    from utils.pdf_replacer import PDFDocument, PDFSection, FormattedText

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFDirectReplacer:
    """
    Class for directly replacing content in PDF files while preserving formatting.
    
    This class provides methods to:
    1. Extract text with formatting information from PDFs
    2. Identify and classify sections in the document
    3. Replace text content while preserving layout
    4. Directly modify the original PDF to produce a visually identical PDF with improved content
    """
    
    def __init__(self):
        """Initialize the PDF direct replacer."""
        self.section_classifier = SectionClassifier()
        self.cached_section_analysis = {}  # Cache for section analysis results
    
    def extract_document_structure(self, pdf_path) -> Dict:
        """
        Extract document structure including sections, formatting, and text.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing the document structure
        """
        # Open the PDF with PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Store document structure
        structure = {
            'pages': [],
            'sections': [],
            'meta': {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'page_count': len(doc),
                'page_sizes': [(page.rect.width, page.rect.height) for page in doc]
            }
        }
        
        # Extract text blocks with their formatting and position
        for page_num, page in enumerate(doc):
            # Get text with format information
            blocks = page.get_text("dict", flags=fitz.TEXT_DEHYPHENATE)["blocks"]
            
            page_structure = {
                'blocks': [],
                'images': [],
                'drawings': []
            }
            
            # Extract text blocks
            for block in blocks:
                if "lines" in block:
                    block_info = {
                        'bbox': block['bbox'],
                        'lines': []
                    }
                    
                    for line in block['lines']:
                        line_info = {
                            'bbox': line['bbox'],
                            'spans': []
                        }
                        
                        for span in line['spans']:
                            # Convert color from RGB to hex
                            color = span.get('color')
                            if color:
                                if isinstance(color, int):
                                    color = f"#{color:06x}"
                            
                            span_info = {
                                'text': span['text'],
                                'font': span['font'],
                                'size': span['size'],
                                'color': color,
                                'bbox': span['bbox'],
                                'origin': span.get('origin', (0, 0)),
                                'flags': span.get('flags', 0)  # Includes bold, italic info
                            }
                            
                            # Detect formatting attributes
                            span_info['is_bold'] = bool(span.get('flags', 0) & 2**0)  # Bit 0 is bold
                            span_info['is_italic'] = bool(span.get('flags', 0) & 2**1)  # Bit 1 is italic
                            
                            line_info['spans'].append(span_info)
                        
                        block_info['lines'].append(line_info)
                    
                    page_structure['blocks'].append(block_info)
            
            # Get images
            images = page.get_images(full=True)
            for img_index, img_info in enumerate(images):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    image_data = {
                        'xref': xref,
                        'bbox': fitz.Rect(img_info[1]),  # Transform matrix to rectangle
                        'width': base_image['width'],
                        'height': base_image['height'],
                        'colorspace': base_image['colorspace'],
                    }
                    page_structure['images'].append(image_data)
            
            # Get drawings (shapes, lines, etc.)
            paths = page.get_drawings()
            for path in paths:
                drawing_data = {
                    'type': path['type'],
                    'color': path.get('color'),
                    'fill': path.get('fill'),
                    'line_width': path.get('width'),
                    'rect': path.get('rect'),
                    'items': path.get('items', [])
                }
                page_structure['drawings'].append(drawing_data)
            
            structure['pages'].append(page_structure)
        
        # Identify sections based on formatting and content
        sections = self._identify_sections(doc)
        structure['sections'] = sections
        
        # Classify sections
        classified_sections = self._classify_sections(sections)
        structure['classified_sections'] = classified_sections
        
        doc.close()
        
        return structure
    
    def _identify_sections(self, doc) -> List[Dict]:
        """
        Identify sections in the document based on formatting and content.
        
        Args:
            doc: PyMuPDF document
            
        Returns:
            List of section dictionaries with positions and content
        """
        sections = []
        potential_headers = []
        
        # First pass: identify potential section headers
        for page_num, page in enumerate(doc):
            # Extract text with bounding boxes
            blocks = page.get_text("dict")["blocks"]
            
            for block_num, block in enumerate(blocks):
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    line_text = ""
                    
                    # Examine spans in this line
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                            
                        # Check if this might be a header
                        is_potential_header = False
                        
                        # Look for formatting clues
                        font_size = span["size"]
                        font_flags = span.get("flags", 0)
                        is_bold = bool(font_flags & 2**0)
                        is_all_caps = text.upper() == text and len(text) > 1
                        
                        # Headers are often bold, larger font, all caps, etc.
                        if (font_size > 11 and (is_bold or is_all_caps)) or font_size >= 14:
                            is_potential_header = True
                        
                        # Check for section keywords - expanded patterns for better matching
                        for pattern in [
                            r'EDUCATION|ACADEMIC|QUALIFICATION|DEGREE|SCHOOL|UNIVERSITY',
                            r'EXPERIENCE|WORK|EMPLOYMENT|CAREER|PROFESSIONAL|JOB',
                            r'SKILLS|COMPETENCIES|EXPERTISE|PROFICIENCY|ABILITIES|KNOWLEDGE',
                            r'PROJECTS|PROJECT EXPERIENCE|PORTFOLIO|ASSIGNMENTS',
                            r'SUMMARY|PROFILE|OBJECTIVE|ABOUT|INTRODUCTION|OVERVIEW',
                            r'CERTIFICATIONS|CERTIFICATES|CREDENTIALS|LICENSES',
                            r'AWARDS|HONORS|ACHIEVEMENTS|ACCOMPLISHMENTS|RECOGNITION',
                            r'PUBLICATIONS|PAPERS|RESEARCH|ARTICLES|JOURNALS',
                            r'LANGUAGES|LANGUAGE PROFICIENCY|FLUENCY',
                            r'VOLUNTEER|COMMUNITY|SERVICE|EXTRACURRICULAR|ACTIVITIES'
                        ]:
                            if re.search(pattern, text, re.IGNORECASE):
                                is_potential_header = True
                                break
                        
                        # Also check for formatting patterns that might indicate a header
                        # Look for lines that look like headers (short, bold or all caps)
                        if len(text) < 30 and (is_bold or is_all_caps or font_size > 10):
                            # Likely a header based on formatting
                            is_potential_header = True
                        
                        if is_potential_header:
                            # Convert PDF coordinates to consistent format
                            # PyMuPDF uses top-left origin
                            x0, y0, x1, y1 = span["bbox"]
                            
                            potential_headers.append({
                                'page_num': page_num,
                                'text': text,
                                'bbox': (x0, y0, x1, y1),
                                'font_size': font_size,
                                'is_bold': is_bold,
                                'is_all_caps': is_all_caps,
                                'block_num': block_num
                            })
                        
                        line_text += text + " "
        
        # Sort potential headers by page and position
        potential_headers.sort(key=lambda h: (h['page_num'], h['bbox'][1]))
        
        # Second pass: define sections based on identified headers
        for i, header in enumerate(potential_headers):
            # Determine section boundaries
            start_page = header['page_num']
            start_block = header['block_num']
            start_y = header['bbox'][1]
            
            # Find the next header (if any) to determine the section end
            if i < len(potential_headers) - 1:
                next_header = potential_headers[i + 1]
                end_page = next_header['page_num']
                end_block = next_header['block_num']
                end_y = next_header['bbox'][1]
            else:
                end_page = len(doc) - 1
                end_block = float('inf')
                end_y = float('inf')
            
            # Extract section content
            section_content = self._extract_section_content(
                doc, header['text'],
                start_page, end_page, 
                start_y, end_y,
                start_block, end_block
            )
            
            # Create section record
            section = {
                'title': header['text'],
                'content': section_content,
                'page_span': (start_page, end_page),
                'start_pos': (header['bbox'][0], header['bbox'][1]),
                'formatting': {
                    'font_size': header['font_size'],
                    'is_bold': header['is_bold'],
                    'is_all_caps': header['is_all_caps']
                }
            }
            
            sections.append(section)
        
        # If no sections are detected, create fallback sections based on content analysis
        if not sections:
            logger.warning("No sections detected using formatting clues. Using fallback section detection.")
            sections = self._fallback_section_detection(doc)
        
        # If still no sections, at least create one "Resume" section with all content
        if not sections:
            logger.warning("Fallback detection failed. Creating a single section with all content.")
            all_text = ""
            for page in doc:
                all_text += page.get_text("text") + "\n"
                
            if all_text.strip():
                sections.append({
                    'title': "Resume",
                    'name': "Resume",
                    'text': all_text.strip(),
                    'content': all_text.strip(),
                    'page_span': (0, len(doc) - 1),
                    'start_pos': (0, 0),
                    'formatting': {
                        'font_size': 12,
                        'is_bold': False,
                        'is_all_caps': False
                    }
                })
        
        return sections
    
    def _extract_section_content(self, doc, header_text, 
                               start_page, end_page, 
                               start_y, end_y,
                               start_block, end_block) -> str:
        """
        Extract content for a specific section from the PDF document.
        
        Args:
            doc: PyMuPDF document
            header_text: Section header text
            start_page, end_page: Page range
            start_y, end_y: Y-coordinate range
            start_block, end_block: Block range
            
        Returns:
            Extracted section content
        """
        content = []
        
        # Process pages in the section
        for page_num in range(start_page, end_page + 1):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            
            for block_num, block in enumerate(blocks):
                # Skip blocks outside the section boundaries
                if page_num == start_page and block_num <= start_block:
                    continue
                if page_num == end_page and block_num >= end_block:
                    continue
                
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    # Skip lines above the section start or below the section end
                    line_y = line["bbox"][1]  # Top Y coordinate
                    if page_num == start_page and line_y < start_y:
                        continue
                    if page_num == end_page and line_y >= end_y:
                        continue
                    
                    # Extract line text
                    line_text = " ".join(span["text"] for span in line["spans"])
                    if line_text.strip() and line_text.strip() != header_text:
                        content.append(line_text)
        
        return "\n".join(content)
    
    def _classify_sections(self, sections) -> Dict:
        """
        Classify sections using the section classifier.
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            Dictionary with classified sections
        """
        classified_sections = {}
        
        for section in sections:
            title = section['title']
            content = section['content']
            
            # Use our section classifier
            section_type, confidence = self.section_classifier.classify_section(title, content)
            
            classified_sections[title] = {
                'type': section_type,
                'confidence': confidence,
                'content': content,
                'original_section': section
            }
        return classified_sections
    
    def replace_content_direct(self, pdf_path, section_replacements, output_path=None):
        """
        Replace content in a PDF file using direct manipulation.
        
        Args:
            pdf_path: Path to the original PDF file
            section_replacements: Dict mapping section types to replacement text
            output_path: Path for the output PDF file
            
        Returns:
            Path to the modified PDF file
        """
        if output_path is None:
            output_path = pdf_path.replace('.pdf', '_modified.pdf')
        
        # Extract document structure
        structure = self.extract_document_structure(pdf_path)
        
        # Open the document for modification
        doc = fitz.open(pdf_path)
        
        # Process each classified section
        for section_title, section_info in structure['classified_sections'].items():
            section_type = section_info['type']
            
            # Check if this section type has replacement content
            if section_type in section_replacements:
                replacement_text = section_replacements[section_type]
                
                # Get the original section details
                original_section = section_info['original_section']
                start_page, end_page = original_section['page_span']
                
                # Replace section content through redaction and insertion
                self._replace_section_content(
                    doc, section_title, 
                    section_info['content'], replacement_text,
                    start_page, end_page
                )
        
        # Save the modified document
        doc.save(output_path)
        doc.close()
        
        return output_path
    
    def _replace_section_content(self, doc, section_title, original_content, 
                                replacement_content, start_page, end_page):
        """
        Replace content in a section while preserving formatting.
        
        Args:
            doc: PyMuPDF document being modified
            section_title: Title of the section
            original_content: Original section content
            replacement_content: Replacement section content
            start_page, end_page: Page span of the section
        """
        # Strategy: Use redaction to remove original content and then insert new content
        # This is a more complex operation than it might initially appear
        
        # First, prepare the replacement content by breaking it into paragraphs
        replacement_paragraphs = replacement_content.split('\n')
        
        # Find text instances on pages in the section
        for page_num in range(start_page, end_page + 1):
            page = doc[page_num]
            
            # Use a two-pass approach: 
            # 1. First find content to redact
            # 2. Then add new content
            
            # Find the portions of original content on this page
            original_paragraphs = original_content.split('\n')
            
            # Search for each paragraph in the page
            for paragraph in original_paragraphs:
                if not paragraph.strip():
                    continue
                    
                # Look for this text in the page
                instances = page.search_for(paragraph.strip())
                
                # Redact each instance (replace with white rectangles)
                for rect in instances:
                    # Create a white rectangle to cover the text
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Now find the section header to position the new content
            if page_num == start_page:
                # Find the section title on this page
                title_instances = page.search_for(section_title)
                
                if title_instances:
                    # Position below the title
                    title_rect = title_instances[0]
                    
                    # Insert the replacement content
                    insert_point = fitz.Point(
                        title_rect.x0, 
                        title_rect.y1 + 10  # Position below the title
                    )
                    
                    # Insert new text
                    for i, paragraph in enumerate(replacement_paragraphs):
                        if not paragraph.strip():
                            continue
                            
                        # Set font and size (could be improved by using original formatting)
                        fontname = "helv"  # Helvetica
                        fontsize = 11
                        
                        # Insert the text
                        page.insert_text(
                            insert_point, 
                            paragraph,
                            fontname=fontname,
                            fontsize=fontsize
                        )
                        
                        # Move insertion point down for next paragraph
                        insert_point.y += fontsize + 5
        
        # The above implementation is simplified and has limitations:
        # - It doesn't preserve complex formatting
        # - It may not perfectly align with the original layout
        # - It may cause pagination issues
        # 
        # For a production system, a more sophisticated approach would involve:
        # 1. Maintaining block-level formatting information
        # 2. Using text extraction to preserve paragraph structure
        # 3. Preserving bullet points and other formatting elements
        # 4. Handling pagination and overflow
    
    def rebuild_resume_with_llm(self, pdf_path, job_description, output_path=None):
        """
        Rebuild a resume using LLM integration, preserving the original layout.
        
        Args:
            pdf_path: Path to the original PDF file
            job_description: Job description text to target
            output_path: Path for the output PDF file
            
        Returns:
            Path to the improved resume PDF
        """
        if output_path is None:
            output_path = pdf_path.replace('.pdf', '_improved.pdf')
        
        # Extract document structure
        structure = self.extract_document_structure(pdf_path)
        
        try:
            # Import LLM refiner with fallback for different contexts
            try:
                from src.utils.llm_refiner import LLMRefiner
            except ImportError:
                from utils.llm_refiner import LLMRefiner
            refiner = LLMRefiner()
            
            # Prepare sections for LLM processing
            sections_for_llm = {}
            for section_title, section_info in structure['classified_sections'].items():
                section_type = section_info['type']
                content = section_info['content']
                
                # Create a formatted version for the LLM
                formatted_section = f"# {section_title}\n\n{content}"
                sections_for_llm[section_type] = formatted_section
            
            # Send to LLM for improvement
            improved_sections = {}
            
            # Process each section with the LLM
            for section_type, section_content in sections_for_llm.items():
                if section_type in ['contact', 'header']:
                    # Skip contact info/header sections as they shouldn't be modified
                    continue
                
                # Create a tailored prompt for this section
                prompt = f"""
                Improve this resume section for the following job description:
                
                JOB DESCRIPTION:
                {job_description[:500]}...
                
                RESUME SECTION ({section_type}):
                {section_content}
                
                Please provide a revised version of this section that better targets the job.
                Keep a similar length and formatting style as the original.
                Only return the improved section content, not an explanation.
                """
                
                # Get LLM improvement
                improved_content = refiner._analyze_and_improve_resume(prompt)
                
                if improved_content:
                    # Extract just the content part (removing any headers the LLM might add)
                    if '#' in improved_content:
                        # Try to remove section header
                        content_parts = improved_content.split('\n', 2)
                        if len(content_parts) >= 3:  # [header, blank line, content]
                            improved_content = content_parts[2].strip()
                    
                    improved_sections[section_type] = improved_content
            
            # Replace content in the PDF
            return self.replace_content_direct(pdf_path, improved_sections, output_path)
            
        except ImportError:
            logger.warning("LLM refiner not available. Using original content.")
            return pdf_path
        except Exception as e:
            logger.error(f"Error during LLM improvement: {e}")
            return pdf_path

    def _fallback_section_detection(self, doc) -> List[Dict]:
        """
        Fallback method for detecting sections when the regular method doesn't find any.
        Uses content analysis and common section patterns to create sections.
        
        Args:
            doc: PyMuPDF document
            
        Returns:
            List of section dictionaries
        """
        sections = []
        
        # Extract all text from the document
        full_text = ""
        for page in doc:
            full_text += page.get_text("text") + "\n"
        
        # Common resume section patterns with broader matching
        section_patterns = [
            (r'(?i)(?:^|\n)(?:EDUCATION|ACADEMIC|QUALIFICATIONS|DEGREES?)(?:\s|:|\n)', "Education"),
            (r'(?i)(?:^|\n)(?:WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT|WORK\s+HISTORY|CAREER|EXPERIENCE)(?:\s|:|\n)', "Experience"),
            (r'(?i)(?:^|\n)(?:SKILLS|TECHNICAL\s+SKILLS|COMPETENCIES|EXPERTISE|PROFICIENCIES)(?:\s|:|\n)', "Skills"),
            (r'(?i)(?:^|\n)(?:PROJECTS|PROJECT\s+EXPERIENCE|PORTFOLIO|ASSIGNMENTS)(?:\s|:|\n)', "Projects"),
            (r'(?i)(?:^|\n)(?:SUMMARY|PROFESSIONAL\s+SUMMARY|PROFILE|OBJECTIVE|ABOUT|INTRODUCTION)(?:\s|:|\n)', "Summary"),
            (r'(?i)(?:^|\n)(?:CERTIFICATIONS|CERTIFICATES|CREDENTIALS|LICENSES|ACCREDITATIONS)(?:\s|:|\n)', "Certifications"),
            (r'(?i)(?:^|\n)(?:AWARDS|HONORS|ACHIEVEMENTS|ACCOMPLISHMENTS|RECOGNITION)(?:\s|:|\n)', "Awards"),
            (r'(?i)(?:^|\n)(?:PUBLICATIONS|PAPERS|RESEARCH|ARTICLES|JOURNALS)(?:\s|:|\n)', "Publications"),
            (r'(?i)(?:^|\n)(?:LANGUAGES|LANGUAGE\s+PROFICIENCY|FLUENCY|LANGUAGE\s+SKILLS)(?:\s|:|\n)', "Languages"),
            (r'(?i)(?:^|\n)(?:VOLUNTEER|COMMUNITY\s+SERVICE|EXTRACURRICULAR|ACTIVITIES)(?:\s|:|\n)', "Volunteer")
        ]
        
        # Find all potential sections
        matches = []
        for pattern, section_name in section_patterns:
            for match in re.finditer(pattern, full_text):
                matches.append((match.start(), match.group().strip(), section_name))
        
        # Sort matches by position
        matches.sort(key=lambda x: x[0])
        
        # Create sections based on matches
        for i, (start_pos, header_text, section_name) in enumerate(matches):
            # Determine section boundaries
            start = start_pos + len(header_text)
            if i < len(matches) - 1:
                end = matches[i+1][0]
            else:
                end = len(full_text)
            
            # Extract section content
            content = full_text[start:end].strip()
            
            # Create section record
            section = {
                'title': header_text.strip(),
                'name': section_name,
                'text': content,
                'content': content,
                'page_span': (0, len(doc) - 1),  # Approximate page span
                'start_pos': (0, start_pos),  # Approximate position
                'formatting': {
                    'font_size': 12,  # Default formatting
                    'is_bold': True,
                    'is_all_caps': header_text.upper() == header_text
                }
            }
            
            sections.append(section)
        
        # If we found at least one section, check if we're missing contact info at the top
        if sections and matches[0][0] > 50:  # If first section doesn't start near the beginning
            header_section = {
                'title': 'Contact Information',
                'name': 'Contact',
                'text': full_text[:matches[0][0]].strip(),
                'content': full_text[:matches[0][0]].strip(),
                'page_span': (0, 0),  # Typically on first page
                'start_pos': (0, 0),
                'formatting': {
                    'font_size': 12,
                    'is_bold': False,
                    'is_all_caps': False
                }
            }
            sections.insert(0, header_section)
        
        return sections
# Helper functions for font matching

def match_font(pdf_font_name):
    """Match PDF font name to a PyMuPDF font name."""
    pdf_font_name = pdf_font_name.lower()
    
    # Basic mapping of common fonts
    font_map = {
        'times': 'times',
        'helvetica': 'helv',
        'arial': 'helv',
        'courier': 'cour',
        'symbol': 'symb',
        'zapfdingbats': 'zadb'
    }
    
    # Find the best match
    for key, value in font_map.items():
        if key in pdf_font_name:
            base_font = value
            
            # Handle style variants
            if 'bold' in pdf_font_name and 'italic' in pdf_font_name:
                return f"{base_font}-bo"  # bold-oblique
            elif 'bold' in pdf_font_name:
                return f"{base_font}-b"  # bold
            elif 'italic' in pdf_font_name or 'oblique' in pdf_font_name:
                return f"{base_font}-o"  # oblique
            else:
                return base_font
    
    # Default to Helvetica if no match
    return 'helv'
