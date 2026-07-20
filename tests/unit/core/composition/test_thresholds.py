from types import SimpleNamespace

from src.core.composition.scorers.common import confidence_for
from src.core.composition.thresholds import (
    MODE_EVIDENCE_WEIGHTS,
    MODE_DISPLAY_ENTER_SCORES,
    MODE_DISPLAY_EXIT_SCORES,
    MODE_ENTER_SCORES,
    MODE_EXIT_SCORES,
    display_enter_score,
    display_exit_score,
    enter_score,
    exit_score,
    evidence_weight,
)
from src.core.entities import CompositionConfidence, CompositionMode


def test_mode_thresholds_cover_contract_and_keep_hysteresis_gap():
    assert set(MODE_ENTER_SCORES) == set(CompositionMode)
    assert set(MODE_EXIT_SCORES) == set(CompositionMode)
    assert set(MODE_DISPLAY_ENTER_SCORES) == set(CompositionMode)
    assert set(MODE_DISPLAY_EXIT_SCORES) == set(CompositionMode)
    for mode in CompositionMode:
        assert 0 <= exit_score(mode) < enter_score(mode) <= 100
        assert 0 <= display_exit_score(mode) < display_enter_score(mode) <= 100


def test_frozen_per_mode_thresholds_match_calibration_baseline():
    expected = {
        CompositionMode.RULE_OF_THIRDS: (59.46, 49.46),
        CompositionMode.DYNAMIC_SYMMETRY: (50.86, 40.86),
        CompositionMode.BALANCED: (78.85, 68.85),
        CompositionMode.TRIANGLE: (65.93, 55.93),
        CompositionMode.DIAGONAL: (21.22, 11.22),
        CompositionMode.HORIZONTAL: (75.0, 65.0),
        CompositionMode.OBLIQUE: (44.72, 34.72),
        CompositionMode.CURVE: (35.46, 25.46),
        CompositionMode.RADIAL: (49.49, 39.49),
        CompositionMode.CHECKERBOARD: (38.0, 28.0),
        CompositionMode.CENTRIPETAL: (17.65, 7.65),
        CompositionMode.TUNNEL: (36.34, 26.34),
        CompositionMode.FRAME_WITHIN_FRAME: (95.85, 85.85),
        CompositionMode.CROSS: (46.13, 36.13),
        CompositionMode.VERTICAL: (23.38, 13.38),
    }

    assert {
        mode: (enter_score(mode), exit_score(mode)) for mode in CompositionMode
    } == expected


def test_evidence_weights_are_centralized_for_every_mode():
    assert set(MODE_EVIDENCE_WEIGHTS) == set(CompositionMode)
    for mode, components in MODE_EVIDENCE_WEIGHTS.items():
        assert components
        assert all(name.strip() for name in components)
        assert all(0 < value <= 1 for value in components.values())
        for name, value in components.items():
            assert evidence_weight(mode, name) == value


def test_high_confidence_uses_the_calibrated_mode_threshold(monkeypatch):
    mode = CompositionMode.CENTRIPETAL
    monkeypatch.setitem(MODE_ENTER_SCORES, mode, 20.0)
    monkeypatch.setitem(MODE_EXIT_SCORES, mode, 10.0)
    features = SimpleNamespace(evidence_quality=0.8)

    assert confidence_for(21.0, features, mode) is CompositionConfidence.HIGH
    assert confidence_for(15.0, features, mode) is CompositionConfidence.MEDIUM
