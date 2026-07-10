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
