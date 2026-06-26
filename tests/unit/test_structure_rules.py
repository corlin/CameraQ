import pytest
import numpy as np
import cv2
from src.core.rules.horizon_rule import detect_horizon

def test_horizon_detection_horizontal_line():
    # Create a blank image
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    # Draw a distinct white horizontal line
    cv2.line(img, (50, 200), (350, 200), (255, 255, 255), 3)
    
    line = detect_horizon(img)
    assert line is not None
    # Angle should be near 0
    angle = np.abs(np.degrees(np.arctan2(line.p2.y - line.p1.y, line.p2.x - line.p1.x)))
    # arctan2 can return ~0 or ~180 depending on p1/p2 order
    assert angle < 10 or angle > 170

def test_horizon_detection_no_line():
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    # Blank image should have no horizon
    line = detect_horizon(img)
    assert line is None
