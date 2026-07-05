from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FocusFeature:
    x: float
    y: float
    weight: float
    source: str


@dataclass(frozen=True)
class LineFeature:
    x1: float
    y1: float
    x2: float
    y2: float
    angle: float
    length: float

    @property
    def tuple(self) -> tuple[float, float, float, float]:
        return self.x1, self.y1, self.x2, self.y2


@dataclass(frozen=True)
class ContourFeature:
    points: np.ndarray
    area: float
    perimeter: float
    parent: int
    depth: int
    rectangularity: float


@dataclass(frozen=True)
class CompositionFeatures:
    frame_width: int
    frame_height: int
    analysis_width: int
    analysis_height: int
    gray: np.ndarray
    edges: np.ndarray
    gradient_magnitude: np.ndarray
    gradient_angle: np.ndarray
    lines: tuple[LineFeature, ...]
    contours: tuple[ContourFeature, ...]
    corners: np.ndarray
    intersections: np.ndarray
    orientation_histogram: np.ndarray
    visual_mass: np.ndarray
    mass_centroid: tuple[float, float]
    quadrant_mass: tuple[float, float, float, float]
    primary_focus: FocusFeature | None
    subject_area_ratio: float
    subject_clipped: bool
    evidence_quality: float
