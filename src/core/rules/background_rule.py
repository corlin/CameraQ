from typing import List
from ..entities import DetectedSubject, Feedback, PriorityLevel, ActionType

def analyze_background_interference(subjects: List[DetectedSubject]) -> List[Feedback]:
    feedbacks = []
    primary = next((s for s in subjects if s.is_primary_subject), None)
    
    if not primary:
        return feedbacks
        
    p_box = primary.bounding_box
    # Define a "head area" (top 20% of the primary subject's bounding box and slightly above)
    head_x1 = p_box.x
    head_y1 = p_box.y - p_box.height * 0.2 
    head_x2 = p_box.x + p_box.width
    head_y2 = p_box.y + p_box.height * 0.2
    
    for sub in subjects:
        if sub.is_primary_subject:
            continue
            
        s_box = sub.bounding_box
        s_x1 = s_box.x
        s_y1 = s_box.y
        s_x2 = s_box.x + s_box.width
        s_y2 = s_box.y + s_box.height
        
        # Check intersection with head area
        intersect_x = max(0, min(head_x2, s_x2) - max(head_x1, s_x1))
        intersect_y = max(0, min(head_y2, s_y2) - max(head_y1, s_y1))
        
        if intersect_x > 0 and intersect_y > 0:
            feedbacks.append(Feedback(
                priority_level=PriorityLevel.INTERFERENCE,
                action_type=ActionType.MOVE_LEFT, # Suggesting angle change
                message=f"背景中有【{sub.class_name}】干扰主体头部，建议换个角度或移动机位。"
            ))
            break # One warning is enough
            
    return feedbacks
