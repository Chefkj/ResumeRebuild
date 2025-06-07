#!/usr/bin/env python3
"""
Test script for the Resume Rebuilder Web Interface
"""

import sys
import os
import subprocess
import time
import webbrowser
from pathlib import Path

def main():
    print("🚀 Starting Resume Rebuilder Web Interface Test...")
    
    # Change to src directory
    src_dir = Path(__file__).parent / "src"
    os.chdir(src_dir)
    
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Check if web_server.py exists
    if not os.path.exists("web_server.py"):
        print("❌ web_server.py not found!")
        return
    
    # Start the web server
    print("🌐 Starting Flask web server...")
    
    try:
        # Run the web server
        process = subprocess.Popen([
            sys.executable, "web_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Check if server is running
        if process.poll() is None:
            print("✅ Web server started successfully!")
            print("🌐 Opening browser to http://localhost:5000")
            
            # Open browser
            webbrowser.open("http://localhost:5000")
            
            print("\n📋 Instructions:")
            print("1. Upload a resume file (PDF or TXT)")
            print("2. Use the AI chat to ask questions or get suggestions")
            print("3. Edit your resume in the editor panel")
            print("4. Preview changes in real-time")
            print("5. Save your session for later")
            print("\n⌨️  Press Ctrl+C to stop the server")
            
            # Wait for user to stop
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping server...")
                process.terminate()
                process.wait()
        else:
            # Server failed to start
            stdout, stderr = process.communicate()
            print("❌ Server failed to start!")
            if stdout:
                print("STDOUT:", stdout)
            if stderr:
                print("STDERR:", stderr)
                
    except FileNotFoundError:
        print("❌ Python not found! Please ensure Python is installed.")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
    
    print("🏁 Test completed.")

if __name__ == "__main__":
    main()