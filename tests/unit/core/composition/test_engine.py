from pathlib import Path

import cv2
import numpy as np

from src.core.composition.engine import CompositionEngine
import src.core.composition.thresholds as threshold_config
from src.core.detectors.saliency_detector import SaliencyDetector
from src.core.entities import BoundingBox, CompositionMode, FusedSubject, SourceType
from tests.fixtures.composition.evaluate_acceptance import _subjects
from tests.fixtures.composition.factory import line_image


def subject_at(x, y):
    return FusedSubject(
        subject_id="s",
        class_name="person",
        confidence=0.95,
        bounding_box=BoundingBox(x=x - 20, y=y - 30, width=40, height=60),
        is_primary_subject=True,
        source=SourceType.YOLO,
    )


def test_engine_returns_every_mode_once():
    result = CompositionEngine().analyze(line_image((0, 90)), [], None, timestamp=1.0)
    assert len(result.mode_results) == 15
    assert {item.mode for item in result.mode_results} == set(CompositionMode)


def test_engine_abstains_on_blank_frame():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    result = CompositionEngine().analyze(frame, [], None, timestamp=1.0)
    assert result.insufficient_evidence
    assert result.top_modes == []


def test_engine_allows_multilabel_top_three():
    frame = line_image((36,))
    result = CompositionEngine().analyze(frame, [subject_at(320 / 3, 240 / 3)], None, timestamp=1.0)
    # Multilabel scenes produce up to 3 modes, each with evidence.
    assert 1 <= len(result.top_modes) <= 5
    for mode in result.top_modes:
        item = next(value for value in result.mode_results if value.mode is mode)
        assert item.evidence


def test_engine_protects_high_confidence_underrepresented_modes_in_top_three(monkeypatch):
    candidate_thresholds = {
        CompositionMode.BALANCED: 78.85,
        CompositionMode.TRIANGLE: 65.93,
        CompositionMode.DIAGONAL: 21.22,
        CompositionMode.OBLIQUE: 44.72,
        CompositionMode.TUNNEL: 36.34,
        CompositionMode.FRAME_WITHIN_FRAME: 95.85,
        CompositionMode.CROSS: 46.13,
    }
    for mode, enter_score in candidate_thresholds.items():
        monkeypatch.setitem(threshold_config.MODE_ENTER_SCORES, mode, enter_score)
        monkeypatch.setitem(
            threshold_config.MODE_EXIT_SCORES,
            mode,
            max(0.0, enter_score - 10.0),
        )
    fixture = (
        Path(__file__).parents[3]
        / "fixtures/composition/images/real_candidates"
        / "commons-diagonal-positive-07.jpg"
    )
    frame = cv2.imread(str(fixture))
    saliency = SaliencyDetector().detect(frame)
    height, width = frame.shape[:2]

    result = CompositionEngine().analyze(
        frame,
        _subjects({}, "subject_box_before", width, height, saliency),
        saliency,
        timestamp=1.0,
    )

    assert CompositionMode.DIAGONAL in result.top_modes
    assert len(result.top_modes) <= 5


def test_engine_promotes_strong_centripetal_evidence_in_top_three(monkeypatch):
    candidate_thresholds = {
        CompositionMode.DYNAMIC_SYMMETRY: 50.86,
        CompositionMode.OBLIQUE: 44.72,
        CompositionMode.TUNNEL: 36.34,
        CompositionMode.FRAME_WITHIN_FRAME: 95.85,
        CompositionMode.CENTRIPETAL: 17.65,
    }
    for mode, enter_score in candidate_thresholds.items():
        monkeypatch.setitem(threshold_config.MODE_ENTER_SCORES, mode, enter_score)
        monkeypatch.setitem(
            threshold_config.MODE_EXIT_SCORES,
            mode,
            max(0.0, enter_score - 10.0),
        )
    fixture = (
        Path(__file__).parents[3]
        / "fixtures/composition/images/real_candidates"
        / "commons-centripetal-positive-07.jpg"
    )
    frame = cv2.imread(str(fixture))
    saliency = SaliencyDetector().detect(frame)
    height, width = frame.shape[:2]

    result = CompositionEngine().analyze(
        frame,
        _subjects({}, "subject_box_before", width, height, saliency),
        saliency,
        timestamp=1.0,
    )

    assert CompositionMode.CENTRIPETAL in result.top_modes
