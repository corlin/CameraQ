from __future__ import annotations

import math

import cv2
import numpy as np

from src.core.composition.features import CompositionFeatures
from src.core.composition.geometry import point_within_polygon
from src.core.composition.thresholds import evidence_weight
from src.core.entities import CompositionEvidenceType, CompositionMode

from .common import evidence, normalized_line, point, result


def _curve(features: CompositionFeatures):
    best = None
    best_score = 0.0
    for contour in features.contours:
        if len(contour.points) < 4 or contour.perimeter < 0.15:
            continue
        approximation = cv2.approxPolyDP(contour.points.reshape(-1, 1, 2), 0.025, False)
        complexity = min(1.0, len(approximation) / 8.0)
        non_rectangular = max(0.0, 1.0 - contour.rectangularity)
        score = 100 * (
            evidence_weight(CompositionMode.CURVE, "complexity") * complexity
            + evidence_weight(CompositionMode.CURVE, "shape") * non_rectangular
        ) * min(1.0, contour.perimeter / 0.5)
        if score > best_score:
            best_score, best = score, contour
    return result(
        CompositionMode.CURVE,
        best_score,
        features,
        [
            evidence(
                CompositionEvidenceType.CURVATURE,
                best_score / 100,
                "长曲线轮廓引导视线",
                contour=[point(float(x), float(y)) for x, y in best.points[:: max(1, len(best.points) // 20)]],
            )
        ] if best else [],
    )


def _convergence(features: CompositionFeatures):
    if len(features.intersections) < 3 or len(features.lines) < 3:
        return 0.0, None
    center = np.median(features.intersections, axis=0)
    distances = np.linalg.norm(features.intersections - center, axis=1)
    close_ratio = float(np.mean(distances < 0.12))
    angle_bins = {int(line.angle // 15) for line in features.lines if line.length > 0.12}
    spread = min(1.0, len(angle_bins) / 4.0)
    return close_ratio * spread, center


def _radial_and_centripetal(features: CompositionFeatures):
    convergence, center = _convergence(features)
    radial_score = convergence * evidence_weight(CompositionMode.RADIAL, "convergence") * 100
    radial = result(
        CompositionMode.RADIAL,
        radial_score,
        features,
        [
            evidence(
                CompositionEvidenceType.VANISHING_POINT,
                convergence,
                "多方向结构共享辐射中心",
                points=[point(float(center[0]), float(center[1]))],
                lines=[normalized_line(line) for line in features.lines[:6]],
            )
        ] if center is not None else [],
    )
    focus_alignment = 0.0
    focus = features.primary_focus
    if center is not None and focus is not None:
        focus_alignment = max(0.0, 1.0 - math.dist((focus.x, focus.y), center) / 0.25)
    centripetal_strength = convergence * (
        evidence_weight(CompositionMode.CENTRIPETAL, "convergence")
        + evidence_weight(CompositionMode.CENTRIPETAL, "focus") * focus_alignment
    ) if focus else 0.0
    centripetal = result(
        CompositionMode.CENTRIPETAL,
        centripetal_strength * 100,
        features,
        [
            evidence(
                CompositionEvidenceType.VANISHING_POINT,
                centripetal_strength,
                "周边结构收束到主焦点",
                points=[point(float(center[0]), float(center[1])), point(focus.x, focus.y)],
            )
        ] if center is not None and focus is not None else [],
    )
    return radial, centripetal


def _checkerboard(features: CompositionFeatures):
    horizontal = [line for line in features.lines if line.angle <= 10]
    vertical = [line for line in features.lines if line.angle >= 80]
    family_strength = min(len(horizontal), len(vertical)) / 4.0
    intersection_strength = min(1.0, len(features.intersections) / 12.0)
    strength = (
        min(1.0, family_strength) * evidence_weight(CompositionMode.CHECKERBOARD, "families")
        + intersection_strength * evidence_weight(CompositionMode.CHECKERBOARD, "intersections")
    )
    if len(horizontal) < 3 or len(vertical) < 3:
        strength *= evidence_weight(CompositionMode.CHECKERBOARD, "sparse")
    return result(
        CompositionMode.CHECKERBOARD,
        strength * 100,
        features,
        [
            evidence(
                CompositionEvidenceType.REPETITION,
                strength,
                "两组正交重复线形成网格",
                lines=[normalized_line(line) for line in (horizontal[:3] + vertical[:3])],
            )
        ] if horizontal and vertical else [],
    )


def _frame_and_tunnel(features: CompositionFeatures):
    focus = features.primary_focus
    enclosing = []
    for contour in features.contours:
        if contour.rectangularity < 0.35 or contour.area < 0.08:
            continue
        if focus is None or point_within_polygon((focus.x, focus.y), contour.points):
            enclosing.append(contour)
    frame_strength = (
        min(1.0, max((item.area for item in enclosing), default=0.0) / 0.25)
        * evidence_weight(CompositionMode.FRAME_WITHIN_FRAME, "enclosure")
    )
    frame = result(
        CompositionMode.FRAME_WITHIN_FRAME,
        frame_strength * 100,
        features,
        [
            evidence(
                CompositionEvidenceType.CONTOUR,
                frame_strength,
                "边界包围内部焦点",
                contour=[point(float(x), float(y)) for x, y in enclosing[0].points[:: max(1, len(enclosing[0].points) // 12)]],
            )
        ] if enclosing else [],
    )
    distinct_levels = []
    for item in sorted(enclosing, key=lambda value: value.area, reverse=True):
        if not distinct_levels or item.area / distinct_levels[-1].area < 0.82:
            distinct_levels.append(item)
    max_depth = max((item.depth for item in distinct_levels), default=0)
    tunnel_strength = (
        min(1.0, max_depth / 3.0)
        * evidence_weight(CompositionMode.TUNNEL, "depth")
        * min(1.0, max(0, len(distinct_levels) - 1) / 3.0)
        * evidence_weight(CompositionMode.TUNNEL, "nesting")
    )
    tunnel = result(
        CompositionMode.TUNNEL,
        tunnel_strength * 100,
        features,
        [
            evidence(
                CompositionEvidenceType.NESTED_CONTOUR,
                tunnel_strength,
                "重复嵌套边界形成纵深通道",
                contour=[
                    point(float(x), float(y))
                    for item in distinct_levels[:3]
                    for x, y in item.points[:: max(1, len(item.points) // 8)]
                ],
            )
        ] if tunnel_strength else [],
    )
    return tunnel, frame


def score_topology_modes(features: CompositionFeatures):
    radial, centripetal = _radial_and_centripetal(features)
    tunnel, frame = _frame_and_tunnel(features)
    return [_curve(features), radial, _checkerboard(features), centripetal, tunnel, frame]
