from src.core.composition.engine import CompositionEngine
from src.core.composition.temporal import CompositionTemporalFilter
from src.core.entities import CompositionConfidence, CompositionMode, CompositionModeResult
from tests.fixtures.composition.factory import line_image
import numpy as np


def score_set(score):
    return [
        CompositionModeResult(
            mode=mode,
            match_score=score if mode is CompositionMode.HORIZONTAL else 0,
            confidence=CompositionConfidence.HIGH if mode is CompositionMode.HORIZONTAL else CompositionConfidence.LOW,
            evidence=[],
        )
        for mode in CompositionMode
    ]


def test_threshold_jitter_does_not_toggle_visible_mode_over_thirty_seconds():
    temporal = CompositionTemporalFilter()
    previous = False
    transitions = 0
    for index in range(201):
        score = 90 if index == 0 else (64 if index % 2 else 66)
        output = temporal.update(score_set(score), timestamp=index * 0.15)
        current = next(item.is_visible for item in output if item.mode is CompositionMode.HORIZONTAL)
        transitions += current != previous
        previous = current
    assert transitions <= 1


def test_engine_replaces_horizontal_with_vertical_after_material_scene_change():
    engine = CompositionEngine()
    first = engine.analyze(line_image((0,)), [], None, timestamp=0.0)
    changed = engine.analyze(line_image((90,)), [], None, timestamp=0.2)
    assert CompositionMode.HORIZONTAL in first.top_modes
    assert CompositionMode.VERTICAL in changed.top_modes
    assert CompositionMode.HORIZONTAL not in changed.top_modes


def test_engine_reinterprets_lines_in_display_coordinates_after_ninety_degree_rotation():
    engine = CompositionEngine()
    horizontal = line_image((0,))
    vertical_display_frame = np.ascontiguousarray(np.rot90(horizontal))

    first = engine.analyze(horizontal, [], None, timestamp=0.0)
    engine.analyze(vertical_display_frame, [], None, timestamp=0.2)
    engine.analyze(vertical_display_frame, [], None, timestamp=0.35)
    rotated = engine.analyze(vertical_display_frame, [], None, timestamp=0.5)

    assert CompositionMode.HORIZONTAL in first.top_modes
    assert CompositionMode.VERTICAL in rotated.top_modes
    assert CompositionMode.HORIZONTAL not in rotated.top_modes
