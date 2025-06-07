"""
Enhanced Chat Interface component for the Chat Workspace
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import datetime
from typing import List, Dict, Any, Callable

class ChatInterface:
    """An enhanced chat interface with LLM integration and context awareness."""
    
    def __init__(self, parent_frame, llm_callback: Callable[[str], str] = None):
        self.parent_frame = parent_frame
        self.llm_callback = llm_callback or self._default_llm_response
        self.chat_history = []
        self.is_collapsed = False
        
        self.setup_interface()
    
    def setup_interface(self):
        """Setup the chat interface."""
        # Header with controls
        self.header_frame = ttk.Frame(self.parent_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Title and collapse button
        title_frame = ttk.Frame(self.header_frame)
        title_frame.pack(fill=tk.X)
        
        ttk.Label(
            title_frame, 
            text="Resume Assistant Chat", 
            font=("", 11, "bold")
        ).pack(side=tk.LEFT)
        
        self.collapse_btn = ttk.Button(
            title_frame,
            text="◀ Collapse",
            width=12,
            command=self.toggle_collapse
        )
        self.collapse_btn.pack(side=tk.RIGHT, padx=5)
        
        # Chat controls
        controls_frame = ttk.Frame(self.header_frame)
        controls_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            controls_frame,
            text="Clear Chat",
            width=12,
            command=self.clear_chat
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            controls_frame,
            text="Export Chat",
            width=12,
            command=self.export_chat
        ).pack(side=tk.LEFT, padx=5)
        
        # Main content frame (collapsible)
        self.content_frame = ttk.Frame(self.parent_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Chat history display
        self.setup_chat_display()
        
        # Chat input area
        self.setup_chat_input()
        
        # Initialize with welcome message
        self.add_system_message("Welcome! I'm your Resume Assistant. How can I help you improve your resume today?")
    
    def setup_chat_display(self):
        """Setup the chat history display area."""
        # Chat display with custom styling
        self.chat_display = scrolledtext.ScrolledText(
            self.content_frame,
            wrap=tk.WORD,
            height=15,
            state=tk.DISABLED,
            font=("", 10),
            bg="#f8f9fa",
            relief=tk.FLAT,
            borderwidth=1
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Configure text tags for different message types
        self.chat_display.tag_config("user", foreground="#2c3e50", font=("", 10, "normal"))
        self.chat_display.tag_config("assistant", foreground="#27ae60", font=("", 10, "normal"))
        self.chat_display.tag_config("system", foreground="#7f8c8d", font=("", 9, "italic"))
        self.chat_display.tag_config("timestamp", foreground="#95a5a6", font=("", 8))
        self.chat_display.tag_config("sender", font=("", 10, "bold"))
    
    def setup_chat_input(self):
        """Setup the chat input area."""
        input_container = ttk.Frame(self.content_frame)
        input_container.pack(fill=tk.X, pady=5)
        
        # Input label
        ttk.Label(
            input_container, 
            text="Ask about your resume:"
        ).pack(anchor=tk.W, pady=(0, 2))
        
        # Input text area
        self.chat_input = scrolledtext.ScrolledText(
            input_container,
            height=3,
            wrap=tk.WORD,
            font=("", 10)
        )
        self.chat_input.pack(fill=tk.X, pady=2)
        
        # Bind Enter key for sending (Shift+Enter for new line)
        self.chat_input.bind("<Return>", self._on_enter_key)
        self.chat_input.bind("<KeyRelease>", self._on_key_release)
        
        # Button area
        button_frame = ttk.Frame(input_container)
        button_frame.pack(fill=tk.X, pady=2)
        
        # Send button
        self.send_btn = ttk.Button(
            button_frame,
            text="Send",
            command=self.send_message,
            style="Accent.TButton"
        )
        self.send_btn.pack(side=tk.RIGHT, padx=2)
        
        # Character counter
        self.char_counter = tk.StringVar(value="0/500")
        ttk.Label(
            button_frame,
            textvariable=self.char_counter,
            font=("", 8)
        ).pack(side=tk.RIGHT, padx=10)
        
        # Quick action buttons
        self.setup_quick_actions(button_frame)
    
    def setup_quick_actions(self, parent):
        """Setup quick action buttons."""
        quick_actions = [
            ("💡 Improve", "Please review my resume and suggest specific improvements"),
            ("🎯 Tailor", "Help me tailor this resume for a specific job position"),
            ("📝 Format", "Check the formatting and structure of my resume"),
            ("🔍 Keywords", "Suggest relevant keywords to add to my resume")
        ]
        
        for text, prompt in quick_actions:
            ttk.Button(
                parent,
                text=text,
                width=12,
                command=lambda p=prompt: self.send_quick_message(p)
            ).pack(side=tk.LEFT, padx=2)
    
    def toggle_collapse(self):
        """Toggle the collapsed state of the chat interface."""
        if self.is_collapsed:
            # Expand
            self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            self.collapse_btn.config(text="◀ Collapse")
            self.is_collapsed = False
        else:
            # Collapse
            self.content_frame.pack_forget()
            self.collapse_btn.config(text="▶ Expand")
            self.is_collapsed = True
    
    def clear_chat(self):
        """Clear the chat history."""
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear the chat history?"):
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.chat_history.clear()
            self.add_system_message("Chat cleared. How can I help you with your resume?")
    
    def export_chat(self):
        """Export chat history to a text file."""
        if not self.chat_history:
            messagebox.showinfo("Export Chat", "No chat history to export.")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            title="Export Chat History",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Resume Assistant Chat History\n")
                    f.write("=" * 40 + "\n\n")
                    
                    for msg in self.chat_history:
                        f.write(f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}\n\n")
                
                messagebox.showinfo("Export Successful", f"Chat history exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export chat: {str(e)}")
    
    def send_message(self):
        """Send a user message."""
        message = self.chat_input.get(1.0, tk.END).strip()
        if not message:
            return
        
        # Clear input
        self.chat_input.delete(1.0, tk.END)
        self.update_char_counter()
        
        # Add user message
        self.add_message("You", message, "user")
        
        # Get AI response
        try:
            self.add_system_message("Thinking...")
            response = self.llm_callback(message)
            
            # Remove "Thinking..." message
            self._remove_last_message()
            
            # Add AI response
            self.add_message("Assistant", response, "assistant")
        except Exception as e:
            self._remove_last_message()
            self.add_message("System", f"Error: {str(e)}", "system")
    
    def send_quick_message(self, message):
        """Send a predefined quick message."""
        self.chat_input.delete(1.0, tk.END)
        self.chat_input.insert(1.0, message)
        self.send_message()
    
    def add_message(self, sender: str, message: str, msg_type: str = "user"):
        """Add a message to the chat display."""
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        # Store in history
        msg_data = {
            "timestamp": timestamp,
            "sender": sender,
            "message": message,
            "type": msg_type
        }
        self.chat_history.append(msg_data)
        
        # Display message
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp and sender
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_display.insert(tk.END, f"{sender}: ", "sender")
        self.chat_display.insert(tk.END, f"{message}\n\n", msg_type)
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def add_system_message(self, message: str):
        """Add a system message."""
        self.add_message("System", message, "system")
    
    def _remove_last_message(self):
        """Remove the last message from display (used for removing 'Thinking...')."""
        self.chat_display.config(state=tk.NORMAL)
        content = self.chat_display.get(1.0, tk.END)
        lines = content.split('\n')
        
        # Find and remove the last non-empty message
        while lines and not lines[-1].strip():
            lines.pop()
        if lines:
            lines.pop()  # Remove the message line
            lines.pop()  # Remove the empty line after message
        
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.insert(1.0, '\n'.join(lines))
        self.chat_display.config(state=tk.DISABLED)
        
        # Also remove from history
        if self.chat_history:
            self.chat_history.pop()
    
    def _on_enter_key(self, event):
        """Handle Enter key press."""
        if event.state & 0x1:  # Shift key pressed
            return  # Allow normal newline
        else:
            self.send_message()
            return "break"  # Prevent default behavior
    
    def _on_key_release(self, event):
        """Handle key release for character counter."""
        self.update_char_counter()
    
    def update_char_counter(self):
        """Update the character counter."""
        content = self.chat_input.get(1.0, tk.END).strip()
        char_count = len(content)
        self.char_counter.set(f"{char_count}/500")
        
        # Change color based on length
        if char_count > 450:
            self.chat_input.config(bg="#ffebee")  # Light red
        elif char_count > 400:
            self.chat_input.config(bg="#fff3e0")  # Light orange
        else:
            self.chat_input.config(bg="white")
    
    def _default_llm_response(self, message: str) -> str:
        """Default LLM response when no callback is provided."""
        return f"I received your message: '{message}'. This is a placeholder response. Please integrate with your LLM service."
    
    def set_llm_callback(self, callback: Callable[[str], str]):
        """Set the LLM callback function."""
        self.llm_callback = callback
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get the chat history."""
        return self.chat_history.copy()