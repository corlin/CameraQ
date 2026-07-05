import json
from pathlib import Path

import pytest

from tests.fixtures.composition.validate_manifest import audit_manifest, assert_acceptance_ready


LABELS = [
    "RULE_OF_THIRDS",
    "DYNAMIC_SYMMETRY",
    "BALANCED",
    "TRIANGLE",
    "DIAGONAL",
    "HORIZONTAL",
    "OBLIQUE",
    "CURVE",
    "RADIAL",
    "CHECKERBOARD",
    "CENTRIPETAL",
    "TUNNEL",
    "FRAME_WITHIN_FRAME",
    "CROSS",
    "VERTICAL",
]


def write_manifest(tmp_path: Path, cases: list[dict]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "labels": LABELS,
                "required_counts": {
                    "positive_per_label": 1,
                    "hard_negative_per_label": 1,
                    "degraded_per_category": 1,
                    "recommendation_total": 4,
                    "recommendation_per_action_group": 1,
                },
                "cases": cases,
            }
        )
    )
    return path


def accepted_case(case_id: str, kind: str, **extra) -> dict:
    return {
        "id": case_id,
        "path": f"images/{case_id}.jpg",
        "kind": kind,
        "labels": [],
        "negative_for": [],
        "source": "fixture-source",
        "source_item_id": case_id,
        "provenance_url": f"https://example.test/{case_id}",
        "license": "CC0-1.0",
        "annotation_source": "independent-human-label",
        "review_status": "accepted",
        "split": "acceptance",
        **extra,
    }


def test_manifest_audit_rejects_pending_algorithm_self_labels_and_split_leakage(tmp_path):
    cases = [
        accepted_case(
            "pending",
            "positive",
            labels=["RULE_OF_THIRDS"],
            annotation_source="composition-engine-output",
            review_status="pending",
        ),
        accepted_case("duplicate-a", "positive", labels=["DIAGONAL"], source_item_id="same"),
        accepted_case(
            "duplicate-b",
            "positive",
            labels=["VERTICAL"],
            source_item_id="same",
            split="calibration",
        ),
    ]

    report = audit_manifest(write_manifest(tmp_path, cases), require_files=False)

    assert any("algorithm self-label" in issue for issue in report.issues)
    assert any("duplicate source item" in issue for issue in report.issues)
    assert any("split leakage" in issue for issue in report.issues)
    with pytest.raises(AssertionError):
        assert_acceptance_ready(report)


def test_manifest_audit_rejects_unknown_status_and_unreviewed_accepted_commons_case(tmp_path):
    cases = [
        accepted_case("typo", "positive", review_status="approve", labels=["DIAGONAL"]),
        accepted_case(
            "commons-unreviewed",
            "positive",
            labels=["RULE_OF_THIRDS"],
            source="Wikimedia Commons",
        ),
    ]

    report = audit_manifest(write_manifest(tmp_path, cases), require_files=False)

    assert any("invalid review status" in issue for issue in report.issues)
    assert any("missing independent reviewer" in issue for issue in report.issues)


def test_manifest_audit_counts_only_accepted_independent_annotations(tmp_path):
    cases = []
    for label in LABELS:
        cases.append(accepted_case(f"positive-{label}", "positive", labels=[label]))
        cases.append(accepted_case(f"negative-{label}", "hard_negative", negative_for=[label]))
    for category in ("low_information", "blur", "solid_color", "exposure"):
        cases.append(
            accepted_case(
                f"degraded-{category}",
                "degraded",
                degradation_category=category,
                expected_abstention=True,
            )
        )
    for group, action in (
        ("translation", "MOVE_LEFT"),
        ("rotation", "ROTATE_CLOCKWISE"),
        ("closer", "MOVE_CLOSER"),
        ("back", "MOVE_BACK"),
    ):
        cases.append(
            accepted_case(
                f"recommendation-{group}",
                "recommendation",
                recommendation_action=action,
                recommendation_action_group=group,
            )
        )

    report = audit_manifest(write_manifest(tmp_path, cases), require_files=False)

    assert report.issues == []
    assert_acceptance_ready(report)


def test_manifest_audit_counts_cross_mode_negatives_on_positive_cases(tmp_path):
    case = accepted_case(
        "positive-for-one-negative-for-another",
        "positive",
        labels=["HORIZONTAL"],
        negative_for=["VERTICAL"],
    )

    report = audit_manifest(write_manifest(tmp_path, [case]), require_files=False)

    assert report.positive_counts["HORIZONTAL"] == 1
    assert report.hard_negative_counts["VERTICAL"] == 1


def test_manifest_audit_requires_recommendation_after_image_when_files_are_checked(tmp_path):
    cases = []
    for label in LABELS:
        cases.append(accepted_case(f"positive-{label}", "positive", labels=[label]))
        cases.append(accepted_case(f"negative-{label}", "hard_negative", negative_for=[label]))
    for category in ("low_information", "blur", "solid_color", "exposure"):
        cases.append(
            accepted_case(
                f"degraded-{category}",
                "degraded",
                degradation_category=category,
                expected_abstention=True,
            )
        )
    for group, action in (
        ("translation", "MOVE_LEFT"),
        ("rotation", "ROTATE_CLOCKWISE"),
        ("closer", "MOVE_CLOSER"),
        ("back", "MOVE_BACK"),
    ):
        cases.append(
            accepted_case(
                f"recommendation-{group}",
                "recommendation",
                recommendation_action=action,
                recommendation_action_group=group,
                after_path=f"images/recommendation-{group}-after.jpg",
                after_sha256="0" * 64,
            )
        )
    manifest_path = write_manifest(tmp_path, cases)

    report = audit_manifest(manifest_path, require_files=True)

    assert any("missing after image file" in issue for issue in report.issues)


def test_manifest_audit_reports_unreferenced_real_candidate_files(tmp_path):
    manifest_path = write_manifest(tmp_path, [])
    orphan = tmp_path / "images/real_candidates/orphan.jpg"
    orphan.parent.mkdir(parents=True)
    orphan.write_bytes(b"not-an-image")

    report = audit_manifest(manifest_path, require_files=True)

    assert any("orphan real candidate files" in issue for issue in report.issues)
