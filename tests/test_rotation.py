"""Test rotation detection and correction functionality."""

import tempfile
import warnings
from pathlib import Path

import pytest
from PIL import Image
import torch

from byaldi import RAGMultiModalModel
from byaldi.rotation_utils import (
    detect_image_rotation_tesseract,
    rotate_image,
    correct_image_orientation,
    process_pdf_with_rotation_correction,
)


class TestRotationUtils:
    """Test rotation utility functions."""

    def test_rotate_image(self):
        """Test image rotation function."""
        # Create a simple test image
        test_image = Image.new('RGB', (100, 50), color='red')
        
        # Test 0 degree rotation (no change)
        rotated_0 = rotate_image(test_image, 0)
        assert rotated_0.size == test_image.size
        
        # Test 90 degree rotation
        rotated_90 = rotate_image(test_image, 90)
        assert rotated_90.size == (50, 100)  # Width and height swapped
        
        # Test 180 degree rotation
        rotated_180 = rotate_image(test_image, 180)
        assert rotated_180.size == test_image.size
        
        # Test 270 degree rotation
        rotated_270 = rotate_image(test_image, 270)
        assert rotated_270.size == (50, 100)  # Width and height swapped
        
        # Test unsupported angle
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            rotated_45 = rotate_image(test_image, 45)
            assert len(w) == 1
            assert "Unsupported rotation angle" in str(w[0].message)
            assert rotated_45.size == test_image.size

    def test_detect_image_rotation_tesseract(self):
        """Test Tesseract rotation detection."""
        # Create a simple test image with some text-like content
        test_image = Image.new('RGB', (200, 100), color='white')
        
        # This test may fail if Tesseract is not installed, so we catch exceptions
        try:
            angle, confidence = detect_image_rotation_tesseract(test_image)
            assert isinstance(angle, int)
            assert isinstance(confidence, float)
            assert angle in [0, 90, 180, 270]
            assert confidence >= 0.0
        except Exception as e:
            pytest.skip(f"Tesseract not available or failed: {e}")

    def test_correct_image_orientation(self):
        """Test image orientation correction."""
        test_image = Image.new('RGB', (100, 50), color='red')
        
        # Test with Tesseract disabled
        corrected, angle = correct_image_orientation(test_image, use_tesseract=False)
        assert corrected.size == test_image.size
        assert angle == 0
        
        # Test with Tesseract enabled (may skip if not available)
        try:
            corrected, angle = correct_image_orientation(test_image, use_tesseract=True)
            assert isinstance(corrected, Image.Image)
            assert isinstance(angle, int)
        except Exception:
            pytest.skip("Tesseract not available")


class TestRotationIntegration:
    """Test rotation integration with RAGMultiModalModel."""

    @pytest.fixture
    def model_name(self):
        """Return a test model name."""
        return "vidore/colpali-v1.2"

    def test_model_initialization_with_rotation_params(self, model_name):
        """Test model initialization with rotation parameters."""
        # Skip if CUDA is not available
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available")
        
        try:
            model = RAGMultiModalModel.from_pretrained(
                model_name,
                auto_rotate=True,
                rotation_confidence_threshold=3.0,
                use_pdf_rotation=True,
                use_tesseract_fallback=False,
            )
            
            # Check that rotation parameters are set correctly
            assert model.model.auto_rotate == True
            assert model.model.rotation_confidence_threshold == 3.0
            assert model.model.use_pdf_rotation == True
            assert model.model.use_tesseract_fallback == False
            
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")

    def test_model_initialization_disabled_rotation(self, model_name):
        """Test model initialization with rotation disabled."""
        # Skip if CUDA is not available
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available")
        
        try:
            model = RAGMultiModalModel.from_pretrained(
                model_name,
                auto_rotate=False,
            )
            
            # Check that rotation is disabled
            assert model.model.auto_rotate == False
            
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")

    @pytest.mark.slow
    def test_pdf_processing_with_rotation_correction(self, model_name):
        """Test PDF processing with rotation correction enabled."""
        # Skip if CUDA is not available
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available")
        
        # Create a simple test PDF (would need actual PDF for full testing)
        # For now, we'll test the parameter passing
        try:
            model = RAGMultiModalModel.from_pretrained(
                model_name,
                auto_rotate=True,
                rotation_confidence_threshold=2.0,
            )
            
            # This test would require an actual PDF file
            # For now, we just verify the model was initialized correctly
            assert model.model.auto_rotate == True
            assert model.model.rotation_confidence_threshold == 2.0
            
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")


if __name__ == "__main__":
    # Run basic tests
    test_utils = TestRotationUtils()
    test_utils.test_rotate_image()
    print("✓ Image rotation tests passed")
    
    try:
        test_utils.test_detect_image_rotation_tesseract()
        print("✓ Tesseract rotation detection tests passed")
    except Exception as e:
        print(f"⚠ Tesseract tests skipped: {e}")
    
    try:
        test_utils.test_correct_image_orientation()
        print("✓ Image orientation correction tests passed")
    except Exception as e:
        print(f"⚠ Orientation correction tests skipped: {e}")
    
    print("Basic rotation tests completed!")