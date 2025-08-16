import cv2
import numpy as np
import pytesseract
from typing import List, Tuple
import logging

class AdvancedOCR:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR results
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(enhanced)
            
            # Sharpen
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel)
            
            # Apply thresholding
            _, thresholded = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return thresholded
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            return None
    
    def extract_text_with_multiple_configs(self, image: np.ndarray) -> str:
        """
        Try multiple Tesseract configurations for better text extraction
        """
        configs = [
            '--oem 3 --psm 6',  # Assume uniform block of text
            '--oem 3 --psm 8',  # Single word
            '--oem 3 --psm 11', # Sparse text with OSD
            '--oem 3 --psm 12', # Sparse text with uniform orientation
        ]
        
        best_text = ""
        best_confidence = 0
        
        for config in configs:
            try:
                text = pytesseract.image_to_string(image, config=config)
                # Simple confidence check - longer text with more alphanumeric chars
                confidence = len([c for c in text if c.isalnum()])
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_text = text
            except Exception as e:
                self.logger.warning(f"OCR config {config} failed: {e}")
                continue
        
        return best_text
    
    def extract_text_regions(self, image: np.ndarray, num_regions: int = 4) -> List[str]:
        """
        Extract text from different regions of the image
        """
        height, width = image.shape
        region_height = height // num_regions
        
        texts = []
        for i in range(num_regions):
            y_start = i * region_height
            y_end = (i + 1) * region_height if i < num_regions - 1 else height
            
            region = image[y_start:y_end, :]
            text = pytesseract.image_to_string(region, config='--oem 3 --psm 6')
            texts.append(text.strip())
        
        return texts
    
    def extract_text(self, image_path: str) -> str:
        """
        Main method to extract text from image with advanced preprocessing
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                return ""
            
            # Try multiple extraction methods
            text = self.extract_text_with_multiple_configs(processed_image)
            
            # If main extraction fails, try region-based extraction
            if not text.strip():
                regions = self.extract_text_regions(processed_image)
                text = " ".join(regions)
            
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error extracting text: {e}")
            return ""
