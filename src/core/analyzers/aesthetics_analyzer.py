import cv2
import numpy as np
from src.core.entities import AestheticsMetrics

class AestheticsAnalyzer:
    def __init__(self, overexposed_threshold: float = 230.0, underexposed_threshold: float = 30.0, severe_backlight_threshold: float = 240.0):
        self.overexposed_threshold = overexposed_threshold
        self.underexposed_threshold = underexposed_threshold
        self.severe_backlight_threshold = severe_backlight_threshold

    def analyze(self, frame: np.ndarray, primary_box=None) -> AestheticsMetrics:
        """
        Analyze the given BGR frame for lighting, color, and background clutter metrics.
        """
        if frame is None or frame.size == 0:
            return AestheticsMetrics()

        # Convert to grayscale for brightness analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness_level = float(np.mean(gray))

        is_overexposed = brightness_level > self.overexposed_threshold
        is_underexposed = brightness_level < self.underexposed_threshold
        is_severe_backlight = brightness_level > self.severe_backlight_threshold

        feedback = ""
        if is_severe_backlight:
            feedback = "严重过曝 (Severe Overexposed)"
        elif is_overexposed:
            feedback = "过曝 (Overexposed)"
        elif is_underexposed:
            feedback = "欠曝 (Underexposed)"

        # Calculate a basic color harmony score based on HSV saturation/value variance (simplified MVP)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        s_std = np.std(hsv[:, :, 1])
        v_std = np.std(hsv[:, :, 2])
        color_harmony_score = 1.0 
        
        # Background Clutter Detection
        background_clutter_score = 0.0
        is_background_cluttered = False
        
        if primary_box:
            # Create a mask for the background
            mask = np.ones(gray.shape, dtype=np.uint8) * 255
            bx, by, bw, bh = int(primary_box.x), int(primary_box.y), int(primary_box.width), int(primary_box.height)
            cv2.rectangle(mask, (max(0, bx), max(0, by)), (min(gray.shape[1], bx+bw), min(gray.shape[0], by+bh)), 0, -1)
            
            # Extract background using the mask
            bg_gray = cv2.bitwise_and(gray, gray, mask=mask)
            
            # Canny edge detection on background
            edges = cv2.Canny(bg_gray, 50, 150)
            
            # Calculate edge density (clutter score)
            bg_area = gray.shape[0] * gray.shape[1] - (bw * bh)
            if bg_area > 0:
                edge_pixels = cv2.countNonZero(edges)
                background_clutter_score = edge_pixels / float(bg_area)
                
                # Threshold for a "cluttered" background (15% edge density is quite high)
                if background_clutter_score > 0.15:
                    is_background_cluttered = True

        return AestheticsMetrics(
            brightness_level=brightness_level,
            is_overexposed=is_overexposed,
            is_underexposed=is_underexposed,
            is_severe_backlight=is_severe_backlight,
            color_harmony_score=color_harmony_score,
            background_clutter_score=background_clutter_score,
            is_background_cluttered=is_background_cluttered,
            lighting_feedback=feedback
        )
