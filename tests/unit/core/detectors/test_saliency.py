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


def test_saliency_detector_keeps_small_clear_subject_at_analysis_resolution():
    detector = SaliencyDetector()
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    image[55:80, 130:155] = 255

    saliency_map = detector.detect(image)

    assert any(
        125 <= box.x <= 135
        and 50 <= box.y <= 60
        and 20 <= box.width <= 35
        and 20 <= box.height <= 35
        for box in saliency_map.bounding_boxes
    )
    assert saliency_map.max_salient_score > 0.2
