import pytest

from src.core.entities import CompositionMode
from tests.fixtures.composition.calibrate_thresholds import (
    ScoredExample,
    assert_calibration_ready,
    build_calibration_report,
    calibrate_mode,
    evaluate_threshold,
)


def example(score, truth, split):
    return ScoredExample(
        case_id=f"{split}-{score}-{truth}",
        mode=CompositionMode.DIAGONAL,
        score=score,
        truth=truth,
        split=split,
    )


def test_calibration_selects_precision_constrained_threshold_and_reports_holdout_recall():
    examples = [
        example(90, True, "calibration"),
        example(80, True, "calibration"),
        example(70, False, "calibration"),
        example(20, False, "calibration"),
        example(85, True, "acceptance"),
        example(60, True, "acceptance"),
        example(75, False, "acceptance"),
        example(10, False, "acceptance"),
    ]

    assert_calibration_ready(examples, [CompositionMode.DIAGONAL])
    result = calibrate_mode(examples, CompositionMode.DIAGONAL, minimum_precision=0.8)
    holdout = evaluate_threshold(
        [item for item in examples if item.split == "acceptance"], result.enter_score
    )

    assert result.enter_score == 80
    assert result.exit_score == 70
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert holdout.precision == 1.0
    assert holdout.recall == 0.5
    assert holdout.fn == 1

    report = build_calibration_report(examples, [CompositionMode.DIAGONAL])
    assert report["_metadata"]["weight_config_version"] == "initial-rule-weights-v1"
    assert report["_metadata"]["evidence_weights"]["DIAGONAL"] == {
        "dominance": 0.65,
        "coverage": 0.35,
    }
    assert report["DIAGONAL"]["proposed_enter_score"] == 80
    assert report["DIAGONAL"]["acceptance"]["recall"] == 0.5


def test_calibration_gate_requires_positive_and_negative_examples_in_both_splits():
    incomplete = [
        example(90, True, "calibration"),
        example(20, False, "calibration"),
        example(85, True, "acceptance"),
    ]

    with pytest.raises(ValueError, match="acceptance negative"):
        assert_calibration_ready(incomplete, [CompositionMode.DIAGONAL])
