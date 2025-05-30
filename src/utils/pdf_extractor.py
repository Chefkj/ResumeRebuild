"""
PDF Extractor module for extracting text and structure from PDF resumes.
Uses a combination of PyPDF2 and pdfminer.six for more accurate extraction.
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
        
        # Try with external tools if available
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
        
        # Try using PyMuPDF (fitz) first - it often gives the best results
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            all_text = ""
            for page in doc:
                all_text += page.get_text("text") + "\n\n"
            if all_text.strip():
                print("Using PyMuPDF for extraction - generally best quality")
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
    
    def _combine_extracted_text(self, text_versions):
        """
        Combine and clean multiple extracted text versions.
        Choose the best version or combine them for best results.
        """
        # Filter out empty versions
        valid_versions = [t for t in text_versions if t.strip()]
        
        if not valid_versions:
            return ""
        
        # Choose the version with the most content for now
        # In a more sophisticated version, you could combine them intelligently
        best_version = max(valid_versions, key=len)
        
        # Clean up the text
        cleaned_text = self._clean_text(best_version)
        
        return cleaned_text
    
    def _clean_text(self, text):
        """Clean up extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Fix broken lines
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
        
        # Remove page numbers and headers/footers (simplified)
        lines = text.split('\n')
        filtered_lines = []
        for line in lines:
            # Skip lines that are just page numbers
            if re.match(r'^\s*\d+\s*$', line):
                continue
            # Skip likely header/footer lines (very short lines at page boundaries)
            if len(line.strip()) < 5 and len(filtered_lines) > 0 and filtered_lines[-1] == '':
                continue
            
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _extract_contact_info(self, text, resume):
        """Extract contact information from the text."""
        # Extract name - assume it's one of the first non-empty lines
        lines = [line for line in text.split('\n') if line.strip()]
        name = lines[0].strip() if lines else ""
        
        # Look at a few more lines for a better name candidate (if first line looks like a title)
        if len(lines) > 1 and (len(name) < 5 or name.isupper() or "RESUME" in name.upper()):
            for i in range(1, min(5, len(lines))):
                candidate = lines[i].strip()
                # A name typically has 2+ words and isn't too long
                if 5 <= len(candidate) <= 40 and len(candidate.split()) >= 2:
                    name = candidate
                    break
        
        # Find email using regex - look for standard email patterns
        email_matches = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
        email = email_matches[0] if email_matches else ""
        
        # Find phone using regex - look for various phone formats
        phone_patterns = [
            r'(\+\d{1,2}\s?)?(\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}',  # (123) 456-7890
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 123-456-7890
            r'\+\d{1,2}\s\d{3}\s\d{3}\s\d{4}'  # +1 123 456 7890
        ]
        
        phone = ""
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    # If the match returned groups, combine them
                    phone = ''.join(filter(None, matches[0]))
                else:
                    phone = matches[0]
                break
        
        # Find LinkedIn URL or username
        linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'linkedin\.com/profile/[\w-]+'
        ]
        
        linkedin = ""
        for pattern in linkedin_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                linkedin = matches[0]
                if not linkedin.startswith('http'):
                    linkedin = 'www.' + linkedin
                break
        
        # Try to find address - look for lines that might contain an address
        address_patterns = [
            r'\d+\s+[\w\s]+,\s*[\w\s]+,\s*[A-Z]{2}\s+\d{5}(-\d{4})?',  # 123 Main St, City, ST 12345
            r'[A-Z][a-z]+,\s*[A-Z]{2}\s+\d{5}',  # City, ST 12345
            r'\d+\s+[\w\s]+\s+[A-Za-z]+,\s*[A-Z]{2}'  # 123 Street Name City, ST
        ]
        
        address = ""
        for pattern in address_patterns:
            matches = re.findall(pattern, text)
            if matches:
                address = matches[0]
                break
        
        # Set the contact info
        resume.set_contact_info(name=name, email=email, phone=phone, linkedin=linkedin, address=address)
    
    def _extract_sections(self, text, resume):
        """Extract sections from the text."""
        # Compile all section patterns into a single regex
        section_pattern = '|'.join(f"({pattern})" for pattern in self.section_patterns)
        
        # Find all potential section headers
        headers = list(re.finditer(fr'(?:\n|^)([^\n]*(?:{section_pattern})[^\n]*)\n', text, re.IGNORECASE))
        
        if not headers:
            # If no section headers found, try more aggressive patterns
            headers = list(re.finditer(r'(?:\n|^)([A-Z][A-Z\s]{2,}:?)(?:\n|$)', text))
        
        # If still no headers, look for bold or underlined text that may indicate sections
        if not headers:
            # This would require layout analysis that we've already done, so just add a fallback
            # Look for lines that might be section headers (all caps, short lines)
            potential_headers = re.finditer(r'\n([A-Z][A-Z\s&]{2,})(?:\n|$)', text)
            headers = list(potential_headers)
        
        section_matches = []
        for match in headers:
            section_title = match.group(1).strip()
            start_pos = match.end()
            section_matches.append((section_title, start_pos))
        
        # Extract content for each section
        for i, (title, start_pos) in enumerate(section_matches):
            # Section content goes from start position to the next section or end of text
            end_pos = section_matches[i+1][1] if i < len(section_matches) - 1 else len(text)
            content = text[start_pos:end_pos].strip()
            
            resume.add_section(title, content)
        
        # If no sections found or not enough content extracted, try a different approach
        if not resume.sections or sum(len(s.content) for s in resume.sections) < len(text) * 0.3:
            # Look for potential section boundaries (line breaks followed by capitalized text)
            lines = text.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line looks like a section header
                if re.match(r'^[A-Z][A-Za-z\s]{2,}$', line) and len(line) < 30:
                    # If we have a previous section, add it
                    if current_section:
                        resume.add_section(current_section, '\n'.join(current_content).strip())
                    
                    # Start a new section
                    current_section = line
                    current_content = []
                else:
                    # Add to current section content
                    current_content.append(line)
            
            # Add the last section
            if current_section and current_content:
                resume.add_section(current_section, '\n'.join(current_content).strip())
        
        # If still no sections found, add the whole text as a single section
        if not resume.sections:
            resume.add_section("Resume", text.strip())
        
        return resume
    
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