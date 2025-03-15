"""
OCR (Optical Character Recognition) utility for the AI Assistant.
"""

import os
import logging
import pytesseract
from PIL import Image
import numpy as np
import cv2

logger = logging.getLogger("ai_assistant")

class OCRProcessor:
    """
    Utility for extracting text from images using OCR.
    
    Attributes:
        tesseract_path (str): Path to Tesseract executable (Windows only)
    """
    
    def __init__(self):
        """Initialize the OCR processor."""
        # Set up Tesseract path for Windows
        if os.name == 'nt':  # Windows
            default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path
            else:
                logger.warning("Tesseract OCR not found at default location. OCR may not work.")
                print("\n⚠️ Tesseract OCR not found. Please install it for text extraction:")
                print("Download from: https://github.com/UB-Mannheim/tesseract/wiki")
    
    def extract_text_from_file(self, image_path):
        """
        Extract text from an image file.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: Extracted text
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return f"Error: Image file not found: {image_path}"
                
            # Load the image
            image = Image.open(image_path)
            
            # Extract text using pytesseract
            text = pytesseract.image_to_string(image)
            
            if not text.strip():
                logger.info(f"No text detected in image: {image_path}")
                return "No text detected in image."
                
            logger.info(f"Extracted {len(text)} characters of text from image: {image_path}")
            return text
            
        except Exception as e:
            logger.error(f"OCR error with file {image_path}: {e}")
            return f"Error extracting text: {str(e)}"
    
    def extract_text(self, image):
        """
        Extract text from an image.
        
        Args:
            image (numpy.ndarray or PIL.Image): Image to process
            
        Returns:
            str: Extracted text
        """
        try:
            # Convert numpy array to PIL Image if needed
            if isinstance(image, np.ndarray):
                # Convert BGR to RGB if it's a CV2 image
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                image = Image.fromarray(image)
            
            # Make sure we have a valid PIL Image
            if not isinstance(image, Image.Image):
                logger.error(f"Unsupported image type: {type(image)}")
                return f"Error: Unsupported image type: {type(image)}"
            
            # Extract text using pytesseract
            text = pytesseract.image_to_string(image)
            
            if not text.strip():
                logger.info("No text detected in image")
                return "No text detected in image."
                
            logger.info(f"Extracted {len(text)} characters of text from image")
            return text
            
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return f"Error extracting text: {str(e)}"