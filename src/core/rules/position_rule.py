from typing import List
from ..entities import DetectedSubject, Feedback, PriorityLevel, ActionType

def analyze_position(subjects: List[DetectedSubject], image_width: int, image_height: int) -> List[Feedback]:
    feedbacks = []
    primary = next((s for s in subjects if s.is_primary_subject), None)
    
    if not primary:
        return feedbacks
        
    # Calculate subject center
    cx = primary.bounding_box.x + primary.bounding_box.width / 2
    
    # Thirds
    left_third = image_width / 3
    right_third = image_width * 2 / 3
    center = image_width / 2
    
    dist_to_center = abs(cx - center)
    dist_to_left = abs(cx - left_third)
    dist_to_right = abs(cx - right_third)
    
    min_dist = min(dist_to_center, dist_to_left, dist_to_right)
    
    # Only suggest if it's off by more than 5% but less than 15%
    threshold = image_width * 0.05
    max_threshold = image_width * 0.15
    
    if threshold < min_dist < max_threshold:
        if min_dist == dist_to_center:
            action = ActionType.MOVE_RIGHT if cx < center else ActionType.MOVE_LEFT
            dir_str = "右" if cx < center else "左"
            feedbacks.append(Feedback(
                priority_level=PriorityLevel.OPTIMIZATION,
                action_type=action,
                message=f"主体偏离中心，建议将镜头稍微向{dir_str}移，实现居中构图。"
            ))
        elif min_dist == dist_to_left:
            action = ActionType.MOVE_RIGHT if cx < left_third else ActionType.MOVE_LEFT
            dir_str = "右" if cx < left_third else "左"
            feedbacks.append(Feedback(
                priority_level=PriorityLevel.STYLE,
                action_type=action,
                message=f"主体靠近左三分线，建议镜头向{dir_str}微调，贴合三分法则。"
            ))
        else:
            action = ActionType.MOVE_RIGHT if cx < right_third else ActionType.MOVE_LEFT
            dir_str = "右" if cx < right_third else "左"
            feedbacks.append(Feedback(
                priority_level=PriorityLevel.STYLE,
                action_type=action,
                message=f"主体靠近右三分线，建议镜头向{dir_str}微调，贴合三分法则。"
            ))

    return feedbacks
