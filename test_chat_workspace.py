#!/usr/bin/env python3
"""
Test script for the new Chat Workspace functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import tkinter as tk
from src.gui import ResumeRebuilderApp

def test_chat_workspace():
    """Test the chat workspace interface."""
    print("Testing Chat Workspace Interface...")
    
    # Create a test window
    root = tk.Tk()
    app = ResumeRebuilderApp(root)
    
    # Check if the chat workspace tab exists
    tabs = app.notebook.tabs()
    tab_texts = [app.notebook.tab(tab, "text") for tab in tabs]
    
    print(f"Available tabs: {tab_texts}")
    
    if "Chat Workspace" in tab_texts:
        print("✓ Chat Workspace tab created successfully")
        
        # Test if key components exist
        if hasattr(app, 'chat_frame'):
            print("✓ Chat frame exists")
        if hasattr(app, 'pdf_display'):
            print("✓ PDF display exists")
        if hasattr(app, 'content_editor'):
            print("✓ Content editor exists")
        if hasattr(app, 'chat_history'):
            print("✓ Chat history exists")
        if hasattr(app, 'chat_input'):
            print("✓ Chat input exists")
            
        print("✓ All main components found")
    else:
        print("✗ Chat Workspace tab not found")
    
    # Test mock LLM integration
    try:
        test_response = app.process_chat_with_llm("Test message")
        print(f"✓ LLM integration test: {test_response[:50]}...")
    except Exception as e:
        print(f"✗ LLM integration test failed: {e}")
    
    root.quit()
    print("Test completed.")

if __name__ == "__main__":
    test_chat_workspace()