#!/bin/bash
# Get Job Ready - One-command script for job application preparation

# Display banner
echo ""
echo "=========================================================="
echo "               🚀 GET JOB READY 🚀"
echo "     Complete job hunting and application toolkit"
echo "=========================================================="
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python and required libraries
if ! command_exists python3; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check for PDF file
if [ $# -eq 0 ]; then
  # No argument provided, look for PDF files in current directory and Downloads
  echo "No resume PDF specified. Looking for resume PDF files..."
  PDF_FILES=$(find . -maxdepth 1 -name "*.pdf" | sort)
  
  # Also check for the common file in Downloads folder
  if [ -f "$HOME/Downloads/KJ Cowen - Resume.pdf" ]; then
    PDF_FILES="$PDF_FILES$IFS$HOME/Downloads/KJ Cowen - Resume.pdf"
  fi
  
  if [ -z "$PDF_FILES" ]; then
    echo "Error: No PDF files found in current directory or Downloads."
    echo "Usage: ./get_job_ready.sh path/to/your_resume.pdf"
    exit 1
  fi
  
  # List found PDF files
  echo "Found these PDF files:"
  count=1
  for file in $PDF_FILES; do
    echo "  $count) $(basename "$file")"
    count=$((count+1))
  done
  
  # Ask user to select a file
  echo ""
  read -p "Enter the number of the resume PDF to process: " selection
  
  # Validate selection
  count=1
  for file in $PDF_FILES; do
    if [ "$count" -eq "$selection" ]; then
      RESUME_PDF="$file"
      break
    fi
    count=$((count+1))
  done
  
  if [ -z "$RESUME_PDF" ]; then
    echo "Error: Invalid selection."
    exit 1
  fi
else
  RESUME_PDF="$1"
  
  # Check if the specified file exists
  if [ ! -f "$RESUME_PDF" ]; then
    echo "Error: File not found: $RESUME_PDF"
    exit 1
  fi
fi

# Create output directory
OUTPUT_DIR="job_applications_$(date +%Y%m%d)"
mkdir -p "$OUTPUT_DIR"

echo ""
echo "Processing resume: $(basename "$RESUME_PDF")"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check if we can run the targeted OCR directly
if [ -f ./targeted_ocr_improvement.py ]; then
  echo "Running targeted OCR improvement first..."
  python3 targeted_ocr_improvement.py "$RESUME_PDF" --dpi 1200 --output "$OUTPUT_DIR"
  
  # Set the processed file as the input for job assistant
  PROCESSED_PDF="${OUTPUT_DIR}/$(basename "${RESUME_PDF%.*}_processed.pdf")"
  if [ -f "$PROCESSED_PDF" ]; then
    RESUME_PDF="$PROCESSED_PDF"
    echo "Using pre-processed PDF: $PROCESSED_PDF"
  fi
fi

# Try to run the job search assistant
echo "Running job search assistant..."
python3 job_search_assistant.py "$RESUME_PDF" --output "$OUTPUT_DIR" || {
  echo "Job search assistant failed. Trying direct targeted OCR..."
  
  if [ -f ./direct_ocr_resume.py ]; then
    echo "Running direct OCR resume processor..."
    python3 direct_ocr_resume.py "$RESUME_PDF" --output "$OUTPUT_DIR"
  else
    python3 targeted_ocr_improvement.py "$RESUME_PDF" --dpi 1500 --output "$OUTPUT_DIR"
    
    # Create a simple text file with extracted text - macOS friendly version
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS version (no -printf support)
      LATEST_OCR=$(find "$OUTPUT_DIR" -name "*_targeted_ocr_*.txt" -type f -exec stat -f "%m %N" {} \; | sort -nr | head -1 | cut -d' ' -f2-)
    else
      # Linux version
      LATEST_OCR=$(find "$OUTPUT_DIR" -name "*_targeted_ocr_*.txt" -type f -printf "%T@ %p\n" | sort -nr | head -1 | cut -d' ' -f2-)
    fi
    
    if [ -n "$LATEST_OCR" ]; then
      cp "$LATEST_OCR" "$OUTPUT_DIR/$(basename ${RESUME_PDF%.*})_job_app_$(date +%Y%m%d_%H%M%S).txt"
      echo "Created job application text from OCR result"
    else
      echo "Warning: Could not find OCR output file"
    fi
  fi
}

# Main menu for job hunting and application
show_main_menu() {
    echo ""
    echo "=========================================================="
    echo "              🧰 JOB HUNTING TOOLKIT 🧰"
    echo "=========================================================="
    echo ""
    echo "What would you like to do next?"
    echo ""
    echo "  1) Search for jobs"
    echo "  2) Track job applications"
    echo "  3) Create a new job application"
    echo "  4) Tailor resume for a specific job"
    echo "  5) Create a cover letter"
    echo "  6) View job application guides"
    echo "  0) Exit"
    echo ""
    read -p "Enter your choice: " choice
    
    case $choice in
        1)
            search_for_jobs
            ;;
        2)
            track_applications
            ;;
        3)
            create_job_application
            ;;
        4)
            tailor_resume
            ;;
        5)
            create_cover_letter
            ;;
        6)
            view_guides
            ;;
        0)
            echo "Thank you for using the Job Hunting Toolkit!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            show_main_menu
            ;;
    esac
}

# Function to search for jobs
search_for_jobs() {
    echo ""
    echo "=========================================================="
    echo "                   🔍 JOB SEARCH 🔍"
    echo "=========================================================="
    echo ""
    
    # Get search keywords
    read -p "Enter search keywords (e.g., Python Developer): " keywords
    if [ -z "$keywords" ]; then
        echo "Error: Search keywords are required."
        search_for_jobs
        return
    fi
    
    # Get location (optional)
    read -p "Enter location (optional, press Enter to skip): " location
    
    # Determine the latest resume text file
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS version
      LATEST_RESUME=$(find "$OUTPUT_DIR" -name "*_job_app_*.txt" -not -name "*_ATS.txt" -type f -exec stat -f "%m %N" {} \; | sort -nr | head -1 | cut -d' ' -f2-)
    else
      # Linux version
      LATEST_RESUME=$(find "$OUTPUT_DIR" -name "*_job_app_*.txt" -not -name "*_ATS.txt" -type f -printf "%T@ %p\n" | sort -nr | head -1 | cut -d' ' -f2-)
    fi
    
    if [ -z "$LATEST_RESUME" ]; then
        echo "Warning: Could not find processed resume text file. Search will proceed without resume analysis."
        RESUME_ARG=""
    else
        RESUME_ARG="--resume \"$LATEST_RESUME\""
    fi
    
    # Convert keywords to array and format for command
    keyword_array=($keywords)
    keyword_args=""
    for kw in "${keyword_array[@]}"; do
        keyword_args+="\"$kw\" "
    done
    
    # Run the job finder command
    echo "Searching for jobs matching: $keywords"
    if [ -z "$location" ]; then
        # shellcheck disable=SC2086
        python3 job_hunter.py search --keywords $keyword_args $RESUME_ARG --output "$OUTPUT_DIR"
    else
        # shellcheck disable=SC2086
        python3 job_hunter.py search --keywords $keyword_args --location "$location" $RESUME_ARG --output "$OUTPUT_DIR"
    fi
    
    # Return to main menu
    show_main_menu
}

# Function to track job applications
track_applications() {
    echo ""
    echo "=========================================================="
    echo "            📋 JOB APPLICATION TRACKER 📋"
    echo "=========================================================="
    echo ""
    
    # Determine the latest resume text file
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS version
      LATEST_RESUME=$(find "$OUTPUT_DIR" -name "*_job_app_*.txt" -not -name "*_ATS.txt" -type f -exec stat -f "%m %N" {} \; | sort -nr | head -1 | cut -d' ' -f2-)
    else
      # Linux version
      LATEST_RESUME=$(find "$OUTPUT_DIR" -name "*_job_app_*.txt" -not -name "*_ATS.txt" -type f -printf "%T@ %p\n" | sort -nr | head -1 | cut -d' ' -f2-)
    fi
    
    if [ -z "$LATEST_RESUME" ]; then
        echo "Warning: Could not find processed resume text file."
        RESUME_ARG=""
    else
        RESUME_ARG="--resume \"$LATEST_RESUME\""
    fi
    
    # Run the application tracker
    # shellcheck disable=SC2086
    python3 job_hunter.py track $RESUME_ARG --output "$OUTPUT_DIR"
    
    # Return to main menu
    show_main_menu
}

# Function to create a new job application
create_job_application() {
    echo ""
    echo "=========================================================="
    echo "            ➕ CREATE JOB APPLICATION ➕"
    echo "=========================================================="
    echo ""
    
    # Get job details
    read -p "Enter job title: " title
    if [ -z "$title" ]; then
        echo "Error: Job title is required."
        create_job_application
        return
    fi
    
    read -p "Enter company name: " company
    if [ -z "$company" ]; then
        echo "Error: Company name is required."
        create_job_application
        return
    fi
    
    read -p "Enter job location: " location
    read -p "Enter job URL: " url
    
    # Ask for job description
    echo "Enter job description (press Ctrl+D when finished):"
    description=$(cat)
    
    # Determine the latest resume text file
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS version
      LATEST_RESUME=$(find "$OUTPUT_DIR" -name "*_job_app_*.txt" -not -name "*_ATS.txt" -type f -exec stat -f "%m %N" {} \; | sort -nr | head -1 | cut -d' ' -f2-)
    else
      # Linux version
      LATEST_RESUME=$(find "$OUTPUT_DIR" -name "*_job_app_*.txt" -not -name "*_ATS.txt" -type f -printf "%T@ %p\n" | sort -nr | head -1 | cut -d' ' -f2-)
    fi
    
    if [ -z "$LATEST_RESUME" ]; then
        echo "Warning: Could not find processed resume text file."
        RESUME_ARG=""
    else
        RESUME_ARG="--resume \"$LATEST_RESUME\""
    fi
    
    # Ask if user wants to create tailored materials
    read -p "Create tailored resume and cover letter? (y/n): " create_materials
    if [[ "$create_materials" =~ ^[Yy] ]]; then
        MATERIALS_ARG="--create-materials"
    else
        MATERIALS_ARG=""
    fi
    
    # Run the job application assistant
    echo "Creating job application..."
    # shellcheck disable=SC2086
    python3 job_hunter.py apply $RESUME_ARG --output "$OUTPUT_DIR" \
        --title "$title" --company "$company" --location "$location" \
        --url "$url" --description "$description" $MATERIALS_ARG
    
    # Return to main menu
    show_main_menu
}

# Function to tailor resume for a specific job
tailor_resume() {
    echo ""
    echo "=========================================================="
    echo "              ✂️ TAILOR YOUR RESUME ✂️"
    echo "=========================================================="
    echo ""
    
    # Run the application tracker first to list applications
    python3 job_hunter.py track --output "$OUTPUT_DIR"
    
    # Ask for application ID
    read -p "Enter application ID to tailor resume for: " app_id
    if [ -z "$app_id" ]; then
        echo "Error: Application ID is required."
        tailor_resume
        return
    fi
    
    # Determine the latest resume text file
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS version
      LATEST_RESUME=$(find "$OUTPUT_DIR" -name "*_job_app_*.txt" -not -name "*_ATS.txt" -type f -exec stat -f "%m %N" {} \; | sort -nr | head -1 | cut -d' ' -f2-)
    else
      # Linux version
      LATEST_RESUME=$(find "$OUTPUT_DIR" -name "*_job_app_*.txt" -not -name "*_ATS.txt" -type f -printf "%T@ %p\n" | sort -nr | head -1 | cut -d' ' -f2-)
    fi
    
    if [ -z "$LATEST_RESUME" ]; then
        echo "Warning: Could not find processed resume text file."
        RESUME_ARG=""
    else
        RESUME_ARG="--resume \"$LATEST_RESUME\""
    fi
    
    # Run the job application assistant to tailor resume
    echo "Creating tailored resume..."
    # shellcheck disable=SC2086
    python3 job_application_assistant.py $RESUME_ARG --output "$OUTPUT_DIR" tailor "$app_id"
    
    # Return to main menu
    show_main_menu
}

# Function to create a cover letter
create_cover_letter() {
    echo ""
    echo "=========================================================="
    echo "             ✉️ CREATE COVER LETTER ✉️"
    echo "=========================================================="
    echo ""
    
    # Run the application tracker first to list applications
    python3 job_hunter.py track --output "$OUTPUT_DIR"
    
    # Ask for application ID
    read -p "Enter application ID to create cover letter for: " app_id
    if [ -z "$app_id" ]; then
        echo "Error: Application ID is required."
        create_cover_letter
        return
    fi
    
    # Determine the latest resume text file
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS version
      LATEST_RESUME=$(find "$OUTPUT_DIR" -name "*_job_app_*.txt" -not -name "*_ATS.txt" -type f -exec stat -f "%m %N" {} \; | sort -nr | head -1 | cut -d' ' -f2-)
    else
      # Linux version
      LATEST_RESUME=$(find "$OUTPUT_DIR" -name "*_job_app_*.txt" -not -name "*_ATS.txt" -type f -printf "%T@ %p\n" | sort -nr | head -1 | cut -d' ' -f2-)
    fi
    
    if [ -z "$LATEST_RESUME" ]; then
        echo "Warning: Could not find processed resume text file."
        RESUME_ARG=""
    else
        RESUME_ARG="--resume \"$LATEST_RESUME\""
    fi
    
    # Run the job application assistant to create cover letter
    echo "Creating cover letter..."
    # shellcheck disable=SC2086
    python3 job_application_assistant.py $RESUME_ARG --output "$OUTPUT_DIR" cover "$app_id"
    
    # Return to main menu
    show_main_menu
}

# Function to view job application guides
view_guides() {
    echo ""
    echo "=========================================================="
    echo "              📚 JOB APPLICATION GUIDES 📚"
    echo "=========================================================="
    echo ""
    echo "Available guides:"
    echo ""
    echo "  1) Getting Started Guide"
    echo "  2) Job Search README"
    echo "  3) OCR Improvement Guide"
    echo "  4) Resume to Job Text Guide"
    echo ""
    read -p "Enter your choice (or 0 to go back): " choice
    
    case $choice in
        1)
            if [ -f "./GETTING_STARTED.md" ]; then
                # Try to use a markdown viewer if available
                if command_exists mdless; then
                    mdless "./GETTING_STARTED.md"
                elif command_exists glow; then
                    glow "./GETTING_STARTED.md"
                else
                    cat "./GETTING_STARTED.md"
                fi
            else
                echo "Guide not found."
            fi
            ;;
        2)
            if [ -f "./JOB_SEARCH_README.md" ]; then
                # Try to use a markdown viewer if available
                if command_exists mdless; then
                    mdless "./JOB_SEARCH_README.md"
                elif command_exists glow; then
                    glow "./JOB_SEARCH_README.md"
                else
                    cat "./JOB_SEARCH_README.md"
                fi
            else
                echo "Guide not found."
            fi
            ;;
        3)
            if [ -f "./OCR_IMPROVEMENT_GUIDE.md" ]; then
                # Try to use a markdown viewer if available
                if command_exists mdless; then
                    mdless "./OCR_IMPROVEMENT_GUIDE.md"
                elif command_exists glow; then
                    glow "./OCR_IMPROVEMENT_GUIDE.md"
                else
                    cat "./OCR_IMPROVEMENT_GUIDE.md"
                fi
            else
                echo "Guide not found."
            fi
            ;;
        4)
            if [ -f "./RESUME_TO_JOB_TEXT.md" ]; then
                # Try to use a markdown viewer if available
                if command_exists mdless; then
                    mdless "./RESUME_TO_JOB_TEXT.md"
                elif command_exists glow; then
                    glow "./RESUME_TO_JOB_TEXT.md"
                else
                    cat "./RESUME_TO_JOB_TEXT.md"
                fi
            else
                echo "Guide not found."
            fi
            ;;
        0)
            show_main_menu
            return
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
    
    # After viewing guide, show guide menu again
    view_guides
}

# Show the main menu
show_main_menu
