"""
Raw OCR Text Extraction Utility

This module provides utilities for extracting raw text from PDFs using OCR,
without any post-processing or header detection.
"""

import os
import logging
import pytesseract
from pdf2image import convert_from_path
import re

logger = logging.getLogger(__name__)

class RawOCRTextExtractor:
    """Utility class for extracting raw text from PDFs using OCR without post-processing."""
    
    def __init__(self, dpi=1400, aggressive_mode=True, try_multiple_scales=True):
        """Initialize the raw OCR text extractor.
        
        Args:
            dpi: DPI value for PDF to image conversion (default: 1400)
            aggressive_mode: Whether to use aggressive image enhancement (default: True)
            try_multiple_scales: Whether to try extracting text at different scales (default: True)
        """
        self.dpi = dpi  # Higher DPI for better quality and recognition of small text
        self.aggressive_mode = aggressive_mode  # Enable aggressive image processing
        self.try_multiple_scales = try_multiple_scales  # Try different scale factors
        
        # Increase PIL's DecompressionBomb limit if needed for high DPI processing
        try:
            from PIL import Image
            # Set a higher limit for large images (only if we're using high DPI)
            if self.dpi > 1200:
                Image.MAX_IMAGE_PIXELS = 300000000  # Increased limit to handle higher DPI
                
                # Set warning threshold higher too to avoid unnecessary warnings
                Image.warnings.filterwarnings(
                    "ignore", 
                    category=Image.DecompressionBombWarning
                )
        except Exception as e:
            logger.warning(f"Could not increase PIL decompression bomb limit: {e}")
            logger.warning("If you encounter DecompressionBombError, consider using a lower DPI value")
        
        # Adjust tesseract OCR parameters based on mode
        base_config = f'--dpi {self.dpi} -l eng -c preserve_interword_spaces=1'
        
        # PSM 4 is better at handling single column with various text sizes typical in resumes
        # OEM 3 is the LSTM neural network OCR engine which is most accurate for modern texts
        self.tesseract_config = f'--oem 3 --psm 4 {base_config}'
        if self.aggressive_mode:
            self.tesseract_config += ' -c textord_old_xheight=0 -c tessedit_char_blacklist="|" -c textord_fix_xheight=1'
        
        # Alternative configuration with PSM 3 (fully automatic page segmentation)
        self.tesseract_config_alt = f'--oem 3 --psm 3 {base_config}'
        if self.aggressive_mode:
            self.tesseract_config_alt += ' -c textord_min_linesize=1.0'
    
    def _check_tesseract_setup(self):
        """
        Check if Tesseract OCR is properly installed and configured.
        
        Returns:
            bool: True if Tesseract is ready for use, False otherwise
        """
        # Check if Tesseract is installed
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR version {version} is available.")
            
            # Check for TESSDATA_PREFIX environment variable
            import os
            tessdata_prefix = os.environ.get('TESSDATA_PREFIX')
            if not tessdata_prefix:
                # Try to find tessdata directory
                import shutil
                tesseract_path = shutil.which('tesseract')
                if tesseract_path:
                    # Common locations based on OS
                    import platform
                    system = platform.system().lower()
                    
                    if 'darwin' in system:  # macOS
                        possible_paths = [
                            '/usr/local/share/tessdata',
                            '/opt/homebrew/share/tessdata',
                            '/usr/share/tessdata'
                        ]
                    elif 'linux' in system:  # Linux
                        possible_paths = [
                            '/usr/share/tessdata',
                            '/usr/local/share/tessdata'
                        ]
                    else:  # Windows or other
                        possible_paths = []
                        
                    # Try to find tessdata directory
                    tessdata_path = None
                    for path in possible_paths:
                        if os.path.exists(path) and os.path.isdir(path):
                            # Check if it contains eng.traineddata
                            if os.path.exists(os.path.join(path, 'eng.traineddata')):
                                tessdata_path = path
                                break
                    
                    if tessdata_path:
                        logger.info(f"Found tessdata directory at: {tessdata_path}")
                        logger.info(f"Setting TESSDATA_PREFIX to: {tessdata_path}")
                        os.environ['TESSDATA_PREFIX'] = tessdata_path
                    else:
                        logger.warning("TESSDATA_PREFIX environment variable not set, and tessdata directory not found.")
                        logger.warning("OCR quality may be reduced without language data files.")
            else:
                logger.info(f"TESSDATA_PREFIX is set to: {tessdata_prefix}")
                
            return True
        except Exception as e:
            logger.error(f"Tesseract OCR is not properly installed or configured: {e}")
            logger.error("Please install Tesseract OCR and ensure it's in your PATH.")
            logger.error("On macOS: brew install tesseract")
            logger.error("On Ubuntu: sudo apt-get install tesseract-ocr")
            logger.error("On Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki")
            return False
    
    def extract_raw_text(self, pdf_path, ocr_mode="all"):
        """
        Extract raw text from a PDF using OCR with no post-processing.
        
        Args:
            pdf_path: Path to the PDF file
            ocr_mode: OCR mode to use ("psm3", "psm4", or "all" for both)
            
        Returns:
            str: Raw extracted text without any formatting or header detection
        """
        try:
            # Check if Tesseract is installed and configured
            if not self._check_tesseract_setup():
                raise RuntimeError("Tesseract OCR is required but not properly installed or configured.")
            
            # Convert PDF to images
            logger.info(f"Converting PDF to images: {pdf_path} with DPI={self.dpi}")
            try:
                images = convert_from_path(pdf_path, dpi=self.dpi)
            except Exception as e:
                logger.error(f"PDF to image conversion failed: {e}")
                if "poppler" in str(e).lower():
                    raise RuntimeError("Poppler utilities must be installed. On macOS: brew install poppler")
                raise
            
            if not images:
                logger.warning("No images were extracted from the PDF")
                return ""
            
            logger.info(f"Successfully converted {len(images)} pages to images")
            
            all_text = []
            
            # Advanced OCR configurations for experimentation
            ocr_configs = {
                # Default configurations
                'psm4': self.tesseract_config,
                'psm3': self.tesseract_config_alt,
                
                # Additional PSM modes for specialized cases
                'psm6': f'--oem 3 --psm 6 -l eng --dpi {self.dpi} -c preserve_interword_spaces=1',  # Single uniform block of text
                'psm11': f'--oem 3 --psm 11 -l eng --dpi {self.dpi} -c preserve_interword_spaces=1',  # Sparse text - no block detection
                
                # Extra configuration that might help with specific cases
                'psm4_advanced': f'--oem 3 --psm 4 -l eng --dpi {self.dpi} -c preserve_interword_spaces=1 -c textord_min_linesize=1.0'
            }
            
            # Process each page with OCR using improved methods
            for i, img in enumerate(images):
                logger.info(f"Processing page {i+1} with OCR (mode: {ocr_mode})")
                
                # Create a dictionary to store text from different OCR configs and scales
                page_texts = {}
                
                # Define scale factors to try if multi-scale is enabled
                scale_factors = [1.0]
                if self.try_multiple_scales:
                    scale_factors = [1.0, 1.2]  # Try original scale and slightly larger
                
                # Try each scale factor
                for scale_factor in scale_factors:
                    scale_name = f"scale_{int(scale_factor*100)}"
                    logger.info(f"Trying scale factor: {scale_factor:.2f}")
                    
                    # Apply scaling if not 1.0
                    current_img = img
                    if scale_factor != 1.0:
                        from PIL import Image
                        if isinstance(img, Image.Image):
                            width, height = img.size
                            new_width = int(width * scale_factor)
                            new_height = int(height * scale_factor)
                            current_img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Preprocess the image using enhanced techniques
                    preprocessed_img = self._preprocess_image(current_img)
                    
                    # Determine which configurations to use based on the mode
                    configs_to_try = []
                    if ocr_mode == "psm3":
                        configs_to_try = ['psm3']
                    elif ocr_mode == "psm4":
                        configs_to_try = ['psm4']
                    else:  # "all" mode or any other value
                        configs_to_try = ['psm3', 'psm4', 'psm6', 'psm11', 'psm4_advanced']
                    
                    # Skip some configurations for non-original scales to save time
                    if scale_factor != 1.0:
                        # For alternate scales, just try the main PSM modes
                        configs_to_try = [cfg for cfg in configs_to_try if cfg in ['psm3', 'psm4']]
                
                    # Try each selected configuration
                    for config_name in configs_to_try:
                        config = ocr_configs[config_name]
                        logger.info(f"Running OCR with configuration: {config_name} at {scale_name}")
                        
                        # Create a unique identifier for this combination of scale and config
                        config_id = f"{scale_name}_{config_name}"
                        
                        # Try with preprocessed image
                        page_texts[config_id] = pytesseract.image_to_string(preprocessed_img, config=config)
                        
                        # For "all" mode, also try with image rotated slightly in case of alignment issues
                        # But only for the primary PSM modes and only at the original scale to save time
                        if ocr_mode == "all" and config_name in ['psm3', 'psm4'] and scale_factor == 1.0:
                            try:
                                from PIL import Image
                                # Try with a slight clockwise rotation
                                rotated_img_cw = preprocessed_img.rotate(-1, resample=Image.BICUBIC, expand=True)
                                page_texts[f"{config_id}_rot_cw"] = pytesseract.image_to_string(rotated_img_cw, config=config)
                                
                                # Try with a slight counter-clockwise rotation
                                rotated_img_ccw = preprocessed_img.rotate(1, resample=Image.BICUBIC, expand=True)
                                page_texts[f"{config_id}_rot_ccw"] = pytesseract.image_to_string(rotated_img_ccw, config=config)
                            except Exception as e:
                                logger.warning(f"Rotation attempt failed: {e}")
                
                # Choose the best text based on the mode and content
                if ocr_mode == "psm3" and "scale_100_psm3" in page_texts:
                    page_text = page_texts["scale_100_psm3"]
                elif ocr_mode == "psm4" and "scale_100_psm4" in page_texts:
                    page_text = page_texts["scale_100_psm4"]
                else:
                    # For "all" mode, select the result with the most text content after filtering out noise
                    def score_text(text):
                        # Count real words (more than 2 characters) as a simple quality metric
                        # Filter out garbage strings that are likely OCR errors
                        words = [word for word in text.split() if len(word) > 2 and len(word) < 20]
                        
                        # Count words that appear to be valid (containing vowels, etc.)
                        valid_word_count = 0
                        for word in words:
                            if len(word) > 1:
                                if any(vowel in word.lower() for vowel in 'aeiou'):
                                    valid_word_count += 1
                        
                        # Count lines that have meaningful content
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        content_lines = len(lines)
                        
                        # Calculate a weighted score that favors more valid words and reasonable number of lines
                        return (valid_word_count * 10) + content_lines
                    
                    # Get the text with the highest score
                    best_text = ""
                    best_score = 0
                    best_config = ""
                    
                    # Score each text variant
                    for config_name, text in page_texts.items():
                        score = score_text(text)
                        
                        # Log the scores for debugging
                        logger.info(f"Configuration '{config_name}' score: {score} (words: {len(text.split())})")
                        
                        if score > best_score:
                            best_score = score
                            best_text = text
                            best_config = config_name
                    
                    logger.info(f"Selected text from configuration '{best_config}' with score {best_score}")
                    page_text = best_text
                    
                    # If the best score is very low, we might have missed something important
                    # Try combining results from multiple configurations
                    if best_score < 30 and len(page_texts) > 1:
                        logger.warning(f"Best score is very low ({best_score}). Attempting combined approach.")
                        
                        # Combine texts from the best configurations of each scale factor
                        # First, get the best config for each scale
                        best_by_scale = {}
                        for config_name, text in page_texts.items():
                            if "_rot_" not in config_name:  # Skip rotated versions
                                parts = config_name.split('_')
                                if len(parts) >= 2:
                                    scale = f"{parts[0]}_{parts[1]}"
                                    score = score_text(text)
                                    
                                    if scale not in best_by_scale or score > best_by_scale[scale]['score']:
                                        best_by_scale[scale] = {
                                            'text': text,
                                            'score': score,
                                            'config': config_name
                                        }
                        
                        # Combine the texts from different scales
                        if len(best_by_scale) > 1:
                            combined_texts = []
                            for scale, data in best_by_scale.items():
                                combined_texts.append(data['text'])
                                logger.info(f"Including {scale} with score {data['score']}")
                            
                            # Join texts with double newlines
                            combined_text = "\n\n".join(combined_texts)
                            
                            # Remove duplicate lines
                            lines = combined_text.split('\n')
                            unique_lines = []
                            seen = set()
                            for line in lines:
                                line_clean = line.strip()
                                if line_clean and line_clean not in seen:
                                    seen.add(line_clean)
                                    unique_lines.append(line)
                            
                            combined_text = '\n'.join(unique_lines)
                            combined_score = score_text(combined_text)
                            
                            if combined_score > best_score:
                                logger.info(f"Using combined text with score {combined_score}")
                                page_text = combined_text
                
                # Add to the combined text
                all_text.append(page_text)
            
            # Combine text from all pages with minimal formatting (just page separators)
            combined_text = "\n\n".join(all_text)
            
            logger.info("Raw OCR text extraction completed successfully")
            return combined_text
        
        except Exception as e:
            logger.error(f"Raw OCR text extraction failed: {e}")
            raise
    
    def _preprocess_image(self, img):
        """
        Preprocess image to improve OCR quality with enhanced techniques.
        
        Args:
            img: PIL Image or numpy array
            
        Returns:
            PIL Image: Enhanced image for better OCR
        """
        try:
            # Import the necessary libraries
            from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageChops
            import numpy as np
            
            # Try to import OpenCV if available
            try:
                import cv2
                has_cv2 = True
            except ImportError:
                has_cv2 = False
                logger.warning("OpenCV (cv2) not available. Using PIL-only image processing.")
            
            # Convert to numpy array if needed
            if not isinstance(img, np.ndarray):
                img_np = np.array(img)
            else:
                img_np = img
                
            # Convert back to PIL image for processing
            img_pil = Image.fromarray(img_np)
            
            # 1. Even higher resolution scaling for better small text detection
            scale_factor = 2.0  # Increased from 1.5
            if img_pil.width < 3000 or img_pil.height < 3000:  # Increased threshold
                new_width = int(img_pil.width * scale_factor)
                new_height = int(img_pil.height * scale_factor)
                img_pil = img_pil.resize((new_width, new_height), Image.LANCZOS)
            
            # 2. Convert to grayscale if not already
            if img_pil.mode != 'L':
                img_pil = img_pil.convert('L')
            
            # 3. Apply multiple enhancement techniques
            
            # 3a. Sharpening for better edge definition
            enhancer = ImageEnhance.Sharpness(img_pil)
            img_pil = enhancer.enhance(2.5)  # Increased from 2.0
            
            # 3b. Contrast enhancement for better text/background separation
            enhancer = ImageEnhance.Contrast(img_pil)
            img_pil = enhancer.enhance(2.5)  # Increased from 2.0
            
            # 3c. Brightness adjustment if needed
            enhancer = ImageEnhance.Brightness(img_pil)
            img_pil = enhancer.enhance(1.1)  # Slight brightness increase
            
            # 3d. Apply more aggressive unsharp mask for edge detection
            img_pil = img_pil.filter(ImageFilter.UnsharpMask(radius=2.0, percent=200, threshold=2))                # 4. Advanced processing with OpenCV if available
            if has_cv2:
                # Convert to OpenCV format
                img_cv = np.array(img_pil)
                
                # 4a. Try using a bilateral filter to preserve edges while reducing noise
                img_cv = cv2.bilateralFilter(img_cv, 9, 75, 75)
                
                # 4b. Apply a gentle Gaussian blur to reduce noise while preserving edges
                img_cv = cv2.GaussianBlur(img_cv, (3, 3), 0)
                
                # 4c. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                img_cv_clahe = clahe.apply(img_cv)
                
                # 4d. Use a more conservative threshold approach
                # First, get global threshold with Otsu's method
                _, otsu_threshold = cv2.threshold(img_cv_clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # 4e. Then also apply adaptive thresholding
                adaptive_threshold = cv2.adaptiveThreshold(
                    img_cv_clahe, 
                    255, 
                    cv2.ADAPTIVE_THRESH_MEAN_C,  # Mean instead of Gaussian
                    cv2.THRESH_BINARY, 
                    11,  # Block size
                    2    # Constant subtracted from mean
                )
                
                # 4f. Combine the two approaches, but with a bias toward the otsu result
                img_cv_cleaned = cv2.bitwise_and(otsu_threshold, adaptive_threshold)
                
                # 4g. De-skew/rotate the image if text is slightly rotated
                try:
                    # Finding all text contours
                    contours, _ = cv2.findContours(255 - img_cv_cleaned, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                    
                    # Finding the orientation of text blocks
                    angles = []
                    for contour in contours:
                        if cv2.contourArea(contour) > 50:  # Filter small noise
                            rect = cv2.minAreaRect(contour)
                            angle = rect[2]
                            # Normalize the angle
                            if angle < -45:
                                angle += 90
                            angles.append(angle)
                    
                    # If we have angles, calculate the average skew
                    if angles:
                        avg_angle = sum(angles) / len(angles)
                        if abs(avg_angle) > 0.5:  # Only rotate if skew is significant
                            logger.info(f"Detected text skew of {avg_angle:.2f} degrees, correcting...")
                            
                            # Rotate the image to correct the skew
                            h, w = img_cv_cleaned.shape
                            center = (w//2, h//2)
                            M = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                            img_cv_cleaned = cv2.warpAffine(img_cv_cleaned, M, (w, h), flags=cv2.INTER_CUBIC, 
                                                           borderMode=cv2.BORDER_REPLICATE)
                except Exception as e:
                    logger.warning(f"De-skew operation failed: {e}")
                
                # Convert back to PIL
                img_pil = Image.fromarray(img_cv_cleaned)
            else:
                # If OpenCV is not available, use PIL's thresholding as a fallback
                # Use ImageOps to enhance contrast but be more conservative
                img_pil = ImageOps.autocontrast(img_pil, cutoff=0.2)
                img_pil = ImageOps.equalize(img_pil)
                
                # Don't apply aggressive thresholding which can destroy information
                enhancer = ImageEnhance.Contrast(img_pil)
                img_pil = enhancer.enhance(1.5)  # More mild contrast enhancement
            
            # Final pass with noise reduction filter
            img_pil = img_pil.filter(ImageFilter.MedianFilter(size=1))
            
            return img_pil
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}. Using original image.")
            return img
