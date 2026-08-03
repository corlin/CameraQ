from __future__ import annotations

import math

import numpy as np

from src.core.composition.features import CompositionFeatures
from src.core.composition.geometry import point_line_distance, point_within_polygon
from src.core.composition.thresholds import evidence_weight
from src.core.entities import CompositionEvidenceType, CompositionMode

from .common import evidence, normalized_line, point, result


def _curve(features: CompositionFeatures):
    best = None
    best_score = 0.0
    arch_score = 0.0
    arch_contour = None
    straight_line_total = sum(line.length for line in features.lines)
    for contour in features.contours:
        if len(contour.points) < 8:
            continue
        min_x = float(contour.points[:, 0].min())
        max_x = float(contour.points[:, 0].max())
        min_y = float(contour.points[:, 1].min())
        max_y = float(contour.points[:, 1].max())
        width = max_x - min_x
        height = max_y - min_y
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        if (
            0.002 <= contour.area <= 0.020
            and 0.30 <= width <= 0.75
            and 0.25 <= height <= 0.70
            and 0.35 <= center_x <= 0.65
            and center_y >= 0.45
            and contour.rectangularity <= 0.20
        ):
            centrality = max(
                0.0,
                1.0 - math.dist((center_x, center_y), (0.5, 0.62)) / 0.30,
            )
            strength = (
                min(1.0, width / 0.50)
                * min(1.0, height / 0.45)
                * (1.0 - contour.rectangularity / 0.20)
                * centrality
            )
            if 75.0 * strength > arch_score:
                arch_score = 75.0 * strength
                arch_contour = contour
        sampled = contour.points[:: max(1, len(contour.points) // 32)]
        segments = np.diff(np.vstack([sampled, sampled[0]]), axis=0)
        segments = segments[np.linalg.norm(segments, axis=1) > 0.005]
        if len(segments) < 5:
            continue
        angles = np.arctan2(segments[:, 1], segments[:, 0])
        turns = np.abs(
            (np.diff(np.r_[angles, angles[0]]) + np.pi) % (2 * np.pi) - np.pi
        )
        smooth_turns = float(
            np.mean(
                (turns >= np.deg2rad(4.0))
                & (turns <= np.deg2rad(50.0))
            )
        )
        non_rectangular = max(0.0, 1.0 - contour.rectangularity)
        coverage = min(1.0, contour.perimeter / 0.5)
        curved_strength = (
            evidence_weight(CompositionMode.CURVE, "complexity") * smooth_turns
            + evidence_weight(CompositionMode.CURVE, "shape") * non_rectangular
        ) * coverage
        score = min(
            100.0,
            300.0 * curved_strength / (1.0 + straight_line_total),
        )
        if score > best_score:
            best_score, best = score, contour
    if arch_score > best_score:
        best_score, best = arch_score, arch_contour
    return result(
        CompositionMode.CURVE,
        best_score,
        features,
        [
            evidence(
                CompositionEvidenceType.CURVATURE,
                best_score / 100,
                "平滑转向轮廓主导且直线结构较弱",
                contour=[point(float(x), float(y)) for x, y in best.points[:: max(1, len(best.points) // 20)]],
            )
        ] if best else [],
    )


def _convergence(features: CompositionFeatures):
    if not len(features.intersections) or len(features.lines) < 3:
        return 0.0, None
    strongest_lines = sorted(
        features.lines,
        key=lambda line: line.length,
        reverse=True,
    )[:12]
    reference_length = sum(line.length for line in strongest_lines)
    best_strength = 0.0
    best_center = None
    for candidate in features.intersections:
        supporting = [
            line
            for line in features.lines
            if point_line_distance(tuple(candidate), line.tuple) < 0.025
        ]
        if len(supporting) < 3:
            continue
        coverage = min(
            1.0,
            sum(line.length for line in supporting) / max(reference_length, 1e-6),
        )
        angle_bins = {int(line.angle // 15) for line in supporting}
        spread = min(1.0, len(angle_bins) / 4.0)
        strength = coverage * spread
        if strength > best_strength:
            best_strength = strength
            best_center = candidate
    return best_strength, best_center


def _clustered_convergence(features: CompositionFeatures):
    """Conservative convergence used when depth/enclosure semantics are required."""
    if len(features.intersections) < 3 or len(features.lines) < 3:
        return 0.0, None
    center = np.median(features.intersections, axis=0)
    distances = np.linalg.norm(features.intersections - center, axis=1)
    close_ratio = float(np.mean(distances < 0.12))
    angle_bins = {
        int(line.angle // 15)
        for line in features.lines
        if line.length > 0.12
    }
    spread = min(1.0, len(angle_bins) / 4.0)
    return close_ratio * spread, center


def _spoke_alignment(
    features: CompositionFeatures, center: tuple[float, float]
) -> float:
    height, width = features.gradient_magnitude.shape
    yy, xx = np.indices((height, width))
    center_x = center[0] * (width - 1)
    center_y = center[1] * (height - 1)
    radial_angle = (
        np.degrees(np.arctan2(yy - center_y, xx - center_x)) + 360.0
    ) % 180.0
    difference = np.abs(
        ((features.gradient_angle - radial_angle + 90.0) % 180.0) - 90.0
    )
    tangential_gradient = np.sin(np.deg2rad(difference)) ** 2
    magnitude = features.gradient_magnitude
    threshold = float(np.percentile(magnitude, 80))
    radius = np.hypot(xx - center_x, yy - center_y)
    mask = (magnitude > threshold) & (radius > 0.05 * min(width, height))
    if not np.any(mask):
        return 0.0
    alignment = float(
        np.average(tangential_gradient[mask], weights=magnitude[mask])
    )
    position_angle = (
        np.arctan2(yy - center_y, xx - center_x) + 2.0 * np.pi
    ) % (2.0 * np.pi)
    sector_indices = np.floor(position_angle / (2.0 * np.pi) * 12).astype(int)
    aligned_energy = magnitude * tangential_gradient * mask
    sector_energy = np.bincount(
        sector_indices.ravel(),
        weights=aligned_energy.ravel(),
        minlength=12,
    )
    total_energy = float(sector_energy.sum())
    if total_energy <= 0:
        return 0.0
    active_sectors = int(np.count_nonzero(sector_energy >= total_energy * 0.04))
    direction_coverage = min(1.0, max(0.0, (active_sectors - 2) / 8.0))
    return alignment * direction_coverage


def _radial_texture_symmetry(
    features: CompositionFeatures, center: tuple[float, float]
) -> float:
    magnitude = np.asarray(features.gradient_magnitude)
    height, width = magnitude.shape
    yy, xx = np.indices((height, width))
    center_x = center[0] * (width - 1)
    center_y = center[1] * (height - 1)
    radius = np.hypot(xx - center_x, yy - center_y)
    position_angle = (
        np.arctan2(yy - center_y, xx - center_x) + 2.0 * np.pi
    ) % (2.0 * np.pi)
    strong = magnitude > np.percentile(magnitude, 80)
    radial_band = (
        strong
        & (radius > 0.12 * min(height, width))
        & (radius < 0.48 * min(height, width))
    )
    if not np.any(radial_band):
        return 0.0
    sector_indices = np.floor(position_angle / (2.0 * np.pi) * 24).astype(int)
    sector_energy = np.bincount(
        sector_indices[radial_band].ravel(),
        weights=magnitude[radial_band].ravel(),
        minlength=24,
    )
    total_energy = float(sector_energy.sum())
    if total_energy <= 0:
        return 0.0
    active_sectors = int(np.count_nonzero(sector_energy >= total_energy * 0.025))
    sector_coverage = float(np.clip((active_sectors - 14) / 8.0, 0.0, 1.0))
    normalized_radius = np.minimum(
        (radius / (0.5 * min(height, width)) * 20).astype(int),
        19,
    )
    ring_energy = np.bincount(
        normalized_radius.ravel(),
        weights=(magnitude * strong).ravel(),
        minlength=20,
    )
    ring_peaks = (
        int(np.count_nonzero(ring_energy > ring_energy.max() * 0.35))
        if ring_energy.max() > 0
        else 20
    )
    ring_simplicity = float(np.clip((7 - ring_peaks) / 6.0, 0.0, 1.0))
    return sector_coverage * ring_simplicity


def _radial_and_centripetal(features: CompositionFeatures):
    convergence, center = _convergence(features)
    candidate_centers = [(0.5, 0.5)]
    if center is not None and math.dist((0.5, 0.5), center) <= 0.2:
        candidate_centers.append((float(center[0]), float(center[1])))
    radial_center, radial_strength = max(
        (
            (
                candidate,
                max(
                    _spoke_alignment(features, candidate),
                    0.68 * _radial_texture_symmetry(features, candidate),
                ),
            )
            for candidate in candidate_centers
        ),
        key=lambda item: item[1],
    )
    radial_strength *= evidence_weight(CompositionMode.RADIAL, "convergence")
    radial_score = radial_strength * 100
    radial = result(
        CompositionMode.RADIAL,
        radial_score,
        features,
        [
            evidence(
                CompositionEvidenceType.VANISHING_POINT,
                radial_strength,
                "多方向边缘围绕共同中心呈辐射排列",
                points=[point(*radial_center)],
                lines=[normalized_line(line) for line in features.lines[:6]],
            )
        ] if radial_strength else [],
    )
    focus_alignment = 0.0
    focus = features.primary_focus
    if center is not None and focus is not None:
        focus_alignment = max(0.0, 1.0 - math.dist((focus.x, focus.y), center) / 0.25)
    centripetal_strength = convergence * (
        evidence_weight(CompositionMode.CENTRIPETAL, "convergence")
        + evidence_weight(CompositionMode.CENTRIPETAL, "focus") * max(focus_alignment, 0.45)
    )
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


def _line_position_regularity(positions: list[float]) -> float:
    if len(positions) < 2:
        return 0.0
    clustered: list[float] = []
    for value in sorted(positions):
        if not clustered or abs(value - clustered[-1]) > 0.04:
            clustered.append(value)
        else:
            clustered[-1] = (clustered[-1] + value) / 2.0
    if len(clustered) < 3:
        return len(clustered) / 3.0
    spacings = np.diff(np.asarray(clustered, dtype=np.float32))
    mean_spacing = float(np.mean(spacings))
    if mean_spacing <= 0:
        return 0.0
    spacing_variation = float(np.std(spacings) / mean_spacing)
    repeat_support = min(1.0, len(clustered) / 5.0)
    return repeat_support * float(np.clip(1.0 - spacing_variation / 0.75, 0.0, 1.0))


def _checkerboard(features: CompositionFeatures):
    horizontal = [line for line in features.lines if line.angle <= 10]
    vertical = [line for line in features.lines if line.angle >= 80]
    family_strength = min(len(horizontal), len(vertical)) / 4.0
    intersection_strength = min(
        1.0,
        len(horizontal) * len(vertical) / 12.0,
    )
    horizontal_regularity = _line_position_regularity(
        [(line.y1 + line.y2) / 2.0 for line in horizontal]
    )
    vertical_regularity = _line_position_regularity(
        [(line.x1 + line.x2) / 2.0 for line in vertical]
    )
    grid_regularity = max(0.55, math.sqrt(horizontal_regularity * vertical_regularity))
    strength = (
        min(1.0, family_strength) * evidence_weight(CompositionMode.CHECKERBOARD, "families")
        + intersection_strength * evidence_weight(CompositionMode.CHECKERBOARD, "intersections")
    ) * grid_regularity
    if len(horizontal) < 3 or len(vertical) < 3:
        strength *= evidence_weight(CompositionMode.CHECKERBOARD, "sparse")
    magnitude = np.asarray(features.gradient_magnitude)
    angles = np.asarray(features.gradient_angle) % 180.0
    strong = magnitude > np.percentile(magnitude, 80)
    total_energy = float(magnitude[strong].sum())
    gradient_fallback = 0.0
    if total_energy:
        vertical_energy = float(
            magnitude[strong & ((angles <= 10) | (angles >= 170))].sum()
        ) / total_energy
        horizontal_energy = float(
            magnitude[strong & (np.abs(angles - 90) <= 10)].sum()
        ) / total_energy
        if vertical_energy >= horizontal_energy * 1.15:
            gradient_fallback = 0.75 * min(1.0, vertical_energy / 0.15) * min(
                1.0,
                horizontal_energy / 0.03,
            )
    strength = max(strength, gradient_fallback)
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
        ] if (horizontal and vertical) or gradient_fallback else [],
    )


def _frame_and_tunnel(features: CompositionFeatures):
    focus = features.primary_focus
    convergence, convergence_center = _clustered_convergence(features)
    gray = np.asarray(features.gray, dtype=np.float32)
    height, width = gray.shape
    center_y, center_x = int(0.30 * height), int(0.30 * width)
    center = gray[center_y : height - center_y, center_x : width - center_x]
    border_y, border_x = int(0.22 * height), int(0.22 * width)
    border_mask = np.ones_like(gray, dtype=bool)
    border_mask[border_y : height - border_y, border_x : width - border_x] = False
    border = gray[border_mask]
    center_texture = min(1.0, float(center.std()) / 45.0)
    center_non_blank = min(1.0, (1.0 - float(np.mean(center > 150))) / 0.25)
    tonal_enclosure = min(
        1.0, abs(float(center.mean()) - float(border.mean())) / 35.0
    )
    scene_frame_strength = min(
        center_texture, center_non_blank, tonal_enclosure
    )
    edge_map = np.asarray(features.edges)
    center_edges = edge_map[
        center_y : height - center_y,
        center_x : width - center_x,
    ]
    border_edges = edge_map[border_mask]
    center_edge_density = float(np.count_nonzero(center_edges)) / max(
        1,
        center_edges.size,
    )
    border_edge_density = float(np.count_nonzero(border_edges)) / max(
        1,
        border_edges.size,
    )
    low_border_clutter = float(np.clip(1.0 - border_edge_density / 0.12, 0.0, 1.0))
    interior_structure = min(1.0, center_edge_density / 0.05)
    scene_depth_strength = low_border_clutter * interior_structure
    spatial_convergence, _ = _convergence(features)
    if (
        float(center.mean()) > float(border.mean()) + 30.0
        and spatial_convergence < 0.35
    ):
        scene_depth_strength = 0.0
    enclosing = []
    for contour in features.contours:
        if contour.rectangularity < 0.35 or contour.area < 0.08:
            continue
        if focus is None or point_within_polygon((focus.x, focus.y), contour.points):
            enclosing.append(contour)
    enclosure_strength = (
        min(1.0, max((item.area for item in enclosing), default=0.0) / 0.25)
        * evidence_weight(CompositionMode.FRAME_WITHIN_FRAME, "enclosure")
    )
    focus_support = min(1.0, (focus.weight if focus else 0.0) / 0.2)
    enclosure_strength *= focus_support
    convergence_strength = (
        convergence * evidence_weight(CompositionMode.FRAME_WITHIN_FRAME, "enclosure")
    )
    explicit_subject = bool(
        focus is not None and focus.source == "subject" and focus.weight >= 0.5
    )
    interior_support = 1.0 if explicit_subject else min(
        center_texture, center_non_blank
    )
    structural_strength = max(enclosure_strength, convergence_strength)
    frame_strength = max(
        scene_frame_strength,
        structural_strength * interior_support,
    )
    frame_evidence = []
    if frame_strength:
        if enclosure_strength >= convergence_strength and enclosing:
            frame_evidence.append(
                evidence(
                    CompositionEvidenceType.CONTOUR,
                    frame_strength,
                    "边界包围内部焦点",
                    contour=[
                        point(float(x), float(y))
                        for x, y in enclosing[0].points[
                            :: max(1, len(enclosing[0].points) // 12)
                        ]
                    ],
                )
            )
        elif frame_strength == scene_frame_strength:
            frame_evidence.append(
                evidence(
                    CompositionEvidenceType.VISUAL_MASS,
                    frame_strength,
                    "外缘明暗边界围出具有细节的内部场景",
                    points=[point(0.3, 0.3), point(0.7, 0.7)],
                )
            )
        elif convergence_center is not None:
            frame_evidence.append(
                evidence(
                    CompositionEvidenceType.VANISHING_POINT,
                    frame_strength,
                    "周边空间结构围合内部视点",
                    points=[
                        point(
                            float(convergence_center[0]),
                            float(convergence_center[1]),
                        )
                    ],
                )
            )
    frame = result(
        CompositionMode.FRAME_WITHIN_FRAME,
        frame_strength * 100,
        features,
        frame_evidence,
    )
    distinct_levels = []
    for item in sorted(enclosing, key=lambda value: value.area, reverse=True):
        if not distinct_levels or item.area / distinct_levels[-1].area < 0.82:
            distinct_levels.append(item)
    max_depth = max((item.depth for item in distinct_levels), default=0)
    nesting_strength = (
        min(1.0, max_depth / 3.0)
        * evidence_weight(CompositionMode.TUNNEL, "depth")
        * min(1.0, max(0, len(distinct_levels) - 1) / 3.0)
        * evidence_weight(CompositionMode.TUNNEL, "nesting")
    )
    convergence_depth = convergence * evidence_weight(CompositionMode.TUNNEL, "depth")
    tunnel_strength = max(
        nesting_strength,
        convergence_depth,
        scene_depth_strength,
    )
    tunnel_evidence = []
    if tunnel_strength:
        if nesting_strength >= convergence_depth and distinct_levels:
            tunnel_evidence.append(
                evidence(
                    CompositionEvidenceType.NESTED_CONTOUR,
                    tunnel_strength,
                    "重复嵌套边界形成纵深通道",
                    contour=[
                        point(float(x), float(y))
                        for item in distinct_levels[:3]
                        for x, y in item.points[
                            :: max(1, len(item.points) // 8)
                        ]
                    ],
                )
            )
        elif (
            scene_depth_strength >= convergence_depth
            and scene_depth_strength >= nesting_strength
        ):
            tunnel_evidence.append(
                evidence(
                    CompositionEvidenceType.VISUAL_MASS,
                    tunnel_strength,
                    "低干扰外缘围绕具有连续细节的内部通道",
                    points=[point(0.3, 0.3), point(0.7, 0.7)],
                )
            )
        elif convergence_center is not None:
            tunnel_evidence.append(
                evidence(
                    CompositionEvidenceType.VANISHING_POINT,
                    tunnel_strength,
                    "透视线向通道深处收束",
                    points=[
                        point(
                            float(convergence_center[0]),
                            float(convergence_center[1]),
                        )
                    ],
                    lines=[normalized_line(line) for line in features.lines[:6]],
                )
            )
    tunnel = result(
        CompositionMode.TUNNEL,
        tunnel_strength * 100,
        features,
        tunnel_evidence,
    )
    return tunnel, frame


def score_topology_modes(features: CompositionFeatures):
    radial, centripetal = _radial_and_centripetal(features)
    tunnel, frame = _frame_and_tunnel(features)
    return [_curve(features), radial, _checkerboard(features), centripetal, tunnel, frame]
