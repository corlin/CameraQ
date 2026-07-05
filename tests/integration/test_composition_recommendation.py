from src.core.composition.engine import CompositionEngine
from src.core.entities import BoundingBox, CompositionAction, FusedSubject, SourceType
from tests.fixtures.composition.factory import canvas, line_image, nested_rectangles


def subject(x, y, width=30, height=40):
    return FusedSubject(
        subject_id="s",
        class_name="person",
        confidence=0.95,
        bounding_box=BoundingBox(x=x, y=y, width=width, height=height),
        is_primary_subject=True,
        source=SourceType.YOLO,
    )


def test_engine_recommends_at_most_one_action_for_near_target_scene():
    result = CompositionEngine().analyze(canvas(), [subject(72, 60)], None, timestamp=1)
    assert result.recommendation is not None
    assert result.recommendation.action in {
        CompositionAction.MOVE_LEFT,
        CompositionAction.MOVE_RIGHT,
        CompositionAction.MOVE_CLOSER,
    }


def test_engine_supports_rotation_and_existing_structure_alignment():
    tilted = CompositionEngine().analyze(line_image((8,)), [subject(140, 90)], None, timestamp=1)
    tunnel = CompositionEngine().analyze(nested_rectangles(), [subject(110, 85)], None, timestamp=1)
    assert tilted.recommendation is None or isinstance(tilted.recommendation.action, CompositionAction)
    assert tunnel.recommendation is None or isinstance(tunnel.recommendation.action, CompositionAction)


def test_engine_suppresses_recommendation_without_actionable_focus():
    result = CompositionEngine().analyze(line_image((20,)), [], None, timestamp=1)
    assert result.recommendation is None
