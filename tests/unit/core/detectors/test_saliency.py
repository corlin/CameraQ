import pytest
import numpy as np
from src.core.detectors.saliency_detector import SaliencyDetector

def test_saliency_detector():
    detector = SaliencyDetector()
    
    # Create a dummy image: black background, white square in the middle
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[50:150, 50:150] = 255  # bright square
    
    saliency_map = detector.detect(img)
    
    assert saliency_map is not None
    assert saliency_map.max_salient_score > 0
    assert len(saliency_map.bounding_boxes) > 0
    
    # Check if the bounding box roughly matches the bright square
    box = saliency_map.bounding_boxes[0]
    assert 40 <= box.x <= 60
    assert 40 <= box.y <= 60
    assert 90 <= box.width <= 110
    assert 90 <= box.height <= 110
