from typing import List, Optional
from ..entities import Feedback, PriorityLevel

def select_primary_feedback(feedbacks: List[Feedback]) -> Optional[Feedback]:
    """
    Selects the single most important piece of feedback to show the user.
    Lower priority_level values mean higher urgency (e.g. 1 is highest priority).
    """
    if not feedbacks:
        return None
        
    # Sort by priority level (ascending)
    sorted_feedbacks = sorted(feedbacks, key=lambda f: f.priority_level.value)
    
    return sorted_feedbacks[0]
