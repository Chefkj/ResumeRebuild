"""
PDF Extractor module for extracting text and structure from PDF resumes.
Uses a combination of PyPDF2, pdfminer.six, and Tesseract OCR for more accurate extraction.
"""

import io
import re
import os
import tempfile
from pdfminer.high_level import extract_text_to_fp, extract_text
from pdfminer.layout import LAParams, LTTextContainer, LTChar
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from PyPDF2 import PdfReader
import subprocess
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import logging

# Set up logger
logger = logging.getLogger(__name__)

class ResumeSection:
    """Class representing a section of a resume."""
    def __init__(self, title, content):
        self.title = title
        self.content = content
    
    def __str__(self):
        return f"{self.title}\n{'-' * len(self.title)}\n{self.content}\n"

class ResumeContent:
    """Class representing the structured content of a resume."""
    def __init__(self):
        self.contact_info = {}
        self.sections = []
        self.raw_text = ""
    
    def add_section(self, title, content):
        """Add a section to the resume content."""
        self.sections.append(ResumeSection(title, content))
    
    def set_contact_info(self, name="", email="", phone="", address="", linkedin=""):
        """Set contact information."""
        self.contact_info = {
            'name': name,
            'email': email,
            'phone': phone,
            'address': address,
            'linkedin': linkedin
        }
    
    def __str__(self):
        """String representation of the resume content."""
        result = []
        if self.contact_info.get('name'):
            result.append(f"# {self.contact_info['name']}")
            
        contact_line = []
        for k in ['email', 'phone', 'linkedin']:
            if self.contact_info.get(k):
                contact_line.append(self.contact_info[k])
        
        if contact_line:
            result.append(" | ".join(contact_line))
        
        if self.contact_info.get('address'):
            result.append(self.contact_info['address'])
            
        result.append("\n")
        
        for section in self.sections:
            result.append(str(section))
            
        return "\n".join(result)

class PDFExtractor:
    """Class for extracting content from PDF resumes."""
    
    def __init__(self):
        self.section_patterns = [
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
    
    def extract(self, pdf_path):
        """
        Extract content from a PDF resume using multiple methods for better accuracy.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ResumeContent object containing the structured resume content
        """
        # Extract text using multiple methods for better accuracy
        raw_text1 = self._extract_with_pdfminer(pdf_path)
        raw_text2 = self._extract_with_pypdf2(pdf_path)
        raw_text3 = self._extract_with_layout_analysis(pdf_path)
        
        # Try with external tools if available (including Tesseract OCR)
        raw_text4 = ""
        try:
            raw_text4 = self._extract_with_external_tools(pdf_path)
        except:
            pass
        
        # Combine and clean extracted text
        raw_text = self._combine_extracted_text([raw_text1, raw_text2, raw_text3, raw_text4])
        
        # Create resume content object
        resume = ResumeContent()
        resume.raw_text = raw_text
        
        # Extract contact information
        self._extract_contact_info(raw_text, resume)
        
        # Extract sections
        self._extract_sections(raw_text, resume)
        
        # Apply LLM refinement if available
        try:
            from utils.llm_refiner import LLMRefiner
            refiner = LLMRefiner()
            resume = refiner.refine_resume(resume)
        except ImportError:
            print("LLM refinement not available. Using raw extraction.")
        except Exception as e:
            print(f"Error during LLM refinement: {str(e)}. Using raw extraction.")
        
        return resume
    
    def _extract_with_pdfminer(self, pdf_path):
        """Extract text using PDFMiner."""
        output = io.StringIO()
        with open(pdf_path, 'rb') as pdf_file:
            extract_text_to_fp(pdf_file, output, laparams=LAParams())
        
        return output.getvalue()
    
    def _extract_with_pypdf2(self, pdf_path):
        """Extract text using PyPDF2."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf = PdfReader(file)
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"PyPDF2 extraction error: {e}")
        return text
    
    def _extract_with_layout_analysis(self, pdf_path):
        """Extract text with more layout awareness."""
        text = ""
        try:
            # Set up PDFMiner tools
            rsrcmgr = PDFResourceManager()
            laparams = LAParams()
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            
            with open(pdf_path, 'rb') as fp:
                for page in PDFPage.get_pages(fp):
                    interpreter.process_page(page)
                    layout = device.get_result()
                    
                    # Sort text elements by their position to respect the layout
                    text_elements = []
                    for elem in layout:
                        if isinstance(elem, LTTextContainer):
                            # Get position and text
                            x, y = elem.bbox[0], -elem.bbox[1]  # Negate y for top-down sorting
                            text_elements.append((y, x, elem.get_text()))
                    
                    # Sort by y position first (line), then by x position (column)
                    text_elements.sort()
                    
                    # Combine text respecting the layout
                    current_y = None
                    line_text = ""
                    for y, x, txt in text_elements:
                        if current_y is None:
                            current_y = y
                        
                        # If this is a new line
                        if abs(y - current_y) > 5:  # Threshold for a new line
                            text += line_text + "\n"
                            line_text = txt
                            current_y = y
                        else:
                            # Check if this is a continuation or a new column
                            if x - len(line_text)*5 > 10:  # Rough estimate for spacing
                                line_text += "    " + txt  # Add spacing for columns
                            else:
                                line_text += txt
                    
                    text += line_text + "\n"
        except Exception as e:
            print(f"Layout extraction error: {e}")
        
        return text
    
    def _extract_with_external_tools(self, pdf_path):
        """Try extraction with external tools if available (like pdf2text)."""
        text = ""
        
        # First try the OCR method - it often gives the best results for headers
        try:
            ocr_text = self._extract_with_tesseract_ocr(pdf_path)
            if ocr_text and len(ocr_text.strip()) > 100:
                # If OCR returned substantial text, use it
                print("Using Tesseract OCR for extraction - best for section headers")
                return ocr_text
        except Exception as e:
            print(f"Tesseract OCR extraction error: {e}, falling back to other methods")
        
        # Try using PyMuPDF (fitz) next if OCR failed
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            all_text = ""
            for page in doc:
                all_text += page.get_text("text") + "\n\n"
            if all_text.strip():
                print("Using PyMuPDF for extraction - generally good quality")
                return all_text
        except ImportError:
            print("PyMuPDF not available, trying other methods")
        except Exception as e:
            print(f"Error using PyMuPDF: {e}, trying other methods")
                
        # Create a temporary file for output
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
            
            # Try using pdftotext from poppler-utils if available
            try:
                # Check if pdftotext is installed and available in PATH
                which_cmd = 'which' if os.name != 'nt' else 'where'
                which_pdftotext = subprocess.run(
                    [which_cmd, 'pdftotext'],
                    capture_output=True, text=True
                )
                
                if which_pdftotext.returncode == 0:
                    # pdftotext is available
                    pdftotext_path = which_pdftotext.stdout.strip()
                    result = subprocess.run([pdftotext_path, pdf_path, tmp_path], capture_output=True)
                    
                    if result.returncode == 0:
                        with open(tmp_path, 'r', encoding='utf-8', errors='replace') as f:
                            text = f.read()
                        
                        # Clean up
                        os.remove(tmp_path)
                        print("Using pdftotext for extraction - good quality")
                        return text
                    else:
                        # pdftotext failed, use fallback method
                        print(f"pdftotext failed with error code {result.returncode}, falling back to other methods")
                        print(f"Error output: {result.stderr.decode('utf-8', errors='replace') if result.stderr else 'None'}")
                else:
                    # pdftotext is not available, use fallback
                    print("pdftotext not found in PATH. To install it on macOS, run: brew install poppler")
                    print("On Ubuntu/Debian: sudo apt-get install poppler-utils")
                    print("Falling back to other methods")
            except Exception as e:
                # Log the error but continue with alternative extraction method
                print(f"External tool extraction error: {e}, falling back to PyPDF2")
            
            # Fallback to PyPDF2
            print("Falling back to PyPDF2 for extraction")
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            # Try PDFMiner.six as a last resort if PyPDF2 didn't extract much
            if len(text.strip()) < 100:  # If PyPDF2 extracted very little text
                print("PyPDF2 extracted very little text, trying PDFMiner")
                try:
                    text = extract_text(pdf_path)
                    if len(text.strip()) > 0:
                        print("Using PDFMiner for extraction - last resort")
                except Exception as e:
                    print(f"PDFMiner extraction error: {e}")
                    # Stay with PyPDF2 result
        except Exception as e:
            print(f"PDF extraction error: {e}")
        
        # Clean up temporary file if it was created
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except:
            pass
            
        return text
        
    def _extract_with_tesseract_ocr(self, pdf_path):
        """
        Extract text from PDF using Tesseract OCR for better header recognition.
        
        This method converts PDF pages to images and uses OCR to extract text.
        It's particularly effective for detecting section headers in resumes
        that may be embedded within text without proper line breaks.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text with proper section header separation
        """
        try:
            # Check if Tesseract is installed and available
            try:
                pytesseract.get_tesseract_version()
                logger.info("Tesseract OCR is available.")
            except Exception as e:
                logger.warning(f"Tesseract OCR is not properly installed: {e}")
                return ""
                
            # Convert PDF to images
            logger.info(f"Converting PDF to images: {pdf_path}")
            images = convert_from_path(pdf_path, dpi=300)  # Higher DPI for better quality
            
            if not images:
                logger.warning("No images extracted from PDF")
                return ""
                
            logger.info(f"Successfully converted {len(images)} pages to images")
            
            # Process each page with OCR
            all_text = []
            
            # OCR Configuration for better section header detection
            custom_config = r'--oem 3 --psm 6 -l eng'  # Page segmentation mode 6: Assume a single uniform block of text
            
            for i, img in enumerate(images):
                logger.info(f"Processing page {i+1} with OCR")
                
                # Apply preprocessing to enhance text readability if needed
                # img = self._preprocess_image_for_ocr(img)  # Uncomment if needed
                
                # Extract text using Tesseract
                page_text = pytesseract.image_to_string(img, config=custom_config)
                
                # Post-process the extracted text
                processed_text = self._post_process_ocr_text(page_text)
                
                all_text.append(processed_text)
            
            combined_text = "\n\n".join(all_text)
            
            # Apply specialized section header detection
            result = self._enhance_section_headers(combined_text)
            
            logger.info("OCR extraction completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error during OCR extraction: {str(e)}")
            return ""
            
    def _post_process_ocr_text(self, text):
        """
        Post-process OCR-extracted text to correct common OCR issues.
        
        Args:
            text: OCR-extracted text
            
        Returns:
            str: Corrected text
        """
        if not text:
            return ""
            
        # Remove excessive whitespace while preserving paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)  # Replace multiple spaces/tabs with a single space
            
        # Handle common resume section headers more aggressively
        header_patterns = {
            'SUMMARY': ['SUMMARY', 'PROFESSIONAL SUMMARY', 'CAREER SUMMARY', 'OBJECTIVE', 'PROFILE'],
            'EXPERIENCE': ['EXPERIENCE', 'WORK EXPERIENCE', 'EMPLOYMENT HISTORY', 'WORK HISTORY', 'PROFESSIONAL EXPERIENCE'],
            'EDUCATION': ['EDUCATION', 'ACADEMIC BACKGROUND', 'EDUCATIONAL BACKGROUND', 'ACADEMIC QUALIFICATIONS'],
            'SKILLS': ['SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'EXPERTISE', 'KEY SKILLS'],
            'PROJECTS': ['PROJECTS', 'PROJECT EXPERIENCE', 'KEY PROJECTS', 'RELEVANT PROJECTS'],
            'CERTIFICATIONS': ['CERTIFICATIONS', 'CERTIFICATES', 'PROFESSIONAL CERTIFICATIONS', 'CREDENTIALS'],
            'AWARDS': ['AWARDS', 'HONORS', 'ACHIEVEMENTS', 'RECOGNITIONS'],
            'PUBLICATIONS': ['PUBLICATIONS', 'PAPERS', 'RESEARCH', 'ARTICLES'],
            'LANGUAGES': ['LANGUAGES', 'LANGUAGE SKILLS', 'LANGUAGE PROFICIENCY'],
            'INTERESTS': ['INTERESTS', 'HOBBIES', 'ACTIVITIES', 'PERSONAL INTERESTS'],
            'REFERENCES': ['REFERENCES', 'RECOMMENDATIONS', 'PROFESSIONAL REFERENCES']
        }
        
        # First, normalize the text to help with pattern matching
        for standardized, variations in header_patterns.items():
            for variation in variations:
                # Replace variations with standardized header name, add proper spacing
                # Pattern covers: headers stuck to text before or after them
                pattern = fr'([a-z])({variation})([A-Z]|[a-z])'
                text = re.sub(pattern, fr'\1\n\n{standardized}\n\n\3', text, flags=re.IGNORECASE)
                
                # Pattern for headers at start of line with text immediately after
                pattern = fr'^({variation})([A-Z]|[a-z])'
                text = re.sub(pattern, fr'{standardized}\n\n\2', text, flags=re.IGNORECASE)
                
                # Pattern for headers in the middle of text
                pattern = fr'([.!?])(\s+)({variation})(\s+)'
                text = re.sub(pattern, fr'\1\2\n\n{standardized}\n\n', text, flags=re.IGNORECASE)
                
                # Standalone headers - ensure they have proper newlines before/after
                pattern = fr'(\n|\s)({variation})(\n|\s|:|$)'
                text = re.sub(pattern, fr'\n\n{standardized}\n\n', text, flags=re.IGNORECASE)
                
        # Fix bullet points to ensure they're on new lines
        text = re.sub(r'([^\n])(\s*[•\-\*])(\s)', r'\1\n\2\3', text)
        
        # Clean up excessive newlines and normalize to double newlines between sections
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Ensure no orphaned single newlines (make them double or remove)
        lines = text.split('\n')
        processed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip entirely empty lines
            if not line:
                i += 1
                continue
                
            processed_lines.append(line)
            
            # Check for section headers to ensure proper spacing
            is_header = False
            for header_list in header_patterns.values():
                if any(re.match(fr'^{re.escape(h)}$', line, re.IGNORECASE) for h in header_list):
                    is_header = True
                    break
                    
            if is_header and i < len(lines) - 1:
                # Add an empty line after headers if not already present
                processed_lines.append('')
                
            i += 1
            
        return '\n'.join(processed_lines)
        
    def _enhance_section_headers(self, text):
        """
        Enhance section headers in the extracted text to ensure they're properly separated.
        
        Args:
            text: Extracted text
            
        Returns:
            str: Text with enhanced section headers
        """
        if not text:
            return ""
            
        lines = text.split('\n')
        processed_lines = []
        
        # Common resume section headers (case insensitive)
        header_patterns = [
            r'^.*\b(EDUCATION|ACADEMIC)\b.*$',
            r'^.*\b(EXPERIENCE|EMPLOYMENT|WORK\s+HISTORY)\b.*$',
            r'^.*\b(SKILLS|TECHNICAL\s+SKILLS|EXPERTISE)\b.*$', 
            r'^.*\b(SUMMARY|PROFILE|OBJECTIVE)\b.*$',
            r'^.*\b(PROJECTS|PROJECT\s+EXPERIENCE)\b.*$',
            r'^.*\b(CERTIFICATIONS|CERTIFICATES|CREDENTIALS)\b.*$',
            r'^.*\b(AWARDS|HONORS|ACHIEVEMENTS)\b.*$',
            r'^.*\b(PUBLICATIONS|RESEARCH|PAPERS)\b.*$',
            r'^.*\b(VOLUNTEER|COMMUNITY\s+SERVICE)\b.*$',
            r'^.*\b(LANGUAGES|LANGUAGE\s+PROFICIENCY)\b.*$',
            r'^.*\b(INTERESTS|HOBBIES|ACTIVITIES)\b.*$',
            r'^.*\b(REFERENCES|RECOMMENDATIONS)\b.*$'
        ]
        
        for i, line in enumerate(lines):
            line_added = False
            
            # Check if line matches a section header pattern
            for pattern in header_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # If previous line wasn't empty, add an empty line before header
                    if processed_lines and processed_lines[-1].strip():
                        processed_lines.append('')
                    
                    # Add the header line
                    processed_lines.append(line.strip())
                    
                    # Add empty line after header if next line isn't empty
                    if i+1 < len(lines) and lines[i+1].strip():
                        processed_lines.append('')
                        
                    line_added = True
                    break
            
            if not line_added:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _combine_extracted_text(self, texts):
        """
        Combine text extracted using different methods, prioritizing higher quality extractions.
        
        Args:
            texts: List of extracted texts from different methods
            
        Returns:
            str: Combined text
        """
        # Filter out empty texts
        texts = [t for t in texts if t and len(t.strip()) > 0]
        
        if not texts:
            return ""
            
        # Use OCR text if available (usually the best for section headers)
        if texts[3] and len(texts[3]) > 200:  # text4 is from Tesseract OCR
            return texts[3]
        
        # Compare extraction quality of the different methods
        # Simple heuristic: longer content and more line breaks often means better extraction
        scores = []
        
        for text in texts:
            # Calculate score based on:
            # 1. Length of text (after normalization)
            # 2. Number of proper newlines (indicating paragraph breaks)
            # 3. Presence of section header keywords
            
            score = 0
            
            # Score for length (normalized to avoid extremely long garbage text)
            score += min(len(text) / 1000, 10)  # Cap at 10 points
            
            # Score for proper newlines and paragraphs (indicating structure)
            paragraphs = text.split('\n\n')
            score += min(len(paragraphs) / 5, 5)  # Cap at 5 points
            
            # Score for section headers (common in resumes)
            section_headers = [
                'education', 'experience', 'skills', 'summary', 'profile',
                'certifications', 'projects', 'publications'
            ]
            
            for header in section_headers:
                if re.search(r'\b' + header + r'\b', text.lower()):
                    score += 1
            
            scores.append(score)
        
        # Use the text with the highest score
        best_idx = scores.index(max(scores))
        return texts[best_idx]
    
    def install_pdftotext_guide():
        """
        Returns installation instructions for pdftotext based on the user's platform.
        """
        import platform
        
        system = platform.system()
        
        if system == 'Darwin':  # macOS
            return (
                "To install pdftotext on macOS, use Homebrew:\n\n"
                "1. If you don't have Homebrew installed, run:\n"
                "   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n\n"
                "2. Then install poppler:\n"
                "   brew install poppler\n\n"
                "3. Restart the application after installation."
            )
        elif system == 'Windows':
            return (
                "To install pdftotext on Windows:\n\n"
                "1. Download the latest poppler release for Windows from:\n"
                "   https://github.com/oschwartz10612/poppler-windows/releases/\n\n"
                "2. Extract the ZIP file and add the 'bin' directory to your PATH environment variable.\n\n"
                "3. Restart your computer after installation."
            )
        else:  # Linux
            return (
                "To install pdftotext on Linux:\n\n"
                "For Ubuntu/Debian:\n"
                "   sudo apt-get update && sudo apt-get install -y poppler-utils\n\n"
                "For Fedora:\n"
                "   sudo dnf install poppler-utils\n\n"
                "For Arch Linux:\n"
                "   sudo pacman -S poppler\n\n"
                "Restart the application after installation."
            )
    
    def _extract_contact_info(self, text, resume):
        """Extract contact information from the resume text."""
        # Extract email addresses
        email_pattern = r'[\w.+-]+@[\w-]+\.[\w.-]+'
        emails = re.findall(email_pattern, text)
        
        # Extract phone numbers
        phone_pattern = r'(\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
        phones = re.findall(phone_pattern, text)
        
        # Extract LinkedIn URLs
        linkedin_pattern = r'(linkedin\.com/in/[^\s]+)'
        linkedin = re.findall(linkedin_pattern, text, re.IGNORECASE)
        
        # Simple name extraction - look for lines with just names at the beginning
        lines = text.split('\n')
        name = ""
        for i in range(min(5, len(lines))):  # Check first 5 lines
            line = lines[i].strip()
            # Names are usually short, all letters, no numbers
            if len(line) > 0 and len(line.split()) <= 4 and not re.search(r'\d', line):
                name = line
                break
        
        # Set the contact info
        resume.set_contact_info(
            name=name,
            email=emails[0] if emails else "",
            phone=phones[0] if phones else "",
            linkedin=linkedin[0] if linkedin else ""
        )
    
    def _extract_sections(self, text, resume):
        """Extract sections from the resume text."""
        # Simple section extraction based on regex patterns
        section_text = text
        
        # Try to find sections based on common patterns
        for pattern in self.section_patterns:
            # Look for the pattern in the text
            matches = list(re.finditer(rf'\b({pattern})\b', section_text, re.IGNORECASE))
            
            # Process each match
            for i, match in enumerate(matches):
                section_name = match.group(1).upper()
                
                # Determine the start of the section content
                start = match.end()
                
                # Determine the end of the section content (next section or end of text)
                if i < len(matches) - 1:
                    end = matches[i+1].start()
                else:
                    end = len(section_text)
                
                # Extract the section content
                section_content = section_text[start:end].strip()
                
                # Add the section to the resume
                if section_content and len(section_content) > 10:  # Minimum content length
                    resume.add_section(section_name, section_content)