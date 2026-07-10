from src.core.composition.temporal import CompositionTemporalFilter
from src.core.entities import CompositionConfidence, CompositionMode, CompositionModeResult


def results(score: float, mode=CompositionMode.HORIZONTAL, confidence=CompositionConfidence.HIGH):
    return [
        CompositionModeResult(
            mode=item,
            match_score=score if item is mode else 0,
            confidence=confidence if item is mode else CompositionConfidence.LOW,
            evidence=[],
        )
        for item in CompositionMode
    ]


def visible(output, mode=CompositionMode.HORIZONTAL):
    return next(item for item in output if item.mode is mode).is_visible


def test_first_high_confidence_frame_can_be_visible_immediately():
    temporal = CompositionTemporalFilter()
    assert visible(temporal.update(results(90), timestamp=0.0))


def test_medium_confidence_display_candidate_can_be_visible():
    temporal = CompositionTemporalFilter()
    output = temporal.update(
        results(50, confidence=CompositionConfidence.MEDIUM), timestamp=0.0
    )
    assert visible(output)


def test_medium_display_candidate_uses_display_exit_hysteresis():
    temporal = CompositionTemporalFilter()
    temporal.update(results(50, confidence=CompositionConfidence.MEDIUM), timestamp=0.0)
    for timestamp in (0.1, 0.2):
        assert visible(
            temporal.update(
                results(30, confidence=CompositionConfidence.MEDIUM),
                timestamp=timestamp,
            )
        )
    assert not visible(
        temporal.update(
            results(30, confidence=CompositionConfidence.MEDIUM), timestamp=0.3
        )
    )


def test_candidate_requires_three_entries_after_reset():
    temporal = CompositionTemporalFilter()
    temporal.update(results(10), timestamp=0.0, scene_changed=True)
    assert not visible(temporal.update(results(70), timestamp=0.1))
    assert not visible(temporal.update(results(70), timestamp=0.2))
    assert visible(temporal.update(results(70), timestamp=0.3))


def test_active_mode_survives_hysteresis_and_three_exit_samples():
    temporal = CompositionTemporalFilter()
    temporal.update(results(90), timestamp=0.0)
    assert visible(temporal.update(results(60), timestamp=0.1))
    assert visible(temporal.update(results(50), timestamp=0.2))
    assert visible(temporal.update(results(50), timestamp=0.3))
    assert not visible(temporal.update(results(50), timestamp=0.4))


def test_scene_change_clears_old_mode_and_allows_new_first_frame():
    temporal = CompositionTemporalFilter()
    temporal.update(results(90, CompositionMode.HORIZONTAL), timestamp=0.0)
    changed = temporal.update(
        results(92, CompositionMode.VERTICAL), timestamp=0.2, scene_changed=True
    )
    assert not visible(changed, CompositionMode.HORIZONTAL)
    assert visible(changed, CompositionMode.VERTICAL)
