#!/usr/bin/env python3
"""
Dependency Installer for Resume Rebuilder

This script checks for and installs necessary dependencies for the Resume Rebuilder application.
"""

import os
import sys
import platform
import subprocess
import importlib.util

def check_command_availability(command):
    """Check if a command is available in the system PATH."""
    which_cmd = 'where' if platform.system() == 'Windows' else 'which'
    try:
        subprocess.run([which_cmd, command], check=True, capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def install_pdftotext():
    """Install pdftotext based on the operating system."""
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        if check_command_availability('brew'):
            print("Installing pdftotext via Homebrew...")
            try:
                subprocess.run(['brew', 'install', 'poppler'], check=True)
                print("✅ pdftotext installed successfully!")
                return True
            except subprocess.SubprocessError as e:
                print(f"❌ Error installing pdftotext: {e}")
                print("Please try installing manually: brew install poppler")
        else:
            print("Homebrew not found. Please install Homebrew first:")
            print("  /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            print("Then run: brew install poppler")
        
    elif system == 'Linux':
        # Try apt-get (Debian/Ubuntu)
        if check_command_availability('apt-get'):
            print("Installing pdftotext via apt-get...")
            try:
                subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'poppler-utils'], check=True)
                print("✅ pdftotext installed successfully!")
                return True
            except subprocess.SubprocessError as e:
                print(f"❌ Error installing pdftotext: {e}")
        
        # Try yum (Red Hat/CentOS)
        elif check_command_availability('yum'):
            print("Installing pdftotext via yum...")
            try:
                subprocess.run(['sudo', 'yum', 'install', '-y', 'poppler-utils'], check=True)
                print("✅ pdftotext installed successfully!")
                return True
            except subprocess.SubprocessError as e:
                print(f"❌ Error installing pdftotext: {e}")
                
        print("Please install poppler-utils manually using your system's package manager.")
        
    elif system == 'Windows':
        print("On Windows, pdftotext can be installed by:")
        print("1. Install Xpdf tools from: http://www.xpdfreader.com/download.html")
        print("2. Add the installation directory to your system PATH")
        
    return False

def check_python_dependencies():
    """Check for required Python packages and offer to install them."""
    required_packages = {
        'pymupdf': 'fitz',  # PyMuPDF's import name is fitz
        'PyPDF2': 'PyPDF2', 
        'pdfminer.six': 'pdfminer',
        'reportlab': 'reportlab',
        'requests': 'requests'
    }
    
    missing_packages = []
    
    print("\nChecking Python dependencies...")
    for package, import_name in required_packages.items():
        if not importlib.util.find_spec(import_name):
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing Python packages: {', '.join(missing_packages)}")
        install = input("Would you like to install them now? (y/n): ")
        
        if install.lower() == 'y':
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
                print("✅ Python dependencies installed successfully!")
                return True
            except subprocess.SubprocessError as e:
                print(f"❌ Error installing Python dependencies: {e}")
                print("Please install them manually using: pip install " + " ".join(missing_packages))
                return False
    else:
        print("✅ All required Python packages are installed.")
        return True
    
    return False

def main():
    """Main function checking and installing dependencies."""
    print("Resume Rebuilder Dependency Installer")
    print("====================================\n")
    
    # Check for pdftotext
    print("Checking for pdftotext...")
    if check_command_availability('pdftotext'):
        print("✅ pdftotext is already installed!")
    else:
        print("❌ pdftotext not found.")
        install = input("Would you like to install pdftotext now? (y/n): ")
        if install.lower() == 'y':
            install_pdftotext()
    
    # Check Python dependencies
    check_python_dependencies()
    
    print("\nSetup complete! You can now run the Resume Rebuilder application.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
