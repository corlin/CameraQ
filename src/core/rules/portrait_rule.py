from typing import List, Optional
import numpy as np
from ..entities import DetectedSubject, Feedback, PriorityLevel, ActionType, Point

def analyze_portrait(subject: DetectedSubject, image_height: int, image_width: int) -> List[Feedback]:
    feedbacks = []
    
    if not subject.keypoints:
        return feedbacks
        
    bbox = subject.bounding_box
    
    # 1. Headroom analysis
    # Headroom is the space between the top of the image and the top of the subject
    headroom_ratio = bbox.y / image_height
    
    # Thresholds are approximate
    if headroom_ratio < 0.05:
        feedbacks.append(Feedback(
            priority_level=PriorityLevel.SUBJECT,
            action_type=ActionType.TILT_UP,
            message="头顶空间过小，请将镜头稍微上抬或后退。"
        ))
    elif headroom_ratio > 0.35:
        feedbacks.append(Feedback(
            priority_level=PriorityLevel.SUBJECT,
            action_type=ActionType.TILT_DOWN,
            message="头顶留白过多，请将镜头稍微下压或靠近。"
        ))
        
    # 2. Awkward crop detection
    # COCO keypoints: 9: L_Wrist, 10: R_Wrist, 15: L_Ankle, 16: R_Ankle
    kpts = subject.keypoints
    
    # Check if wrists are near the edge
    for wrist_idx in [9, 10]:
        if wrist_idx < len(kpts):
            wrist = kpts[wrist_idx]
            if wrist.confidence > 0.5:
                # If wrist is very close to image edge
                if wrist.x < image_width * 0.05 or wrist.x > image_width * 0.95 or wrist.y > image_height * 0.95:
                    feedbacks.append(Feedback(
                        priority_level=PriorityLevel.SUBJECT,
                        action_type=ActionType.MOVE_BACK,
                        message="手部边缘被裁切，请稍微后退将手完整纳入画面。"
                    ))
                    break # One warning is enough
                    
    # Check if ankles are near the edge
    for ankle_idx in [15, 16]:
        if ankle_idx < len(kpts):
            ankle = kpts[ankle_idx]
            if ankle.confidence > 0.5:
                # If ankle is very close to bottom edge
                if ankle.y > image_height * 0.95:
                    feedbacks.append(Feedback(
                        priority_level=PriorityLevel.SUBJECT,
                        action_type=ActionType.MOVE_BACK,
                        message="脚部边缘被裁切，请稍微后退将全身完整纳入画面。"
                    ))
                    break

    return feedbacks
