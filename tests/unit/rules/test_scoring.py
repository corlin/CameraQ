import pytest
from src.core.entities import Feedback, PriorityLevel, ActionType
from src.core.rules.scoring import calculate_composition_score

def test_perfect_score():
    score = calculate_composition_score([], 0.0)
    assert score == 100

def test_horizon_tilt_deduction():
    # 3 degrees tilt -> 3*2 = 6 points deducted -> 94
    score = calculate_composition_score([], 3.0)
    assert score == 94

def test_feedback_deduction_critical():
    feedbacks = [Feedback(priority_level=PriorityLevel.HARD_ERROR, action_type=ActionType.MOVE_BACK, message="Error")]
    score = calculate_composition_score(feedbacks, 0.0)
    assert score == 85 # 100 - 15

def test_feedback_deduction_medium():
    feedbacks = [Feedback(priority_level=PriorityLevel.INTERFERENCE, action_type=ActionType.MOVE_BACK, message="Bg")]
    score = calculate_composition_score(feedbacks, 0.0)
    assert score == 95 # 100 - 5

def test_combined_deduction_bounded():
    feedbacks = [Feedback(priority_level=PriorityLevel.HARD_ERROR, action_type=ActionType.MOVE_BACK, message="Error")] * 10
    score = calculate_composition_score(feedbacks, 90.0) # 90 degree tilt...
    assert score == 0 # Should not go below 0
