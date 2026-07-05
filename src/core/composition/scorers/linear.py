from __future__ import annotations

import math

from src.core.composition.features import CompositionFeatures
from src.core.composition.thresholds import evidence_weight
from src.core.entities import CompositionEvidenceType, CompositionMode

from .common import evidence, normalized_line, point, result


def _weighted_strength(features: CompositionFeatures, mode: CompositionMode, predicate) -> tuple[float, list]:
    total = sum(line.length for line in features.lines)
    matching = [line for line in features.lines if predicate(line)]
    if total <= 0:
        return 0.0, []
    dominance = sum(line.length for line in matching) / total
    coverage = min(1.0, sum(line.length for line in matching) / 1.4)
    return (
        dominance * evidence_weight(mode, "dominance")
        + coverage * evidence_weight(mode, "coverage")
    ), matching


def _mode(features, mode, predicate, description):
    strength, lines = _weighted_strength(features, mode, predicate)
    score = strength * 100
    return result(
        mode,
        score,
        features,
        [
            evidence(
                CompositionEvidenceType.LINE,
                strength,
                description,
                lines=[normalized_line(line) for line in sorted(lines, key=lambda item: item.length, reverse=True)[:5]],
            )
        ] if lines else [],
    )


def score_linear_modes(features: CompositionFeatures):
    diagonal_angle = math.degrees(math.atan2(features.analysis_height, features.analysis_width))
    horizontal = _mode(features, CompositionMode.HORIZONTAL, lambda line: line.angle <= 10, "长水平线主导画面")
    vertical = _mode(features, CompositionMode.VERTICAL, lambda line: line.angle >= 80, "长垂直线主导画面")
    diagonal = _mode(
        features,
        CompositionMode.DIAGONAL,
        lambda line: abs(line.angle - diagonal_angle) <= 8 and line.length >= 0.35,
        "跨画面线条贴近对角方向",
    )
    oblique = _mode(
        features,
        CompositionMode.OBLIQUE,
        lambda line: 12 <= line.angle <= 78 and abs(line.angle - diagonal_angle) > 8,
        "倾斜主方向形成动势",
    )
    h_strength, h_lines = _weighted_strength(
        features, CompositionMode.CROSS, lambda line: line.angle <= 10
    )
    v_strength, v_lines = _weighted_strength(
        features, CompositionMode.CROSS, lambda line: line.angle >= 80
    )
    intersections = [
        pair
        for pair in features.intersections
        if 0.15 <= pair[0] <= 0.85 and 0.15 <= pair[1] <= 0.85
    ]
    intersection_weight = evidence_weight(
        CompositionMode.CROSS,
        "intersection" if intersections else "missing_intersection",
    )
    cross_strength = min(h_strength, v_strength) * intersection_weight
    cross = result(
        CompositionMode.CROSS,
        cross_strength * 100,
        features,
        [
            evidence(
                CompositionEvidenceType.LINE_INTERSECTION,
                cross_strength,
                "主水平与垂直结构形成交叉",
                points=[point(float(value[0]), float(value[1])) for value in intersections[:3]],
                lines=[normalized_line(line) for line in (h_lines[:2] + v_lines[:2])],
            )
        ] if h_lines and v_lines else [],
    )
    return [diagonal, horizontal, oblique, cross, vertical]
