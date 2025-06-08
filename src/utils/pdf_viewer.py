"""
PDF Viewer component for the Chat Workspace
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os

class PDFViewer:
    """A simple PDF viewer component for the chat workspace."""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.current_pdf_path = None
        self.current_content = None
        self.zoom_level = 1.0
        
        self.setup_viewer()
    
    def setup_viewer(self):
        """Setup the PDF viewer interface."""
        # Control panel
        self.control_frame = ttk.Frame(self.parent_frame)
        self.control_frame.pack(fill=tk.X, pady=5)
        
        # File controls
        ttk.Button(
            self.control_frame, 
            text="Load Resume", 
            command=self.load_pdf
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            self.control_frame, 
            text="Refresh", 
            command=self.refresh_view
        ).pack(side=tk.LEFT, padx=5)
        
        # Zoom controls
        ttk.Label(self.control_frame, text="Zoom:").pack(side=tk.LEFT, padx=(20, 5))
        
        ttk.Button(
            self.control_frame, 
            text="−", 
            width=3,
            command=self.zoom_out
        ).pack(side=tk.LEFT, padx=2)
        
        self.zoom_var = tk.StringVar(value="100%")
        self.zoom_label = ttk.Label(
            self.control_frame, 
            textvariable=self.zoom_var,
            width=6
        )
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            self.control_frame, 
            text="+", 
            width=3,
            command=self.zoom_in
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            self.control_frame, 
            text="Fit", 
            command=self.zoom_fit
        ).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="No PDF loaded")
        ttk.Label(
            self.control_frame, 
            textvariable=self.status_var
        ).pack(side=tk.RIGHT, padx=5)
        
        # Display area
        self.display_frame = ttk.Frame(self.parent_frame)
        self.display_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # For now, use text display until we implement real PDF rendering
        self.text_display = scrolledtext.ScrolledText(
            self.display_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Courier", 10)
        )
        self.text_display.pack(fill=tk.BOTH, expand=True)
        
        # Add placeholder content
        self.show_placeholder()
    
    def show_placeholder(self):
        """Show placeholder content when no PDF is loaded."""
        placeholder_text = """
PDF Preview
───────────

No resume loaded. Click 'Load Resume' to start.

Features:
• Real-time preview of resume changes
• Zoom controls for better visibility
• Support for PDF and text formats
• Integration with chat suggestions

This area will show your resume content
for easy editing and review.
        """
        
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, placeholder_text.strip())
        self.text_display.config(state=tk.DISABLED)
    
    def load_pdf(self, pdf_path=None, content=None):
        """Load a PDF file or content for viewing."""
        if pdf_path:
            self.current_pdf_path = pdf_path
            self.status_var.set(f"Loaded: {os.path.basename(pdf_path)}")
        
        if content:
            self.current_content = content
            self.display_content(content)
        else:
            # For now, show a mock preview
            mock_content = f"""
Resume Preview: {os.path.basename(pdf_path) if pdf_path else 'Unknown'}
{'='*60}

[This is a text representation of the PDF content]

JOHN SMITH
Email: john.smith@email.com | Phone: (555) 123-4567
LinkedIn: linkedin.com/in/johnsmith

EXPERIENCE
─────────────────────────────────────────────────────────────
Senior Software Engineer | Tech Corp | 2020 - Present
• Led development of web applications using React and Node.js
• Improved system performance by 40% through optimization
• Mentored 3 junior developers

Software Engineer | StartupXYZ | 2018 - 2020
• Developed REST APIs and microservices
• Implemented automated testing reducing bugs by 60%
• Collaborated with cross-functional teams

EDUCATION
─────────────────────────────────────────────────────────────
Bachelor of Science in Computer Science
University of Technology | 2018

SKILLS
─────────────────────────────────────────────────────────────
• Languages: Python, JavaScript, Java, C++
• Frameworks: React, Node.js, Django, Spring
• Databases: PostgreSQL, MongoDB, Redis
• Tools: Git, Docker, Jenkins, AWS

Zoom: {int(self.zoom_level * 100)}%
            """
            self.display_content(mock_content.strip())
    
    def display_content(self, content):
        """Display content in the viewer."""
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        
        # Apply zoom by changing font size
        base_font_size = 10
        font_size = max(6, int(base_font_size * self.zoom_level))
        self.text_display.config(font=("Courier", font_size))
        
        self.text_display.insert(tk.END, content)
        self.text_display.config(state=tk.DISABLED)
    
    def refresh_view(self):
        """Refresh the current view."""
        if self.current_content:
            self.display_content(self.current_content)
        elif self.current_pdf_path:
            self.load_pdf(self.current_pdf_path)
        else:
            self.show_placeholder()
    
    def zoom_in(self):
        """Zoom in the view."""
        self.zoom_level = min(3.0, self.zoom_level + 0.25)
        self.update_zoom_display()
        self.refresh_view()
    
    def zoom_out(self):
        """Zoom out the view."""
        self.zoom_level = max(0.5, self.zoom_level - 0.25)
        self.update_zoom_display()
        self.refresh_view()
    
    def zoom_fit(self):
        """Reset zoom to fit."""
        self.zoom_level = 1.0
        self.update_zoom_display()
        self.refresh_view()
    
    def update_zoom_display(self):
        """Update the zoom level display."""
        self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
    
    def update_content(self, new_content):
        """Update the displayed content."""
        self.current_content = new_content
        self.display_content(new_content)
    
    def get_content(self):
        """Get the currently displayed content."""
        return self.current_content