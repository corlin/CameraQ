from __future__ import annotations

import itertools
import math

import numpy as np

from src.core.composition.features import CompositionFeatures
from src.core.composition.thresholds import evidence_weight
from src.core.entities import CompositionEvidenceType, CompositionMode

from .common import evidence, normalized_line, point, result


def _thirds(features: CompositionFeatures):
    focus = features.primary_focus
    if focus is None:
        return result(CompositionMode.RULE_OF_THIRDS, 0, features)
    nodes = [(x, y) for x in (1 / 3, 2 / 3) for y in (1 / 3, 2 / 3)]
    node, node_distance = min(
        ((node, math.dist((focus.x, focus.y), node)) for node in nodes), key=lambda item: item[1]
    )
    line_distance = min(abs(focus.x - 1 / 3), abs(focus.x - 2 / 3), abs(focus.y - 1 / 3), abs(focus.y - 2 / 3))
    score = max(
        100 * evidence_weight(CompositionMode.RULE_OF_THIRDS, "node") * (1 - node_distance / 0.22),
        100 * evidence_weight(CompositionMode.RULE_OF_THIRDS, "line") * (1 - line_distance / 0.18),
    )
    strength = max(0.0, min(1.0, score / 100))
    return result(
        CompositionMode.RULE_OF_THIRDS,
        score,
        features,
        [
            evidence(
                CompositionEvidenceType.SUBJECT_POSITION,
                strength,
                "主焦点接近三分线/交点",
                points=[point(focus.x, focus.y), point(*node)],
            )
        ],
    )


def _balanced(features: CompositionFeatures):
    cx, cy = features.mass_centroid
    center_distance = math.dist((cx, cy), (0.5, 0.5))
    q1, q2, q3, q4 = features.quadrant_mass
    horizontal_difference = abs((q1 + q3) - (q2 + q4))
    vertical_difference = abs((q1 + q2) - (q3 + q4))
    score = (
        100
        * evidence_weight(CompositionMode.BALANCED, "centroid")
        * max(0.0, 1.0 - center_distance / 0.5)
        * evidence_weight(CompositionMode.BALANCED, "mass_symmetry")
        * max(0.0, 1.0 - (horizontal_difference + vertical_difference) / 1.2)
    )
    return result(
        CompositionMode.BALANCED,
        score,
        features,
        [
            evidence(
                CompositionEvidenceType.VISUAL_MASS,
                score / 100,
                "视觉质量围绕画面中心保持均衡",
                points=[point(cx, cy), point(0.5, 0.5)],
            )
        ] if score > 0 else [],
    )


def _dynamic_symmetry(features: CompositionFeatures):
    diagonal_angle = math.degrees(math.atan2(features.analysis_height, features.analysis_width))
    reciprocal_angle = 90.0 - diagonal_angle
    matching = [
        line
        for line in features.lines
        if min(abs(line.angle - diagonal_angle), abs(line.angle - reciprocal_angle)) <= 10
    ]
    line_strength = min(1.0, sum(line.length for line in matching) / 1.2)
    focus_strength = 0.0
    focus = features.primary_focus
    if focus:
        distances = (
            abs(focus.y - focus.x),
            abs(focus.y - (1 - focus.x)),
        )
        focus_strength = max(0.0, 1.0 - min(distances) / 0.25)
    score = 100 * (
        evidence_weight(CompositionMode.DYNAMIC_SYMMETRY, "line") * line_strength
        + evidence_weight(CompositionMode.DYNAMIC_SYMMETRY, "focus") * focus_strength
    ) if matching else 0.0
    return result(
        CompositionMode.DYNAMIC_SYMMETRY,
        score,
        features,
        [
            evidence(
                CompositionEvidenceType.SYMMETRY,
                score / 100,
                "焦点与动态对称斜线形成呼应",
                points=[point(focus.x, focus.y)] if focus else [],
                lines=[normalized_line(line) for line in matching[:4]],
            )
        ] if matching else [],
    )


def _triangle(features: CompositionFeatures):
    candidates = np.asarray(features.corners[:12], dtype=float)
    max_area = 0.0
    best: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None
    for a, b, c in itertools.combinations(candidates, 3):
        area = abs(float(np.cross(b - a, c - a))) / 2.0
        if area > max_area:
            max_area = area
            best = a, b, c
    score = min(
        100.0,
        max_area / 0.22 * 100.0 * evidence_weight(CompositionMode.TRIANGLE, "area"),
    ) if best else 0.0
    return result(
        CompositionMode.TRIANGLE,
        score,
        features,
        [
            evidence(
                CompositionEvidenceType.CONTOUR,
                score / 100,
                "三个稳定焦点形成非共线三角关系",
                contour=[point(float(item[0]), float(item[1])) for item in best],
            )
        ] if best and score >= 20 else [],
    )


def score_position_modes(features: CompositionFeatures):
    return [_thirds(features), _dynamic_symmetry(features), _balanced(features), _triangle(features)]
