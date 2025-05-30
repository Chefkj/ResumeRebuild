"""
PDF Content Replacement Handler for Resume Rebuilder.

This module integrates all PDF extraction, content refinement, and reconstruction
capabilities to enable replacing resume content while preserving the original layout.
"""

import os
import re
import logging
import tempfile
from typing import Dict, List, Optional, Union

# Import our PDF handling modules with fallback for different contexts
try:
    from src.utils.pdf_replacer import PDFReplacer
    from src.utils.pdf_replacer_enhanced import EnhancedPDFReplacer
    from src.utils.pdf_direct_replacer import PDFDirectReplacer
    from src.utils.section_classifier import SectionClassifier
    from src.utils.pdf_extractor import PDFExtractor, ResumeContent, ResumeSection
    from src.utils.section_extractor import SectionExtractor
except ImportError:
    from utils.pdf_replacer import PDFReplacer
    from utils.pdf_replacer_enhanced import EnhancedPDFReplacer
    from utils.pdf_direct_replacer import PDFDirectReplacer
    from utils.section_classifier import SectionClassifier
    from utils.pdf_extractor import PDFExtractor, ResumeContent, ResumeSection
    from utils.section_extractor import SectionExtractor

# LLM integration
try:
    try:
        from src.utils.llm_refiner import LLMRefiner
    except ImportError:
        from utils.llm_refiner import LLMRefiner
    HAS_LLM = True
except ImportError:
    HAS_LLM = False

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFContentReplacer:
    """
    Central handler for PDF content replacement functionality.
    
    Combines PDF extraction, content improvement, and reconstruction to enable
    replacing resume content while preserving the original layout.
    """
    
    def __init__(self, use_enhanced=True, use_llm=True, use_ocr=False, use_direct=True):
        """
        Initialize the PDF content replacer.
        
        Args:
            use_enhanced: Whether to use the enhanced PDF replacer with better formatting
            use_llm: Whether to use LLM for content refinement
            use_ocr: Whether to use OCR for text extraction (requires external tools)
            use_direct: Whether to use direct PDF manipulation (preferred method)
        """
        self.use_enhanced = use_enhanced
        self.use_llm = use_llm and HAS_LLM
        self.use_ocr = use_ocr
        self.use_direct = use_direct
        
        # Initialize components
        if use_direct:
            # Prefer direct PDF manipulation when available
            try:
                self.pdf_replacer = PDFDirectReplacer()
                logger.info("Using direct PDF manipulation for content replacement")
            except Exception as e:
                logger.warning(f"Direct PDF manipulation not available: {e}. Falling back to enhanced replacer.")
                self.use_direct = False
                self.pdf_replacer = EnhancedPDFReplacer(use_ocr=use_ocr)
        elif use_enhanced:
            self.pdf_replacer = EnhancedPDFReplacer(use_ocr=use_ocr)
        else:
            self.pdf_replacer = PDFReplacer()
        
        self.pdf_extractor = PDFExtractor()
        self.section_classifier = SectionClassifier()
        
        if self.use_llm:
            try:
                self.llm_refiner = LLMRefiner()
            except Exception as e:
                logger.warning(f"Failed to initialize LLM refiner: {e}")
                self.use_llm = False
    
    def analyze_resume(self, pdf_path):
        """
        Analyze a resume PDF to extract structure and content.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with analysis results including sections and structure
        """
        # Extract formatted content
        document = self.pdf_replacer.extract_formatted_pdf(pdf_path)
        
        # Extract plaintext content using the regular extractor
        basic_resume = self.pdf_extractor.extract(pdf_path)
        
        # Classify sections
        section_classifications = self.section_classifier.classify_sections_in_document(document.sections)
        
        # Analyze structure
        structure_analysis = self.section_classifier.analyze_resume_structure(document.sections)
        
        return {
            'formatted_document': document,
            'basic_resume': basic_resume,
            'section_classifications': section_classifications,
            'structure_analysis': structure_analysis,
        }
    
    def improve_resume(self, pdf_path, job_description=None, output_path=None):
        """
        Improve a resume PDF while preserving its layout.
        
        Args:
            pdf_path: Path to the original resume PDF
            job_description: Optional job description to tailor the resume for
            output_path: Path for the output PDF (default: new_resume.pdf)
            
        Returns:
            Path to the improved resume PDF
        """
        if output_path is None:
            output_path = os.path.join(os.path.dirname(pdf_path), 'new_resume.pdf')
        
        # If we have the direct replacer and a job description, use the optimized approach
        if self.use_direct and isinstance(self.pdf_replacer, PDFDirectReplacer) and job_description:
            try:
                # Use direct PDF manipulation with LLM integration
                return self.pdf_replacer.rebuild_resume_with_llm(
                    pdf_path, 
                    job_description, 
                    output_path
                )
            except Exception as e:
                logger.error(f"Direct PDF replacement failed: {e}. Falling back to standard approach.")
        
        # Fall back to standard approach if direct replacement isn't available
        
        # Step 1: Analyze the resume to extract structure and content
        analysis = self.analyze_resume(pdf_path)
        document = analysis['formatted_document']
        basic_resume = analysis['basic_resume']
        
        # Step 2: Generate improved content for each section
        improved_sections = {}
        
        if self.use_llm:
            # Try using LLM to improve the content
            try:
                improved_resume = self.llm_refiner.refine_resume(basic_resume, job_description)
                
                # Check if the improved resume is different from the original
                is_improved = False
                
                # Extract sections from improved content
                for section in document.sections:
                    section_name = section.name
                    section_content = section.get_text()
                    
                    # Store original header if available
                    original_header = section_name
                    if hasattr(section, 'original_header') and section.original_header:
                        original_header = section.original_header
                    
                    # Find matching section in the improved resume
                    for improved_section in improved_resume.sections:
                        if self._section_names_match(section_name, improved_section.title):
                            # Only use improved content if it's actually different
                            if improved_section.content != section_content and improved_section.content.strip():
                                # Preserve original header format if possible
                                if original_header and original_header != section_name:
                                    # Replace the section title in the improved content with the original header
                                    if improved_section.content.startswith(improved_section.title):
                                        improved_content = improved_section.content.replace(
                                            improved_section.title, original_header, 1
                                        )
                                    else:
                                        improved_content = f"{original_header}\n{improved_section.content}"
                                    improved_sections[section_name] = improved_content
                                else:
                                    improved_sections[section_name] = improved_section.content
                                is_improved = True
                            else:
                                # If content is the same, use original
                                improved_sections[section_name] = section_content
                            break
                    else:
                        # No matching section found, use original content
                        improved_sections[section_name] = section_content
                        
                # Also check for new sections in the improved resume that don't exist in original
                for improved_section in improved_resume.sections:
                    if improved_section.title.startswith("NEW_SECTION_"):
                        # This is a newly generated section, add it with a modified name
                        actual_title = improved_section.title.replace("NEW_SECTION_", "")
                        improved_sections[actual_title] = improved_section.content
                        is_improved = True
                        logger.info(f"Added new section '{actual_title}' generated by LLM")
                        
                # If nothing was actually improved, log a warning
                if not is_improved:
                    logger.warning("LLM did not make any meaningful changes to the resume content.")
                    
            except Exception as e:
                logger.error(f"Error during LLM refinement: {e}")
                # Fall back to using original content if LLM improvement fails
                for section in document.sections:
                    improved_sections[section.name] = section.get_text()
        else:
            # Without LLM, we don't modify the content
            logger.info("LLM refinement not available, using original content.")
            for section in document.sections:
                improved_sections[section.name] = section.get_text()
        
        # Step 3: Replace content in the PDF while preserving layout
        if self.use_direct and isinstance(self.pdf_replacer, PDFDirectReplacer):
            # Convert section names to section types
            section_types = {}
            for section_name, content in improved_sections.items():
                section_type, _ = self.section_classifier.classify_section(section_name, content)
                section_types[section_type] = content
            
            output_path = self.pdf_replacer.replace_content_direct(
                pdf_path,
                section_replacements=section_types,
                output_path=output_path
            )
        else:
            output_path = self.pdf_replacer.replace_content(
                pdf_path,
                section_replacements=improved_sections,
                output_path=output_path
            )
        
        return output_path
    
    def extract_content(self, pdf_path):
        """
        Extract content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            The extracted content as a data structure
        """
        try:
            # Extract formatted content - use the appropriate method based on the replacer type
            if isinstance(self.pdf_replacer, PDFDirectReplacer):
                document = self.pdf_replacer.extract_document_structure(pdf_path)
                # Direct replacer already includes classified sections
                section_classifications = document.get('classified_sections', {})
            else:
                document = self.pdf_replacer.extract_formatted_pdf(pdf_path)
                # Classify sections for other replacers
                section_classifications = self.section_classifier.classify_sections_in_document(document.sections)
            
            # Extract plaintext content using the regular extractor
            basic_resume = self.pdf_extractor.extract(pdf_path)
            
            # Create a complete content object
            content = {
                'formatted_document': document,
                'basic_resume': basic_resume,
                'section_classifications': section_classifications,
                'pdf_path': pdf_path
            }
            
            return content
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            raise
    
    def replace_content(self, input_path, output_path=None, job_description=None):
        """
        Replace content in a PDF while preserving the layout.
        
        Args:
            input_path: Path to the input PDF
            output_path: Path for the output PDF (default: new_resume.pdf)
            job_description: Optional job description to tailor the resume for
            
        Returns:
            Path to the modified PDF
        """
        # This is just a wrapper around improve_resume
        return self.improve_resume(input_path, job_description, output_path)
    
    def replace_content_with_data(self, input_path, output_path, content, job_description=None):
        """
        Replace content in a PDF using pre-loaded content data.
        
        Args:
            input_path: Path to the input PDF
            output_path: Path for the output PDF
            content: Pre-loaded content data from extract_content()
            job_description: Optional job description to tailor the resume for
            
        Returns:
            Path to the modified PDF
        """
        if output_path is None:
            output_path = os.path.join(os.path.dirname(input_path), 'new_resume.pdf')
        
        # If we have the direct replacer and a job description, use the optimized approach
        if self.use_direct and isinstance(self.pdf_replacer, PDFDirectReplacer) and job_description:
            try:
                # Use direct PDF manipulation with LLM integration
                return self.pdf_replacer.rebuild_resume_with_llm(
                    input_path, 
                    job_description, 
                    output_path
                )
            except Exception as e:
                logger.error(f"Direct PDF replacement failed: {e}. Falling back to standard approach.")
        
        # Use the pre-loaded content
        document = content.get('formatted_document')
        basic_resume = content.get('basic_resume')
        
        # Generate improved content for each section
        improved_sections = {}
        
        if self.use_llm:
            # Try using LLM to improve the content
            try:
                improved_resume = self.llm_refiner.refine_resume(basic_resume, job_description)
                
                # Check if the improved resume is different from the original
                is_improved = False
                
                # Handle PDFDirectReplacer vs. other replacers differently
                if isinstance(self.pdf_replacer, PDFDirectReplacer):
                    # For PDFDirectReplacer, document is a dict with sections list
                    for section in document.get('sections', []):
                        section_name = section.get('name', '')
                        section_text = section.get('text', '')
                        
                        # Find matching section in the improved resume
                        for improved_section in improved_resume.sections:
                            if self._section_names_match(section_name, improved_section.title):
                                # Only use improved content if it's actually different
                                if improved_section.content != section_text and improved_section.content.strip():
                                    improved_sections[section_name] = improved_section.content
                                    is_improved = True
                                else:
                                    # If content is the same, use original
                                    improved_sections[section_name] = section_text
                                break
                        else:
                            # No matching section found, use original content
                            improved_sections[section_name] = section_text
                else:
                    # For other replacers, document has section objects with name and text attributes
                    for section in document.sections:
                        section_name = section.name
                        section_content = section.get_text()
                        
                        # Find matching section in the improved resume
                        for improved_section in improved_resume.sections:
                            if self._section_names_match(section_name, improved_section.title):
                                # Only use improved content if it's actually different
                                if improved_section.content != section_content and improved_section.content.strip():
                                    improved_sections[section_name] = improved_section.content
                                    is_improved = True
                                else:
                                    # If content is the same, use original
                                    improved_sections[section_name] = section_content
                                break
                        else:
                            # No matching section found, use original content
                            improved_sections[section_name] = section_content
                    
                # If nothing was actually improved, log a warning
                if not is_improved:
                    logger.warning("LLM did not make any meaningful changes to the resume content.")
                    
            except Exception as e:
                logger.error(f"Error during LLM refinement: {e}")
                # Fall back to using original content if LLM improvement fails
                if isinstance(self.pdf_replacer, PDFDirectReplacer):
                    for section in document.get('sections', []):
                        section_name = section.get('name', '')
                        section_text = section.get('text', '')
                        improved_sections[section_name] = section_text
                else:
                    for section in document.sections:
                        improved_sections[section.name] = section.get_text()
        else:
            # Without LLM, we don't modify the content
            logger.info("LLM refinement not available, using original content.")
            if isinstance(self.pdf_replacer, PDFDirectReplacer):
                for section in document.get('sections', []):
                    section_name = section.get('name', '')
                    section_text = section.get('text', '')
                    improved_sections[section_name] = section_text
            else:
                for section in document.sections:
                    improved_sections[section.name] = section.get_text()
        
        # Replace content in the PDF while preserving layout
        if self.use_direct and isinstance(self.pdf_replacer, PDFDirectReplacer):
            # Convert section names to section types
            section_types = {}
            for section_name, section_content in improved_sections.items():
                section_type, _ = self.section_classifier.classify_section(section_name, section_content)
                section_types[section_type] = section_content
            
            output_path = self.pdf_replacer.replace_content_direct(
                input_path,
                section_replacements=section_types,
                output_path=output_path
            )
        else:
            output_path = self.pdf_replacer.replace_content(
                input_path,
                section_replacements=improved_sections,
                output_path=output_path
            )
        
        return output_path
        
    def analyze_structure(self, pdf_path):
        """
        Analyze the structure of a PDF resume without modifying it.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with analysis results including sections and structure
        """
        # First try using the specialized SectionExtractor for more robust section detection
        try:
            section_extractor = SectionExtractor()
            extracted_sections = section_extractor.extract_sections(pdf_path)
            
            if extracted_sections and len(extracted_sections) > 1:
                logger.info(f"Successfully extracted {len(extracted_sections)} sections using SectionExtractor")
                
                # Get page count and other metadata using PyMuPDF
                import fitz
                doc = fitz.open(pdf_path)
                page_count = len(doc)
                text_block_count = sum(len(page.get_text("dict").get("blocks", [])) for page in doc)
                format_type = "Standard"
                
                # Build comprehensive structure analysis with extracted sections
                return {
                    'sections': extracted_sections,
                    'page_count': page_count,
                    'text_block_count': text_block_count,
                    'format_type': format_type
                }
            else:
                logger.info("SectionExtractor didn't find enough sections, falling back to standard approach")
        except Exception as e:
            logger.warning(f"Error using SectionExtractor: {e}, falling back to standard approach")
            
        # Fall back to standard approach
        # Extract formatted content - use the appropriate method based on the replacer type
        if isinstance(self.pdf_replacer, PDFDirectReplacer):
            document = self.pdf_replacer.extract_document_structure(pdf_path)
            # Direct replacer already includes classified sections
            section_classifications = document.get('classified_sections', {})
            
            # Fix for when no sections are detected
            if not section_classifications or len(section_classifications) <= 1:
                logger.warning("No or few sections detected in PDF. Using enhanced section detection.")
                try:
                    # Use PyMuPDF directly for better section detection
                    import fitz
                    doc = fitz.open(pdf_path)
                    
                    # Extract full text
                    full_text = ""
                    for page in doc:
                        full_text += page.get_text("text") + "\n"
                    
                    # Try to identify sections based on common section headers with expanded patterns
                    section_patterns = [
                        # Education patterns - now more flexible with word boundaries and special characters
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(EDUCATION|EDUCATIONAL|ACADEMIC|QUALIFICATIONS|DEGREES?|EDUCATIONAL\s+BACKGROUND|ACADEMIC\s+HISTORY)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Education"),
                        
                        # Experience patterns - more flexible matching
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT|WORK\s*HISTORY|EXPERIENCE|PROFESSIONAL\s+BACKGROUND|CAREER\s+HISTORY|JOB\s+HISTORY)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Experience"),
                        
                        # Skills patterns - with additional handling for special characters
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(SKILLS|TECHNICAL\s+SKILLS|PROFICIENCIES|EXPERTISE|CORE\s+COMPETENCIES|KEY\s+SKILLS|PROFESSIONAL\s+SKILLS|SKILL\s+SET)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Skills"),
                        
                        # Summary patterns - capturing various formats
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE|CAREER\s+OBJECTIVE|PROFESSIONAL\s+PROFILE|ABOUT\s+ME|CAREER\s+SUMMARY)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Summary"),
                        
                        # Other common sections
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(CERTIFICATIONS?|CERTIFICATES|CREDENTIALS|LICENSES|PROFESSIONAL\s+CERTIFICATIONS)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Certifications"),
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(LANGUAGES?|LANGUAGE\s+PROFICIENCY|LANGUAGE\s+SKILLS|FLUENCY|FOREIGN\s+LANGUAGES)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Languages"),
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(PROJECTS|PROJECT\s+EXPERIENCE|PORTFOLIO|PERSONAL\s+PROJECTS|PROFESSIONAL\s+PROJECTS|KEY\s+PROJECTS)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Projects"),
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(ACCOMPLISHMENTS|AWARDS|HONORS|ACHIEVEMENTS|ACCOLADES|RECOGNITIONS)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Accomplishments"),
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(PUBLICATIONS|PAPERS|RESEARCH|RESEARCH\s+EXPERIENCE|PUBLISHED\s+WORKS)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Publications"),
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(VOLUNTEER|COMMUNITY\s+SERVICE|VOLUNTEERING|CIVIC\s+ACTIVITIES|COMMUNITY\s+INVOLVEMENT)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Volunteer"),
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(INTERESTS|HOBBIES|ACTIVITIES|PERSONAL\s+INTERESTS)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Interests"),
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(REFERENCES|PROFESSIONAL\s+REFERENCES)(?:\s|:|$|\n|\(cid:[0-9]+\))', "References"),
                        (r'(?i)(?:^|\n|\(cid:[0-9]+\))(?:\s*)(ADDITIONAL\s+INFORMATION|OTHER\s+INFORMATION|MISCELLANEOUS)(?:\s|:|$|\n|\(cid:[0-9]+\))', "Additional")
                    ]
                    
                    # Find all matches
                    matches = []
                    for pattern, section_name in section_patterns:
                        for match in re.finditer(pattern, full_text):
                            matches.append((match.start(), match.group().strip(), section_name))
                            print(f"DEBUG: Found section '{match.group().strip()}' of type '{section_name}' at position {match.start()}")
                    
                    # Sort by position in text
                    matches.sort(key=lambda x: x[0])
                    
                    # Log the detected sections
                    if matches:
                        print(f"DEBUG: Found {len(matches)} section matches: {[m[2] for m in matches]}")
                    else:
                        print(f"DEBUG: No sections matched using patterns, attempting fallback detection")
                        # Print a sample of the text to help diagnose the issue
                        print(f"DEBUG: Text sample (first 200 chars): {full_text[:200].replace('\n', '\\n')}")
                    
                    # Create section objects
                    manual_sections = {}
                    
                    # Create sections based on matches
                    if matches:
                        logger.info(f"Found {len(matches)} sections using pattern matching")
                        for i, (start_pos, header_text, section_type) in enumerate(matches):
                            # Get section content (text between this header and next, or end)
                            if i < len(matches) - 1:
                                content = full_text[start_pos + len(header_text):matches[i+1][0]]
                            else:
                                content = full_text[start_pos + len(header_text):]
                                
                            # Clean up the content
                            content = content.strip()
                            
                            # Add the header as part of the key to avoid duplicates
                            section_key = header_text.strip()
                            if not section_key:
                                section_key = section_type
                                
                            # Clean up section key by removing any (cid:xxx) tokens
                            section_key = re.sub(r'\(cid:[0-9]+\)', '', section_key).strip()
                            
                            # If it's still empty, use the section type
                            if not section_key:
                                section_key = section_type
                                
                            # Store the section with classification
                            manual_sections[section_key] = {
                                'type': section_type,
                                'confidence': 0.9,  # High confidence for pattern-based detection
                                'content': content
                            }
                        
                        # Use these manually detected sections
                        section_classifications = manual_sections
                    else:
                        # If pattern matching fails, try to detect sections based on formatting
                        logger.info("Pattern matching failed, trying formatting-based section detection")
                        formatted_sections = {}
                        
                        # Look for potential headers based on formatting
                        for page_num, page in enumerate(doc):
                            blocks = page.get_text("dict")["blocks"]
                            
                            for block_num, block in enumerate(blocks):
                                if "lines" not in block:
                                    continue
                                    
                                for line in block["lines"]:
                                    for span in line["spans"]:
                                        text = span["text"].strip()
                                        if not text:
                                            continue
                                        
                                        # Check for formatting clues: larger font, bold, all caps
                                        font_size = span["size"]
                                        font_flags = span.get("flags", 0)
                                        is_bold = bool(font_flags & 2**0)
                                        is_all_caps = text.upper() == text and len(text) > 1
                                        
                                        # Enhanced header detection heuristics
                                        is_potential_header = False
                                        confidence_boost = 0.0
                                        
                                        # Headers are often bold, larger font, all caps, etc.
                                        if font_size > 12 and (is_bold or is_all_caps):
                                            is_potential_header = True
                                            confidence_boost = 0.2  # High confidence
                                        elif font_size >= 14:
                                            is_potential_header = True
                                            confidence_boost = 0.3  # Higher confidence for larger font
                                        elif is_all_caps and len(text.split()) <= 3:
                                            is_potential_header = True
                                            confidence_boost = 0.1  # Moderate confidence
                                        elif is_bold and len(text) < 30 and len(text.split()) <= 4:
                                            is_potential_header = True
                                            confidence_boost = 0.1  # Moderate confidence
                                        
                                        # Additional factors that might indicate a header
                                        if text.endswith(':'):
                                            confidence_boost += 0.1
                                            is_potential_header = True
                                            
                                        if is_potential_header:
                                            # Try to classify this potential header
                                            section_type, confidence = self.section_classifier.classify_section(text, "")
                                            
                                            # Boost confidence based on formatting
                                            confidence += confidence_boost
                                            
                                            # Only use sections with good confidence
                                            if confidence > 0.6 or section_type != "unknown":
                                                # Attempt to extract content following this header
                                                block_index = block_num
                                                section_content = text + "\n"
                                                
                                                # Try to extract a bit of content after this header
                                                # This is improved but still simplified
                                                try:
                                                    if block_index + 1 < len(blocks):
                                                        next_block = blocks[block_index + 1]
                                                        if "lines" in next_block:
                                                            next_text = ""
                                                            for line in next_block["lines"][:3]:  # Get just the first few lines
                                                                for span in line["spans"]:
                                                                    next_text += span["text"] + " "
                                                            section_content += next_text.strip()
                                                except Exception as e:
                                                    print(f"Error extracting section content: {e}")
                                                    
                                                formatted_sections[text] = {
                                                    'type': section_type,
                                                    'confidence': confidence,
                                                    'content': section_content  # Better content extraction
                                                }
                        
                        if formatted_sections:
                            section_classifications = formatted_sections
                    
                except Exception as e:
                    logger.error(f"Error in fallback section detection: {e}")
        else:
            document = self.pdf_replacer.extract_formatted_pdf(pdf_path)
            # Classify sections for other replacers
            section_classifications = self.section_classifier.classify_sections_in_document(document.sections)
        
        # Organize sections by type - handling differs based on the document structure
        sections = {}
        
        if isinstance(self.pdf_replacer, PDFDirectReplacer):
            # For PDFDirectReplacer, document is a dict and sections are already organized
            for section in document.get('sections', []):
                section_name = section.get('name', '')
                section_text = section.get('text', '')
                
                # Get classification from the classified sections
                classification = section_classifications.get(section_name, {})
                section_type = classification.get('type', 'unknown')
                confidence = classification.get('confidence', 0.0)
                
                sections[section_name] = {
                    'type': section_type,
                    'confidence': confidence,
                    'content': section_text
                }
        else:
            # For other replacers, document has a sections attribute with section objects
            for section in document.sections:
                section_name = section.name
                section_text = section.get_text()
                
                classification = section_classifications.get(section, {})
                section_type = classification.get('type', 'unknown')
                confidence = classification.get('confidence', 0.0)
                
                sections[section_name] = {
                    'type': section_type,
                    'confidence': confidence,
                    'content': section_text
                }
        
        # Count pages and text blocks - handling differs based on document structure
        if isinstance(self.pdf_replacer, PDFDirectReplacer):
            # For PDFDirectReplacer, these values are in the meta dictionary
            page_count = document.get('meta', {}).get('page_count', 1)
            text_block_count = sum(len(page.get('blocks', [])) for page in document.get('pages', []))
            
            # Detect format type based on document structure
            format_type = "Standard"
            if len(document.get('pages', [])) > 0:
                first_page = document.get('pages')[0]
                if len(first_page.get('blocks', [])) > 10:
                    format_type = "Complex"
                # Check for multi-column layout
                if any(len(page.get('columns', [])) > 1 for page in document.get('pages', [])):
                    format_type = "Multi-column"
        else:
            # For other replacers, use the original approach
            page_count = len(document.pages) if hasattr(document, 'pages') else 1
            text_block_count = sum(len(page.blocks) for page in document.pages) if hasattr(document, 'pages') else len(document.sections)
            
            # Detect format type based on layout analysis
            format_type = "Standard"
            if hasattr(document, 'layout_analysis'):
                if document.layout_analysis.get('columns', 1) > 1:
                    format_type = "Multi-column"
                if document.layout_analysis.get('design_elements', 0) > 5:
                    format_type = "Creative"
        
        # Build comprehensive structure analysis
        structure = {
            'sections': sections,
            'page_count': page_count,
            'text_block_count': text_block_count,
            'format_type': format_type
        }
        
        return structure
    
    def _section_names_match(self, name1, name2):
        """
        Check if two section names match, ignoring case, punctuation, and common variations.
        
        Args:
            name1: First section name
            name2: Second section name
            
        Returns:
            bool: True if the names are considered matching
        """
        if not name1 or not name2:
            return False
        
        try:
            # Convert to string if we got objects
            name1 = str(name1).strip()
            name2 = str(name2).strip()
            
            # Handle empty strings after conversion
            if not name1 or not name2:
                return False
                
            # Special case: if either name starts with "NEW_SECTION_", always return false
            # This allows the LLM to create new sections that don't match existing ones
            if name1.startswith("NEW_SECTION_") or name2.startswith("NEW_SECTION_"):
                return False
                
            # Handle our special section keys with embedded type information
            # Format: "SECTION_TYPE: Original Header Text"
            section_type1 = None
            section_type2 = None
            
            if ": " in name1 and name1.split(": ")[0] in ["SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS", "CERTIFICATIONS", "PROJECTS"]:
                section_type1 = name1.split(": ")[0]
                
            if ": " in name2 and name2.split(": ")[0] in ["SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS", "CERTIFICATIONS", "PROJECTS"]:
                section_type2 = name2.split(": ")[0]
                
            # If both have section types embedded and they match, return true
            if section_type1 and section_type2 and section_type1 == section_type2:
                return True
                
            # If one has section type embedded, use it for matching
            if section_type1 and name2 == section_type1:
                return True
                
            if section_type2 and name1 == section_type2:
                return True
                
            # Debug output to help diagnose matching issues
            # print(f"Comparing section names: '{name1}' and '{name2}'")
                
            # Normalize strings by removing punctuation and converting to lowercase
            def normalize(name):
                # Convert to lowercase and remove punctuation
                result = re.sub(r'[^\w\s]', '', name.lower())
                
                # Define expanded common variations with more variants
                replacements = {
                    'experience': ['work experience', 'professional experience', 'employment', 'work history', 
                                  'job experience', 'career experience', 'career history', 'experience'],
                    'education': ['academic background', 'academic', 'qualifications', 'degrees', 'schooling', 
                                 'educational background', 'academic qualifications', 'education'],
                    'skills': ['technical skills', 'expertise', 'competencies', 'proficiencies', 'abilities', 
                              'core competencies', 'professional skills', 'skill set', 'technical expertise', 'skills'],
                    'projects': ['personal projects', 'project experience', 'portfolio', 'projects accomplished', 
                                'professional projects', 'projects'],
                    'certifications': ['certificates', 'professional certifications', 'credentials', 'licenses',
                                      'certifications'],
                    'languages': ['language proficiency', 'language skills', 'fluency', 'foreign languages', 
                                 'spoken languages', 'languages'],
                    'summary': ['professional summary', 'profile', 'about me', 'objective', 'overview',
                               'career objective', 'professional profile', 'summary'],
                    'achievements': ['accomplishments', 'awards', 'recognitions', 'honors', 'accolades', 
                                    'achievements'],
                    'contact': ['personal information', 'contact details', 'contact information', 
                               'personal details', 'contact']
                }
                
                # Check if the name matches any of the common variations
                result_words = result.split()
                for standard, variations in replacements.items():
                    # Direct match with standard name
                    if standard in result_words or standard == result:
                        return standard
                    
                    # Check against all variations
                    for variant in variations:
                        variant_words = variant.split()
                        # Exact match
                        if result == variant:
                            return standard
                        # Substring match (e.g., "work history" in "professional work history")
                        if variant in result or result in variant:
                            return standard
                        # Word-by-word match for significant words (length > 3)
                        if any(word in variant_words for word in result_words if len(word) > 3):
                            return standard
                        # Special case for short section names like "skills"
                        if len(variant) <= 6 and variant == result:
                            return standard
                
                return result
            
            # Get normalized versions
            norm1 = normalize(name1)
            norm2 = normalize(name2)
            
            # Check for exact match after normalization
            if norm1 == norm2:
                # print(f"Exact match: {norm1} == {norm2}")
                return True
                
            # Check if one is a substring of the other
            if norm1 in norm2 or norm2 in norm1:
                # print(f"Substring match: '{norm1}' in '{norm2}' or vice versa")
                return True
                
            # Compare word by word
            words1 = set(norm1.split())
            words2 = set(norm2.split())
            common_words = words1.intersection(words2)
            
            # List of common words to ignore in comparisons
            stop_words = {'and', 'the', 'for', 'with', 'this', 'that', 'from', 'have', 'has', 
                         'to', 'of', 'in', 'on', 'at', 'by', 'as', 'an', 'a'}
            
            # If they share significant words (excluding common words like "and", "the", etc.)
            significant_words = {word for word in common_words if len(word) > 2 and word.lower() not in stop_words}
            
            # Specific handling for short section names (common in resumes)
            short_section_match = (len(words1) <= 2 and len(words2) <= 2 and 
                                  any(w1 == w2 for w1 in words1 for w2 in words2 
                                     if len(w1) > 3 and w1.lower() not in stop_words))
            
            # Special case for section headers that are just one word
            single_word_match = (len(words1) == 1 and len(words2) == 1 and 
                list(words1)[0][:3].lower() == list(words2)[0][:3].lower() and
                len(list(words1)[0]) > 3 and len(list(words2)[0]) > 3)
            
            if significant_words and (len(significant_words) >= 1 or len(words1) == 1 or len(words2) == 1):
                # print(f"Word match: significant words = {significant_words}")
                return True
                
            if short_section_match:
                # print(f"Short section match: {words1} and {words2}")
                return True
                
            if single_word_match:
                # First 3 letters match for single-word sections
                # print(f"First 3 letters match: {words1} and {words2}")
                return True
                
            # If we get here, the names don't match
            return False
        except Exception as e:
            print(f"Error in section name matching: {e}")
            # If there's any error, assume they don't match
            return False
