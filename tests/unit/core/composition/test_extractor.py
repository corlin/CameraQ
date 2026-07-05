from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from src.core.composition.extractor import CompositionFeatureExtractor
from src.core.entities import BoundingBox, FusedSubject, SaliencyMap, SourceType
from tests.fixtures.composition.factory import grid_image, line_image


def saliency_for(frame: np.ndarray, x: int, y: int) -> SaliencyMap:
    heatmap = np.zeros(frame.shape[:2], dtype=np.uint8)
    heatmap[max(0, y - 8) : y + 8, max(0, x - 8) : x + 8] = 255
    return SaliencyMap(heatmap=heatmap, bounding_boxes=[], max_salient_score=1.0)


def test_extractor_downscales_to_max_edge_320():
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    features = CompositionFeatureExtractor().extract(frame, [], saliency_for(frame, 640, 360))
    assert max(features.analysis_width, features.analysis_height) == 320
    assert (features.frame_width, features.frame_height) == (1280, 720)


def test_extractor_reuses_primary_subject_as_strongest_focus():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    subject = FusedSubject(
        subject_id="p",
        class_name="person",
        confidence=0.9,
        bounding_box=BoundingBox(x=80, y=40, width=80, height=120),
        is_primary_subject=True,
        source=SourceType.YOLO,
    )
    features = CompositionFeatureExtractor().extract(frame, [subject], saliency_for(frame, 250, 180))
    assert features.primary_focus is not None
    assert features.primary_focus.source == "subject"
    assert features.primary_focus.weight > 0.5


def test_all_subjects_contribute_to_visual_mass_while_primary_owns_focus():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    primary = FusedSubject(
        subject_id="primary",
        class_name="person",
        confidence=0.9,
        bounding_box=BoundingBox(x=32, y=72, width=64, height=96),
        is_primary_subject=True,
        source=SourceType.YOLO,
    )
    secondary = FusedSubject(
        subject_id="secondary",
        class_name="person",
        confidence=0.8,
        bounding_box=BoundingBox(x=224, y=72, width=64, height=96),
        is_primary_subject=False,
        source=SourceType.YOLO,
    )

    features = CompositionFeatureExtractor().extract(frame, [primary, secondary], None)

    assert features.primary_focus is not None
    assert features.primary_focus.x < 0.5
    left_mass = features.quadrant_mass[0] + features.quadrant_mass[2]
    right_mass = features.quadrant_mass[1] + features.quadrant_mass[3]
    assert left_mass > right_mass > 0.1


def test_extractor_falls_back_to_saliency_without_subject():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    features = CompositionFeatureExtractor().extract(frame, [], saliency_for(frame, 250, 180))
    assert features.primary_focus is not None
    assert features.primary_focus.source == "saliency"
    assert features.primary_focus.x > 0.7


def test_extractor_detects_lines_contours_and_orientation():
    frame = grid_image()
    features = CompositionFeatureExtractor().extract(frame, [], saliency_for(frame, 160, 120))
    assert len(features.lines) >= 4
    assert len(features.contours) >= 1
    assert features.orientation_histogram.shape == (18,)


def test_feature_snapshot_is_frozen_and_arrays_are_read_only():
    frame = line_image((0,))
    features = CompositionFeatureExtractor().extract(frame, [], saliency_for(frame, 160, 120))
    with pytest.raises(FrozenInstanceError):
        features.frame_width = 1
    assert not features.edges.flags.writeable


def test_empty_frame_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        CompositionFeatureExtractor().extract(np.array([], dtype=np.uint8), [], None)
