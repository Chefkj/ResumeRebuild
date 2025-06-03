#!/bin/bash
# This script runs a comprehensive OCR improvement workflow:
# 1. Traditional OCR and Raw OCR for comparison
# 2. Targeted OCR improvement focused on fixing specific problematic words
# 3. Saves all outputs with timestamps

# Display help if requested
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
  echo "Usage: $0 path/to/resume.pdf [output_dir] [dpi]"
  echo ""
  echo "Arguments:"
  echo "  path/to/resume.pdf  - Path to the PDF file to process (required)"
  echo "  output_dir          - Directory to save output files (optional, default: current dir)"
  echo "  dpi                 - DPI value for processing (optional, default: 1200)"
  echo ""
  echo "Example: $0 improved_resume.pdf ./output 1500"
  exit 0
fi

# Check for required arguments
if [ -z "$1" ]; then
  echo "Error: PDF path is required"
  echo "Run '$0 --help' for usage information"
  exit 1
fi

# Get arguments with defaults
PDF_PATH="$1"
OUTPUT_DIR="${2:-.}"
DPI="${3:-1200}"  # Default to 1200 DPI for speed, use 1500 for higher quality

# Ensure the PDF file exists
if [ ! -f "$PDF_PATH" ]; then
  echo "Error: PDF file not found: $PDF_PATH"
  exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "===== OCR IMPROVEMENT WORKFLOW ====="
echo "Processing PDF: $PDF_PATH"
echo "Output directory: $OUTPUT_DIR"
echo "DPI setting: $DPI"
echo "=================================="

# Step 1: Run comparison of traditional methods
echo -e "\n[1/3] COMPARING OCR METHODS FOR BENCHMARKING"
python3 compare_ocr_methods.py "$PDF_PATH" --output "$OUTPUT_DIR"

# Step 2: Run targeted OCR improvement with consensus approach
echo -e "\n[2/3] RUNNING TARGETED OCR IMPROVEMENT WITH CONSENSUS"
python3 targeted_ocr_improvement.py "$PDF_PATH" --dpi "$DPI" --output "$OUTPUT_DIR"

# Step 3: Run targeted OCR improvement with higher DPI if using default
if [ "$DPI" -lt 1500 ]; then
  echo -e "\n[3/3] RUNNING HIGH-QUALITY TARGETED OCR (DPI=1500)"
  python3 targeted_ocr_improvement.py "$PDF_PATH" --dpi 1500 --output "$OUTPUT_DIR"
else
  echo -e "\n[3/3] SKIPPING HIGH-QUALITY RUN (ALREADY USING DPI≥1500)"
fi

echo -e "\n===== OCR IMPROVEMENT COMPLETE ====="
echo "All output files saved to: $OUTPUT_DIR"

# Find the most recent targeted OCR output file
LATEST_OCR_FILE=$(find "$OUTPUT_DIR" -name "*_targeted_ocr_*.txt" -type f -printf "%T@ %p\n" | sort -nr | head -1 | cut -d' ' -f2-)

if [ -n "$LATEST_OCR_FILE" ]; then
  echo -e "\nMOST RECENT OCR RESULT:"
  echo "$LATEST_OCR_FILE"
  echo -e "\nSample (first 5 lines):"
  head -n 5 "$LATEST_OCR_FILE"
fi

echo -e "\nDone."
