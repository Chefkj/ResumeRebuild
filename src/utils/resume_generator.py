"""
Enhanced Resume Generator module for creating well-formatted PDF resumes from structured content.
"""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import HRFlowable, PageBreak, Image, ListFlowable, ListItem
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
import re

class ResumeGenerator:
    """Class for generating professionally formatted PDF resumes from structured content."""
    
    def __init__(self):
        self.templates = {
            'modern': self._generate_modern_template,
            'classic': self._generate_classic_template,
            'minimal': self._generate_minimal_template,
            'professional': self._generate_professional_template,
            'creative': self._generate_creative_template
        }
        
        # Define common colors
        self.colors = {
            'primary': colors.HexColor('#2c3e50'),
            'secondary': colors.HexColor('#3498db'),
            'accent': colors.HexColor('#e74c3c'),
            'light': colors.HexColor('#ecf0f1'),
            'dark': colors.HexColor('#34495e'),
            'gray': colors.HexColor('#95a5a6'),
            'highlight': colors.HexColor('#f1c40f')
        }
    
    def generate(self, resume_content, template='modern', output_path='new_resume.pdf'):
        """
        Generate a PDF resume from structured content.
        
        Args:
            resume_content: ResumeContent object containing the structured resume content
            template: Template name to use ('modern', 'classic', 'minimal', 'professional', 'creative')
            output_path: Path for the output PDF file
            
        Returns:
            Path to the generated PDF file
        """
        # Ensure the template exists
        if template not in self.templates:
            print(f"Warning: Template '{template}' not found. Using 'modern' template.")
            template = 'modern'
        
        # Pre-process the resume content
        processed_content = self._preprocess_resume_content(resume_content)
        
        # Generate the PDF using the selected template
        generator_func = self.templates[template]
        generator_func(processed_content, output_path)
        
        return output_path
    
    def _preprocess_resume_content(self, resume_content):
        """
        Pre-process the resume content to prepare it for PDF generation.
        This includes formatting and structuring the text.
        """
        # Create a deep copy to avoid modifying the original
        from copy import deepcopy
        processed = deepcopy(resume_content)
        
        # Process each section's content
        for section in processed.sections:
            # Format bullet points
            section.content = self._format_bullet_points(section.content)
            
            # Format dates and company names
            section.content = self._format_dates_and_companies(section.content)
            
            # Format links
            section.content = self._format_links(section.content)
        
        return processed
    
    def _format_bullet_points(self, content):
        """Format bullet points in section content."""
        # Convert lines starting with - or * or • to proper bullet points
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if re.match(r'^[-*•]', line):
                # Remove the bullet character and add proper spacing
                line = '• ' + re.sub(r'^[-*•]\s*', '', line)
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_dates_and_companies(self, content):
        """Format dates and company names in section content."""
        # Look for date patterns (MM/YYYY or Month YYYY)
        date_pattern = r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})|(?:\d{1,2}/\d{4})'
        
        # Find date ranges
        date_range_pattern = f"({date_pattern}\\s*[-–—]\\s*(?:{date_pattern}|Present|Current))"
        
        # Replace with formatted date ranges
        content = re.sub(date_range_pattern, r'<i>\1</i>', content, flags=re.IGNORECASE)
        
        # Try to identify company names (simplified approach)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # If a line starts with a capitalized word and isn't a bullet point
            if re.match(r'^[A-Z][a-zA-Z0-9\s&,.]+$', line.strip()) and not line.strip().startswith('•'):
                # Format as a company name
                lines[i] = f"<b>{line}</b>"
        
        return '\n'.join(lines)
    
    def _format_links(self, content):
        """Format links in section content."""
        # Find URLs
        url_pattern = r'(https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_+.~#?&//=]*)'
        
        # Replace with hyperlinks
        content = re.sub(url_pattern, r'<link href="\1">\1</link>', content)
        
        return content
    
    def _create_styles(self, base_font="Helvetica"):
        """Create common styles for use in templates."""
        styles = getSampleStyleSheet()
        
        # Basic styles
        styles.add(ParagraphStyle(
            name='Name',
            fontName=f'{base_font}-Bold',
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        
        styles.add(ParagraphStyle(
            name='ContactInfo',
            fontName=base_font,
            fontSize=10,
            leading=12,
            alignment=TA_CENTER
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            fontName=f'{base_font}-Bold',
            fontSize=12,
            leading=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=self.colors['primary']
        ))
        
        styles.add(ParagraphStyle(
            name='SectionContent',
            fontName=base_font,
            fontSize=10,
            leading=14
        ))
        
        styles.add(ParagraphStyle(
            name='BulletPoint',
            fontName=base_font,
            fontSize=10,
            leading=14,
            leftIndent=10,
            firstLineIndent=-10
        ))
        
        styles.add(ParagraphStyle(
            name='Company',
            fontName=f'{base_font}-Bold',
            fontSize=11,
            leading=14,
            spaceBefore=6
        ))
        
        styles.add(ParagraphStyle(
            name='JobTitle',
            fontName=f'{base_font}-Oblique',
            fontSize=10,
            leading=14
        ))
        
        styles.add(ParagraphStyle(
            name='DateRange',
            fontName=base_font,
            fontSize=10,
            leading=12,
            alignment=TA_RIGHT
        ))
        
        return styles
    
    def _parse_section_content(self, content, styles):
        """
        Parse section content into structured elements.
        Returns a list of flowable elements.
        """
        elements = []
        paragraphs = content.split('\n\n')
        
        for para in paragraphs:
            if not para.strip():
                continue
                
            # Check if paragraph contains bullet points
            if '• ' in para:
                # Split into bullet points
                bullet_items = []
                for line in para.split('\n'):
                    if line.strip().startswith('• '):
                        bullet_text = line.strip()[2:]  # Remove the bullet character
                        bullet_items.append(ListItem(Paragraph(bullet_text, styles['SectionContent'])))
                    elif bullet_items:  # If we're already in a bullet list and this is a continuation
                        last_bullet = bullet_items[-1].content.text
                        bullet_items[-1].content.text = last_bullet + " " + line.strip()
                    else:  # Regular text before any bullets
                        elements.append(Paragraph(line, styles['SectionContent']))
                
                if bullet_items:
                    elements.append(ListFlowable(
                        bullet_items,
                        bulletType='bullet',
                        start=None,
                        bulletFormat='•',
                        leftIndent=15,
                        bulletFontName='Helvetica',
                        bulletFontSize=10
                    ))
            else:
                # Check for company/role format
                lines = para.split('\n')
                if len(lines) >= 2 and '<b>' in lines[0]:
                    # Company name on first line
                    company_name = lines[0].replace('<b>', '').replace('</b>', '')
                    elements.append(Paragraph(company_name, styles['Company']))
                    
                    # Check for date on same line as company or job title
                    date_match = re.search(r'<i>(.+?)</i>', '\n'.join(lines[1:2]))
                    
                    if date_match:
                        # If we have a date, create a table with role and date
                        date_text = date_match.group(1)
                        role_text = lines[1].replace(f'<i>{date_text}</i>', '').strip()
                        
                        if role_text:  # If there's a role text
                            data = [[
                                Paragraph(role_text, styles['JobTitle']), 
                                Paragraph(date_text, styles['DateRange'])
                            ]]
                            
                            table = Table(data, colWidths=[4.5*inch, 2*inch])
                            table.setStyle(TableStyle([
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('ALIGNMENT', (1, 0), (1, 0), 'RIGHT'),
                            ]))
                            elements.append(table)
                        else:  # Just the date
                            elements.append(Paragraph(date_text, styles['DateRange']))
                        
                        # Add the rest of the text if any
                        rest_text = '\n'.join(lines[2:])
                        if rest_text.strip():
                            elements.append(Paragraph(rest_text, styles['SectionContent']))
                    else:
                        # No date found, just add the remaining lines
                        rest_text = '\n'.join(lines[1:])
                        if rest_text.strip():
                            elements.append(Paragraph(rest_text, styles['SectionContent']))
                else:
                    # Regular paragraph
                    elements.append(Paragraph(para, styles['SectionContent']))
                    
        return elements
    
    def _generate_modern_template(self, resume_content, output_path):
        """Generate a resume using the modern template."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Create styles
        styles = self._create_styles()
        
        # Build document content
        content = []
        
        # Add name and contact info
        if resume_content.contact_info.get('name'):
            content.append(Paragraph(resume_content.contact_info['name'], styles['Name']))
        
        contact_line = []
        for k in ['email', 'phone', 'linkedin']:
            if resume_content.contact_info.get(k):
                contact_line.append(resume_content.contact_info[k])
        
        if contact_line:
            content.append(Paragraph(" | ".join(contact_line), styles['ContactInfo']))
        
        if resume_content.contact_info.get('address'):
            content.append(Paragraph(resume_content.contact_info['address'], styles['ContactInfo']))
        
        content.append(Spacer(1, 0.2*inch))
        content.append(HRFlowable(width="100%", thickness=1, color=self.colors['secondary']))
        content.append(Spacer(1, 0.2*inch))
        
        # Add sections
        for section in resume_content.sections:
            # Add section header
            content.append(Paragraph(section.title, styles['SectionHeader']))
            content.append(Spacer(1, 0.05*inch))
            
            # Parse and add section content
            section_elements = self._parse_section_content(section.content, styles)
            content.extend(section_elements)
            
            content.append(Spacer(1, 0.1*inch))
        
        # Build the PDF document
        doc.build(content)
    
    def _generate_classic_template(self, resume_content, output_path):
        """Generate a resume using the classic template."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Create styles
        styles = self._create_styles()
        
        # Override styles for classic look
        styles['Name'] = ParagraphStyle(
            name='Name',
            fontName='Times-Bold',
            fontSize=16,
            leading=20,
            alignment=TA_CENTER
        )
        
        styles['SectionHeader'] = ParagraphStyle(
            name='SectionHeader',
            fontName='Times-Bold',
            fontSize=12,
            leading=14,
            spaceBefore=12,
            spaceAfter=6,
            alignment=TA_LEFT,
            borderWidth=0,
            borderPadding=0,
            borderColor=None,
            textColor=colors.black
        )
        
        styles['SectionContent'] = ParagraphStyle(
            name='SectionContent',
            fontName='Times-Roman',
            fontSize=11,
            leading=14
        )
        
        # Build document content
        content = []
        
        # Add name and contact info
        if resume_content.contact_info.get('name'):
            content.append(Paragraph(resume_content.contact_info['name'], styles['Name']))
        
        contact_line = []
        for k in ['email', 'phone', 'linkedin']:
            if resume_content.contact_info.get(k):
                contact_line.append(resume_content.contact_info[k])
        
        if contact_line:
            content.append(Paragraph(" | ".join(contact_line), styles['ContactInfo']))
        
        if resume_content.contact_info.get('address'):
            content.append(Paragraph(resume_content.contact_info['address'], styles['ContactInfo']))
        
        content.append(Spacer(1, 0.25*inch))
        
        # Add sections
        for section in resume_content.sections:
            # Add section header with underline
            content.append(Paragraph(section.title.upper(), styles['SectionHeader']))
            content.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=0, spaceAfter=6))
            
            # Parse and add section content
            section_elements = self._parse_section_content(section.content, styles)
            content.extend(section_elements)
            
            content.append(Spacer(1, 0.15*inch))
        
        # Build the PDF document
        doc.build(content)
    
    def _generate_minimal_template(self, resume_content, output_path):
        """Generate a resume using the minimal template."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.6*inch,
            leftMargin=0.6*inch,
            topMargin=0.6*inch,
            bottomMargin=0.6*inch
        )
        
        # Create styles
        styles = self._create_styles()
        
        # Override styles for minimal look
        styles['Name'] = ParagraphStyle(
            name='Name',
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            alignment=TA_LEFT
        )
        
        styles['ContactInfo'] = ParagraphStyle(
            name='ContactInfo',
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            alignment=TA_LEFT
        )
        
        styles['SectionHeader'] = ParagraphStyle(
            name='SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=13,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.black
        )
        
        styles['SectionContent'] = ParagraphStyle(
            name='SectionContent',
            fontName='Helvetica',
            fontSize=9,
            leading=12
        )
        
        # Build document content
        content = []
        
        # Add name and contact info
        if resume_content.contact_info.get('name'):
            content.append(Paragraph(resume_content.contact_info['name'], styles['Name']))
        
        contact_info = []
        for k in ['email', 'phone', 'linkedin']:
            if resume_content.contact_info.get(k):
                contact_info.append(resume_content.contact_info[k])
        
        if contact_info:
            content.append(Paragraph(" · ".join(contact_info), styles['ContactInfo']))
        
        if resume_content.contact_info.get('address'):
            content.append(Paragraph(resume_content.contact_info['address'], styles['ContactInfo']))
        
        content.append(Spacer(1, 0.15*inch))
        
        # Add sections
        for section in resume_content.sections:
            # Add section header
            content.append(Paragraph(section.title, styles['SectionHeader']))
            content.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceAfter=6))
            
            # Parse and add section content
            section_elements = self._parse_section_content(section.content, styles)
            content.extend(section_elements)
            
            content.append(Spacer(1, 0.1*inch))
        
        # Build the PDF document
        doc.build(content)
    
    def _generate_professional_template(self, resume_content, output_path):
        """Generate a resume using the professional template with a cleaner layout."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.6*inch,
            leftMargin=0.6*inch,
            topMargin=0.6*inch,
            bottomMargin=0.6*inch
        )
        
        # Create styles
        styles = self._create_styles("Helvetica")
        
        # Override styles for professional look
        styles['Name'] = ParagraphStyle(
            name='Name',
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            alignment=TA_LEFT,
            textColor=self.colors['primary']
        )
        
        styles['ContactInfo'] = ParagraphStyle(
            name='ContactInfo',
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            textColor=self.colors['dark']
        )
        
        styles['SectionHeader'] = ParagraphStyle(
            name='SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=self.colors['primary'],
            borderWidth=0,
            borderPadding=0,
            borderColor=None
        )
        
        # Build document content
        content = []
        
        # Header with name and contact info in two columns
        header_data = []
        
        # Name on the left
        name_cell = Paragraph(resume_content.contact_info.get('name', ''), styles['Name'])
        
        # Contact info on the right
        contact_parts = []
        if resume_content.contact_info.get('email'):
            contact_parts.append(resume_content.contact_info['email'])
        if resume_content.contact_info.get('phone'):
            contact_parts.append(resume_content.contact_info['phone'])
        if resume_content.contact_info.get('linkedin'):
            contact_parts.append(resume_content.contact_info['linkedin'])
        
        contact_info = Paragraph("<br/>".join(contact_parts), styles['ContactInfo'])
        
        header_data.append([name_cell, contact_info])
        
        # Create a table for the header
        header_table = Table(header_data, colWidths=[4*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGNMENT', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        content.append(header_table)
        
        # Add address if available
        if resume_content.contact_info.get('address'):
            content.append(Paragraph(resume_content.contact_info['address'], styles['ContactInfo']))
        
        content.append(Spacer(1, 0.15*inch))
        content.append(HRFlowable(width="100%", thickness=1, color=self.colors['secondary'], spaceBefore=0, spaceAfter=10))
        
        # Add sections
        for section in resume_content.sections:
            # Add section header
            content.append(Paragraph(section.title, styles['SectionHeader']))
            content.append(Spacer(1, 0.05*inch))
            
            # Parse and add section content
            section_elements = self._parse_section_content(section.content, styles)
            content.extend(section_elements)
            
            content.append(Spacer(1, 0.1*inch))
        
        # Build the PDF document
        doc.build(content)
    
    def _generate_creative_template(self, resume_content, output_path):
        """Generate a resume using a creative template with more design elements."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Create styles
        styles = self._create_styles()
        
        # Override styles for creative look
        styles['Name'] = ParagraphStyle(
            name='Name',
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            alignment=TA_LEFT,
            textColor=self.colors['accent']
        )
        
        styles['ContactInfo'] = ParagraphStyle(
            name='ContactInfo',
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            textColor=self.colors['dark']
        )
        
        styles['SectionHeader'] = ParagraphStyle(
            name='SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=16,
            spaceBefore=12,
            spaceAfter=6,
            textColor=self.colors['secondary']
        )
        
        # Build document content
        content = []
        
        # Create a decorative header
        content.append(HRFlowable(width="100%", thickness=10, color=self.colors['accent'], spaceBefore=0, spaceAfter=10, lineCap=1))
        
        # Add name and contact info
        if resume_content.contact_info.get('name'):
            content.append(Paragraph(resume_content.contact_info['name'], styles['Name']))
        
        contact_line = []
        for k in ['email', 'phone', 'linkedin']:
            if resume_content.contact_info.get(k):
                contact_line.append(resume_content.contact_info[k])
        
        if contact_line:
            content.append(Paragraph(" | ".join(contact_line), styles['ContactInfo']))
        
        if resume_content.contact_info.get('address'):
            content.append(Paragraph(resume_content.contact_info['address'], styles['ContactInfo']))
        
        content.append(Spacer(1, 0.2*inch))
        
        # Add sections with decorative elements
        for section in resume_content.sections:
            # Add section header with decorative element
            content.append(HRFlowable(width=0.5*inch, thickness=4, color=self.colors['secondary'], spaceBefore=6, spaceAfter=6, lineCap=1))
            content.append(Paragraph(section.title, styles['SectionHeader']))
            content.append(Spacer(1, 0.05*inch))
            
            # Parse and add section content
            section_elements = self._parse_section_content(section.content, styles)
            content.extend(section_elements)
            
            content.append(Spacer(1, 0.1*inch))
        
        # Add decorative footer
        content.append(Spacer(1, 0.1*inch))
        content.append(HRFlowable(width="100%", thickness=4, color=self.colors['accent'], spaceBefore=0, spaceAfter=0, lineCap=1))
        
        # Build the PDF document
        doc.build(content)