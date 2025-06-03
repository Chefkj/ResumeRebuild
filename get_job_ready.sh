#!/bin/bash
# Get Job Ready - One-command script for job application preparation

# Display banner
echo ""
echo "=========================================================="
echo "               📝 GET JOB READY 📝"
echo "     Extract your resume text for job applications"
echo "=========================================================="
echo ""

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
  # Use the provided argument
  RESUME_PDF="$1"
  
  # Check if the file exists
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
      echo "OCR completed successfully. Results in: $LATEST_OCR"
      cp "$LATEST_OCR" "$OUTPUT_DIR/$(basename "${RESUME_PDF%.*}")_job_ready.txt"
    fi
  fi
}

# Open the output directory
if command -v open >/dev/null 2>&1; then
  # macOS
  open "$OUTPUT_DIR"
elif command -v xdg-open >/dev/null 2>&1; then
  # Linux
  xdg-open "$OUTPUT_DIR"
elif command -v explorer.exe >/dev/null 2>&1; then
  # Windows
  explorer.exe "$(wslpath -w "$OUTPUT_DIR")"
fi

# Find the output files
JOB_READY_FILES=$(find "$OUTPUT_DIR" -name "*job*ready*.txt" -o -name "*_job_app_*.txt" -o -name "*_targeted_ocr_*.txt" 2>/dev/null)

if [ -z "$JOB_READY_FILES" ]; then
  echo ""
  echo "⚠️  Resume processing may have had issues."
  echo "   Check the $OUTPUT_DIR directory for any output files."
  echo ""
else
  echo ""
  echo "✅ Resume processed successfully!"
  echo "   Your job application text is ready in: $OUTPUT_DIR"
  
  # Count words in the latest file
  LATEST_FILE=$(ls -t $OUTPUT_DIR/*.txt 2>/dev/null | head -1)
  if [ -n "$LATEST_FILE" ]; then
    WORD_COUNT=$(wc -w < "$LATEST_FILE")
    echo "   Latest file: $(basename "$LATEST_FILE") ($WORD_COUNT words)"
  fi
  echo ""
fi
