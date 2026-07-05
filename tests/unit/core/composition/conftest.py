from __future__ import annotations

import numpy as np
import pytest

from src.core.entities import BoundingBox, FusedSubject, SaliencyMap, SourceType


@pytest.fixture
def blank_frame() -> np.ndarray:
    return np.zeros((240, 320, 3), dtype=np.uint8)


@pytest.fixture
def primary_subject() -> FusedSubject:
    return FusedSubject(
        subject_id="primary",
        class_name="person",
        confidence=0.95,
        bounding_box=BoundingBox(x=90, y=45, width=80, height=150),
        is_primary_subject=True,
        source=SourceType.YOLO,
    )


@pytest.fixture
def empty_saliency() -> SaliencyMap:
    return SaliencyMap(
        heatmap=np.zeros((240, 320), dtype=np.uint8),
        bounding_boxes=[],
        max_salient_score=0.0,
    )
