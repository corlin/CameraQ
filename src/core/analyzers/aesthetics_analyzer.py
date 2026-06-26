import cv2
import numpy as np
from src.core.entities import AestheticsMetrics

class AestheticsAnalyzer:
    def __init__(self, overexposed_threshold: float = 230.0, underexposed_threshold: float = 30.0):
        self.overexposed_threshold = overexposed_threshold
        self.underexposed_threshold = underexposed_threshold

    def analyze(self, frame: np.ndarray) -> AestheticsMetrics:
        """
        Analyze the given BGR frame for lighting and color metrics.
        """
        if frame is None or frame.size == 0:
            return AestheticsMetrics()

        # Convert to grayscale for brightness analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness_level = float(np.mean(gray))

        is_overexposed = brightness_level > self.overexposed_threshold
        is_underexposed = brightness_level < self.underexposed_threshold

        feedback = ""
        if is_overexposed:
            feedback = "过曝 (Overexposed)"
        elif is_underexposed:
            feedback = "欠曝 (Underexposed)"

        # Calculate a basic color harmony score based on HSV saturation/value variance (simplified MVP)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        s_std = np.std(hsv[:, :, 1])
        v_std = np.std(hsv[:, :, 2])
        # A simple heuristic: extremely low variance in both might mean plain/boring, 
        # but for now we just output 1.0 as a baseline MVP.
        color_harmony_score = 1.0 

        return AestheticsMetrics(
            brightness_level=brightness_level,
            is_overexposed=is_overexposed,
            is_underexposed=is_underexposed,
            color_harmony_score=color_harmony_score,
            lighting_feedback=feedback
        )
