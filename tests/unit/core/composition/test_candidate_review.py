import csv
import json

import cv2
import numpy as np
import pytest

from tests.fixtures.composition import curate_commons_cases
from tests.fixtures.composition import review_candidates
from tests.fixtures.composition.review_candidates import (
    export_review_queue,
    import_review_decisions,
    review_candidate,
)


def test_cross_mode_negative_annotation_resets_prior_review(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "labels": ["HORIZONTAL", "OBLIQUE"],
                "cases": [
                    {
                        "id": "level-horizon",
                        "labels": ["HORIZONTAL"],
                        "negative_for": [],
                        "review_status": "accepted",
                        "reviewer": "first-reviewer",
                        "review_notes": "clear level horizon",
                        "reviewed_at": "2026-07-05T00:00:00Z",
                    }
                ],
            }
        )
    )

    changed = review_candidates.add_negative_annotations(
        manifest, {"level-horizon": ["OBLIQUE"]}
    )

    saved = json.loads(manifest.read_text())["cases"][0]
    assert changed == 1
    assert saved["negative_for"] == ["OBLIQUE"]
    assert saved["review_status"] == "pending"
    assert "reviewer" not in saved
    assert "review_notes" not in saved
    assert "reviewed_at" not in saved


def test_cross_mode_positive_annotation_promotes_case_and_resets_review(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "labels": ["CENTRIPETAL", "TUNNEL"],
                "cases": [
                    {
                        "id": "tunnel-leading-lines",
                        "kind": "hard_negative",
                        "labels": [],
                        "negative_for": ["CENTRIPETAL"],
                        "review_status": "accepted",
                        "reviewer": "first-reviewer",
                        "review_notes": "old decision",
                        "reviewed_at": "2026-07-05T00:00:00Z",
                    }
                ],
            }
        )
    )

    changed = review_candidates.add_positive_annotations(
        manifest, {"tunnel-leading-lines": ["TUNNEL"]}
    )

    saved = json.loads(manifest.read_text())["cases"][0]
    assert changed == 1
    assert saved["labels"] == ["TUNNEL"]
    assert saved["kind"] == "positive"
    assert saved["review_status"] == "pending"
    assert "reviewer" not in saved


def test_apply_unbalanced_edge_crops_is_reproducible_and_resets_review(tmp_path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    image_path = image_dir / "candidate.jpg"
    frame = np.zeros((40, 100, 3), dtype=np.uint8)
    frame[:, 40:60] = 255
    assert cv2.imwrite(str(image_path), frame)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "candidate",
                        "path": "images/candidate.jpg",
                        "review_status": "accepted",
                        "reviewer": "reviewer",
                        "review_notes": "reviewed",
                        "modifications": "resized",
                    }
                ]
            }
        )
    )

    assert curate_commons_cases.apply_unbalanced_edge_crops(
        manifest, ["candidate"]
    ) == 1
    assert curate_commons_cases.apply_unbalanced_edge_crops(
        manifest, ["candidate"]
    ) == 0

    cropped = cv2.imread(str(image_path))
    updated = json.loads(manifest.read_text())["cases"][0]
    assert cropped.shape[:2] == (40, 62)
    assert updated["review_status"] == "pending"
    assert "reviewer" not in updated
    assert "directional 62% edge crop" in updated["modifications"]
    assert len(updated["sha256"]) == 64


def test_review_candidate_records_human_decision_without_changing_source_annotation(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "commons-tunnel-positive-00",
                        "annotation_source": "Wikimedia Commons human-curated category: tunnel",
                        "review_status": "pending",
                    }
                ]
            }
        )
    )

    reviewed = review_candidate(
        manifest,
        "commons-tunnel-positive-00",
        status="ambiguous",
        reviewer="cameraq-human-reviewer",
        notes="single portal is visible but nested depth is unclear",
    )

    assert reviewed["review_status"] == "ambiguous"
    assert reviewed["reviewer"] == "cameraq-human-reviewer"
    assert reviewed["review_notes"].startswith("single portal")
    assert reviewed["reviewed_at"].endswith("Z")
    assert reviewed["annotation_source"].startswith("Wikimedia Commons")


def test_review_candidate_requires_reviewer_notes_and_known_id(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"cases": [{"id": "candidate", "review_status": "pending"}]}))

    with pytest.raises(ValueError):
        review_candidate(manifest, "candidate", status="accepted", reviewer="", notes="looks valid")
    with pytest.raises(ValueError):
        review_candidate(manifest, "candidate", status="rejected", reviewer="reviewer", notes="")
    with pytest.raises(KeyError):
        review_candidate(manifest, "missing", status="accepted", reviewer="reviewer", notes="valid")


def test_review_queue_round_trip_only_applies_decision_fields(tmp_path):
    manifest = tmp_path / "manifest.json"
    original = {
        "id": "commons-diagonal-positive-00",
        "path": "images/real_candidates/example.jpg",
        "kind": "positive",
        "labels": ["DIAGONAL"],
        "negative_for": [],
        "source": "Wikimedia Commons",
        "source_title": "File:Example.jpg",
        "provenance_url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
        "license": "CC BY 4.0",
        "annotation_source": "Wikimedia Commons human-curated category: Diagonal images",
        "review_status": "pending",
    }
    manifest.write_text(json.dumps({"cases": [original]}))
    queue = tmp_path / "review.csv"

    assert export_review_queue(manifest, queue) == 1
    assert b"\r\n" not in queue.read_bytes()
    with queue.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["proposed_labels"] == "DIAGONAL"
    assert rows[0]["decision"] == ""

    rows[0]["decision"] = "accepted"
    rows[0]["reviewer"] = "independent-reviewer"
    rows[0]["review_notes"] = "dominant line traverses the frame diagonally"
    rows[0]["proposed_labels"] = "TUNNEL"
    with queue.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    assert import_review_decisions(manifest, queue) == 1
    saved = json.loads(manifest.read_text())["cases"][0]
    assert saved["review_status"] == "accepted"
    assert saved["reviewer"] == "independent-reviewer"
    assert saved["labels"] == ["DIAGONAL"]
    assert saved["annotation_source"] == original["annotation_source"]


def test_review_queue_import_rejects_unknown_ids_and_blank_decisions(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"cases": [{"id": "known", "review_status": "pending"}]}))
    queue = tmp_path / "review.csv"
    queue.write_text(
        "id,decision,reviewer,review_notes\n"
        "known,,,\n"
        "missing,accepted,reviewer,valid\n"
    )

    with pytest.raises(KeyError):
        import_review_decisions(manifest, queue)
