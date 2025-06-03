#!/usr/bin/env python3
"""
OCR Extractor with Traditional Preprocessing

This script provides a more traditional OCR processing pipeline
that doesn't use advanced image processing techniques, which might
work better for certain types of resumes.
"""

import os
import sys
import logging
from PIL import Image, ImageEnhance
import pytesseract
from pdf2image import convert_from_path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path, dpi=1500):
    """
    Extract text from a PDF using a traditional OCR approach
    
    Args:
        pdf_path: Path to the PDF file
        dpi: DPI to use for PDF to image conversion
        
    Returns:
        str: Extracted text
    """
    try:
        # Convert PDF to images
        logger.info(f"Converting PDF to images with DPI={dpi}")
        
        # Prevent PIL DecompressionBomb errors
        Image.MAX_IMAGE_PIXELS = 300000000
        
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=dpi)
        logger.info(f"Converted {len(images)} pages")
        
        all_text = []
        
        # Process each page
        for i, img in enumerate(images):
            logger.info(f"Processing page {i+1}")
            
            # Convert to grayscale
            if img.mode != 'L':
                img = img.convert('L')
            
            # Enhance contrast slightly
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.7)  # Increased from 1.5
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.7)  # Increased from 1.5
            
            # Slightly increase brightness
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)
            
            # Use OCR with different PSM modes
            logger.info("Running OCR with PSM mode 4")
            config_psm4 = f"--oem 3 --psm 4 -l eng --dpi {dpi} -c preserve_interword_spaces=1"
            text_psm4 = pytesseract.image_to_string(img, config=config_psm4)
            
            logger.info("Running OCR with PSM mode 3")
            config_psm3 = f"--oem 3 --psm 3 -l eng --dpi {dpi} -c preserve_interword_spaces=1"
            text_psm3 = pytesseract.image_to_string(img, config=config_psm3)
            
            logger.info("Running OCR with PSM mode 6") 
            config_psm6 = f"--oem 3 --psm 6 -l eng --dpi {dpi} -c preserve_interword_spaces=1"
            text_psm6 = pytesseract.image_to_string(img, config=config_psm6)
            
            # Choose the text based on content length
            texts = [text_psm3, text_psm4, text_psm6]
            # Pick the one with the most words (simple metric)
            word_counts = [len(text.split()) for text in texts]
            max_index = word_counts.index(max(word_counts))
            page_text = texts[max_index]
            logger.info(f"Selected text from PSM mode {[3, 4, 6][max_index]} with {word_counts[max_index]} words")
            all_text.append(page_text)
        
        # Combine all pages
        return "\n\n".join(all_text)
    
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        import traceback
        traceback.print_exc()
        return ""

if __name__ == "__main__":
    import argparse
    import time
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Extract text from PDF using traditional OCR approach")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--dpi", type=int, default=1500, help="DPI for PDF to image conversion")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    parser.add_argument("--view-full", "-f", action="store_true", help="View the full extracted text in the terminal")
    
    args = parser.parse_args()
    
    print(f"\nExtracting text from {args.pdf_path} using traditional OCR (DPI={args.dpi})")
    print("This may take a while...")
    
    start_time = time.time()
    extracted_text = extract_text_from_pdf(args.pdf_path, args.dpi)
    elapsed_time = time.time() - start_time
    
    print(f"Extraction completed in {elapsed_time:.2f} seconds")
    
    # Save output to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
    output_file = os.path.join(args.output, f"{base_name}_trad_ocr_{timestamp}.txt")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(extracted_text)
    
    print(f"Saved extracted text to {output_file}")
    print(f"Word count: {len(extracted_text.split())}")
    
    # Print text
    if args.view_full:
        print("\n--- Full extracted text ---")
        print("="*80)
        print(extracted_text)
        print("="*80)
    else:
        print("\n--- Sample of extracted text (first 1000 characters) ---")
        print("="*80)
        print(extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text)
        print("="*80)
