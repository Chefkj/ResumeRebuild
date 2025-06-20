#!/usr/bin/env python3
"""
GUI interface for the Resume Rebuilder application
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox, simpledialog

# Try to import real classes, fall back to mocks if not available
try:
    from utils.pdf_extractor import PDFExtractor
    from utils.resume_generator import ResumeGenerator
    from utils.job_analyzer import JobAnalyzer
    from utils.api_client import APIClient
    from utils.manageai_api_manager import ManageAIAPIManager
    from utils.resume_api_integration import ResumeAPIIntegration, ConnectionType
    from utils.pdf_content_replacer import PDFContentReplacer
except ImportError:
    # Import mock classes when real ones are not available
    from utils.mock_classes import (
        MockPDFExtractor as PDFExtractor,
        MockResumeGenerator as ResumeGenerator,
        MockJobAnalyzer as JobAnalyzer,
        MockAPIClient as APIClient,
        MockManageAIAPIManager as ManageAIAPIManager,
        MockResumeAPIIntegration as ResumeAPIIntegration,
        MockConnectionType as ConnectionType,
        MockPDFContentReplacer as PDFContentReplacer
    )

class ResumeRebuilderApp:
    """Main application class for the Resume Rebuilder GUI."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Resume Rebuilder")
        self.root.geometry("800x600")
        
        self.resume_content = None
        self.job_description = ""
        self.input_pdf_path = ""
        self.output_pdf_path = ""
        
        # Create status var early so it's available before UI setup
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing...")
        
        # Initialize ManageAI API Manager
        self.manageai_api_manager = ManageAIAPIManager(
            host="localhost",
            port=8080
        )
        
        # Initialize unified API integration
        self.api_integration = ResumeAPIIntegration(
            connection_type=ConnectionType.LOCAL_SERVER,
            local_url="http://localhost:8080",
            manageai_url="http://localhost:8080",
            api_key=os.environ.get("RESUME_API_KEY", "test-api-key-1234")
        )
        
        # Keep API client for backward compatibility
        self.api_client = APIClient()
        
        # Check for PyMuPDF availability
        has_pymupdf = self._check_pymupdf_availability()
        
        # Initialize PDF content replacer
        self.pdf_replacer = PDFContentReplacer(
            use_enhanced=True,
            use_llm=True,
            use_ocr=False,
            use_direct=has_pymupdf
        )
        
        # Store PyMuPDF availability for UI setup
        self.has_pymupdf = has_pymupdf
        
        # Setup the UI
        self.setup_ui()
        
        # Register window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Try to start the ManageAI API server (after UI is set up)
        self._start_manageai_server()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.tab_upload = ttk.Frame(self.notebook)
        self.tab_edit = ttk.Frame(self.notebook)
        self.tab_analyze = ttk.Frame(self.notebook)
        self.tab_generate = ttk.Frame(self.notebook)
        self.tab_replace = ttk.Frame(self.notebook)  # New tab for PDF content replacement
        self.tab_chat_workspace = ttk.Frame(self.notebook)  # New unified chat workspace
        self.tab_api = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_upload, text="Upload Resume")
        self.notebook.add(self.tab_edit, text="Edit Content")
        self.notebook.add(self.tab_analyze, text="Analyze Job")
        self.notebook.add(self.tab_generate, text="Generate Resume")
        self.notebook.add(self.tab_replace, text="Replace PDF Content")  # New tab
        self.notebook.add(self.tab_chat_workspace, text="Chat Workspace")  # New unified interface
        self.notebook.add(self.tab_api, text="API Settings")
        
        # Setup Upload tab
        self.setup_upload_tab()
        
        # Setup Edit tab
        self.setup_edit_tab()
        
        # Setup Analyze tab
        self.setup_analyze_tab()
        
        # Setup Generate tab
        self.setup_generate_tab()
        
        # Setup Replace Content tab
        self.setup_replace_tab()
        
        # Setup Chat Workspace tab
        self.setup_chat_workspace_tab()
        
        # Setup API Settings tab
        self.setup_api_tab()
        
        # Status bar (status_var is already created in __init__)
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_upload_tab(self):
        """Setup the Upload Resume tab."""
        frame = ttk.Frame(self.tab_upload, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Upload your current resume PDF:", font=("", 12)).pack(pady=10)
        
        # File upload button
        upload_frame = ttk.Frame(frame)
        upload_frame.pack(pady=20)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(upload_frame, textvariable=self.file_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(upload_frame, text="Browse...", command=self.browse_resume).pack(side=tk.LEFT)
        
        # LLM refinement options
        llm_frame = ttk.LabelFrame(frame, text="LLM Refinement Options")
        llm_frame.pack(fill=tk.X, pady=10)
        
        # Enable LLM refinement checkbox
        self.use_llm_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            llm_frame, 
            text="Use LLM to improve extraction quality", 
            variable=self.use_llm_var
        ).pack(anchor=tk.W, padx=5, pady=5)

        # LLM source selection
        llm_source_frame = ttk.Frame(llm_frame)
        llm_source_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.use_local_llm_var = tk.BooleanVar(value=True)
        ttk.Radiobutton(
            llm_source_frame,
            text="Use local LLM (LLM Studio with Qwen 14B)",
            variable=self.use_local_llm_var,
            value=True
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            llm_source_frame,
            text="Use OpenAI API",
            variable=self.use_local_llm_var,
            value=False
        ).pack(anchor=tk.W)
        
        # Local LLM settings
        local_llm_frame = ttk.Frame(llm_frame)
        local_llm_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(local_llm_frame, text="LLM Studio Host:").grid(row=0, column=0, sticky=tk.W)
        self.llm_host_var = tk.StringVar(value="localhost")
        ttk.Entry(local_llm_frame, textvariable=self.llm_host_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(local_llm_frame, text="Port:").grid(row=0, column=2, sticky=tk.W)
        self.llm_port_var = tk.StringVar(value="1234")
        ttk.Entry(local_llm_frame, textvariable=self.llm_port_var, width=6).grid(row=0, column=3, padx=5)
        
        ttk.Button(
            local_llm_frame, 
            text="Test Connection", 
            command=self.test_local_llm_connection
        ).grid(row=0, column=4, padx=10)
        
        # API Key input
        api_frame = ttk.Frame(llm_frame)
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(api_frame, text="OpenAI API Key:").pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar(value=os.environ.get("OPENAI_API_KEY", ""))
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=50, show="*")
        api_entry.pack(side=tk.LEFT, padx=5)
        
        # Show/hide API key button
        self.show_api_key = tk.BooleanVar(value=False)
        
        def toggle_show_api_key():
            if self.show_api_key.get():
                api_entry.config(show="")
            else:
                api_entry.config(show="*")
        
        ttk.Checkbutton(
            api_frame, 
            text="Show", 
            variable=self.show_api_key,
            command=toggle_show_api_key
        ).pack(side=tk.LEFT)
        
        # Extract button
        ttk.Button(
            frame, 
            text="Extract Resume Content", 
            command=self.extract_resume,
            style="Accent.TButton"
        ).pack(pady=20)
        
        # Info text
        info_text = (
            "This application helps you:\n\n"
            "1. Extract content from your existing PDF resume\n"
            "2. Edit and optimize the content for specific job positions\n"
            "3. Analyze your resume against job descriptions\n"
            "4. Generate a new tailored PDF resume\n\n"
            "Start by uploading your current resume PDF."
        )
        
        info_label = ttk.Label(frame, text=info_text, justify=tk.LEFT, wraplength=600)
        info_label.pack(pady=20)
    
    def setup_edit_tab(self):
        """Setup the Edit Content tab."""
        frame = ttk.Frame(self.tab_edit, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Edit Resume Content:", font=("", 12)).pack(pady=10)
        
        # Edit fields
        edit_frame = ttk.Frame(frame)
        edit_frame.pack(fill=tk.BOTH, expand=True)
        
        # Contact Info
        contact_frame = ttk.LabelFrame(edit_frame, text="Contact Information")
        contact_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Name field
        name_frame = ttk.Frame(contact_frame)
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # Email field
        email_frame = ttk.Frame(contact_frame)
        email_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(email_frame, text="Email:").pack(side=tk.LEFT)
        self.email_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # Phone field
        phone_frame = ttk.Frame(contact_frame)
        phone_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(phone_frame, text="Phone:").pack(side=tk.LEFT)
        self.phone_var = tk.StringVar()
        ttk.Entry(phone_frame, textvariable=self.phone_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # LinkedIn field
        linkedin_frame = ttk.Frame(contact_frame)
        linkedin_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(linkedin_frame, text="LinkedIn:").pack(side=tk.LEFT)
        self.linkedin_var = tk.StringVar()
        ttk.Entry(linkedin_frame, textvariable=self.linkedin_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # Section content
        sections_frame = ttk.LabelFrame(edit_frame, text="Resume Sections")
        sections_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.sections_text = scrolledtext.ScrolledText(sections_frame, wrap=tk.WORD, width=80, height=15)
        self.sections_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Save button
        ttk.Button(
            frame, 
            text="Save Changes", 
            command=self.save_changes
        ).pack(pady=10)
    
    def setup_analyze_tab(self):
        """Setup the Analyze Job tab."""
        frame = ttk.Frame(self.tab_analyze, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Enter Job Description:", font=("", 12)).pack(pady=10)
        
        # Job description input
        self.job_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=10)
        self.job_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Or upload job description file
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="Or upload job description file:").pack(side=tk.LEFT)
        self.job_file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.job_file_path_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_job_description).pack(side=tk.LEFT)
        
        # Analyze button
        ttk.Button(
            frame, 
            text="Analyze Resume Against Job", 
            command=self.analyze_job,
            style="Accent.TButton"
        ).pack(pady=10)
        
        # Results
        ttk.Label(frame, text="Analysis Results:", font=("", 12)).pack(pady=5)
        
        results_frame = ttk.Frame(frame)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Keywords found
        ttk.Label(results_frame, text="Keywords:").pack(anchor=tk.W)
        self.keywords_var = tk.StringVar()
        ttk.Entry(results_frame, textvariable=self.keywords_var, state="readonly", width=80).pack(fill=tk.X, pady=5)
        
        # Suggestions
        ttk.Label(results_frame, text="Suggestions:").pack(anchor=tk.W)
        self.suggestions_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, width=80, height=8, state=tk.DISABLED)
        self.suggestions_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_generate_tab(self):
        """Setup the Generate Resume tab."""
        frame = ttk.Frame(self.tab_generate, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Generate New Resume PDF:", font=("", 12)).pack(pady=10)
        
        # Template selection
        template_frame = ttk.Frame(frame)
        template_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(template_frame, text="Select Template:").pack(side=tk.LEFT)
        self.template_var = tk.StringVar(value="modern")
        template_combo = ttk.Combobox(
            template_frame, 
            textvariable=self.template_var,
            values=["modern", "classic", "minimal", "professional", "creative"],
            state="readonly",
            width=20
        )
        template_combo.pack(side=tk.LEFT, padx=5)
        
        # Output location
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(output_frame, text="Output File:").pack(side=tk.LEFT)
        self.output_path_var = tk.StringVar(value="new_resume.pdf")
        ttk.Entry(output_frame, textvariable=self.output_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output_location).pack(side=tk.LEFT)
        
        # Preview text
        ttk.Label(frame, text="Preview:").pack(anchor=tk.W, pady=5)
        
        preview_frame = ttk.Frame(frame, relief=tk.SUNKEN, borderwidth=1)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, width=80, height=15)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Generate button
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame, 
            text="Update Preview", 
            command=self.update_preview
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Generate PDF Resume", 
            command=self.generate_resume,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        # Continue iteration button - newly added
        ttk.Button(
            button_frame, 
            text="Continue to iterate?", 
            command=self.continue_iteration
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_replace_tab(self):
        """Setup the Replace PDF Content tab."""
        frame = ttk.Frame(self.tab_replace, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Replace PDF Content While Preserving Format", font=("", 12, "bold")).pack(pady=10)
        
        # Description
        description = (
            "This feature allows you to replace the content of your resume PDF while preserving "
            "the original formatting, layout, and visual style. The resume structure is analyzed, "
            "content is improved using AI, and the original PDF format is maintained."
        )
        
        desc_label = ttk.Label(frame, text=description, wraplength=600)
        desc_label.pack(pady=10, fill=tk.X)
        
        # Input PDF selection
        input_frame = ttk.LabelFrame(frame, text="Input PDF")
        input_frame.pack(fill=tk.X, pady=10, padx=5)
        
        pdf_selection_frame = ttk.Frame(input_frame)
        pdf_selection_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(pdf_selection_frame, text="PDF Resume:").pack(side=tk.LEFT)
        self.replace_pdf_path_var = tk.StringVar()
        ttk.Entry(pdf_selection_frame, textvariable=self.replace_pdf_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            pdf_selection_frame, 
            text="Browse...", 
            command=lambda: self.browse_pdf_file(self.replace_pdf_path_var)
        ).pack(side=tk.LEFT)
        
        # Output PDF selection
        output_frame = ttk.LabelFrame(frame, text="Output PDF")
        output_frame.pack(fill=tk.X, pady=10, padx=5)
        
        output_selection_frame = ttk.Frame(output_frame)
        output_selection_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(output_selection_frame, text="Output:").pack(side=tk.LEFT)
        self.replace_output_path_var = tk.StringVar(value="improved_resume.pdf")
        ttk.Entry(output_selection_frame, textvariable=self.replace_output_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            output_selection_frame, 
            text="Browse...", 
            command=lambda: self.browse_output_location_for_var(self.replace_output_path_var)
        ).pack(side=tk.LEFT)
        
        # Job Description for targeting
        job_frame = ttk.LabelFrame(frame, text="Job Description (Optional)")
        job_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        self.replace_job_text = scrolledtext.ScrolledText(job_frame, wrap=tk.WORD, height=8)
        self.replace_job_text.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(frame, text="Options")
        options_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Use OCR option
        self.use_ocr_var = tk.BooleanVar(value=False)
        ocr_check = ttk.Checkbutton(
            options_frame,
            text="Use OCR (for scanned or image-based PDFs)",
            variable=self.use_ocr_var
        )
        ocr_check.pack(anchor=tk.W, pady=5, padx=5)
        
        # Use direct PDF manipulation option
        self.use_direct_var = tk.BooleanVar(value=True)
        direct_check = ttk.Checkbutton(
            options_frame,
            text="Use direct PDF manipulation (better format preservation)",
            variable=self.use_direct_var
        )
        direct_check.pack(anchor=tk.W, pady=5, padx=5)
        
        # Action buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text="Load PDF",
            command=self.load_pdf_for_replacement
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Analyze PDF Structure",
            command=self.analyze_pdf_structure
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Replace Content",
            command=self.replace_pdf_content,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        # Status and results frame
        results_frame = ttk.LabelFrame(frame, text="Analysis Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        self.replace_results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, height=6)
        self.replace_results_text.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
    
    def setup_api_tab(self):
        """Set up the API Settings tab."""
        frame = ttk.Frame(self.tab_api, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # API URL
        ttk.Label(frame, text="API URL:").grid(column=0, row=0, sticky=tk.W, pady=5)
        self.api_url_var = tk.StringVar(value=self.api_client.base_url)
        self.api_url_entry = ttk.Entry(frame, width=50, textvariable=self.api_url_var)
        self.api_url_entry.grid(column=1, row=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # API Key
        ttk.Label(frame, text="API Key:").grid(column=0, row=1, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value=self.api_client.api_key)
        self.api_key_entry = ttk.Entry(frame, width=50, textvariable=self.api_key_var, show="*")
        self.api_key_entry.grid(column=1, row=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Show/Hide API Key
        self.show_api_key_var = tk.BooleanVar(value=False)
        self.show_api_key_check = ttk.Checkbutton(
            frame, 
            text="Show API Key", 
            variable=self.show_api_key_var,
            command=self.toggle_api_key_visibility
        )
        self.show_api_key_check.grid(column=2, row=1, padx=5, pady=5)
        
        # API Timeout
        ttk.Label(frame, text="Timeout (seconds):").grid(column=0, row=2, sticky=tk.W, pady=5)
        # Use a default value if timeout is not set in the API client
        timeout_value = getattr(self.api_client, 'timeout', 30)
        self.api_timeout_var = tk.IntVar(value=timeout_value)
        self.api_timeout_spin = ttk.Spinbox(frame, from_=1, to=120, width=5, textvariable=self.api_timeout_var)
        self.api_timeout_spin.grid(column=1, row=2, sticky=tk.W, padx=5, pady=5)
        
        # Save and Test buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(column=0, row=3, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Save Settings", command=self.save_api_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test Connection", command=self.test_api_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Default", command=self.reset_api_settings).pack(side=tk.LEFT, padx=5)
        
        # Status message
        self.api_status_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.api_status_var, foreground="blue").grid(
            column=0, row=4, columnspan=3, sticky=tk.W, pady=10
        )
        
        # Available API endpoints section
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(column=0, row=5, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        ttk.Label(frame, text="Available API Endpoints:", font=("", 10, "bold")).grid(
            column=0, row=6, sticky=tk.W, pady=5
        )
        
        endpoints_text = (
            "• /analyze-resume - Analyze resume for keywords and suggestions\n"
            "• /upload-pdf - Upload resume PDF for processing\n"
            "• /templates - Get available resume templates\n"
            "• /generate-resume - Generate optimized resume\n"
            "• /optimize-keywords - Get keyword optimization suggestions"
        )
        endpoints_label = ttk.Label(frame, text=endpoints_text, justify=tk.LEFT)
        endpoints_label.grid(column=0, row=7, columnspan=3, sticky=tk.W, pady=5)
    
    def toggle_api_key_visibility(self):
        """Toggle the visibility of the API key."""
        if self.show_api_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
    
    def test_local_llm_connection(self):
        """Test connection to the local LLM server."""
        host = self.llm_host_var.get()
        port = self.llm_port_var.get()
        
        if not host or not port:
            messagebox.showerror("Error", "Please provide host and port for the local LLM server.")
            return
        
        try:
            # Update status
            self.status_var.set(f"Testing connection to LLM Studio at {host}:{port}...")
            self.root.update_idletasks()
            
            # Use our adapter class for a proper test
            from utils.local_llm_adapter import LocalLLMAdapter
            adapter = LocalLLMAdapter(
                host=host,
                port=int(port),  # Convert to integer
                model_name="qwen-14b"
            )
            
            # Test the connection
            success = adapter.test_connection()
            
            if success:
                self.status_var.set(f"LLM Studio connection successful at {host}:{port}")
                messagebox.showinfo("Success", f"Successfully connected to LLM Studio at {host}:{port}")
                
                # Update API integration to use this connection
                if self.use_local_llm_var.get():
                    self.api_integration.llm_host = host
                    self.api_integration.llm_port = int(port)
                    self.api_integration.switch_connection(ConnectionType.LLM_DIRECT)
            else:
                self.status_var.set(f"LLM Studio connection failed at {host}:{port}")
                messagebox.showerror("Error", f"Failed to connect to LLM Studio at {host}:{port}")
        except Exception as e:
            self.status_var.set(f"Error connecting to LLM Studio: {str(e)}")
            messagebox.showerror("Error", f"Failed to connect to LLM Studio: {str(e)}")
    
    def save_api_settings(self):
        """Save API settings from the form to the API client."""
        try:
            self.api_client.base_url = self.api_url_var.get().strip()
            self.api_client.api_key = self.api_key_var.get().strip()
            self.api_client.timeout = self.api_timeout_var.get()
            self.api_status_var.set("Settings saved successfully!")
        except Exception as e:
            self.api_status_var.set(f"Error saving settings: {str(e)}")
    
    def reset_api_settings(self):
        """Reset API settings to default values."""
        self.api_client.reset_to_defaults()
        self.api_url_var.set(self.api_client.base_url)
        self.api_key_var.set(self.api_client.api_key)
        self.api_timeout_var.set(self.api_client.timeout)
        self.api_status_var.set("Settings reset to default values.")
    
    def test_api_connection(self):
        """Test the API connection with current settings."""
        self.save_api_settings()
        self.api_status_var.set("Testing connection...")
        self.root.update_idletasks()
        
        try:
            success = self.api_client.test_connection()
            if success:
                self.api_status_var.set("✓ Connection successful! API is available.")
            else:
                self.api_status_var.set("✗ Connection failed. Check API URL and credentials.")
        except Exception as e:
            self.api_status_var.set(f"✗ Error testing connection: {str(e)}")
    
    def browse_resume(self):
        """Open file dialog to select a resume PDF."""
        filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Resume PDF", filetypes=filetypes)
        
        if filename:
            self.file_path_var.set(filename)
            self.input_pdf_path = filename
    
    def extract_resume(self):
        """Extract content from the selected resume PDF."""
        if not self.input_pdf_path:
            messagebox.showerror("Error", "Please select a resume PDF file first.")
            return
        
        try:
            self.status_var.set("Extracting resume content...")
            self.root.update_idletasks()
            
            # Set the OpenAI API key if provided
            api_key = self.api_key_var.get().strip()
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
            
            # Extract content from the PDF
            extractor = PDFExtractor()
            
            # Use LLM refinement if enabled
            if self.use_llm_var.get():
                self.status_var.set("Extracting and refining resume content with LLM...")
                self.root.update_idletasks()
                
                # Import here to ensure we have the latest API key
                from utils.llm_refiner import LLMRefiner
                
                # Extract basic content
                basic_resume = extractor.extract(self.input_pdf_path)
                
                # Refine with LLM
                refiner = LLMRefiner(api_key=api_key)
                self.resume_content = refiner.refine_resume(basic_resume)
            else:
                # Just use regular extraction without LLM refinement
                self.resume_content = extractor.extract(self.input_pdf_path)
            
            # Update edit tab with extracted content
            self.name_var.set(self.resume_content.contact_info.get('name', ''))
            self.email_var.set(self.resume_content.contact_info.get('email', ''))
            self.phone_var.set(self.resume_content.contact_info.get('phone', ''))
            self.linkedin_var.set(self.resume_content.contact_info.get('linkedin', ''))
            
            # Add sections to the text widget
            self.sections_text.delete(1.0, tk.END)
            for section in self.resume_content.sections:
                self.sections_text.insert(tk.END, f"{section.title}\n{'-' * len(section.title)}\n{section.content}\n\n")
            
            # Update preview
            self.update_preview()
            
            # Switch to edit tab
            self.notebook.select(1)  # Switch to the edit tab (index 1)
            
            self.status_var.set("Resume content extracted successfully.")
            messagebox.showinfo("Success", "Resume content extracted successfully.")
        except ImportError as e:
            self.status_var.set("Error: LLM refinement module not available.")
            messagebox.showerror("Error", "LLM refinement module not available. Make sure all required packages are installed.")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to extract resume content: {str(e)}")
    
    def save_changes(self):
        """Save changes made to the resume content."""
        if not self.resume_content:
            messagebox.showerror("Error", "No resume content loaded.")
            return
        
        try:
            # Update contact info
            self.resume_content.set_contact_info(
                name=self.name_var.get(),
                email=self.email_var.get(),
                phone=self.phone_var.get(),
                linkedin=self.linkedin_var.get()
            )
            
            # Update sections (this is a simplified approach)
            # In a more robust application, you'd have a better UI for editing sections
            self.resume_content.sections = []
            
            sections_text = self.sections_text.get(1.0, tk.END)
            sections = sections_text.split('\n\n')
            
            for section_text in sections:
                if not section_text.strip():
                    continue
                    
                lines = section_text.strip().split('\n')
                if len(lines) >= 2:
                    title = lines[0]
                    content = '\n'.join(lines[2:]) if len(lines) > 2 else ''
                    self.resume_content.add_section(title, content)
            
            self.status_var.set("Changes saved.")
            self.update_preview()
            messagebox.showinfo("Success", "Changes saved successfully.")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")
    
    def browse_job_description(self):
        """Open file dialog to select a job description file."""
        filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Job Description File", filetypes=filetypes)
        
        if filename:
            self.job_file_path_var.set(filename)
            try:
                with open(filename, 'r') as f:
                    job_text = f.read()
                    self.job_text.delete(1.0, tk.END)
                    self.job_text.insert(tk.END, job_text)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read job description file: {str(e)}")
    
    def analyze_job(self):
        """Analyze the resume against the job description."""
        if not self.resume_content:
            messagebox.showerror("Error", "No resume content loaded. Please extract a resume first.")
            return
        
        job_text = self.job_text.get(1.0, tk.END).strip()
        if not job_text:
            messagebox.showerror("Error", "Please enter a job description.")
            return
        
        try:
            self.status_var.set("Analyzing resume against job description...")
            self.root.update_idletasks()
            
            analyzer = JobAnalyzer()
            keywords, suggestions = analyzer.analyze(job_text, self.resume_content)
            
            # Update results
            self.keywords_var.set(", ".join(keywords))
            
            self.suggestions_text.config(state=tk.NORMAL)
            self.suggestions_text.delete(1.0, tk.END)
            for suggestion in suggestions:
                self.suggestions_text.insert(tk.END, f"• {suggestion}\n\n")
            self.suggestions_text.config(state=tk.DISABLED)
            
            self.status_var.set("Analysis complete.")
            messagebox.showinfo("Success", "Resume analysis complete.")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to analyze resume: {str(e)}")
    
    def browse_output_location(self):
        """Open file dialog to select output location."""
        filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(title="Save Resume PDF As", filetypes=filetypes, defaultextension=".pdf")
        
        if filename:
            self.output_path_var.set(filename)
            self.output_pdf_path = filename
    
    def update_preview(self):
        """Update the preview of the resume content."""
        if not self.resume_content:
            return
        
        # Update the resume content with current values from UI
        self.resume_content.set_contact_info(
            name=self.name_var.get(),
            email=self.email_var.get(),
            phone=self.phone_var.get(),
            linkedin=self.linkedin_var.get()
        )
        
        # Show preview in text widget
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, str(self.resume_content))
        self.preview_text.config(state=tk.NORMAL)
    
    def generate_resume(self):
        """Generate the new resume PDF."""
        if not self.resume_content:
            messagebox.showerror("Error", "No resume content loaded. Please extract a resume first.")
            return
        
        output_path = self.output_path_var.get()
        if not output_path:
            messagebox.showerror("Error", "Please specify an output file path.")
            return
        
        try:
            self.status_var.set("Generating resume PDF...")
            self.root.update_idletasks()
            
            # Update resume content with current values
            self.update_preview()
            
            # Generate the PDF
            generator = ResumeGenerator()
            output_file = generator.generate(
                self.resume_content,
                template=self.template_var.get(),
                output_path=output_path
            )
            
            self.status_var.set(f"Resume generated successfully: {output_file}")
            messagebox.showinfo("Success", f"Resume PDF generated successfully: {output_file}")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate resume: {str(e)}")
    
    def test_api_connection(self):
        """Test the API connection."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key.")
            return
        
        try:
            self.status_var.set("Testing API connection...")
            self.root.update_idletasks()
            
            self.api_client.set_api_key(api_key)
            success = self.api_client.test_connection()
            
            if success:
                self.status_var.set("API connection successful.")
                messagebox.showinfo("Success", "API connection successful.")
            else:
                self.status_var.set("API connection failed.")
                messagebox.showerror("Error", "API connection failed.")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to test API connection: {str(e)}")
    
    def continue_iteration(self):
        """Allow the user to continue iterating on the resume after initial generation."""
        if not hasattr(self, 'resume_content') or not self.resume_content:
            messagebox.showwarning("Warning", "Please generate a resume first before continuing iteration.")
            return
        
        # Create a dialog to get iteration feedback
        dialog = tk.Toplevel(self.root)
        dialog.title("Continue Iteration")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="What would you like to improve in this version?", font=("", 12)).pack(pady=10)
        
        feedback_frame = ttk.Frame(dialog)
        feedback_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        feedback_text = scrolledtext.ScrolledText(feedback_frame, wrap=tk.WORD, width=70, height=10)
        feedback_text.pack(fill=tk.BOTH, expand=True)
        feedback_text.insert(tk.END, "Example: Make the summary more concise and highlight my leadership skills more prominently.")
        feedback_text.bind("<FocusIn>", lambda e: feedback_text.delete("1.0", tk.END) if feedback_text.get("1.0", tk.END).strip().startswith("Example:") else None)
        
        options_frame = ttk.Frame(dialog)
        options_frame.pack(fill=tk.X, pady=10)
        
        focus_var = tk.StringVar(value="skills")
        ttk.Label(options_frame, text="Focus area:").pack(side=tk.LEFT, padx=5)
        focus_combo = ttk.Combobox(
            options_frame,
            textvariable=focus_var,
            values=["skills", "experience", "education", "summary", "formatting", "keywords"],
            state="readonly",
            width=15
        )
        focus_combo.pack(side=tk.LEFT, padx=5)
        
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        def submit_iteration():
            feedback = feedback_text.get("1.0", tk.END).strip()
            focus = focus_var.get()
            
            if not feedback or feedback.startswith("Example:"):
                messagebox.showwarning("Warning", "Please provide specific feedback for iteration.")
                return
            
            dialog.destroy()
            self.process_iteration_feedback(feedback, focus)
        
        ttk.Button(
            buttons_frame,
            text="Submit for Iteration",
            command=submit_iteration,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(
            buttons_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT)
        
    def process_iteration_feedback(self, feedback, focus):
        """Process the iteration feedback and update the resume."""
        self.status_var.set("Processing iteration feedback...")
        self.root.update_idletasks()
        
        try:
            # Use the API integration with the currently configured backend
            try:
                # Ensure server is running (applies to ManageAI mode)
                self.api_integration.ensure_server_running()
                
                # Process the iteration based on the current connection type
                if self.api_integration.connection_type == ConnectionType.MANAGE_AI:
                    improved_resume = self.api_integration.improve_resume(
                        resume_content=self.resume_content,
                        job_description=self.job_description,
                        feedback=feedback
                    )
                    
                    if improved_resume:
                        if 'improved_resume' in improved_resume:
                            self.resume_content = improved_resume['improved_resume']
                        elif 'content' in improved_resume:
                            self.resume_content = improved_resume['content']
                        else:
                            # Just use what we got back
                            self.resume_content = improved_resume
                    else:
                        messagebox.showwarning("Warning", "No improvements returned from API.")
                        return
                elif self.api_integration.connection_type == ConnectionType.LLM_DIRECT:
                    # Direct LLM mode - send a tailored prompt
                    system_prompt = (
                        "You are a professional resume writer. Your task is to improve the user's resume "
                        "based on their feedback. Focus on making the improvements requested while maintaining "
                        "a professional tone and format."
                    )
                    
                    user_prompt = f"Please improve this resume with a focus on {focus}.\n\n"
                    user_prompt += f"Resume content:\n{self.resume_content}\n\n"
                    user_prompt += f"Feedback: {feedback}\n\n"
                    user_prompt += "Please return the complete improved resume."
                    
                    from utils.local_llm_adapter import LocalLLMAdapter
                    llm = LocalLLMAdapter(
                        host=self.llm_host_var.get(),
                        port=int(self.llm_port_var.get()),
                        model_name="qwen-14b"  # Default model
                    )
                    
                    improved_content = llm.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=0.3,  # Lower temperature for more consistent results
                        max_tokens=4000
                    )
                    
                    if improved_content:
                        self.resume_content = improved_content
                    else:
                        messagebox.showwarning("Warning", "No improvements returned from LLM.")
                        return
                        
                # Fallback for other connection types
                else:
                    # Use the LLM refiner utility as fallback
                    from utils.llm_refiner import refine_resume
                    improved_content = refine_resume(
                        self.resume_content, 
                        feedback=feedback,
                        focus_area=focus
                    )
                    
                    if improved_content:
                        self.resume_content = improved_content
                    else:
                        messagebox.showwarning("Warning", "No improvements generated.")
                        return
                
                # Update the preview with new content
                self.update_preview()
                self.status_var.set(f"Resume updated with focus on {focus}")
                
                # Show confirmation dialog
                messagebox.showinfo("Success", "Resume has been updated based on your feedback.")
                
            except Exception as api_error:
                print(f"API error during iteration: {api_error}")  # Use print instead of logger
                messagebox.showwarning("API Error", f"Error using API for iteration: {str(api_error)}. Falling back to local processing.")
                
                # Fallback to local processing
                from utils.llm_refiner import refine_resume
                improved_content = refine_resume(
                    self.resume_content, 
                    feedback=feedback,
                    focus_area=focus
                )
                
                if improved_content:
                    self.resume_content = improved_content
                    self.update_preview()
                    self.status_var.set(f"Resume updated with focus on {focus} (local processing)")
                else:
                    messagebox.showerror("Error", "Failed to improve resume with local processing.")
                    return
            messagebox.showinfo("Success", "Resume has been updated based on your feedback.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process iteration: {str(e)}")
        finally:
            self.status_var.set("Ready")
    
    def _stop_manageai_server(self):
        """Stop the ManageAI API server if it was started by this application."""
        if hasattr(self, 'manageai_api_manager'):
            self.manageai_api_manager.stop_server()
            self.status_var.set("ManageAI API server stopped.")
    
    def _start_manageai_server(self):
        """Start the ManageAI API server if it's not already running."""
        try:
            if hasattr(self, 'manageai_api_manager'):
                # Try to start the server
                success = self.manageai_api_manager.start_server()
                if success:
                    self.status_var.set("ManageAI API server started.")
                    return True
                else:
                    self.status_var.set("Failed to start ManageAI API server.")
                    return False
        except Exception as e:
            self.status_var.set(f"Error starting ManageAI API server: {str(e)}")
            return False
    
    def _check_pymupdf_availability(self):
        """Check if PyMuPDF is available for direct PDF manipulation."""
        try:
            import fitz  # PyMuPDF
            return True
        except ImportError:
            return False
    
    def _on_window_close(self):
        """Handle window close event."""
        try:
            # Stop the ManageAI API server
            self._stop_manageai_server()
            # Destroy the window
            self.root.destroy()
        except Exception as e:
            print(f"Error shutting down: {e}")
            self.root.destroy()

    def browse_pdf_file(self, path_var):
        """Open file dialog to select a PDF file and set it to the provided StringVar."""
        filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select PDF File", filetypes=filetypes)
        
        if filename:
            path_var.set(filename)
    
    def browse_output_location_for_var(self, path_var):
        """Open file dialog to select output location and set it to the provided StringVar."""
        filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(title="Save PDF As", filetypes=filetypes, defaultextension=".pdf")
        
        if filename:
            path_var.set(filename)
    
    def analyze_pdf_structure(self):
        """Analyze the structure of the selected PDF for content replacement."""
        pdf_path = self.replace_pdf_path_var.get()
        
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "Please select a valid PDF file first.")
            return
        
        try:
            self.status_var.set("Analyzing PDF structure...")
            self.root.update_idletasks()
            
            # Configure the PDF replacer based on UI selections
            self.pdf_replacer.use_enhanced = True
            self.pdf_replacer.use_ocr = self.use_ocr_var.get()
            self.pdf_replacer.use_direct = self.use_direct_var.get() and self.has_pymupdf
            
            # Analyze the structure
            structure = self.pdf_replacer.analyze_structure(pdf_path)
            
            # Format the result for display
            result_text = "PDF Structure Analysis:\n\n"
            
            # Add sections info
            result_text += "Detected Sections:\n"
            for section_name, section_data in structure.get('sections', {}).items():
                word_count = len(section_data.get('content', '').split())
                result_text += f"• {section_name}: {word_count} words\n"
            
            # Add layout info
            result_text += "\nLayout Information:\n"
            result_text += f"• Pages: {structure.get('page_count', 0)}\n"
            result_text += f"• Text blocks: {structure.get('text_block_count', 0)}\n"
            result_text += f"• Detected format: {structure.get('format_type', 'Standard')}\n"
            
            # Add strategy info
            result_text += f"\nSelected Strategy: {'PyMuPDF Direct' if self.use_direct_var.get() and self.has_pymupdf else 'Enhanced PDF Processing'}"
            result_text += f"\nOCR Enabled: {'Yes' if self.use_ocr_var.get() else 'No'}"
            
            # Update the results text
            self.replace_results_text.delete(1.0, tk.END)
            self.replace_results_text.insert(tk.END, result_text)
            
            self.status_var.set("PDF structure analysis complete.")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to analyze PDF structure: {str(e)}")
    
    def replace_pdf_content(self):
        """Replace content in the PDF while preserving formatting."""
        input_pdf = self.replace_pdf_path_var.get()
        output_pdf = self.replace_output_path_var.get()
        job_text = self.replace_job_text.get(1.0, tk.END).strip()
        
        if not input_pdf or not os.path.exists(input_pdf):
            messagebox.showerror("Error", "Please select a valid input PDF file.")
            return
            
        if not output_pdf:
            messagebox.showerror("Error", "Please specify an output PDF file.")
            return
        
        # Check if we need to load the PDF first
        if not hasattr(self, 'pdf_replacement_content'):
            response = messagebox.askyesno("PDF Not Loaded", 
                                        "You haven't loaded the PDF content yet. Would you like to load it now?")
            if response:
                self.load_pdf_for_replacement()
                if not hasattr(self, 'pdf_replacement_content'):
                    return  # Loading failed
            else:
                return  # User cancelled
        
        try:
            self.status_var.set("Replacing PDF content...")
            self.root.update_idletasks()
            
            # Configure the PDF replacer based on UI selections
            self.pdf_replacer.use_enhanced = True
            self.pdf_replacer.use_ocr = self.use_ocr_var.get()
            self.pdf_replacer.use_direct = self.use_direct_var.get() and self.has_pymupdf
            self.pdf_replacer.use_llm = True  # Always use LLM for content improvement
            
            # Process the replacement - use the pre-loaded content if available
            if hasattr(self, 'pdf_replacement_content'):
                result = self.pdf_replacer.replace_content_with_data(
                    input_path=input_pdf,
                    output_path=output_pdf,
                    content=self.pdf_replacement_content,
                    job_description=job_text if job_text else None
                )
            else:
                # Fallback to original method
                result = self.pdf_replacer.replace_content(
                    input_path=input_pdf,
                    output_path=output_pdf,
                    job_description=job_text if job_text else None
                )
            
            if result and os.path.exists(output_pdf):
                self.status_var.set("PDF content replacement complete.")
                
                # Show success details
                message = (
                    f"PDF content has been successfully replaced and saved to:\n\n"
                    f"{output_pdf}\n\n"
                    f"Would you like to open the file now?"
                )
                
                if messagebox.askyesno("Success", message):
                    # Open the PDF with the system's default PDF viewer
                    if sys.platform == "darwin":  # macOS
                        os.system(f"open '{output_pdf}'")
                    elif sys.platform == "win32":  # Windows
                        os.system(f'start "" "{output_pdf}"')
                    else:  # Linux/Unix
                        os.system(f"xdg-open '{output_pdf}'")
            else:
                raise Exception("PDF processing completed but the output file was not created.")
                
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to replace PDF content: {str(e)}")
    
    def load_pdf_for_replacement(self):
        """Load and extract content from the selected PDF for replacement."""
        pdf_path = self.replace_pdf_path_var.get()
        
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "Please select a valid PDF file first.")
            return
        
        try:
            self.status_var.set("Loading PDF content...")
            self.root.update_idletasks()
            
            # Configure the PDF replacer based on UI selections
            self.pdf_replacer.use_enhanced = True
            self.pdf_replacer.use_ocr = self.use_ocr_var.get()
            self.pdf_replacer.use_direct = self.use_direct_var.get() and self.has_pymupdf
            
            # Extract the content
            content = self.pdf_replacer.extract_content(pdf_path)
            
            # Show content summary
            result_text = "PDF Content Loaded Successfully:\n\n"
            result_text += f"• File: {os.path.basename(pdf_path)}\n"
            result_text += f"• Size: {os.path.getsize(pdf_path) / 1024:.1f} KB\n"
            result_text += f"• Content extracted: {len(content)} characters\n"
            result_text += "\nYou can now analyze the structure or replace the content."
            
            # Update the results text
            self.replace_results_text.delete(1.0, tk.END)
            self.replace_results_text.insert(tk.END, result_text)
            
            self.status_var.set("PDF content loaded successfully.")
            
            # Store the extracted content for later use
            self.pdf_replacement_content = content
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to load PDF content: {str(e)}")

    def setup_chat_workspace_tab(self):
        """Setup the unified Chat Workspace tab with enhanced components."""
        try:
            from utils.chat_interface import ChatInterface
            from utils.pdf_viewer import PDFViewer
            from utils.enhanced_editor import EnhancedEditor
        except ImportError:
            # Fallback to basic implementation if enhanced components aren't available
            self.setup_chat_workspace_tab_basic()
            return
        
        # Main container with paned window for resizable panels
        main_paned = ttk.PanedWindow(self.tab_chat_workspace, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for chat interface
        self.chat_frame = ttk.Frame(main_paned, width=350)
        
        # Initialize enhanced chat interface
        self.chat_interface = ChatInterface(
            self.chat_frame,
            llm_callback=self.process_chat_with_llm
        )
        
        # Right panel with PDF viewer and edit tools
        right_paned = ttk.PanedWindow(main_paned, orient=tk.VERTICAL)
        
        # PDF Viewer section
        pdf_frame = ttk.LabelFrame(right_paned, text="Resume Preview")
        self.pdf_viewer = PDFViewer(pdf_frame)
        
        # Enhanced Editor section
        edit_frame = ttk.LabelFrame(right_paned, text="Resume Editor")
        self.enhanced_editor = EnhancedEditor(
            edit_frame,
            content_changed_callback=self.on_editor_content_changed
        )
        
        # Add session management toolbar at the top
        session_toolbar = ttk.Frame(self.tab_chat_workspace)
        session_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(session_toolbar, text="Session:", font=("", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Button(session_toolbar, text="Load Resume", command=self.load_resume_for_enhanced_workspace).pack(side=tk.LEFT, padx=2)
        ttk.Button(session_toolbar, text="Export Session", command=self.export_workspace_session).pack(side=tk.LEFT, padx=2)
        ttk.Button(session_toolbar, text="Import Session", command=self.import_workspace_session).pack(side=tk.LEFT, padx=2)
        ttk.Button(session_toolbar, text="Save Resume", command=self.save_enhanced_workspace_resume).pack(side=tk.LEFT, padx=2)
        
        # Add separator
        ttk.Separator(session_toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Add quick actions
        ttk.Label(session_toolbar, text="Quick Actions:", font=("", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Button(session_toolbar, text="Format Resume", command=self.quick_format_resume).pack(side=tk.LEFT, padx=2)
        ttk.Button(session_toolbar, text="Check ATS", command=self.quick_ats_check).pack(side=tk.LEFT, padx=2)
        ttk.Button(session_toolbar, text="Generate Summary", command=self.quick_generate_summary).pack(side=tk.LEFT, padx=2)
        
        # Add panels to paned windows
        right_paned.add(pdf_frame, weight=2)
        right_paned.add(edit_frame, weight=1)
        
        main_paned.add(self.chat_frame, weight=1)
        main_paned.add(right_paned, weight=3)
        
        # Initialize workspace variables
        self.workspace_resume_content = None
        self.workspace_pdf_path = None
        
        # Add welcome message
        self.chat_interface.add_system_message(
            "Welcome to the Resume Chat Workspace! Load a resume to get started with AI-powered improvements."
        )

    def setup_chat_workspace_tab_basic(self):
        """Basic setup when enhanced components aren't available."""
        # Keep the existing implementation as fallback
        # Main container with paned window for resizable panels
        main_paned = ttk.PanedWindow(self.tab_chat_workspace, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for chat interface (initially collapsed)
        self.chat_frame = ttk.Frame(main_paned)
        self.chat_collapsed = tk.BooleanVar(value=False)  # Start expanded for now
        
        # Chat panel content
        chat_container = ttk.LabelFrame(self.chat_frame, text="Resume Assistant Chat")
        chat_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Chat controls
        chat_controls = ttk.Frame(chat_container)
        chat_controls.pack(fill=tk.X, pady=(0, 5))
        
        # Collapse/expand button
        self.toggle_chat_btn = ttk.Button(
            chat_controls, 
            text="◀ Collapse", 
            command=self.toggle_chat_panel,
            width=12
        )
        self.toggle_chat_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear chat button
        ttk.Button(
            chat_controls, 
            text="Clear Chat", 
            command=self.clear_chat,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        # Chat history display
        chat_history_frame = ttk.Frame(chat_container)
        chat_history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.chat_history = scrolledtext.ScrolledText(
            chat_history_frame,
            wrap=tk.WORD,
            height=15,
            state=tk.DISABLED
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True)
        
        # Chat input area
        input_frame = ttk.Frame(chat_container)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Ask about your resume:").pack(anchor=tk.W)
        
        # Chat input with scrolled text for multiline input
        self.chat_input = scrolledtext.ScrolledText(
            input_frame,
            height=3,
            wrap=tk.WORD
        )
        self.chat_input.pack(fill=tk.X, pady=2)
        
        # Send button and quick actions
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(
            button_frame,
            text="Send",
            command=self.send_chat_message,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=2)
        
        # Quick action buttons
        ttk.Button(
            button_frame,
            text="Improve Resume",
            command=lambda: self.send_quick_message("Please review my resume and suggest improvements")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="Tailor for Job",
            command=lambda: self.send_quick_message("Help me tailor this resume for a specific job")
        ).pack(side=tk.LEFT, padx=2)
        
        # Right panel with PDF viewer and edit tools
        right_paned = ttk.PanedWindow(main_paned, orient=tk.VERTICAL)
        
        # PDF Viewer section
        pdf_frame = ttk.LabelFrame(right_paned, text="Resume Preview")
        
        # PDF viewer controls
        pdf_controls = ttk.Frame(pdf_frame)
        pdf_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(pdf_controls, text="Load Resume", command=self.load_resume_for_workspace).pack(side=tk.LEFT, padx=5)
        ttk.Button(pdf_controls, text="Refresh Preview", command=self.refresh_pdf_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(pdf_controls, text="Save Changes", command=self.save_workspace_changes).pack(side=tk.LEFT, padx=5)
        
        # PDF display area (placeholder for now)
        self.pdf_display = scrolledtext.ScrolledText(
            pdf_frame,
            wrap=tk.WORD,
            height=20,
            state=tk.DISABLED
        )
        self.pdf_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Edit Tools section
        edit_frame = ttk.LabelFrame(right_paned, text="Edit Tools")
        
        # Edit tools controls
        edit_controls = ttk.Frame(edit_frame)
        edit_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(edit_controls, text="Undo", command=self.workspace_undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_controls, text="Redo", command=self.workspace_redo).pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_controls, text="Bold", command=self.apply_bold).pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_controls, text="Italic", command=self.apply_italic).pack(side=tk.LEFT, padx=2)
        
        # Section management
        section_controls = ttk.Frame(edit_frame)
        section_controls.pack(fill=tk.X, pady=5)
        
        ttk.Label(section_controls, text="Sections:").pack(side=tk.LEFT, padx=5)
        ttk.Button(section_controls, text="Add Section", command=self.add_resume_section).pack(side=tk.LEFT, padx=2)
        ttk.Button(section_controls, text="Remove Section", command=self.remove_resume_section).pack(side=tk.LEFT, padx=2)
        ttk.Button(section_controls, text="Reorder", command=self.reorder_sections).pack(side=tk.LEFT, padx=2)
        
        # Content editor
        self.content_editor = scrolledtext.ScrolledText(
            edit_frame,
            wrap=tk.WORD,
            height=15
        )
        self.content_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add panels to paned windows
        right_paned.add(pdf_frame, weight=2)
        right_paned.add(edit_frame, weight=1)
        
        main_paned.add(self.chat_frame, weight=1)
        main_paned.add(right_paned, weight=3)
        
        # Initialize workspace variables
        self.workspace_resume_content = None
        self.workspace_pdf_path = None
        self.chat_history_list = []
        self.edit_history = []
        self.edit_history_index = -1

    def toggle_chat_panel(self):
        """Toggle the visibility of the chat panel."""
        if self.chat_collapsed.get():
            # Expand chat panel
            self.chat_frame.pack(fill=tk.BOTH, expand=True)
            self.toggle_chat_btn.config(text="◀ Collapse")
            self.chat_collapsed.set(False)
        else:
            # Collapse chat panel
            self.chat_frame.pack_forget()
            self.toggle_chat_btn.config(text="▶ Expand")
            self.chat_collapsed.set(True)

    def clear_chat(self):
        """Clear the chat history."""
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.delete(1.0, tk.END)
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history_list.clear()

    def send_chat_message(self):
        """Send a message in the chat interface."""
        message = self.chat_input.get(1.0, tk.END).strip()
        if not message:
            return
        
        # Clear the input
        self.chat_input.delete(1.0, tk.END)
        
        # Add user message to chat
        self.add_chat_message("You", message)
        
        # Process with LLM (simplified for now)
        try:
            self.status_var.set("Processing your question...")
            response = self.process_chat_with_llm(message)
            self.add_chat_message("Assistant", response)
            self.status_var.set("Ready")
        except Exception as e:
            self.add_chat_message("System", f"Error: {str(e)}")
            self.status_var.set("Ready")

    def send_quick_message(self, message):
        """Send a predefined quick message."""
        self.chat_input.delete(1.0, tk.END)
        self.chat_input.insert(1.0, message)
        self.send_chat_message()

    def add_chat_message(self, sender, message):
        """Add a message to the chat history."""
        self.chat_history.config(state=tk.NORMAL)
        
        # Add timestamp and sender
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        # Format message
        formatted_message = f"[{timestamp}] {sender}: {message}\n\n"
        
        self.chat_history.insert(tk.END, formatted_message)
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)
        
        # Store in history list
        self.chat_history_list.append({
            "timestamp": timestamp,
            "sender": sender,
            "message": message
        })

    def process_chat_with_llm(self, message):
        """Process the chat message with LLM integration."""
        try:
            # Use existing API integration
            if not self.workspace_resume_content:
                return "Please load a resume first using the 'Load Resume' button."
            
            # Prepare context with current resume content
            resume_context = str(self.workspace_resume_content) if self.workspace_resume_content else "No resume loaded"
            
            # Create a context-aware prompt
            contextual_prompt = f"User question: {message}\n\nCurrent resume content:\n{resume_context}\n\nPlease provide helpful advice about the resume."
            
            # Use the existing API integration to get response
            response = self.api_integration.improve_resume(
                resume_content=resume_context,
                feedback=message
            )
            
            if isinstance(response, dict) and 'improved_resume' in response:
                return response['improved_resume']
            elif isinstance(response, dict) and 'analysis' in response:
                return response['analysis']
            else:
                return str(response)
                
        except Exception as e:
            return f"Sorry, I couldn't process your request. Error: {str(e)}"

    def load_resume_for_workspace(self):
        """Load a resume for the workspace."""
        filename = filedialog.askopenfilename(
            title="Select Resume PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.status_var.set("Loading resume...")
                self.workspace_pdf_path = filename
                
                # Extract content from PDF
                if hasattr(self, 'pdf_replacer') and self.pdf_replacer:
                    analysis = self.pdf_replacer.analyze_resume(filename)
                    self.workspace_resume_content = analysis.get('basic_resume', 'Could not extract content')
                    
                    # Update PDF display
                    self.pdf_display.config(state=tk.NORMAL)
                    self.pdf_display.delete(1.0, tk.END)
                    self.pdf_display.insert(tk.END, str(self.workspace_resume_content))
                    self.pdf_display.config(state=tk.DISABLED)
                    
                    # Update content editor
                    self.content_editor.delete(1.0, tk.END)
                    self.content_editor.insert(tk.END, str(self.workspace_resume_content))
                    
                    self.status_var.set("Resume loaded successfully")
                    self.add_chat_message("System", f"Resume loaded: {os.path.basename(filename)}")
                else:
                    raise Exception("PDF replacer not available")
                    
            except Exception as e:
                self.status_var.set(f"Error: {str(e)}")
                messagebox.showerror("Error", f"Failed to load resume: {str(e)}")

    def refresh_pdf_preview(self):
        """Refresh the PDF preview with current content."""
        if self.workspace_resume_content:
            self.pdf_display.config(state=tk.NORMAL)
            self.pdf_display.delete(1.0, tk.END)
            self.pdf_display.insert(tk.END, str(self.workspace_resume_content))
            self.pdf_display.config(state=tk.DISABLED)
            self.status_var.set("Preview refreshed")

    def save_workspace_changes(self):
        """Save changes made in the workspace."""
        if not self.workspace_pdf_path:
            messagebox.showwarning("Warning", "No resume loaded to save.")
            return
        
        try:
            # Get updated content from editor
            updated_content = self.content_editor.get(1.0, tk.END).strip()
            self.workspace_resume_content = updated_content
            
            # Save to new PDF (simplified)
            output_path = filedialog.asksaveasfilename(
                title="Save Resume As",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            
            if output_path:
                # For now, save as text file (would need proper PDF generation)
                with open(output_path.replace('.pdf', '.txt'), 'w') as f:
                    f.write(updated_content)
                
                self.status_var.set("Changes saved successfully")
                self.add_chat_message("System", f"Resume saved to: {os.path.basename(output_path)}")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")

    def workspace_undo(self):
        """Undo the last edit operation."""
        # Simplified undo - would need proper implementation
        self.add_chat_message("System", "Undo functionality - to be implemented")

    def workspace_redo(self):
        """Redo the last undone operation."""
        # Simplified redo - would need proper implementation
        self.add_chat_message("System", "Redo functionality - to be implemented")

    def apply_bold(self):
        """Apply bold formatting to selected text."""
        # Simplified formatting - would need proper implementation
        self.add_chat_message("System", "Bold formatting - to be implemented")

    def apply_italic(self):
        """Apply italic formatting to selected text."""
        # Simplified formatting - would need proper implementation
        self.add_chat_message("System", "Italic formatting - to be implemented")

    def add_resume_section(self):
        """Add a new section to the resume."""
        section_name = tk.simpledialog.askstring("Add Section", "Enter section name:")
        if section_name:
            current_content = self.content_editor.get(1.0, tk.END)
            new_section = f"\n\n{section_name}:\n[Add content here]\n"
            self.content_editor.insert(tk.END, new_section)
            self.add_chat_message("System", f"Added new section: {section_name}")

    def remove_resume_section(self):
        """Remove a section from the resume."""
        self.add_chat_message("System", "Section removal - to be implemented")

    def reorder_sections(self):
        """Reorder resume sections."""
        self.add_chat_message("System", "Section reordering - to be implemented")

    def on_editor_content_changed(self, new_content):
        """Handle changes in the enhanced editor."""
        if hasattr(self, 'pdf_viewer'):
            # Update PDF viewer with new content
            self.pdf_viewer.update_content(new_content)
        
        # Update workspace content
        self.workspace_resume_content = new_content
        
        # Notify chat interface about content changes
        if hasattr(self, 'chat_interface') and new_content != getattr(self, '_last_content', ''):
            self.chat_interface.add_system_message("Resume content updated in editor.")
            self._last_content = new_content

    def load_resume_for_enhanced_workspace(self):
        """Enhanced version of load resume for workspace."""
        if not hasattr(self, 'enhanced_editor'):
            # Fall back to basic method
            self.load_resume_for_workspace()
            return
        
        filename = filedialog.askopenfilename(
            title="Select Resume PDF",
            filetypes=[("PDF files", "*.pdf"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.status_var.set("Loading resume...")
                self.workspace_pdf_path = filename
                
                # Extract content from PDF
                if filename.endswith('.pdf') and hasattr(self, 'pdf_replacer') and self.pdf_replacer:
                    analysis = self.pdf_replacer.analyze_resume(filename)
                    content = analysis.get('basic_resume', 'Could not extract content')
                elif filename.endswith('.txt'):
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    content = f"Loaded file: {filename}\n[Content extraction not supported for this file type]"
                
                self.workspace_resume_content = content
                
                # Update all components
                if hasattr(self, 'pdf_viewer'):
                    self.pdf_viewer.load_pdf(filename, content)
                
                if hasattr(self, 'enhanced_editor'):
                    self.enhanced_editor.set_content(content)
                
                if hasattr(self, 'chat_interface'):
                    self.chat_interface.add_system_message(f"Resume loaded: {os.path.basename(filename)}")
                
                self.status_var.set("Resume loaded successfully")
                
            except Exception as e:
                self.status_var.set(f"Error: {str(e)}")
                messagebox.showerror("Error", f"Failed to load resume: {str(e)}")

    def apply_chat_suggestion(self, suggestion_text):
        """Apply a suggestion from the chat to the editor."""
        if hasattr(self, 'enhanced_editor'):
            # Insert suggestion at current cursor position
            self.enhanced_editor.insert_text(f"\n\n--- AI Suggestion ---\n{suggestion_text}\n--- End Suggestion ---\n")
            
            if hasattr(self, 'chat_interface'):
                self.chat_interface.add_system_message("Suggestion applied to editor. Review and integrate as needed.")
        else:
            # Fall back to basic implementation
            if hasattr(self, 'content_editor'):
                current_content = self.content_editor.get(1.0, tk.END)
                self.content_editor.insert(tk.END, f"\n\n--- AI Suggestion ---\n{suggestion_text}\n--- End Suggestion ---\n")

    def export_workspace_session(self):
        """Export the entire workspace session including chat history and content."""
        try:
            from tkinter import filedialog
            import json
            import datetime
            
            filename = filedialog.asksaveasfilename(
                title="Export Workspace Session",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                session_data = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "resume_path": self.workspace_pdf_path,
                    "resume_content": self.workspace_resume_content,
                    "chat_history": [],
                    "editor_content": ""
                }
                
                # Get chat history if available
                if hasattr(self, 'chat_interface'):
                    session_data["chat_history"] = self.chat_interface.get_chat_history()
                
                # Get editor content if available
                if hasattr(self, 'enhanced_editor'):
                    session_data["editor_content"] = self.enhanced_editor.get_content()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                
                if hasattr(self, 'chat_interface'):
                    self.chat_interface.add_system_message(f"Workspace session exported to: {os.path.basename(filename)}")
                
                self.status_var.set("Session exported successfully")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export session: {str(e)}")

    def import_workspace_session(self):
        """Import a previously exported workspace session."""
        try:
            from tkinter import filedialog
            import json
            
            filename = filedialog.askopenfilename(
                title="Import Workspace Session",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Restore resume content
                if "resume_content" in session_data:
                    self.workspace_resume_content = session_data["resume_content"]
                    
                    if hasattr(self, 'enhanced_editor'):
                        self.enhanced_editor.set_content(self.workspace_resume_content)
                    
                    if hasattr(self, 'pdf_viewer'):
                        self.pdf_viewer.update_content(self.workspace_resume_content)
                
                # Restore editor content if different
                if "editor_content" in session_data and hasattr(self, 'enhanced_editor'):
                    self.enhanced_editor.set_content(session_data["editor_content"])
                
                # Restore chat history
                if "chat_history" in session_data and hasattr(self, 'chat_interface'):
                    self.chat_interface.clear_chat()
                    for msg in session_data["chat_history"]:
                        self.chat_interface.add_message(
                            msg["sender"], 
                            msg["message"], 
                            msg.get("type", "user")
                        )
                    
                    self.chat_interface.add_system_message(f"Session imported from: {os.path.basename(filename)}")
                
                self.status_var.set("Session imported successfully")
                
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import session: {str(e)}")

    def save_enhanced_workspace_resume(self):
        """Save the current resume from the enhanced workspace."""
        if not hasattr(self, 'enhanced_editor'):
            messagebox.showwarning("Warning", "Enhanced editor not available.")
            return
        
        content = self.enhanced_editor.get_content()
        if not content.strip():
            messagebox.showwarning("Warning", "No content to save.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Resume",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.txt'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    if hasattr(self, 'chat_interface'):
                        self.chat_interface.add_system_message(f"Resume saved as text: {os.path.basename(filename)}")
                    
                    self.status_var.set("Resume saved successfully")
                else:
                    # For PDF saving, would need proper PDF generation
                    messagebox.showinfo("PDF Save", "PDF generation feature - to be implemented with proper PDF library")
                    
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save resume: {str(e)}")

    def quick_format_resume(self):
        """Quick action to format the resume."""
        if hasattr(self, 'enhanced_editor'):
            self.enhanced_editor.clean_formatting()
            self.enhanced_editor.apply_auto_formatting()
            
            if hasattr(self, 'chat_interface'):
                self.chat_interface.add_system_message("Resume formatting applied automatically.")

    def quick_ats_check(self):
        """Quick action to check ATS compatibility."""
        if not hasattr(self, 'enhanced_editor'):
            return
        
        content = self.enhanced_editor.get_content()
        
        # Simple ATS check analysis
        ats_tips = [
            "✓ Use standard section headers (EXPERIENCE, EDUCATION, SKILLS)",
            "✓ Avoid complex formatting and graphics",
            "✓ Use standard fonts and bullet points",
            "✓ Include relevant keywords from job descriptions",
            "✓ Use consistent date formats",
            "⚠ Consider adding more quantifiable achievements",
            "⚠ Ensure contact information is at the top"
        ]
        
        # Send to chat for detailed analysis
        ats_message = "Please analyze this resume for ATS (Applicant Tracking System) compatibility and suggest improvements."
        
        if hasattr(self, 'chat_interface'):
            self.chat_interface.send_quick_message(ats_message)
            
            # Also add quick tips
            tips_text = "Quick ATS Tips:\n" + "\n".join(ats_tips)
            self.chat_interface.add_message("ATS Assistant", tips_text, "system")

    def quick_generate_summary(self):
        """Quick action to generate a professional summary."""
        if not hasattr(self, 'enhanced_editor'):
            return
        
        content = self.enhanced_editor.get_content()
        
        summary_prompt = "Based on my resume content, please generate a powerful professional summary that highlights my key strengths, experience, and value proposition. Make it concise but impactful."
        
        if hasattr(self, 'chat_interface'):
            self.chat_interface.send_quick_message(summary_prompt)

    def process_chat_with_llm(self, message):
        """Enhanced process chat with more context and better responses."""
        try:
            # Use existing API integration with enhanced context
            if not self.workspace_resume_content:
                # If no resume is loaded, provide general advice
                general_responses = {
                    "hello": "Hello! I'm your Resume Assistant. Please load a resume to get started with personalized advice.",
                    "help": "I can help you improve your resume in many ways: content optimization, ATS compatibility, formatting, keyword suggestions, and more. Load a resume and ask me anything!",
                    "improve": "To provide specific improvement suggestions, please load your resume first using the 'Load Resume' button.",
                    "format": "I can help with resume formatting once you load your resume. I'll analyze structure, consistency, and ATS compatibility.",
                }
                
                message_lower = message.lower()
                for key, response in general_responses.items():
                    if key in message_lower:
                        return response
                
                return "Please load a resume first so I can provide personalized advice. Use the 'Load Resume' button to get started!"
            
            # Enhanced context preparation
            resume_context = str(self.workspace_resume_content) if self.workspace_resume_content else "No resume loaded"
            
            # Get editor content if available and different from original
            editor_content = ""
            if hasattr(self, 'enhanced_editor'):
                current_editor = self.enhanced_editor.get_content()
                if current_editor != resume_context:
                    editor_content = f"\n\nCurrent edited version:\n{current_editor}"
            
            # Create comprehensive context
            full_context = f"""Resume content: {resume_context}{editor_content}

User question: {message}

Please provide specific, actionable advice for improving this resume. Focus on:
- Content improvements and impact statements
- ATS optimization and keyword suggestions  
- Structure and formatting recommendations
- Industry-specific best practices
- Quantifiable achievements and metrics"""
            
            # Use the existing API integration
            response = self.api_integration.improve_resume(
                resume_content=full_context,
                feedback=message
            )
            
            if isinstance(response, dict):
                if 'improved_resume' in response:
                    return response['improved_resume']
                elif 'analysis' in response:
                    return response['analysis']
                else:
                    return str(response)
            else:
                return str(response)
                
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your request: {str(e)}. Please try rephrasing your question or check your API connection."

def main():
    """Main function to start the application."""
    root = tk.Tk()
    app = ResumeRebuilderApp(root)
    
    # Set up a more modern style
    style = ttk.Style()
    if 'clam' in style.theme_names():
        style.theme_use('clam')
    
    # Define custom styles
    style.configure("Accent.TButton", font=("", 10, "bold"))
    
    root.mainloop()


if __name__ == "__main__":
    main()