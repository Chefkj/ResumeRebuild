#!/usr/bin/env python3
"""
Targeted OCR Improvement Script

This script specifically addresses OCR misrecognition issues with certain words
that are consistently misread, such as "diplomacy" being read as "Ciplomacy"
and "millcreek" being read as "villereek".

The script uses a combination of:
1. Word-level image processing techniques
2. Custom OCR configurations
3. Character-level analysis and correction
4. Multiple processing approaches with a voting mechanism
"""

import os
import sys
import time
import logging
import argparse
import re
from datetime import datetime
from collections import Counter

import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TargetedOCRImprover:
    """
    Class that focuses on improving OCR for specific problematic words and phrases
    through specialized image processing and OCR techniques.
    """
    
    def __init__(self, dpi=1500, known_problematic_words=None):
        """
        Initialize the targeted OCR improver
        
        Args:
            dpi: DPI for PDF to image conversion (default: 1500)
            known_problematic_words: Dict of known problematic words and their correct forms
        """
        self.dpi = dpi
        
        # Set default problematic words if none provided
        self.known_problem_words = known_problematic_words or {
            "ciplomacy": "diplomacy",
            "villereek": "millcreek",
            "villereeK": "millcreek",
            "Villereek": "Millcreek",
            "VillereekK": "Millcreek",
            "vill": "mill",
            # Common OCR substitution errors
            "cornpany": "company",
            "comrnittee": "committee", 
            "rnanagement": "management",
            "cornmunication": "communication",
            "rnanufacturing": "manufacturing",
            "rnarketing": "marketing",
            "developrnent": "development",
            "environrnent": "environment",
            "Environrnent": "Environment",
            "requirernents": "requirements",
            "achievernent": "achievement",
            "irnplementation": "implementation",
            "Irnplementation": "Implementation",
            "docurnent": "document",
            "rnonitoring": "monitoring",
            "prornotion": "promotion",
            "recomrnendation": "recommendation",
            "Recomrnendation": "Recommendation",
            # Additional common corrections
            "departrnent": "department",
            "rnanager": "manager",
            # URL and protocol fixes
            "httos": "https",
            "hftp": "http",
            "wwvv": "www",
            # Common character substitutions
            "JJ": "",  # Common phone number misreading
            "JJR": "",  # Another phone pattern
            # Add more known substitutions here
        }
        
        # Set PIL decompression bomb threshold for high-res images
        Image.MAX_IMAGE_PIXELS = 300000000
        
        # Base OCR configurations with various PSM values
        self.base_config_psm3 = f"--oem 3 --psm 3 -l eng --dpi {dpi} -c preserve_interword_spaces=1"
        self.base_config_psm4 = f"--oem 3 --psm 4 -l eng --dpi {dpi} -c preserve_interword_spaces=1"
        self.base_config_psm6 = f"--oem 3 --psm 6 -l eng --dpi {dpi} -c preserve_interword_spaces=1"
        self.base_config_psm11 = f"--oem 3 --psm 11 -l eng --dpi {dpi} -c preserve_interword_spaces=1"
        
        # Specialized configs for better character differentiation
        self.special_config = f"--oem 3 --psm 6 -l eng --dpi {dpi} -c preserve_interword_spaces=1 -c textord_min_linesize=1.2"
        
        # Create character confusion matrix to help with substitutions
        self.char_confusions = {
            'C': ['d', 'D'],  # For "Ciplomacy" -> "diplomacy"
            'v': ['m'],       # For "villereek" -> "millcreek"
            'vi': ['mi'],     # For prefix confusions "vill" -> "mill"
            'rn': ['m'],      # Common OCR confusion "rn" -> "m"
            'cl': ['d'],      # For "clifficulty" -> "difficulty"
            'cI': ['d'],      # Capital I confusion
            'li': ['d'],      # For "lifficulty" -> "difficulty"
            'ij': ['y'],      # For "identifij" -> "identify"
            'tl': ['d'],      # For "studient" -> "student"
            'fi': ['f'],      # For "difficujt" -> "difficult"
            'JJ': [''],       # Phone number artifacts
            'JJR': [''],      # Phone number artifacts
            'l1': ['d'],      # Number/letter confusion
            '0': ['o', 'O'],  # Zero/letter O confusion
            'S': ['5'],       # Letter S/number 5 confusion
            '5': ['S'],       # Number 5/letter S confusion
            '1': ['l', 'I'],  # Number 1/letter l/I confusion
            # Add more common character confusions here
        }
    
    def process_pdf(self, pdf_path):
        """
        Process a PDF file and return improved OCR text
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: The improved OCR text
        """
        try:
            logger.info(f"Converting PDF to images with DPI={self.dpi}")
            images = convert_from_path(pdf_path, dpi=self.dpi)
            logger.info(f"Converted {len(images)} pages")
            
            all_text = []
            
            for i, img in enumerate(images):
                logger.info(f"Processing page {i+1}")
                page_text = self._process_page(img)
                all_text.append(page_text)
            
            return "\n\n".join(all_text)
        
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _process_page(self, img):
        """
        Process a single page image with multiple techniques and combine results
        
        Args:
            img: PIL Image object of the page
            
        Returns:
            str: Improved OCR text for the page
        """
        results = []
        
        # 1. Standard processing with traditional approach
        result1 = self._process_traditional(img)
        results.append(result1)
        
        # 2. Enhanced contrast processing
        result2 = self._process_enhanced_contrast(img)
        results.append(result2)
        
        # 3. Multi-scale processing
        result3 = self._process_multi_scale(img)
        results.append(result3)
        
        # 4. Character-focused processing (better for specific words)
        result4 = self._process_character_focused(img)
        results.append(result4)
        
        # 5. Threshold-based processing
        result5 = self._process_threshold(img)
        results.append(result5)
        
        # 6. Location-specific optimization (for header/address areas)
        result6 = self._process_location_specific(img)
        results.append(result6)
        
        # 7. Enhanced preprocessing approach
        result7 = self._process_enhanced_preprocessing(img)
        results.append(result7)
        
        # Combine results using a word-by-word voting mechanism
        combined_text = self._combine_results(results)
        
        # Apply known corrections
        corrected_text = self._apply_corrections(combined_text)
        
        return corrected_text
    
    def _process_traditional(self, img):
        """Apply traditional OCR approach similar to the effective version from before"""
        # Convert to grayscale
        if img.mode != 'L':
            img = img.convert('L')
        
        # Enhance contrast slightly
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.7)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.7)
        
        # Slightly increase brightness
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        # Run OCR with multiple PSM modes and select best result
        text_psm3 = pytesseract.image_to_string(img, config=self.base_config_psm3)
        text_psm4 = pytesseract.image_to_string(img, config=self.base_config_psm4)
        text_psm6 = pytesseract.image_to_string(img, config=self.base_config_psm6)
        
        # Choose best result based on length
        texts = [text_psm3, text_psm4, text_psm6]
        word_counts = [len(text.split()) for text in texts]
        max_index = word_counts.index(max(word_counts))
        
        return texts[max_index]
    
    def _process_enhanced_contrast(self, img):
        """Apply very high contrast enhancement to help distinguish similar characters"""
        # Convert to grayscale
        if img.mode != 'L':
            img = img.convert('L')
        
        # Apply very high contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.5)  # Much higher contrast
        
        # Higher sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        
        # Run OCR with PSM 6 (assumes a single uniform block of text)
        text = pytesseract.image_to_string(img, config=self.special_config)
        return text
    
    def _process_multi_scale(self, img):
        """Process the image at multiple scales to catch details"""
        # Convert to numpy array for OpenCV processing
        np_img = np.array(img)
        
        if len(np_img.shape) == 3:  # Color image
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        else:
            gray = np_img
        
        # Create upscaled version (120%)
        height, width = gray.shape
        upscaled = cv2.resize(gray, (int(width * 1.2), int(height * 1.2)), 
                             interpolation=cv2.INTER_CUBIC)
        
        # Create downscaled version (80%)
        downscaled = cv2.resize(gray, (int(width * 0.8), int(height * 0.8)), 
                               interpolation=cv2.INTER_AREA)
        
        # Convert back to PIL
        pil_upscaled = Image.fromarray(upscaled)
        pil_downscaled = Image.fromarray(downscaled)
        
        # Run OCR on each scale with PSM 6
        text_normal = pytesseract.image_to_string(img, config=self.base_config_psm6)
        text_up = pytesseract.image_to_string(pil_upscaled, config=self.base_config_psm6)
        text_down = pytesseract.image_to_string(pil_downscaled, config=self.base_config_psm6)
        
        # Combine using word count heuristic
        texts = [text_normal, text_up, text_down]
        word_counts = [len(text.split()) for text in texts]
        max_index = word_counts.index(max(word_counts))
        
        return texts[max_index]
    
    def _process_character_focused(self, img):
        """Process with PSM 11 (sparse text with OSD) to focus on character-level recognition"""
        # Convert to grayscale
        if img.mode != 'L':
            img = img.convert('L')
        
        # Apply median filter to reduce noise
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        # Enhance sharpness significantly
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        
        # Increase contrast dramatically - helps distinguish v/m characters
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.5)
        
        # Convert to numpy for custom processing
        np_img = np.array(img)
        
        # Create an even more processed version to help with v/m distinction
        _, binary = cv2.threshold(np_img, 127, 255, cv2.THRESH_BINARY)
        
        # Dilate slightly - helps merge parts of 'm' that might get separated
        kernel = np.ones((2,1), np.uint8)  # Vertical kernel to help with m/v distinction
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        # Convert back to PIL
        processed = Image.fromarray(dilated)
        
        # Use PSM 11 which is better for character-by-character recognition
        text = pytesseract.image_to_string(processed, config=self.base_config_psm11)
        
        return text
    
    def _process_threshold(self, img):
        """Apply adaptive thresholding for better separation of characters"""
        # Convert to numpy array
        np_img = np.array(img)
        
        if len(np_img.shape) == 3:  # Color image
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        else:
            gray = np_img
            
        # Apply adaptive threshold
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Convert back to PIL
        binary_img = Image.fromarray(binary)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(binary_img)
        binary_img = enhancer.enhance(1.7)
        
        # Run OCR with base PSM 6
        text = pytesseract.image_to_string(binary_img, config=self.base_config_psm6)
        return text
        
    def _process_location_specific(self, img):
        """
        Special processing optimized for location/address fields in resumes
        which often contain the problem words like 'millcreek'
        """
        # Convert to numpy array for OpenCV processing
        np_img = np.array(img)
        
        if len(np_img.shape) == 3:  # Color image
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        else:
            gray = np_img
            
        # Use histogram equalization to improve contrast
        equalized = cv2.equalizeHist(gray)
        
        # Apply gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(equalized, (3, 3), 0)
        
        # Apply Otsu's thresholding
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Try to enhance the "m" character shape which is often misrecognized as "v"
        # Dilate horizontally to connect parts of "m"
        kernel = np.ones((1, 2), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        # Convert back to PIL
        processed = Image.fromarray(dilated)
        
        # Try both standard and character-focused OCR modes
        text1 = pytesseract.image_to_string(
            processed, 
            config=self.special_config + " -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789,. "
        )
        
        # Process the top portion of the image (where the address usually is)
        height, width = gray.shape
        top_portion = gray[0:int(height/4), :]
        
        # Extra processing for the top portion
        _, top_binary = cv2.threshold(top_portion, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Extra dilation for "m" characters in the top section
        kernel = np.ones((1, 2), np.uint8)
        top_dilated = cv2.dilate(top_binary, kernel, iterations=1)
        
        # Convert back to PIL
        top_processed = Image.fromarray(top_dilated)
        
        # OCR the top portion with aggressive settings focusing on addresses
        text2 = pytesseract.image_to_string(
            top_processed, 
            config=self.base_config_psm6 + " -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789,. "
        )
        
        # Combine the results (text1 for whole page, but use text2's address part if it contains location info)
        if "UT" in text2 or "millcreek" in text2.lower():
            # Extract the location part from text2
            location_match = re.search(r'([A-Za-z]+,?\s*UT\s*\d{5})', text2)
            if location_match:
                location_text = location_match.group(1)
                # Force the correct spelling of millcreek if it might be present
                if "vill" in location_text.lower() or "mill" in location_text.lower():
                    corrected_location = re.sub(r'[vV]illereek', 'Millcreek', location_text)
                    # Replace this part in text1
                    text1 = re.sub(r'[vV]illereek,?\s*UT\s*\d{5}', corrected_location, text1)
        
        return text1
    
    def _enhanced_image_preprocessing(self, img):
        """
        Apply advanced image preprocessing techniques to improve OCR accuracy
        
        Args:
            img: PIL Image object
            
        Returns:
            PIL.Image: Preprocessed image
        """
        # Convert to numpy array for OpenCV processing
        np_img = np.array(img)
        
        if len(np_img.shape) == 3:  # Color image
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        else:
            gray = np_img
        
        # Apply bilateral filter to reduce noise while preserving edges
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply histogram equalization to improve contrast
        equalized = cv2.equalizeHist(denoised)
        
        # Apply morphological operations to improve character shapes
        # Create kernel for morphological operations
        kernel = np.ones((1, 1), np.uint8)
        
        # Opening (erosion followed by dilation) to remove noise
        opened = cv2.morphologyEx(equalized, cv2.MORPH_OPEN, kernel)
        
        # Closing (dilation followed by erosion) to fill gaps in characters
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
        
        # Apply adaptive thresholding for better binarization
        adaptive_thresh = cv2.adaptiveThreshold(
            closed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply slight dilation to strengthen character strokes
        dilated = cv2.dilate(adaptive_thresh, kernel, iterations=1)
        
        # Convert back to PIL Image
        processed_img = Image.fromarray(dilated)
        
        return processed_img
    
    def _process_enhanced_preprocessing(self, img):
        """
        Apply enhanced preprocessing before OCR for better accuracy
        
        Args:
            img: PIL Image object
            
        Returns:
            str: OCR text result
        """
        # Apply enhanced preprocessing
        processed_img = self._enhanced_image_preprocessing(img)
        
        # Run OCR with the best configuration for processed images
        text = pytesseract.image_to_string(processed_img, config=self.base_config_psm6)
        
        return text
    
    def _combine_results(self, results):
        """
        Combine multiple OCR results using a word-by-word voting mechanism
        with case-insensitive matching for better consensus
        
        Args:
            results: List of OCR text results
            
        Returns:
            str: Combined text using word-level voting
        """
        # Split each result into words
        word_lists = [result.split() for result in results]
        
        # Get the maximum number of words across all results
        max_words = max(len(words) for words in word_lists)
        
        # Fill shorter lists with None to avoid index errors
        for i in range(len(word_lists)):
            word_lists[i].extend([None] * (max_words - len(word_lists[i])))
        
        # Combine words using case-insensitive voting
        final_words = []
        for i in range(max_words):
            # Get all non-None words at this position
            word_candidates = [word_list[i] for word_list in word_lists if i < len(word_list) and word_list[i] is not None]
            
            if not word_candidates:
                continue
            
            # Create case-insensitive counter for better voting
            word_counts = Counter()
            word_originals = {}  # Store original case versions
            
            # Count occurrences with case-insensitive matching
            for word in word_candidates:
                word_lower = word.lower()
                word_counts[word_lower] += 1
                
                # Keep track of original case versions
                if word_lower not in word_originals:
                    word_originals[word_lower] = []
                word_originals[word_lower].append(word)
                
            # Get most common word (case insensitive)
            most_common_word_lower = word_counts.most_common(1)[0][0]
            
            # Now select the best case version of this word
            versions = word_originals[most_common_word_lower]
            
            # Special handling for problematic words (better case handling)
            if most_common_word_lower in ('ciplomacy', 'diplomacy'):
                # First check if any version starts with capital D (preferred for Diplomacy)
                d_versions = [v for v in versions if v.startswith('D')]
                if d_versions:
                    final_words.append(d_versions[0])
                else:
                    final_words.append('Diplomacy')  # Force correct capitalization
            else:
                # Choose the most common capitalization pattern for this word
                capitalization_counter = Counter(versions)
                final_words.append(capitalization_counter.most_common(1)[0][0])
        
        # Join words back to text
        return " ".join(final_words)
    
    def _apply_corrections(self, text):
        """
        Apply known corrections to the text
        
        Args:
            text: Text to correct
            
        Returns:
            str: Corrected text
        """
        # Split text into words for processing
        words = text.split()
        corrected_words = []
        
        # Look for location patterns: city, state ZIP
        # For example: "villereek, UT 84106" should become "millcreek, UT 84106"
        location_pattern = re.compile(r'(\w+),\s*([A-Z]{2})\s*(\d{5})')
        
        for i, word in enumerate(words):
            # Convert to lowercase for checking
            word_lower = word.lower()
            
            # Check if word is in known problem words
            if word_lower in self.known_problem_words:
                # Replace with correct word, preserving capitalization
                correct_word = self.known_problem_words[word_lower]
                
                # Preserve original capitalization pattern
                if word.isupper():
                    corrected = correct_word.upper()
                elif word[0].isupper():
                    corrected = correct_word.capitalize()
                else:
                    corrected = correct_word
                    
                corrected_words.append(corrected)
                logger.info(f"Corrected '{word}' to '{corrected}'")
            else:
                # Special handling for location patterns
                if i < len(words) - 2 and word.endswith(',') and len(words[i+1]) == 2 and words[i+1].isupper():
                    # This might be part of a location pattern: "villereek, UT 84106"
                    city_part = word.rstrip(',')
                    if city_part.lower() == 'villereek':
                        corrected = 'millcreek,'
                        corrected_words.append(corrected)
                        logger.info(f"Corrected location '{word}' to '{corrected}'")
                    else:
                        corrected_words.append(word)
                else:
                    # Look for standalone instances of villereek without comma
                    if word_lower == 'villereek':
                        corrected = 'millcreek'
                        if word[0].isupper():
                            corrected = corrected.capitalize()
                        corrected_words.append(corrected)
                        logger.info(f"Corrected '{word}' to '{corrected}'")
                    else:
                        corrected_words.append(word)
        
        corrected_text = " ".join(corrected_words)
        
        # Also do a pattern-based replacement for location formats
        corrected_text = location_pattern.sub(
            lambda m: (f"millcreek, {m.group(2)} {m.group(3)}" 
                      if m.group(1).lower() == 'villereek' 
                      else m.group(0)), 
            corrected_text
        )
        
        return corrected_text

    def _apply_pattern_corrections(self, text):
        """
        Apply pattern-based corrections for URLs, phone numbers, emails, and other structured data
        
        Args:
            text: Text to correct
            
        Returns:
            str: Text with pattern corrections applied
        """
        corrected_text = text
        
        # Fix URL patterns
        # Common OCR errors in URLs
        url_fixes = [
            (r'\bhttos://', 'https://'),
            (r'\bhftp://', 'http://'),
            (r'\bwwvv\.', 'www.'),
            (r'\bgithub\.corn/', 'github.com/'),
            (r'\bgmail\.corn\b', 'gmail.com'),
            (r'\byahoo\.corn\b', 'yahoo.com'),
            (r'\boutlook\.corn\b', 'outlook.com'),
            (r'\blinkedin\.corn/', 'linkedin.com/'),
            (r'\bspoti\.fi([0-9a-zA-Z]+)', r'spoti.fi/\1'),
            (r'\.corn\b', '.com'),  # General .corn -> .com fix
        ]
        
        for pattern, replacement in url_fixes:
            corrected_text = re.sub(pattern, replacement, corrected_text, flags=re.IGNORECASE)
        
        # Fix phone number patterns
        # Remove common OCR artifacts in phone numbers
        phone_fixes = [
            # Remove JJ, JJR patterns often found near phone numbers
            (r'\b(JJ|JJR)\s*(\d{3}[-\s]*\d{3}[-\s]*\d{4})', r'\2'),
            (r'(\d{3}[-\s]*\d{3}[-\s]*\d{4})\s*(JJ|JJR)\b', r'\1'),
            # Fix common digit misreading in phone numbers
            (r'\b(\d{3})[-\s]*([O0])(\d{2})[-\s]*(\d{4})\b', r'\1-\g<2>\3-\4'),
        ]
        
        for pattern, replacement in phone_fixes:
            corrected_text = re.sub(pattern, replacement, corrected_text)
        
        # Fix email patterns
        email_fixes = [
            (r'@gmail\.corn\b', '@gmail.com'),
            (r'@yahoo\.corn\b', '@yahoo.com'),
            (r'@outlook\.corn\b', '@outlook.com'),
            (r'@hotmail\.corn\b', '@hotmail.com'),
        ]
        
        for pattern, replacement in email_fixes:
            corrected_text = re.sub(pattern, replacement, corrected_text, flags=re.IGNORECASE)
        
        # Fix common word separations caused by OCR
        word_separation_fixes = [
            # Fix separated words
            (r'\b([Cc])orn pany\b', r'\1ompany'),
            (r'\b([Mm])anage ment\b', r'\1anagement'),
            (r'\b([Dd])evelop ment\b', r'\1evelopment'),
            (r'\b([Ee])nviron ment\b', r'\1nvironment'),
            (r'\b([Ii])mple mentation\b', r'\1mplementation'),
            (r'\b([Rr])equire ments\b', r'\1equirements'),
            (r'\b([Aa])chieve ment\b', r'\1chievement'),
            # Fix common character substitutions in context
            (r'\b([A-Za-z]+)rn([a-z]+)\b', self._fix_rn_substitution),
        ]
        
        for pattern, replacement in word_separation_fixes:
            if callable(replacement):
                corrected_text = re.sub(pattern, replacement, corrected_text)
            else:
                corrected_text = re.sub(pattern, replacement, corrected_text)
        
        return corrected_text
    
    def _fix_rn_substitution(self, match):
        """
        Fix common 'rn' -> 'm' substitution in context
        
        Args:
            match: Regex match object
            
        Returns:
            str: Corrected word
        """
        word = match.group(0)
        prefix = match.group(1)
        suffix = match.group(2)
        
        # Common words where 'rn' should be 'm'
        common_rn_to_m = {
            'cornpany': 'company',
            'comrnittee': 'committee',
            'rnanagement': 'management',
            'cornmunication': 'communication',
            'rnanufacturing': 'manufacturing',
            'rnarketing': 'marketing',
            'developrnent': 'development',
            'environrnent': 'environment',
            'requirernents': 'requirements',
            'achievernent': 'achievement',
            'irnplementation': 'implementation',
            'docurnent': 'document',
            'rnonitoring': 'monitoring',
            'prornotion': 'promotion',
            'recomrnendation': 'recommendation',
        }
        
        word_lower = word.lower()
        if word_lower in common_rn_to_m:
            corrected = common_rn_to_m[word_lower]
            # Preserve original capitalization
            if word[0].isupper():
                corrected = corrected.capitalize()
            if word.isupper():
                corrected = corrected.upper()
            return corrected
        
        return word

    def _apply_corrections(self, text):
        """
        Apply known corrections to the text including pattern-based fixes
        
        Args:
            text: Text to correct
            
        Returns:
            str: Corrected text
        """
        # First apply word-level corrections
        corrected_text = self._apply_word_corrections(text)
        
        # Then apply pattern-based corrections
        corrected_text = self._apply_pattern_corrections(corrected_text)
        
        return corrected_text
    
    def _apply_word_corrections(self, text):
        """
        Apply known word corrections to the text
        
        Args:
            text: Text to correct
            
        Returns:
            str: Corrected text
        """
        # Split text into words for processing
        words = text.split()
        corrected_words = []
        
        # Look for location patterns: city, state ZIP
        # For example: "villereek, UT 84106" should become "millcreek, UT 84106"
        location_pattern = re.compile(r'(\w+),\s*([A-Z]{2})\s*(\d{5})')
        
        for i, word in enumerate(words):
            # Convert to lowercase for checking
            word_lower = word.lower()
            
            # Check if word is in known problem words
            if word_lower in self.known_problem_words:
                # Replace with correct word, preserving capitalization
                correct_word = self.known_problem_words[word_lower]
                
                # Preserve original capitalization pattern
                if word.isupper():
                    corrected = correct_word.upper()
                elif word[0].isupper():
                    corrected = correct_word.capitalize()
                else:
                    corrected = correct_word
                    
                corrected_words.append(corrected)
                logger.info(f"Corrected '{word}' to '{corrected}'")
            else:
                # Special handling for location patterns
                if i < len(words) - 2 and word.endswith(',') and len(words[i+1]) == 2 and words[i+1].isupper():
                    # This might be part of a location pattern: "villereek, UT 84106"
                    city_part = word.rstrip(',')
                    if city_part.lower() == 'villereek':
                        corrected = 'millcreek,'
                        corrected_words.append(corrected)
                        logger.info(f"Corrected location '{word}' to '{corrected}'")
                    else:
                        corrected_words.append(word)
                else:
                    # Look for standalone instances of villereek without comma
                    if word_lower == 'villereek':
                        corrected = 'millcreek'
                        if word[0].isupper():
                            corrected = corrected.capitalize()
                        corrected_words.append(corrected)
                        logger.info(f"Corrected '{word}' to '{corrected}'")
                    else:
                        corrected_words.append(word)
        
        corrected_text = " ".join(corrected_words)
        
        # Also do a pattern-based replacement for location formats
        corrected_text = location_pattern.sub(
            lambda m: (f"millcreek, {m.group(2)} {m.group(3)}" 
                      if m.group(1).lower() == 'villereek' 
                      else m.group(0)), 
            corrected_text
        )
        
        return corrected_text


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Targeted OCR improvement for specific words.')
    parser.add_argument('pdf_path', help='Path to the PDF file to extract text from')
    parser.add_argument('--output', '-o', default='.', help='Output directory for text files')
    parser.add_argument('--dpi', '-d', type=int, default=1500, help='DPI for PDF to image conversion')
    parser.add_argument('--view-full', '-f', action='store_true', help='View full extracted text')
    
    args = parser.parse_args()
    
    print(f"\nRunning targeted OCR improvement on {args.pdf_path}...")
    print(f"Using DPI={args.dpi}")
    
    # Define known problematic words and their corrections
    # This dictionary can be expanded with more problematic words as they're identified
    known_problem_words = {
        # Resume-specific word corrections with all capitalization variants
        "ciplomacy": "diplomacy",
        "Ciplomacy": "Diplomacy",
        "CIPLOMACY": "DIPLOMACY",
        "villereek": "millcreek",
        "Villereek": "Millcreek",
        "VILLEREEK": "MILLCREEK",
        "villereek,": "millcreek,",
        "Villereek,": "Millcreek,",
        
        # Common OCR mistakes with lowercase/uppercase variants
        "cornpany": "company",
        "Cornpany": "Company",
        "CORNPANY": "COMPANY",
        "cornrnunication": "communication",
        "Cornrnunication": "Communication",
        "CORNRNUNICATION": "COMMUNICATION",
        "problern": "problem",
        "Problern": "Problem",
        "PROBLERN": "PROBLEM",
        "rnanagement": "management",
        "Rnanagement": "Management",
        "RNANAGEMENT": "MANAGEMENT",
        "achievernent": "achievement",
        "Achievernent": "Achievement",
        "ACHIEVERNENT": "ACHIEVEMENT",
        "developrnent": "development",
        "Developrnent": "Development",
        "DEVELOPRNENT": "DEVELOPMENT",
        "implernentation": "implementation",
        "Implernentation": "Implementation",
        "IMPLERNENTATION": "IMPLEMENTATION",
        # Add more known substitutions as you identify them
    }
    
    # Start processing timer
    start_time = time.time()
    
    # Initialize the targeted OCR improver
    improver = TargetedOCRImprover(dpi=args.dpi, known_problematic_words=known_problem_words)
    
    # Process the PDF
    improved_text = improver.process_pdf(args.pdf_path)
    
    # End timer
    elapsed_time = time.time() - start_time
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
    output_file = os.path.join(args.output, f"{base_name}_targeted_ocr_{timestamp}.txt")
    
    # Save output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(improved_text)
        
    # Display results
    print(f"\nProcessing completed in {elapsed_time:.2f} seconds")
    print(f"Saved improved OCR text to {output_file}")
    print(f"Word count: {len(improved_text.split())}")
    
    # Print text sample
    if args.view_full:
        print("\n--- Full improved OCR text ---")
        print("="*80)
        print(improved_text)
        print("="*80)
    else:
        print("\n--- Sample of improved OCR text (first 1000 characters) ---")
        print("="*80)
        print(improved_text[:1000] + "..." if len(improved_text) > 1000 else improved_text)
        print("="*80)
    
    # Check for specific problematic words
    for prob_word, correct_word in known_problem_words.items():
        if prob_word.lower() in improved_text.lower():
            print(f"Warning: Problematic word '{prob_word}' still present in text")
        else:
            print(f"Success: Problematic word '{prob_word}' was not found in text")
            
    # Quick validation check
    for correct_word in known_problem_words.values():
        if correct_word.lower() in improved_text.lower():
            print(f"Validation: Correct word '{correct_word}' was found in text")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
