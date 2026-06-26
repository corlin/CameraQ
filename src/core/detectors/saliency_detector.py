import cv2
import numpy as np
from typing import List
from src.core.entities import SaliencyMap, BoundingBox

class SaliencyDetector:
    def __init__(self):
        # We could use cv2.saliency.StaticSaliencySpectralResidual_create()
        # but to avoid opencv-contrib-python dependency issues for the MVP,
        # we implement a lightweight pseudo-saliency using Lab color space and contrast.
        pass

    def detect(self, image: np.ndarray) -> SaliencyMap:
        if image is None or image.size == 0:
            return SaliencyMap(heatmap=np.zeros((1, 1)), bounding_boxes=[], max_salient_score=0.0)

        # Convert to Lab to separate lightness from color
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # Calculate global mean of channels
        l_mean = np.mean(l_channel)
        a_mean = np.mean(a_channel)
        b_mean = np.mean(b_channel)
        
        # Compute "saliency" as distance from the mean
        # Objects that stand out in color or brightness will have higher values
        saliency = (np.square(l_channel - l_mean) + 
                    np.square(a_channel - a_mean) + 
                    np.square(b_channel - b_mean))
        
        # Normalize to 0-255
        cv2.normalize(saliency, saliency, 0, 255, cv2.NORM_MINMAX)
        saliency = saliency.astype(np.uint8)
        
        # Smooth the heatmap
        saliency = cv2.GaussianBlur(saliency, (9, 9), 0)
        
        # Threshold to find salient blobs
        _, thresh = cv2.threshold(saliency, 150, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        boxes = []
        max_score = 0.0
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1000: # Filter out noise
                x, y, w, h = cv2.boundingRect(cnt)
                boxes.append(BoundingBox(x=x, y=y, width=w, height=h))
                
                # Simple score based on area and brightness
                mask = np.zeros_like(saliency)
                cv2.drawContours(mask, [cnt], -1, 255, -1)
                mean_val = cv2.mean(saliency, mask=mask)[0]
                score = (area / (image.shape[0] * image.shape[1])) * (mean_val / 255.0)
                if score > max_score:
                    max_score = score
                    
        # Sort boxes by size (largest first)
        boxes.sort(key=lambda b: b.width * b.height, reverse=True)
        
        return SaliencyMap(
            heatmap=saliency,
            bounding_boxes=boxes,
            max_salient_score=max_score
        )
