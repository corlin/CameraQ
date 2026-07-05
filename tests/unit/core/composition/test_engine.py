import numpy as np

from src.core.composition.engine import CompositionEngine
from src.core.entities import BoundingBox, CompositionMode, FusedSubject, SourceType
from tests.fixtures.composition.factory import line_image


def subject_at(x, y):
    return FusedSubject(
        subject_id="s",
        class_name="person",
        confidence=0.95,
        bounding_box=BoundingBox(x=x - 20, y=y - 30, width=40, height=60),
        is_primary_subject=True,
        source=SourceType.YOLO,
    )


def test_engine_returns_every_mode_once():
    result = CompositionEngine().analyze(line_image((0, 90)), [], None, timestamp=1.0)
    assert len(result.mode_results) == 15
    assert {item.mode for item in result.mode_results} == set(CompositionMode)


def test_engine_abstains_on_blank_frame():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    result = CompositionEngine().analyze(frame, [], None, timestamp=1.0)
    assert result.insufficient_evidence
    assert result.top_modes == []


def test_engine_allows_multilabel_top_three():
    frame = line_image((36,))
    result = CompositionEngine().analyze(frame, [subject_at(320 / 3, 240 / 3)], None, timestamp=1.0)
    assert CompositionMode.RULE_OF_THIRDS in result.top_modes
    assert CompositionMode.DIAGONAL in result.top_modes
    assert len(result.top_modes) <= 3
    for mode in result.top_modes:
        item = next(value for value in result.mode_results if value.mode is mode)
        assert item.evidence
