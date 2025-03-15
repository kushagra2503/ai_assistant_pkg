"""
Desktop screenshot utility for the AI Assistant.
"""

import time
import logging
import cv2
import numpy as np
from PIL import ImageGrab
import base64
from cv2 import imencode

logger = logging.getLogger("ai_assistant")

def encode_image(image):
    """
    Encode an image to base64 for use with AI models.
    
    Args:
        image (numpy.ndarray): Image as a numpy array
        
    Returns:
        str: Base64-encoded image
    """
    _, buffer = imencode(".jpeg", image)
    return base64.b64encode(buffer).decode()

class DesktopScreenshot:
    """
    Utility for capturing and managing desktop screenshots.
    
    Attributes:
        screenshot (numpy.ndarray): The captured screenshot
        cached_image (str): Base64-encoded cached screenshot
        last_capture_time (float): Timestamp of the last capture
    """
    
    def __init__(self):
        """Initialize the desktop screenshot utility."""
        self.screenshot = None
        self.cached_image = None
        self.last_capture_time = 0
        
    def capture(self, force_new=False):
        """
        Capture a screenshot of the desktop.
        
        Args:
            force_new (bool): Force a new capture even if a recent one exists
            
        Returns:
            str: Base64-encoded screenshot
        """
        current_time = time.time()
        # Use cached screenshot if it's less than 2 seconds old
        if not force_new and self.cached_image and current_time - self.last_capture_time < 2:
            return self.cached_image
            
        try:
            # Capture the screenshot
            pil_screenshot = ImageGrab.grab()
            
            # Convert to numpy array and store the raw screenshot
            self.screenshot = np.array(pil_screenshot)
            
            # Convert to BGR for OpenCV operations
            screenshot_bgr = cv2.cvtColor(self.screenshot, cv2.COLOR_RGB2BGR)
            
            # Encode for API usage
            self.cached_image = encode_image(screenshot_bgr)
            self.last_capture_time = current_time
            return self.cached_image
        except Exception as e:
            logger.error(f"Screenshot capture error: {e}")
            return None
