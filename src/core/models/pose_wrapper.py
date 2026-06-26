import numpy as np
from typing import List
from ultralytics import YOLO

from ..entities import DetectedSubject, BoundingBox, Keypoint

class YoloPoseDetector:
    def __init__(self, model_size="n"):
        """
        Initialize the YOLOv11-pose model.
        """
        self.model = YOLO(f"yolo11{model_size}-pose.pt")
        
    def detect(self, image: np.ndarray) -> List[DetectedSubject]:
        """
        Run pose inference on the given BGR image.
        Returns a list of DetectedSubjects (specifically persons) with keypoints.
        """
        results = self.model(image, verbose=False)
        subjects = []
        
        if not results:
            return subjects
            
        result = results[0]
        boxes = result.boxes
        keypoints = result.keypoints
        
        if boxes is None or keypoints is None:
            return subjects
            
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0].cpu().numpy())
            cls_id = int(box.cls[0].cpu().numpy())
            class_name = self.model.names[cls_id]
            
            bbox = BoundingBox(
                x=float(x1),
                y=float(y1),
                width=float(x2 - x1),
                height=float(y2 - y1)
            )
            
            # Extract keypoints
            kpts_data = keypoints[i].data[0].cpu().numpy() # Shape should be (17, 3)
            subject_keypoints = []
            
            for kpt in kpts_data:
                kx, ky, kconf = kpt
                subject_keypoints.append(Keypoint(x=float(kx), y=float(ky), confidence=float(kconf)))
                
            subject = DetectedSubject(
                subject_id=f"pose_{class_name}_{i}",
                class_name=class_name,
                confidence=conf,
                bounding_box=bbox,
                keypoints=subject_keypoints,
                is_primary_subject=False
            )
            subjects.append(subject)
            
        return subjects
