import json

import cv2
import numpy as np
import pytest

from src.core.entities import CompositionMode
from tests.fixtures.composition.assign_calibration_splits import (
    assign_calibration_splits,
)
from tests.fixtures.composition.calibrate_thresholds import (
    ScoredExample,
    assert_calibration_ready,
    build_calibration_report,
    calibrate_mode,
    evaluate_threshold,
    score_reviewed_manifest,
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


def test_split_assignment_is_deterministic_and_preserves_both_classes(tmp_path):
    manifest = tmp_path / "manifest.json"
    cases = []
    for truth in (True, False):
        for index in range(5):
            cases.append(
                {
                    "id": f"{'positive' if truth else 'negative'}-{index}",
                    "kind": "positive" if truth else "hard_negative",
                    "labels": ["DIAGONAL"] if truth else [],
                    "negative_for": [] if truth else ["DIAGONAL"],
                    "review_status": "accepted",
                    "split": "acceptance",
                }
            )
    manifest.write_text(__import__("json").dumps({"cases": cases}))

    first = assign_calibration_splits(manifest)
    first_payload = manifest.read_text()
    second = assign_calibration_splits(manifest)

    assert first == second == {
        "calibration_cases": 4,
        "acceptance_cases": 6,
        "strata": 4,
    }
    assert manifest.read_text() == first_payload
    saved = __import__("json").loads(first_payload)["cases"]
    for split in ("calibration", "acceptance"):
        chosen = [case for case in saved if case["split"] == split]
        assert any(case["labels"] for case in chosen)
        assert any(case["negative_for"] for case in chosen)


def test_split_assignment_preserves_each_source_family_in_both_splits(tmp_path):
    manifest = tmp_path / "manifest.json"
    cases = []
    for family, prefix in (("Rule of thirds", "a"), ("Horizons", "z")):
        for index in range(5):
            cases.append(
                {
                    "id": f"{prefix}-positive-{index}",
                    "kind": "positive",
                    "labels": ["RULE_OF_THIRDS"],
                    "negative_for": [],
                    "review_status": "accepted",
                    "split": "acceptance",
                    "annotation_source": (
                        "Wikimedia Commons human-curated category: " + family
                    ),
                }
            )
    for index in range(10):
        cases.append(
            {
                "id": f"negative-{index}",
                "kind": "hard_negative",
                "labels": [],
                "negative_for": ["RULE_OF_THIRDS"],
                "review_status": "accepted",
                "split": "acceptance",
                "annotation_source": (
                    "Wikimedia Commons human-curated category: Centered objects"
                ),
            }
        )
    manifest.write_text(json.dumps({"cases": cases}))

    assign_calibration_splits(manifest)

    saved = json.loads(manifest.read_text())["cases"]
    for family in ("Rule of thirds", "Horizons", "Centered objects"):
        selected = [
            case for case in saved if family in case.get("annotation_source", "")
        ]
        assert {case["split"] for case in selected} == {
            "calibration",
            "acceptance",
        }


def test_manifest_scoring_runs_local_saliency_when_subject_box_is_absent(tmp_path):
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.rectangle(frame, (85, 55), (135, 105), (255, 255, 255), -1)
    image_path = tmp_path / "thirds.jpg"
    assert cv2.imwrite(str(image_path), frame)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "thirds-with-salient-subject",
                        "path": "thirds.jpg",
                        "kind": "positive",
                        "labels": ["RULE_OF_THIRDS"],
                        "negative_for": [],
                        "review_status": "accepted",
                        "split": "calibration",
                    }
                ]
            }
        )
    )

    examples = score_reviewed_manifest(manifest)

    assert len(examples) == 1
    assert examples[0].score > 0


def test_manifest_scoring_uses_salient_region_center_not_heatmap_edge(tmp_path):
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.rectangle(frame, (110, 70), (210, 170), (255, 255, 255), -1)
    image_path = tmp_path / "centered.jpg"
    assert cv2.imwrite(str(image_path), frame)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "centered-salient-subject",
                        "path": "centered.jpg",
                        "kind": "hard_negative",
                        "labels": [],
                        "negative_for": ["RULE_OF_THIRDS"],
                        "review_status": "accepted",
                        "split": "calibration",
                    }
                ]
            }
        )
    )

    examples = score_reviewed_manifest(manifest)

    assert len(examples) == 1
    assert examples[0].score < 20
