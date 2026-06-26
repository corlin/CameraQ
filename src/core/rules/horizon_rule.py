import cv2
import numpy as np
from typing import Optional

from ..entities import Line, Point

def detect_horizon(image: np.ndarray) -> Optional[Line]:
    """
    Detect the most prominent roughly horizontal line in the image.
    Returns a Line entity or None if no such line is found.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Use probabilistic Hough transform
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=100, 
                            minLineLength=image.shape[1] * 0.3, maxLineGap=20)
    
    if lines is None:
        return None
        
    best_line = None
    max_len = 0
    
    for line in lines:
        x1, y1, x2, y2 = line[0]
        # Calculate angle
        angle = np.abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        
        # We look for lines that are close to horizontal (angle close to 0 or 180)
        if angle < 15 or angle > 165:
            length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if length > max_len:
                max_len = length
                best_line = Line(p1=Point(x=x1, y=y1), p2=Point(x=x2, y=y2))
                
    return best_line
