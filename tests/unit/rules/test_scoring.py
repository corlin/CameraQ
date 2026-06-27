import pytest
from src.core.entities import Feedback, PriorityLevel, ActionType, CompositionScore
from src.core.rules.scoring import calculate_composition_score

def test_perfect_score():
    score = calculate_composition_score([], 0.0)
    assert isinstance(score, CompositionScore)
    assert score.total_score == 98
    assert score.subject_score == 100
    assert score.structure_score == 100
    assert score.balance_score == 100
    assert score.interference_score == 100
    assert score.style_score == 80

def test_horizon_tilt_deduction():
    # 3 degrees tilt -> 3*5 = 15 points deducted -> 85 for structure
    # (100 * 0.3) + (85 * 0.3) + (100 * 0.2) + (100 * 0.1) + (80 * 0.1) = 30 + 25.5 + 20 + 10 + 8 = 93.5 -> 93
    score = calculate_composition_score([], 3.0)
    assert score.total_score == 93
    assert score.structure_score == 85

def test_feedback_deduction_critical():
    feedbacks = [Feedback(priority_level=PriorityLevel.HARD_ERROR, action_type=ActionType.MOVE_BACK, message="Error")]
    score = calculate_composition_score(feedbacks, 0.0)
    # HARD_ERROR -> structure_score -= 20 (80)
    # (100 * 0.3) + (80 * 0.3) + (100 * 0.2) + (100 * 0.1) + (80 * 0.1) = 30 + 24 + 20 + 10 + 8 = 92
    assert score.total_score == 92
    assert score.structure_score == 80

def test_feedback_deduction_medium():
    feedbacks = [Feedback(priority_level=PriorityLevel.INTERFERENCE, action_type=ActionType.MOVE_BACK, message="Bg")]
    score = calculate_composition_score(feedbacks, 0.0)
    # INTERFERENCE -> interference_score -= 15 (85)
    # (100 * 0.3) + (100 * 0.3) + (100 * 0.2) + (85 * 0.1) + (80 * 0.1) = 30 + 30 + 20 + 8.5 + 8 = 96.5 -> 96
    assert score.total_score == 96
    assert score.interference_score == 85

def test_combined_deduction_bounded():
    feedbacks = [Feedback(priority_level=PriorityLevel.HARD_ERROR, action_type=ActionType.MOVE_BACK, message="Error")] * 10
    score = calculate_composition_score(feedbacks, 90.0) # 90 degree tilt...
    assert score.total_score == 68 # Structure becomes 0. Total = 30 + 0 + 20 + 10 + 8 = 68
    assert score.structure_score == 0
