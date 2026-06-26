import pytest
import numpy as np
from src.core.models.yolo_wrapper import YoloObjectDetector

def test_yolo_initialization():
    detector = YoloObjectDetector()
    assert detector.model is not None

def test_yolo_detect_mock_image():
    detector = YoloObjectDetector()
    # Create a dummy image (black square)
    dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
    
    subjects = detector.detect(dummy_img)
    # Depending on the mock/actual YOLO, a black square might have 0 detections
    assert isinstance(subjects, list)
