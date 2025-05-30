"""
PDF Content Replacement module for the Resume Rebuilder application.

This module allows for text extraction with formatting information and strategic
content replacement while preserving the original PDF's visual layout.
"""

import io
import os
import re
import tempfile
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from collections import defaultdict

# PDF processing libraries
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams, LTTextContainer, LTChar, LTTextBox, LTTextLine
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from PyPDF2 import PdfReader, PdfWriter
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FormattedText:
    """Represents a piece of text with its formatting information."""
    
    def __init__(self, text, font_name=None, font_size=None, 
                 color=None, x0=0, y0=0, x1=0, y1=0, page_num=0):
        """
        Initialize a formatted text object.
        
        Args:
            text: The text content
            font_name: Name of the font
            font_size: Size of the font
            color: Text color
            x0, y0: Bottom-left coordinates
            x1, y1: Top-right coordinates
            page_num: Page number where the text appears
        """
        self.text = text
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.page_num = page_num
    
    def __str__(self):
        return f"{self.text} ({self.font_name}, {self.font_size}pt)"


class PDFSection:
    """Represents a section of a PDF with text and formatting."""
    
    def __init__(self, name=None):
        """
        Initialize a PDF section.
        
        Args:
            name: Optional name of the section
        """
        self.name = name
        self.elements: List[FormattedText] = []
        self.bounding_box = None  # (x0, y0, x1, y1) for the section
    
    def add_element(self, element: FormattedText):
        """Add a formatted text element to the section."""
        self.elements.append(element)
        
        # Update bounding box
        if not self.bounding_box:
            self.bounding_box = (element.x0, element.y0, element.x1, element.y1)
        else:
            x0, y0, x1, y1 = self.bounding_box
            self.bounding_box = (
                min(x0, element.x0),
                min(y0, element.y0),
                max(x1, element.x1),
                max(y1, element.y1)
            )
    
    def get_text(self) -> str:
        """Get the combined text of all elements."""
        return " ".join([el.text for el in self.elements])
    
    def __str__(self):
        return f"Section{f' {self.name}' if self.name else ''}: {len(self.elements)} elements"


class PDFDocument:
    """Represents a PDF document with its structure and formatting."""
    
    def __init__(self):
        """Initialize a PDF document object."""
        self.pages = []  # List of pages, each containing a list of elements
        self.sections = []  # List of identified sections
    
    def add_element(self, element: FormattedText):
        """Add a formatted text element to the appropriate page."""
        # Ensure we have enough pages
        while len(self.pages) <= element.page_num:
            self.pages.append([])
        
        # Add element to the page
        self.pages[element.page_num].append(element)
    
    def add_section(self, section: PDFSection):
        """Add a section to the document."""
        self.sections.append(section)
    
    def get_text(self) -> str:
        """Get the combined text of all elements in the document."""
        all_text = []
        for page in self.pages:
            # Sort elements by y-coordinate (top to bottom)
            sorted_elements = sorted(page, key=lambda el: -el.y0)
            page_text = " ".join([el.text for el in sorted_elements])
            all_text.append(page_text)
        
        return "\n\n".join(all_text)
    
    def __str__(self):
        return f"PDFDocument: {len(self.pages)} pages, {len(self.sections)} sections"


class PDFReplacer:
    """
    Class for replacing content in PDF files while preserving formatting.
    
    This class provides methods to:
    1. Extract text with formatting information from PDFs
    2. Identify and classify sections in the document
    3. Replace text content while preserving layout
    4. Generate a new PDF that looks visually identical but with improved content
    """
    
    def __init__(self, section_patterns=None):
        """
        Initialize the PDF replacer.
        
        Args:
            section_patterns: Optional list of regex patterns to identify sections
        """
        self.section_patterns = section_patterns or [
            r'EDUCATION|ACADEMIC BACKGROUND',
            r'EXPERIENCE|WORK HISTORY|EMPLOYMENT',
            r'SKILLS|TECHNICAL SKILLS|COMPETENCIES',
            r'PROJECTS|PROJECT EXPERIENCE',
            r'CERTIFICATIONS|CERTIFICATES',
            r'LANGUAGES|LANGUAGE PROFICIENCY',
            r'AWARDS|HONORS|ACHIEVEMENTS',
            r'PUBLICATIONS|PAPERS|RESEARCH',
            r'VOLUNTEER|COMMUNITY SERVICE',
            r'SUMMARY|PROFILE|OBJECTIVE'
        ]
    
    def extract_formatted_pdf(self, pdf_path) -> PDFDocument:
        """
        Extract text with formatting information from a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            PDFDocument object containing the formatted content
        """
        document = PDFDocument()
        
        # Set up PDFMiner tools
        rsrcmgr = PDFResourceManager()
        laparams = LAParams(line_margin=0.3, char_margin=1.0)
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        
        with open(pdf_path, 'rb') as fp:
            # Track current page number
            page_num = 0
            
            for page in PDFPage.get_pages(fp):
                interpreter.process_page(page)
                layout = device.get_result()
                
                # Process all text elements on the page
                for element in layout:
                    if isinstance(element, LTTextBox):
                        self._process_text_box(element, document, page_num)
                
                # Move to next page
                page_num += 1
        
        # Identify sections in the document
        self._identify_sections(document)
        
        return document
    
    def _process_text_box(self, text_box, document, page_num):
        """
        Process a text box element from PDFMiner and extract formatted text.
        
        Args:
            text_box: LTTextBox element from PDFMiner
            document: PDFDocument to add extracted elements to
            page_num: Current page number
        """
        for line in text_box:
            if isinstance(line, LTTextLine):
                # Process each character to get formatting
                fragments = []
                current_fragment = {
                    'text': '',
                    'font_name': None,
                    'font_size': None,
                    'color': None,
                    'x0': line.bbox[0],
                    'y0': line.bbox[1],
                    'x1': line.bbox[0],  # Will be updated as we go
                    'y1': line.bbox[3]
                }
                
                for char in line:
                    if isinstance(char, LTChar):
                        # Check if formatting is changing
                        if (current_fragment['font_name'] and 
                            (current_fragment['font_name'] != char.fontname or
                             abs(current_fragment['font_size'] - char.size) > 0.1)):
                            
                            # Save the current fragment and start a new one
                            if current_fragment['text']:
                                fragments.append(current_fragment)
                            
                            # Start a new fragment
                            current_fragment = {
                                'text': char.get_text(),
                                'font_name': char.fontname,
                                'font_size': char.size,
                                'color': None,  # PDFMiner doesn't provide color easily
                                'x0': char.bbox[0],
                                'y0': char.bbox[1],
                                'x1': char.bbox[2],
                                'y1': char.bbox[3]
                            }
                        else:
                            # Add to current fragment
                            current_fragment['text'] += char.get_text()
                            current_fragment['font_name'] = current_fragment['font_name'] or char.fontname
                            current_fragment['font_size'] = current_fragment['font_size'] or char.size
                            current_fragment['x1'] = char.bbox[2]  # Extend to include this char
                
                # Add the last fragment
                if current_fragment['text']:
                    fragments.append(current_fragment)
                
                # Create formatted text elements and add to document
                for frag in fragments:
                    element = FormattedText(
                        text=frag['text'],
                        font_name=frag['font_name'],
                        font_size=frag['font_size'],
                        color=frag['color'],
                        x0=frag['x0'],
                        y0=frag['y0'],
                        x1=frag['x1'],
                        y1=frag['y1'],
                        page_num=page_num
                    )
                    document.add_element(element)
    
    def _identify_sections(self, document):
        """
        Identify sections in the document based on formatting and patterns.
        
        Args:
            document: PDFDocument to analyze for sections
        """
        # Compile section patterns
        patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.section_patterns]
        
        # Find potential section headers by looking at formatting and content
        potential_headers = []
        
        for page_num, page in enumerate(document.pages):
            # Look for text elements that might be headers
            for element in page:
                # Check if content matches any section pattern
                text = element.text.strip()
                for pattern in patterns:
                    if pattern.search(text):
                        potential_headers.append((page_num, element))
                        break
                
                # Also look for elements that appear to be headers based on formatting
                if (element.font_size and 
                    element.font_size > 11 and  # Larger font
                    len(text) < 50 and  # Not too long
                    text.isupper()):  # All caps
                    potential_headers.append((page_num, element))
        
        # Sort headers by page and position
        potential_headers.sort(key=lambda h: (h[0], -h[1].y0))
        
        # Create sections based on headers
        for i, (page_num, header) in enumerate(potential_headers):
            # Create a new section
            section = PDFSection(name=header.text.strip())
            
            # Add the header element itself
            section.add_element(header)
            
            # Determine the end of this section (next header or end of document)
            next_header_page = potential_headers[i+1][0] if i < len(potential_headers) - 1 else None
            next_header_y = potential_headers[i+1][1].y0 if i < len(potential_headers) - 1 else None
            
            # Add all elements that belong to this section
            for p_num, page in enumerate(document.pages[page_num:], page_num):
                # If we've reached the page with the next header, stop after processing that page
                if next_header_page is not None and p_num > next_header_page:
                    break
                    
                for element in page:
                    # Skip the header element itself
                    if element is header:
                        continue
                        
                    # If on same page as header, only include elements below it
                    if p_num == page_num and element.y0 >= header.y0:
                        continue
                        
                    # If on the same page as next header, only include elements above it
                    if p_num == next_header_page and next_header_y is not None and element.y0 <= next_header_y:
                        continue
                        
                    # Add the element to this section
                    section.add_element(element)
            
            # Add the section to the document
            document.add_section(section)
    
    def replace_content(self, pdf_path, section_replacements, output_path):
        """
        Replace content in a PDF file while preserving the original layout.
        
        Args:
            pdf_path: Path to the original PDF file
            section_replacements: Dict mapping section names to replacement text
            output_path: Path for the output PDF file
            
        Returns:
            Path to the generated PDF file with replaced content
        """
        # Extract the original PDF structure
        document = self.extract_formatted_pdf(pdf_path)
        
        # Create a new PDF with replaced content
        self._generate_replaced_pdf(document, section_replacements, output_path)
        
        return output_path
    
    def _generate_replaced_pdf(self, document, section_replacements, output_path):
        """
        Generate a new PDF with replaced content that preserves the original layout.
        
        Args:
            document: PDFDocument with the original content and formatting
            section_replacements: Dict mapping section names to replacement text
            output_path: Path for the output PDF file
        """
        # This is a simplified version - a more sophisticated implementation would
        # do a better job of matching the original layout precisely
        
        # Create a PDF with reportlab
        c = canvas.Canvas(output_path, pagesize=letter)
        
        # Process each page
        for page_num, page in enumerate(document.pages):
            if page:  # Only process non-empty pages
                # Add a new page (except for the first page)
                if page_num > 0:
                    c.showPage()
                
                # Process elements on this page
                for element in sorted(page, key=lambda e: (-e.y0, e.x0)):  # Sort top-to-bottom, left-to-right
                    text = element.text
                    
                    # Check if this element is part of a section that needs replacement
                    for section in document.sections:
                        if element in section.elements:
                            # See if this section has replacement text
                            for pattern, replacement in section_replacements.items():
                                if pattern.lower() in section.name.lower():
                                    # Here we would need a more sophisticated algorithm to
                                    # determine exactly what to replace and how to format it
                                    # This is a simplified approach
                                    
                                    # For now, we're just replacing the text
                                    text = _map_text_to_replacement(element.text, section.get_text(), replacement)
                                    break
                            break
                    
                    # Set font properties to match the original
                    font_name = element.font_name
                    if font_name:
                        # Convert PDFMiner font name to ReportLab font name
                        # This is a simplification - would need more mapping in reality
                        if "bold" in font_name.lower():
                            c.setFont("Helvetica-Bold", element.font_size)
                        elif "italic" in font_name.lower() or "oblique" in font_name.lower():
                            c.setFont("Helvetica-Oblique", element.font_size)
                        else:
                            c.setFont("Helvetica", element.font_size)
                    else:
                        c.setFont("Helvetica", element.font_size or 10)
                    
                    # Draw text at the same position as in the original
                    # Note: PDFMiner's coordinates are from bottom-left corner
                    c.drawString(element.x0, element.y0, text)
        
        # Save the PDF
        c.save()


def _map_text_to_replacement(element_text, section_text, replacement_text):
    """
    Map original text to corresponding replacement text.
    
    Args:
        element_text: The specific text element to replace
        section_text: The full text of the section
        replacement_text: The replacement text for the section
        
    Returns:
        The appropriate replacement text for this specific element
    """
    # This is a simplified mapping approach
    # In a real implementation, we would need a more sophisticated algorithm
    
    # For now, we'll just check if the element text appears in the section
    if element_text.strip() and element_text in section_text:
        # Find the position in the section text
        pos = section_text.find(element_text)
        rel_pos = pos / len(section_text)
        
        # Find a proportional position in the replacement text
        replacement_pos = int(rel_pos * len(replacement_text))
        
        # Extract a similar length of text from the replacement
        # This is very simplified and won't work well in practice
        replacement_len = min(len(element_text), len(replacement_text) - replacement_pos)
        return replacement_text[replacement_pos:replacement_pos + replacement_len]
    
    return element_text


# Function to improve readability of a font name
def clean_font_name(font_name):
    """Convert PDFMiner font name to a more readable format."""
    if not font_name:
        return "Default"
    
    # Remove subset prefix (ABCDEF+FontName)
    if "+" in font_name:
        font_name = font_name.split("+")[1]
    
    # Handle common abbreviations
    font_name = font_name.replace("MT", "")
    font_name = font_name.replace("PS", "")
    
    return font_name
