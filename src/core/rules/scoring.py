from typing import List
from ..entities import Feedback, PriorityLevel, CompositionScore

def calculate_composition_score(feedbacks: List[Feedback], horizon_angle: float) -> CompositionScore:
    """
    Calculate an overall composition score out of 100 using a 5-axis model.
    """
    # Initialize sub-scores to 100 (except Style which starts at 80 and can be improved)
    subject_score = 100
    structure_score = 100
    balance_score = 100
    interference_score = 100
    style_score = 80
    
    # Deduct for horizon tilt (Structure axis)
    tilt = min(horizon_angle, 180 - horizon_angle) if horizon_angle > 90 else horizon_angle
    if tilt > 2:
        structure_score -= int(tilt * 5)
        
    # Process feedbacks
    for fb in feedbacks:
        if fb.priority_level == PriorityLevel.HARD_ERROR:
            structure_score -= 20
        elif fb.priority_level == PriorityLevel.SUBJECT:
            subject_score -= 25
        elif fb.priority_level == PriorityLevel.INTERFERENCE:
            interference_score -= 15
        elif fb.priority_level == PriorityLevel.OPTIMIZATION:
            balance_score -= 15
        elif fb.priority_level == PriorityLevel.STYLE:
            style_score += 10
            
    # Clamp sub-scores between 0 and 100
    subject_score = max(0, min(100, subject_score))
    structure_score = max(0, min(100, structure_score))
    balance_score = max(0, min(100, balance_score))
    interference_score = max(0, min(100, interference_score))
    style_score = max(0, min(100, style_score))
    
    # Calculate total score with weights
    total = (
        subject_score * 0.30 +
        structure_score * 0.30 +
        balance_score * 0.20 +
        interference_score * 0.10 +
        style_score * 0.10
    )
    
    return CompositionScore(
        total_score=int(total),
        subject_score=subject_score,
        structure_score=structure_score,
        balance_score=balance_score,
        interference_score=interference_score,
        style_score=style_score
    )
