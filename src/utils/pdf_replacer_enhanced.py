"""
Enhanced PDF Content Replacement module with OCR capabilities.

This module extends the basic PDF replacer with OCR capabilities for more accurate
text extraction and position mapping, especially useful for scanned documents
or PDFs with complex formatting.
"""

import io
import os
import tempfile
import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import defaultdict

# PDF libraries
from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Import the base PDF replacer with fallback for different contexts
try:
    from src.utils.pdf_replacer import PDFReplacer, PDFDocument, PDFSection, FormattedText
except ImportError:
    from utils.pdf_replacer import PDFReplacer, PDFDocument, PDFSection, FormattedText

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OCRTextBlock:
    """Represents a block of text extracted via OCR with position and formatting."""
    
    def __init__(self, text, x0, y0, x1, y1, font_size=None, font_name=None, 
                 is_bold=False, is_italic=False, line_spacing=None, page_num=0):
        """
        Initialize an OCR text block.
        
        Args:
            text: The extracted text content
            x0, y0: Bottom-left coordinates
            x1, y1: Top-right coordinates
            font_size: Estimated font size (points)
            font_name: Estimated font name
            is_bold: Whether the text appears to be bold
            is_italic: Whether the text appears to be italic
            line_spacing: Estimated line spacing
            page_num: Page number where the text appears
        """
        self.text = text
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.font_size = font_size
        self.font_name = font_name
        self.is_bold = is_bold
        self.is_italic = is_italic
        self.line_spacing = line_spacing
        self.page_num = page_num
        
        # Additional attributes for section classification
        self.section_type = None
        self.confidence = 0.0
    
    def to_formatted_text(self) -> FormattedText:
        """Convert to a FormattedText object."""
        # Determine font name based on style
        font_name = self.font_name or "Helvetica"
        if self.is_bold and self.is_italic:
            font_name += "-BoldOblique"
        elif self.is_bold:
            font_name += "-Bold"
        elif self.is_italic:
            font_name += "-Oblique"
            
        return FormattedText(
            text=self.text,
            font_name=font_name,
            font_size=self.font_size or 10,
            color=None,  # We don't have color info from OCR
            x0=self.x0,
            y0=self.y0,
            x1=self.x1,
            y1=self.y1,
            page_num=self.page_num
        )


class EnhancedPDFReplacer(PDFReplacer):
    """
    Enhanced class for replacing content in PDF files with OCR capabilities.
    
    This class extends PDFReplacer with:
    1. OCR-based text extraction for better accuracy
    2. Improved section classification
    3. More sophisticated content replacement logic
    4. Higher-quality PDF reconstruction
    """
    
    def __init__(self, section_patterns=None, use_ocr=True):
        """
        Initialize the enhanced PDF replacer.
        
        Args:
            section_patterns: Optional list of regex patterns to identify sections
            use_ocr: Whether to use OCR for extraction (requires external tools)
        """
        super().__init__(section_patterns)
        self.use_ocr = use_ocr
    
    def extract_with_pymupdf(self, pdf_path) -> PDFDocument:
        """
        Extract text and formatting using PyMuPDF (better formatting detection).
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            PDFDocument object with extracted content
        """
        document = PDFDocument()
        
        try:
            # Open the PDF with PyMuPDF
            doc = fitz.open(pdf_path)
            
            # Process each page
            for page_num, page in enumerate(doc):
                # Extract text with formatting information
                blocks = page.get_text("dict", flags=fitz.TEXT_DEHYPHENATE)["blocks"]
                
                for block in blocks:
                    if "lines" not in block:
                        continue
                        
                    for line in block["lines"]:
                        for span in line["spans"]:
                            # Extract the text and its formatting
                            text = span["text"]
                            if not text.strip():
                                continue
                                
                            font_name = span["font"]
                            font_size = span["size"]
                            # Convert PyMuPDF coordinates to PDF coordinates
                            # PyMuPDF uses top-left origin, we need bottom-left
                            x0, y0, x1, y1 = span["bbox"]
                            y0 = page.rect.height - y0
                            y1 = page.rect.height - y1
                            
                            # Create a formatted text element
                            element = FormattedText(
                                text=text,
                                font_name=font_name,
                                font_size=font_size,
                                color=None,  # Could extract color with more work
                                x0=x0,
                                y0=y1,  # Note the coordinate conversion
                                x1=x1,
                                y1=y0,  # Note the coordinate conversion
                                page_num=page_num
                            )
                            
                            # Add the element to the document
                            document.add_element(element)
            
            # Identify sections in the document
            self._identify_sections(document)
            
            return document
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction error: {e}")
            # Fall back to the base extraction method
            return super().extract_formatted_pdf(pdf_path)
    
    def extract_with_ocr(self, pdf_path) -> PDFDocument:
        """
        Extract text using OCR for better accuracy, especially with scanned documents.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            PDFDocument object with OCR-extracted content
        """
        document = PDFDocument()
        
        try:
            # Convert PDF to images and process with OCR
            import pytesseract
            from PIL import Image
            
            # Open the PDF with PyMuPDF for rendering
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc):
                # Render the page to an image
                pix = page.get_pixmap(alpha=False)
                
                # Create a PIL Image from the pixmap
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Run OCR with layout analysis
                ocr_data = pytesseract.image_to_data(
                    img, 
                    output_type=pytesseract.Output.DICT,
                    config='--psm 1'  # Automatic page segmentation with OSD
                )
                
                # Convert OCR results to text blocks
                blocks = self._process_ocr_data(ocr_data, page.rect.width, page.rect.height, page_num)
                
                # Convert blocks to formatted text and add to document
                for block in blocks:
                    element = block.to_formatted_text()
                    document.add_element(element)
            
            # Identify sections in the document
            self._identify_sections(document)
            
            return document
            
        except ImportError:
            logger.warning("OCR extraction requires pytesseract and Pillow. Falling back to PyMuPDF.")
            return self.extract_with_pymupdf(pdf_path)
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            # Fall back to PyMuPDF extraction
            return self.extract_with_pymupdf(pdf_path)
    
    def _process_ocr_data(self, ocr_data, page_width, page_height, page_num):
        """
        Process OCR data to create text blocks.
        
        Args:
            ocr_data: Dictionary of OCR data from pytesseract
            page_width, page_height: Dimensions of the page
            page_num: Current page number
            
        Returns:
            List of OCRTextBlock objects
        """
        blocks = []
        
        # Group OCR data by block number
        block_data = defaultdict(list)
        for i in range(len(ocr_data['text'])):
            if ocr_data['text'][i].strip():
                block_num = ocr_data['block_num'][i]
                block_data[block_num].append({
                    'text': ocr_data['text'][i],
                    'left': ocr_data['left'][i],
                    'top': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i],
                    'conf': ocr_data['conf'][i],
                    'line_num': ocr_data['line_num'][i],
                    'word_num': ocr_data['word_num'][i]
                })
        
        # Process each block
        for block_num, words in block_data.items():
            # Group words by line
            lines = defaultdict(list)
            for word in words:
                lines[word['line_num']].append(word)
            
            # Process each line
            for line_num, line_words in lines.items():
                # Sort words by position
                line_words.sort(key=lambda w: w['left'])
                
                # Combine words into a line
                line_text = ' '.join(w['text'] for w in line_words)
                
                # Calculate bounding box
                left = min(w['left'] for w in line_words)
                top = min(w['top'] for w in line_words)
                right = max(w['left'] + w['width'] for w in line_words)
                bottom = max(w['top'] + w['height'] for w in line_words)
                
                # Calculate average font size based on height
                avg_height = sum(w['height'] for w in line_words) / len(line_words)
                font_size = avg_height * 0.75  # Estimate font size from height
                
                # Convert to PDF coordinates (bottom-left origin)
                x0 = left
                y0 = page_height - bottom
                x1 = right
                y1 = page_height - top
                
                # Determine if text is bold or italic (simplified)
                # This would need a more sophisticated analysis in reality
                is_bold = any(w['text'].isupper() for w in line_words) and len(line_text) < 40
                is_italic = False  # Can't reliably detect from OCR
                
                # Create a text block
                block = OCRTextBlock(
                    text=line_text,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    font_size=font_size,
                    font_name=None,  # OCR can't determine font name
                    is_bold=is_bold,
                    is_italic=is_italic,
                    page_num=page_num
                )
                
                blocks.append(block)
        
        return blocks
    
    def extract_formatted_pdf(self, pdf_path) -> PDFDocument:
        """
        Extract text with formatting from a PDF using the best available method.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            PDFDocument object with extracted content
        """
        # Try OCR first if enabled
        if self.use_ocr:
            try:
                return self.extract_with_ocr(pdf_path)
            except Exception as e:
                logger.warning(f"OCR extraction failed: {e}. Falling back to PyMuPDF.")
        
        # Try PyMuPDF
        try:
            return self.extract_with_pymupdf(pdf_path)
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}. Falling back to base extractor.")
        
        # Fall back to base extraction method
        return super().extract_formatted_pdf(pdf_path)
    
    def classify_sections(self, document: PDFDocument, use_llm=True):
        """
        Classify sections in the document using patterns and formatting cues.
        Optional LLM-based classification for better accuracy.
        
        Args:
            document: PDFDocument to classify
            use_llm: Whether to use LLM for improved classification
            
        Returns:
            Updated PDFDocument with classified sections
        """
        # Basic classification is already done in _identify_sections
        # We can enhance it with LLM if available
        if use_llm:
            try:
                from utils.llm_refiner import LLMRefiner
                refiner = LLMRefiner()
                
                # For each section, use the LLM to classify it
                for section in document.sections:
                    section_text = section.get_text()
                    
                    # Skip empty or very short sections
                    if not section_text or len(section_text) < 10:
                        continue
                    
                    # Classify the section
                    classify_prompt = f"""
                    Classify the following resume section:
                    
                    Section Heading: {section.name}
                    
                    Section Content (excerpt):
                    {section_text[:200]}...
                    
                    What type of section is this? (e.g., Education, Experience, Skills, etc.)
                    """
                    
                    # Use the ManageAI API to classify
                    try:
                        response = refiner._analyze_and_improve_resume(classify_prompt)
                        if response:
                            # Extract the classification from the response
                            for pattern in self.section_patterns:
                                if re.search(pattern, response, re.IGNORECASE):
                                    section.classification = pattern
                                    break
                    except Exception as e:
                        logger.warning(f"LLM classification failed: {e}")
            
            except ImportError:
                logger.info("LLM refiner not available for section classification.")
        
        return document
    
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
        
        # Classify sections if needed
        document = self.classify_sections(document)
        
        # Generate a new PDF with replaced content
        self._generate_replaced_pdf_advanced(document, section_replacements, output_path, pdf_path)
        
        return output_path
    
    def _generate_replaced_pdf_advanced(self, document, section_replacements, output_path, original_pdf_path):
        """
        Generate a new PDF with replaced content using advanced techniques.
        
        Args:
            document: PDFDocument with the original content and formatting
            section_replacements: Dict mapping section names to replacement text
            output_path: Path for the output PDF file
            original_pdf_path: Path to the original PDF file for reference
        """
        try:
            # Use PyMuPDF for better PDF generation
            doc = fitz.open()
            
            # Get the original PDF for reference (page sizes, etc.)
            orig_doc = fitz.open(original_pdf_path)
            
            # Process each page
            for page_num, page_elements in enumerate(document.pages):
                if not page_elements:
                    continue
                    
                # Create a new page with the same dimensions as the original
                if page_num < len(orig_doc):
                    page = doc.new_page(width=orig_doc[page_num].rect.width,
                                       height=orig_doc[page_num].rect.height)
                else:
                    page = doc.new_page()
                
                # Process elements on this page
                for element in sorted(page_elements, key=lambda e: (-e.y0, e.x0)):
                    text = element.text
                    
                    # Check if this element is part of a section that needs replacement
                    for section in document.sections:
                        if element in section.elements:
                            # See if this section has replacement text
                            for section_name, replacement in section_replacements.items():
                                if section_name.lower() in section.name.lower():
                                    # Here we use a smarter text replacement algorithm
                                    text = self._smart_text_replacement(
                                        element.text, 
                                        section.get_text(), 
                                        replacement
                                    )
                                    break
                            break
                    
                    # Create a text insertion point
                    # PyMuPDF uses top-left origin, convert coordinates
                    insert_x = element.x0
                    insert_y = page.rect.height - element.y0
                    
                    # Determine font size and style
                    font_size = element.font_size or 11
                    font_name = element.font_name or "helv"
                    
                    # Simplify font name for PyMuPDF
                    if "bold" in font_name.lower() and "italic" in font_name.lower():
                        font = "helv-bo"  # bold-oblique
                    elif "bold" in font_name.lower():
                        font = "helv-b"  # bold
                    elif "italic" in font_name.lower() or "oblique" in font_name.lower():
                        font = "helv-o"  # oblique
                    else:
                        font = "helv"  # regular
                    
                    # Insert the text
                    page.insert_text(
                        (insert_x, insert_y),
                        text,
                        fontname=font,
                        fontsize=font_size
                    )
            
            # Save the PDF
            doc.save(output_path)
            doc.close()
            orig_doc.close()
            
        except Exception as e:
            logger.error(f"Advanced PDF generation failed: {e}")
            # Fall back to the base method
            self._generate_replaced_pdf(document, section_replacements, output_path)
    
    def _smart_text_replacement(self, element_text, section_text, replacement_text):
        """
        Smarter algorithm to map original text to appropriate replacement text.
        
        Args:
            element_text: The specific text element to replace
            section_text: The full text of the section
            replacement_text: The replacement text for the section
            
        Returns:
            The appropriate replacement text for this specific element
        """
        # This is a more sophisticated text replacement strategy
        
        # If the element contains a full line, try to find a corresponding line
        if len(element_text.strip()) > 30:
            # This might be a paragraph or sentence
            # Find similar structure in the replacement text
            
            # Calculate position in original section
            lines = section_text.split('\n')
            for i, line in enumerate(lines):
                if element_text.strip() in line:
                    # Found the line - get a proportionally located line in replacement
                    replacement_lines = replacement_text.split('\n')
                    if replacement_lines:
                        target_idx = min(i, len(replacement_lines) - 1)
                        return replacement_lines[target_idx]
        
        # If it's a short text that might be a bullet point
        if element_text.strip().startswith('•') or element_text.strip().startswith('-'):
            # Find a bullet point in the replacement text
            replacement_lines = replacement_text.split('\n')
            for line in replacement_lines:
                if line.strip().startswith('•') or line.strip().startswith('-'):
                    return line
        
        # If it's a short piece of text, try word-level replacement
        if len(element_text.strip().split()) <= 5:
            # It might be a date, company name, job title, etc.
            # Try to preserve the format
            
            # Is it a date?
            if re.search(r'\d{4}', element_text):
                # Look for dates in the replacement text
                date_match = re.search(r'\d{4}', replacement_text)
                if date_match:
                    return element_text  # Keep original dates for now
            
            # Is it a header?
            if element_text.isupper() or element_text.strip().endswith(':'):
                # Look for similar headers in replacement
                for line in replacement_text.split('\n'):
                    if line.isupper() or line.strip().endswith(':'):
                        return line
        
        # Default: keep the original text
        return element_text
