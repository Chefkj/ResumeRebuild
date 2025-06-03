"""
OCR-based Section Extractor for Resume PDFs

This module provides a section extraction approach that uses
Tesseract OCR to better extract text from PDFs, particularly
when section headers are embedded in text.
"""

import os
import re
import logging
import fitz  # PyMuPDF
from src.utils.simple_section_extractor import SimpleSectionExtractor
from src.utils.pdf_extractor import PDFExtractor
from src.utils.ocr_text_extraction import OCRTextExtractor

logger = logging.getLogger(__name__)

class OCRSectionExtractor(SimpleSectionExtractor):
    """
    Section extractor that uses OCR for better text extraction from PDFs,
    particularly when section headers are embedded in text.
    """
    
    def __init__(self):
        """Initialize the OCR-based section extractor."""
        super().__init__()  # Initialize the parent SimpleSectionExtractor
        self.pdf_extractor = PDFExtractor()  # Initialize PDF extractor for OCR
        self.ocr_extractor = OCRTextExtractor()  # Initialize the specialized OCR text extractor
        self._format_info = None  # Initialize format info to avoid attribute error
    
    def extract_sections(self, pdf_path):
        """
        Extract sections using OCR for better text extraction,
        then apply the probabilistic approach from SimpleSectionExtractor.
        
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
            
            # Score each line for being a potential section header
            line_scores = self._score_lines(doc, lines)
            
            # Find section boundaries
            section_boundaries = self._find_section_boundaries(lines, line_scores)
            
            # Extract sections
            sections = self._extract_sections_from_boundaries(lines, section_boundaries)
            
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
    
    def _process_ocr_text(self, ocr_text):
        """
        Process OCR-extracted text to identify and extract sections.
        
        Args:
            ocr_text: Text extracted via OCR
            
        Returns:
            dict: Dictionary of extracted sections
        """
        # Use the same scoring approach as SimpleSectionExtractor
        # but with OCR-preprocessed text that better preserves section headers
        
        # Split text into lines
        lines = ocr_text.split('\n')
        
        # Score each line for being a potential section header
        line_scores = self._score_lines_from_text(lines)
        
        # Identify likely section boundaries based on scores
        section_boundaries = self._find_section_boundaries(lines, line_scores)
        
        # Extract and classify sections
        sections = self._extract_sections_from_boundaries(lines, section_boundaries)
        
        return sections
        
    def _score_lines_from_text(self, lines):
        """
        Score each line on how likely it is to be a section header,
        adapted to work with OCR-extracted text.
        
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
                
            scores.append(score)
        
        return scores
