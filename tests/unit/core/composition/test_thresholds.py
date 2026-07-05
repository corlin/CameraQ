from src.core.composition.thresholds import (
    MODE_EVIDENCE_WEIGHTS,
    MODE_ENTER_SCORES,
    MODE_EXIT_SCORES,
    enter_score,
    exit_score,
    evidence_weight,
)
from src.core.entities import CompositionMode


def test_mode_thresholds_cover_contract_and_keep_hysteresis_gap():
    assert set(MODE_ENTER_SCORES) == set(CompositionMode)
    assert set(MODE_EXIT_SCORES) == set(CompositionMode)
    for mode in CompositionMode:
        assert 0 <= exit_score(mode) < enter_score(mode) <= 100


def test_evidence_weights_are_centralized_for_every_mode():
    assert set(MODE_EVIDENCE_WEIGHTS) == set(CompositionMode)
    for mode, components in MODE_EVIDENCE_WEIGHTS.items():
        assert components
        assert all(name.strip() for name in components)
        assert all(0 < value <= 1 for value in components.values())
        for name, value in components.items():
            assert evidence_weight(mode, name) == value
