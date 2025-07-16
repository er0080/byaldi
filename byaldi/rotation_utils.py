"""Utilities for detecting and correcting PDF page rotation."""

import tempfile
import warnings
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np


def detect_pdf_page_rotation(pdf_path: str) -> List[int]:
    """
    Detect rotation for each page in a PDF using PyMuPDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of rotation angles (0, 90, 180, 270) for each page
    """
    try:
        doc = fitz.open(pdf_path)
        rotations = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            rotation = page.rotation
            rotations.append(rotation)
            
        doc.close()
        return rotations
    except Exception as e:
        warnings.warn(f"Failed to detect PDF rotation using PyMuPDF: {e}")
        return []


def detect_image_rotation_tesseract(image: Image.Image) -> Tuple[int, float]:
    """
    Detect image rotation using Tesseract OSD (Orientation and Script Detection).
    
    Args:
        image: PIL Image object
        
    Returns:
        Tuple of (rotation_angle, confidence_score)
        rotation_angle: 0, 90, 180, or 270 degrees
        confidence_score: Tesseract confidence in the detection
    """
    try:
        # Convert PIL image to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Use Tesseract OSD to detect orientation
        osd_data = pytesseract.image_to_osd(
            image, 
            config='--psm 0 -c min_characters_to_try=5',
            output_type=pytesseract.Output.DICT
        )
        
        rotation_angle = int(osd_data.get('rotate', 0))
        confidence = float(osd_data.get('orientation_conf', 0))
        
        return rotation_angle, confidence
        
    except Exception as e:
        warnings.warn(f"Failed to detect image rotation using Tesseract: {e}")
        return 0, 0.0


def rotate_image(image: Image.Image, angle: int) -> Image.Image:
    """
    Rotate an image by the specified angle.
    
    Args:
        image: PIL Image object
        angle: Rotation angle in degrees (0, 90, 180, 270)
        
    Returns:
        Rotated PIL Image object
    """
    if angle == 0:
        return image
    elif angle == 90:
        return image.rotate(-90, expand=True)
    elif angle == 180:
        return image.rotate(180, expand=True)
    elif angle == 270:
        return image.rotate(90, expand=True)
    else:
        warnings.warn(f"Unsupported rotation angle: {angle}. Using 0 degrees.")
        return image


def correct_image_orientation(
    image: Image.Image, 
    confidence_threshold: float = 2.0,
    use_tesseract: bool = True
) -> Tuple[Image.Image, int]:
    """
    Automatically correct image orientation using Tesseract OSD.
    
    Args:
        image: PIL Image object
        confidence_threshold: Minimum confidence score to apply correction
        use_tesseract: Whether to use Tesseract for rotation detection
        
    Returns:
        Tuple of (corrected_image, applied_rotation_angle)
    """
    if not use_tesseract:
        return image, 0
    
    try:
        rotation_angle, confidence = detect_image_rotation_tesseract(image)
        
        # Only apply rotation if confidence is above threshold
        if confidence >= confidence_threshold and rotation_angle != 0:
            corrected_image = rotate_image(image, rotation_angle)
            return corrected_image, rotation_angle
        else:
            return image, 0
            
    except Exception as e:
        warnings.warn(f"Failed to correct image orientation: {e}")
        return image, 0


def process_pdf_with_rotation_correction(
    pdf_path: str,
    auto_rotate: bool = True,
    confidence_threshold: float = 2.0,
    use_pdf_rotation: bool = True,
    use_tesseract_fallback: bool = True
) -> List[Image.Image]:
    """
    Process a PDF file with automatic rotation correction.
    
    Args:
        pdf_path: Path to the PDF file
        auto_rotate: Whether to enable automatic rotation correction
        confidence_threshold: Minimum confidence for Tesseract rotation
        use_pdf_rotation: Whether to use PDF-level rotation detection
        use_tesseract_fallback: Whether to use Tesseract as fallback for rotation detection
        
    Returns:
        List of PIL Image objects with corrected orientation
    """
    from pdf2image import convert_from_path
    import os
    
    # Convert PDF to images first
    with tempfile.TemporaryDirectory() as temp_dir:
        images = convert_from_path(
            pdf_path,
            thread_count=os.cpu_count() - 1,
            output_folder=temp_dir
        )
    
    if not auto_rotate:
        return images
    
    # Detect PDF-level rotation if enabled
    pdf_rotations = []
    if use_pdf_rotation:
        pdf_rotations = detect_pdf_page_rotation(pdf_path)
    
    corrected_images = []
    
    for i, image in enumerate(images):
        corrected_image = image
        applied_rotation = 0
        
        # Apply PDF-level rotation first if available
        if pdf_rotations and i < len(pdf_rotations):
            pdf_rotation = pdf_rotations[i]
            if pdf_rotation != 0:
                corrected_image = rotate_image(corrected_image, pdf_rotation)
                applied_rotation = pdf_rotation
        
        # Apply Tesseract-based rotation correction as fallback
        if use_tesseract_fallback and applied_rotation == 0:
            corrected_image, tesseract_rotation = correct_image_orientation(
                corrected_image, 
                confidence_threshold=confidence_threshold,
                use_tesseract=True
            )
            applied_rotation = tesseract_rotation
            
        corrected_images.append(corrected_image)
    
    return corrected_images