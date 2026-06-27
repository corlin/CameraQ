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

        # Optimization: Downscale frame for aesthetics analysis to ensure <15ms execution
        h, w = frame.shape[:2]
        max_dim = 320
        scale = 1.0
        if max(h, w) > max_dim:
            scale = max_dim / float(max(h, w))
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

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
        
        # Histogram Clipping (US2)
        histogram_clipping = None
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        total_pixels = gray.shape[0] * gray.shape[1]
        if total_pixels > 0:
            shadow_ratio = hist[0][0] / total_pixels
            highlight_ratio = hist[255][0] / total_pixels
            if highlight_ratio > 0.05:
                histogram_clipping = "highlights"
            elif shadow_ratio > 0.05:
                histogram_clipping = "shadows"

        # Background Clutter Detection
        background_clutter_score = 0.0
        is_background_cluttered = False
        
        lighting_direction = None
        color_contrast_low = False
        vanishing_point_aligned = False
        
        if primary_box:
            # Create a mask for the background
            mask = np.ones(gray.shape, dtype=np.uint8) * 255
            bx = int(max(0, primary_box.x) * scale)
            by = int(max(0, primary_box.y) * scale)
            bw = int(min(w - max(0, primary_box.x), primary_box.width) * scale)
            bh = int(min(h - max(0, primary_box.y), primary_box.height) * scale)
            
            bx = max(0, bx)
            by = max(0, by)
            bw = min(gray.shape[1] - bx, bw)
            bh = min(gray.shape[0] - by, bh)
            cv2.rectangle(mask, (bx, by), (bx+bw, by+bh), 0, -1)
            
            if bw > 0 and bh > 0:
                # 1. Lighting Direction (US1)
                subject_gray = gray[by:by+bh, bx:bx+bw]
                half_w = bw // 2
                if half_w > 0:
                    left_half = subject_gray[:, :half_w]
                    right_half = subject_gray[:, half_w:]
                    left_mean = np.mean(left_half)
                    right_mean = np.mean(right_half)
                    
                    diff = left_mean - right_mean
                    if diff > 30:
                        lighting_direction = "left"
                    elif diff < -30:
                        lighting_direction = "right"
                    elif left_mean < 50 and right_mean < 50:
                        lighting_direction = "backlit"
                    elif left_mean > 150 and right_mean > 150:
                        lighting_direction = "flat"
                
                # 3. Color Contrast (US3)
                subject_hsv = hsv[by:by+bh, bx:bx+bw]
                bg_hsv = cv2.bitwise_and(hsv, hsv, mask=mask)
                
                s_mask = subject_hsv[:,:,1] > 30
                if np.any(s_mask):
                    sub_hue = np.mean(subject_hsv[:,:,0][s_mask])
                    bg_s_mask = (bg_hsv[:,:,1] > 30) & (mask > 0)
                    if np.any(bg_s_mask):
                        bg_hue = np.mean(bg_hsv[:,:,0][bg_s_mask])
                        hue_diff = min(abs(sub_hue - bg_hue), 180 - abs(sub_hue - bg_hue))
                        if hue_diff < 15:
                            color_contrast_low = True
            
            # Extract background using the mask
            bg_gray = cv2.bitwise_and(gray, gray, mask=mask)
            
            # Canny edge detection on background
            edges = cv2.Canny(bg_gray, 50, 150)
            
            # 4. Leading Lines & Geometry (US4)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
            if lines is not None:
                has_diagonal = False
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi)
                    if 20 < angle < 70 or 110 < angle < 160:
                        has_diagonal = True
                        break
                if has_diagonal:
                    # MVP heuristic: diagonal background lines that might not point to subject
                    vanishing_point_aligned = False
            
            # Calculate edge density (clutter score)
            bg_area = gray.shape[0] * gray.shape[1] - (bw * bh)
            if bg_area > 0:
                edge_pixels = cv2.countNonZero(edges)
                background_clutter_score = edge_pixels / float(bg_area)
                
                # Threshold for a "cluttered" background
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
            lighting_feedback=feedback,
            histogram_clipping=histogram_clipping,
            lighting_direction=lighting_direction,
            color_contrast_low=color_contrast_low,
            vanishing_point_aligned=vanishing_point_aligned
        )
