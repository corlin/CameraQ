import pytest
from src.core.rules.scene_rule import SceneContextRule
from src.core.rules.scene_rule import SceneContextRule
from src.core.entities import AnalysisResult, SceneContext, PriorityLevel, CompositionScore

def test_scene_rule_no_context():
    rule = SceneContextRule()
    mock_score = CompositionScore(
        total_score=80, subject_score=20, structure_score=20, 
        balance_score=20, interference_score=10, style_score=10
    )
    result = AnalysisResult(
        feedback_message="",
        score=mock_score,
        current_scene_context=None
    )
    feedbacks = rule.evaluate(result)
    assert len(feedbacks) == 0

def test_scene_rule_with_backlit():
    rule = SceneContextRule()
    mock_score = CompositionScore(
        total_score=80, subject_score=20, structure_score=20, 
        balance_score=20, interference_score=10, style_score=10
    )
    result = AnalysisResult(
        feedback_message="",
        score=mock_score,
        current_scene_context=SceneContext(
            scene_type="Portrait",
            lighting_condition="Backlit",
            recommended_iso=400,
            recommended_shutter="1/200",
            proactive_advice="Turn around",
            confidence=0.9
        )
    )
    feedbacks = rule.evaluate(result)
    assert len(feedbacks) == 2
    assert "backlit" in feedbacks[0].message.lower()
    assert feedbacks[1].message == "Turn around"
    assert feedbacks[1].priority_level == PriorityLevel.STYLE
