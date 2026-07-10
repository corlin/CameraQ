import json
from types import SimpleNamespace

import cv2
import numpy as np

from src.core.composition.engine import CompositionEngine
from src.core.detectors.saliency_detector import SaliencyDetector
from src.core.entities import BoundingBox, SaliencyMap, SourceType
from tests.fixtures.composition.evaluate_acceptance import evaluate_manifest
from tests.fixtures.composition.generate_acceptance_cases import generate_cases


def test_evaluator_measures_generated_degradation_and_recommendation_sets(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "labels": [],
                "required_counts": {},
                "cases": [],
            }
        )
    )
    generate_cases(manifest_path)

    report = evaluate_manifest(manifest_path)

    assert report.degraded_total == 100
    assert report.degraded_abstentions == 100
    assert report.degraded_abstention_rate == 1.0
    assert report.recommendation_total == 50
    assert report.recommendation_improvements == 50
    assert report.recommendation_improvement_rate == 1.0
    assert report.recommendation_action_matches == 50
    assert report.recommendation_action_match_rate == 1.0


def test_evaluator_uses_the_same_saliency_input_as_runtime(monkeypatch, tmp_path):
    image_path = tmp_path / "degraded.jpg"
    cv2.imwrite(str(image_path), np.zeros((80, 120, 3), dtype=np.uint8))
    saliency = SaliencyMap(
        heatmap=np.ones((80, 120), dtype=np.float32),
        bounding_boxes=[BoundingBox(x=30, y=20, width=40, height=30)],
        max_salient_score=0.8,
    )
    monkeypatch.setattr(SaliencyDetector, "detect", lambda self, frame: saliency)
    calls = []

    def capture_analysis(self, frame, subjects, saliency_input, timestamp):
        calls.append((subjects, saliency_input))
        return SimpleNamespace(
            mode_results=[],
            top_modes=[],
            recommendation=None,
            insufficient_evidence=True,
        )

    monkeypatch.setattr(CompositionEngine, "analyze", capture_analysis)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "labels": [],
                "required_counts": {},
                "cases": [
                    {
                        "id": "saliency-parity",
                        "path": image_path.name,
                        "kind": "degraded",
                        "review_status": "accepted",
                    }
                ],
            }
        )
    )

    evaluate_manifest(manifest_path)

    assert calls[0][1] is saliency
    assert calls[0][0][0].source is SourceType.SALIENCY


def test_evaluator_excludes_calibration_cases_from_acceptance_counts(tmp_path):
    image_path = tmp_path / "blank.jpg"
    cv2.imwrite(str(image_path), np.zeros((80, 120, 3), dtype=np.uint8))
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "labels": [],
                "required_counts": {},
                "cases": [
                    {
                        "id": f"{split}-positive",
                        "path": image_path.name,
                        "kind": "positive",
                        "review_status": "accepted",
                        "split": split,
                    }
                    for split in ("calibration", "acceptance")
                ],
            }
        )
    )

    report = evaluate_manifest(manifest_path)

    assert report.positive_cases == 1
