"""
Enhanced Editor component with undo/redo and formatting capabilities
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from typing import List, Dict, Any
import json
import re

class EnhancedEditor:
    """An enhanced text editor with resume-specific features."""
    
    def __init__(self, parent_frame, content_changed_callback=None):
        self.parent_frame = parent_frame
        self.content_changed_callback = content_changed_callback
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_size = 50
        self.current_content = ""
        
        self.setup_editor()
    
    def setup_editor(self):
        """Setup the enhanced editor interface."""
        # Toolbar
        self.toolbar = ttk.Frame(self.parent_frame)
        self.toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # File operations
        file_frame = ttk.LabelFrame(self.toolbar, text="File")
        file_frame.pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        ttk.Button(file_frame, text="Save", width=8, command=self.save_content).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="Revert", width=8, command=self.revert_changes).pack(side=tk.LEFT, padx=2)
        
        # Edit operations
        edit_frame = ttk.LabelFrame(self.toolbar, text="Edit")
        edit_frame.pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        self.undo_btn = ttk.Button(edit_frame, text="Undo", width=8, command=self.undo)
        self.undo_btn.pack(side=tk.LEFT, padx=2)
        
        self.redo_btn = ttk.Button(edit_frame, text="Redo", width=8, command=self.redo)
        self.redo_btn.pack(side=tk.LEFT, padx=2)
        
        # Formatting operations
        format_frame = ttk.LabelFrame(self.toolbar, text="Format")
        format_frame.pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        ttk.Button(format_frame, text="Bold", width=8, command=self.toggle_bold).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="Italic", width=8, command=self.toggle_italic).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="Clean", width=8, command=self.clean_formatting).pack(side=tk.LEFT, padx=2)
        
        # Section operations
        section_frame = ttk.LabelFrame(self.toolbar, text="Sections")
        section_frame.pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        ttk.Button(section_frame, text="Add", width=8, command=self.add_section).pack(side=tk.LEFT, padx=2)
        ttk.Button(section_frame, text="Remove", width=8, command=self.remove_section).pack(side=tk.LEFT, padx=2)
        ttk.Button(section_frame, text="Reorder", width=8, command=self.reorder_sections).pack(side=tk.LEFT, padx=2)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.toolbar, textvariable=self.status_var).pack(side=tk.RIGHT, padx=5)
        
        # Editor area
        editor_container = ttk.Frame(self.parent_frame)
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers frame
        line_frame = ttk.Frame(editor_container)
        line_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.line_numbers = tk.Text(
            line_frame,
            width=4,
            padx=3,
            takefocus=0,
            border=0,
            state='disabled',
            wrap='none',
            bg='#f0f0f0',
            fg='#666666',
            font=("Courier", 10)
        )
        self.line_numbers.pack(fill=tk.Y, expand=True)
        
        # Main editor
        self.text_editor = scrolledtext.ScrolledText(
            editor_container,
            wrap=tk.WORD,
            font=("Courier", 11),
            undo=True,
            maxundo=self.max_undo_size
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        
        # Bind events
        self.text_editor.bind('<KeyRelease>', self._on_content_changed)
        self.text_editor.bind('<Button-1>', self._on_content_changed)
        self.text_editor.bind('<MouseWheel>', self._on_scroll)
        self.text_editor.bind('<Control-z>', lambda e: self.undo())
        self.text_editor.bind('<Control-y>', lambda e: self.redo())
        self.text_editor.bind('<Control-s>', lambda e: self.save_content())
        
        # Configure text tags
        self.setup_text_tags()
        
        # Initialize
        self.update_line_numbers()
        self.update_undo_redo_buttons()
    
    def setup_text_tags(self):
        """Setup text formatting tags."""
        self.text_editor.tag_config("bold", font=("Courier", 11, "bold"))
        self.text_editor.tag_config("italic", font=("Courier", 11, "italic"))
        self.text_editor.tag_config("header", font=("Courier", 12, "bold"), foreground="#2c3e50")
        self.text_editor.tag_config("subheader", font=("Courier", 11, "bold"), foreground="#34495e")
        self.text_editor.tag_config("highlight", background="#ffffcc")
    
    def set_content(self, content: str):
        """Set the editor content."""
        self.save_state()  # Save current state before changing
        
        self.text_editor.delete(1.0, tk.END)
        self.text_editor.insert(1.0, content)
        self.current_content = content
        
        self.update_line_numbers()
        self.apply_auto_formatting()
        self.status_var.set("Content loaded")
    
    def get_content(self) -> str:
        """Get the current editor content."""
        return self.text_editor.get(1.0, tk.END).rstrip()
    
    def save_state(self):
        """Save current state for undo functionality."""
        current = self.get_content()
        if current != self.current_content:
            self.undo_stack.append(self.current_content)
            if len(self.undo_stack) > self.max_undo_size:
                self.undo_stack.pop(0)
            self.redo_stack.clear()
            self.current_content = current
            self.update_undo_redo_buttons()
    
    def undo(self):
        """Undo the last change."""
        if self.undo_stack:
            self.redo_stack.append(self.current_content)
            self.current_content = self.undo_stack.pop()
            
            self.text_editor.delete(1.0, tk.END)
            self.text_editor.insert(1.0, self.current_content)
            
            self.update_undo_redo_buttons()
            self.update_line_numbers()
            self.status_var.set("Undone")
    
    def redo(self):
        """Redo the last undone change."""
        if self.redo_stack:
            self.undo_stack.append(self.current_content)
            self.current_content = self.redo_stack.pop()
            
            self.text_editor.delete(1.0, tk.END)
            self.text_editor.insert(1.0, self.current_content)
            
            self.update_undo_redo_buttons()
            self.update_line_numbers()
            self.status_var.set("Redone")
    
    def update_undo_redo_buttons(self):
        """Update the state of undo/redo buttons."""
        self.undo_btn.config(state=tk.NORMAL if self.undo_stack else tk.DISABLED)
        self.redo_btn.config(state=tk.NORMAL if self.redo_stack else tk.DISABLED)
    
    def toggle_bold(self):
        """Toggle bold formatting for selected text."""
        try:
            if self.text_editor.tag_ranges(tk.SEL):
                current_tags = self.text_editor.tag_names(tk.SEL_FIRST)
                if "bold" in current_tags:
                    self.text_editor.tag_remove("bold", tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    self.text_editor.tag_add("bold", tk.SEL_FIRST, tk.SEL_LAST)
                self.status_var.set("Bold toggled")
            else:
                self.status_var.set("Select text to format")
        except tk.TclError:
            self.status_var.set("Select text to format")
    
    def toggle_italic(self):
        """Toggle italic formatting for selected text."""
        try:
            if self.text_editor.tag_ranges(tk.SEL):
                current_tags = self.text_editor.tag_names(tk.SEL_FIRST)
                if "italic" in current_tags:
                    self.text_editor.tag_remove("italic", tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    self.text_editor.tag_add("italic", tk.SEL_FIRST, tk.SEL_LAST)
                self.status_var.set("Italic toggled")
            else:
                self.status_var.set("Select text to format")
        except tk.TclError:
            self.status_var.set("Select text to format")
    
    def clean_formatting(self):
        """Remove all formatting from the document."""
        content = self.get_content()
        
        # Clean common formatting issues
        content = re.sub(r'\\s+', ' ', content)  # Multiple spaces
        content = re.sub(r'\\n\\s*\\n\\s*\\n+', '\\n\\n', content)  # Multiple newlines
        content = content.strip()
        
        self.set_content(content)
        self.status_var.set("Formatting cleaned")
    
    def apply_auto_formatting(self):
        """Apply automatic formatting to common resume sections."""
        content = self.get_content()
        lines = content.split('\\n')
        
        self.text_editor.delete(1.0, tk.END)
        
        for i, line in enumerate(lines):
            line_start = f"{i+1}.0"
            self.text_editor.insert(tk.END, line + ('\\n' if i < len(lines)-1 else ''))
            
            # Auto-format headers (all caps lines)
            if line.isupper() and len(line.strip()) > 0 and len(line.strip()) < 50:
                self.text_editor.tag_add("header", line_start, f"{i+1}.end")
            
            # Auto-format job titles or section headers (lines ending with colon)
            elif line.strip().endswith(':'):
                self.text_editor.tag_add("subheader", line_start, f"{i+1}.end")
        
        self.update_line_numbers()
    
    def add_section(self):
        """Add a new section to the resume."""
        section_name = simpledialog.askstring("Add Section", "Enter section name:")
        if section_name:
            current_pos = self.text_editor.index(tk.INSERT)
            
            # Find appropriate insertion point (end of document)
            content = self.get_content()
            
            new_section = f"\\n\\n{section_name.upper()}\\n{'-' * len(section_name)}\\n[Add content here]\\n"
            
            self.text_editor.insert(tk.END, new_section)
            self.update_line_numbers()
            self.apply_auto_formatting()
            self.status_var.set(f"Added section: {section_name}")
    
    def remove_section(self):
        """Remove a section from the resume."""
        # Simple implementation - would need more sophisticated section detection
        if messagebox.askyesno("Remove Section", "This will remove the current paragraph. Continue?"):
            try:
                # Get current line
                current_line = self.text_editor.index(tk.INSERT).split('.')[0]
                
                # Find paragraph boundaries
                start_line = int(current_line)
                while start_line > 1:
                    line_content = self.text_editor.get(f"{start_line}.0", f"{start_line}.end")
                    if not line_content.strip():
                        start_line += 1
                        break
                    start_line -= 1
                
                end_line = int(current_line)
                total_lines = int(self.text_editor.index(tk.END).split('.')[0])
                while end_line < total_lines:
                    line_content = self.text_editor.get(f"{end_line}.0", f"{end_line}.end")
                    if not line_content.strip():
                        break
                    end_line += 1
                
                # Delete the section
                self.text_editor.delete(f"{start_line}.0", f"{end_line}.0")
                self.update_line_numbers()
                self.status_var.set("Section removed")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove section: {str(e)}")
    
    def reorder_sections(self):
        """Reorder resume sections."""
        # Simplified implementation
        messagebox.showinfo("Reorder Sections", "Section reordering feature - advanced implementation needed")
        self.status_var.set("Reorder sections - to be implemented")
    
    def save_content(self):
        """Save the current content."""
        self.save_state()
        if self.content_changed_callback:
            self.content_changed_callback(self.get_content())
        self.status_var.set("Content saved")
    
    def revert_changes(self):
        """Revert to the last saved state."""
        if messagebox.askyesno("Revert Changes", "Discard all unsaved changes?"):
            if self.undo_stack:
                self.set_content(self.undo_stack[0])
                self.undo_stack.clear()
                self.redo_stack.clear()
                self.update_undo_redo_buttons()
            self.status_var.set("Changes reverted")
    
    def update_line_numbers(self):
        """Update the line numbers display."""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        
        content = self.text_editor.get(1.0, tk.END)
        lines = content.split('\\n')
        
        for i in range(len(lines)):
            self.line_numbers.insert(tk.END, f"{i+1:>3}\\n")
        
        self.line_numbers.config(state='disabled')
    
    def _on_content_changed(self, event=None):
        """Handle content changes."""
        self.update_line_numbers()
        
        # Call callback if provided
        if self.content_changed_callback:
            # Use a delayed callback to avoid too frequent updates
            self.parent_frame.after_idle(lambda: self.content_changed_callback(self.get_content()))
    
    def _on_scroll(self, event):
        """Synchronize scrolling between editor and line numbers."""
        self.line_numbers.yview_moveto(self.text_editor.yview()[0])
    
    def find_and_highlight(self, text: str):
        """Find and highlight text in the editor."""
        # Remove existing highlights
        self.text_editor.tag_remove("highlight", 1.0, tk.END)
        
        if text:
            start = 1.0
            while True:
                pos = self.text_editor.search(text, start, tk.END)
                if not pos:
                    break
                
                end_pos = f"{pos}+{len(text)}c"
                self.text_editor.tag_add("highlight", pos, end_pos)
                start = end_pos
            
            self.status_var.set(f"Highlighted: {text}")
    
    def get_selection(self) -> str:
        """Get the currently selected text."""
        try:
            return self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            return ""
    
    def insert_text(self, text: str, position=None):
        """Insert text at the specified position or current cursor."""
        if position is None:
            position = tk.INSERT
        
        self.text_editor.insert(position, text)
        self.update_line_numbers()
        self.status_var.set("Text inserted")