#!/usr/bin/env python3
"""
Minimal test for GUI components without dependencies
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

class MinimalWorkspaceTest:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Workspace Test")
        self.root.geometry("1200x800")
        
        # Test the chat workspace layout
        self.setup_chat_workspace()
    
    def setup_chat_workspace(self):
        """Setup a minimal version of the chat workspace."""
        # Main container with paned window for resizable panels
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for chat interface
        chat_frame = ttk.Frame(main_paned)
        
        # Chat panel content
        chat_container = ttk.LabelFrame(chat_frame, text="Resume Assistant Chat")
        chat_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Chat controls
        chat_controls = ttk.Frame(chat_container)
        chat_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(chat_controls, text="◀ Collapse", width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(chat_controls, text="Clear Chat", width=12).pack(side=tk.LEFT, padx=5)
        
        # Chat history display
        chat_history = scrolledtext.ScrolledText(
            chat_container,
            wrap=tk.WORD,
            height=15,
            state=tk.DISABLED
        )
        chat_history.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Chat input area
        input_frame = ttk.Frame(chat_container)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Ask about your resume:").pack(anchor=tk.W)
        
        chat_input = scrolledtext.ScrolledText(input_frame, height=3, wrap=tk.WORD)
        chat_input.pack(fill=tk.X, pady=2)
        
        # Send button and quick actions
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(button_frame, text="Send").pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Improve Resume").pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Tailor for Job").pack(side=tk.LEFT, padx=2)
        
        # Right panel with PDF viewer and edit tools
        right_paned = ttk.PanedWindow(main_paned, orient=tk.VERTICAL)
        
        # PDF Viewer section
        pdf_frame = ttk.LabelFrame(right_paned, text="Resume Preview")
        
        pdf_controls = ttk.Frame(pdf_frame)
        pdf_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(pdf_controls, text="Load Resume").pack(side=tk.LEFT, padx=5)
        ttk.Button(pdf_controls, text="Refresh Preview").pack(side=tk.LEFT, padx=5)
        ttk.Button(pdf_controls, text="Save Changes").pack(side=tk.LEFT, padx=5)
        
        pdf_display = scrolledtext.ScrolledText(
            pdf_frame,
            wrap=tk.WORD,
            height=20,
            state=tk.DISABLED
        )
        pdf_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Edit Tools section
        edit_frame = ttk.LabelFrame(right_paned, text="Edit Tools")
        
        edit_controls = ttk.Frame(edit_frame)
        edit_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(edit_controls, text="Undo").pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_controls, text="Redo").pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_controls, text="Bold").pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_controls, text="Italic").pack(side=tk.LEFT, padx=2)
        
        section_controls = ttk.Frame(edit_frame)
        section_controls.pack(fill=tk.X, pady=5)
        
        ttk.Label(section_controls, text="Sections:").pack(side=tk.LEFT, padx=5)
        ttk.Button(section_controls, text="Add Section").pack(side=tk.LEFT, padx=2)
        ttk.Button(section_controls, text="Remove Section").pack(side=tk.LEFT, padx=2)
        ttk.Button(section_controls, text="Reorder").pack(side=tk.LEFT, padx=2)
        
        content_editor = scrolledtext.ScrolledText(
            edit_frame,
            wrap=tk.WORD,
            height=15
        )
        content_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add panels to paned windows
        right_paned.add(pdf_frame, weight=2)
        right_paned.add(edit_frame, weight=1)
        
        main_paned.add(chat_frame, weight=1)
        main_paned.add(right_paned, weight=3)

def main():
    root = tk.Tk()
    app = MinimalWorkspaceTest(root)
    
    # Set up a more modern style
    style = ttk.Style()
    if 'clam' in style.theme_names():
        style.theme_use('clam')
    
    root.mainloop()

if __name__ == "__main__":
    main()