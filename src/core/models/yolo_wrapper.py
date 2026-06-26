import numpy as np
from typing import List
from ultralytics import YOLO

from ..entities import DetectedSubject, BoundingBox

class YoloObjectDetector:
    def __init__(self, model_size="n"):
        """
        Initialize the YOLOv11 model.
        model_size can be 'n', 's', 'm', 'l', 'x' (nano is default for speed)
        """
        # Load YOLO11 model (will download automatically if not present)
        try:
            self.model = YOLO(f"yolo11{model_size}.pt")
        except Exception as e:
            # Handle missing file or permission issues gracefully
            raise RuntimeError(f"未能加载 YOLO 模型 'yolo11{model_size}.pt'，请检查网络或文件权限。错误信息: {e}")
        
    def detect(self, image: np.ndarray) -> List[DetectedSubject]:
        """
        Run inference on the given BGR image and return a list of DetectedSubjects.
        """
        results = self.model(image, verbose=False)
        subjects = []
        
        if not results:
            return subjects
            
        result = results[0]
        boxes = result.boxes
        
        for i, box in enumerate(boxes):
            # Extract coordinates (xyxy format)
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0].cpu().numpy())
            cls_id = int(box.cls[0].cpu().numpy())
            class_name = self.model.names[cls_id]
            
            # Convert to our BoundingBox format (x, y, width, height)
            bbox = BoundingBox(
                x=float(x1),
                y=float(y1),
                width=float(x2 - x1),
                height=float(y2 - y1)
            )
            
            subject = DetectedSubject(
                subject_id=f"{class_name}_{i}",
                class_name=class_name,
                confidence=conf,
                bounding_box=bbox,
                is_primary_subject=False  # To be determined by analyzer logic
            )
            subjects.append(subject)
            
        return subjects
