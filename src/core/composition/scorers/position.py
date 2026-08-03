from __future__ import annotations

import math

import cv2
import numpy as np

from src.core.composition.features import CompositionFeatures
from src.core.composition.thresholds import evidence_weight
from src.core.entities import CompositionEvidenceType, CompositionMode

from .common import evidence, normalized_line, point, result


def _thirds(features: CompositionFeatures):
    focus = features.primary_focus
    nodes = [(x, y) for x in (1 / 3, 2 / 3) for y in (1 / 3, 2 / 3)]
    node = nodes[0]
    node_distance = float("inf")
    focus_score = 0.0
    if focus is not None:
        node, node_distance = min(
            ((node, math.dist((focus.x, focus.y), node)) for node in nodes),
            key=lambda item: item[1],
        )
        line_distance = min(
            abs(focus.x - 1 / 3),
            abs(focus.x - 2 / 3),
            abs(focus.y - 1 / 3),
            abs(focus.y - 2 / 3),
        )
        focus_score = max(
            100
            * evidence_weight(CompositionMode.RULE_OF_THIRDS, "node")
            * (1 - node_distance / 0.22),
            100
            * evidence_weight(CompositionMode.RULE_OF_THIRDS, "line")
            * (1 - line_distance / 0.18),
        )
        reliability = (
            min(1.0, focus.weight / 0.2)
            if focus.source == "saliency"
            else focus.weight
        )
        focus_score *= reliability
    total_line_length = sum(line.length for line in features.lines)

    def orientation_score(lines, mode: CompositionMode) -> float:
        matching_length = sum(line.length for line in lines)
        if total_line_length <= 0:
            return 0.0
        dominance = matching_length / total_line_length
        coverage = min(1.0, matching_length / 1.4)
        return 100 * (
            dominance * evidence_weight(mode, "dominance")
            + coverage * evidence_weight(mode, "coverage")
        )

    horizontal_lines = [line for line in features.lines if line.angle <= 10]
    vertical_lines = [line for line in features.lines if line.angle >= 80]
    horizontal_score = orientation_score(
        horizontal_lines, CompositionMode.HORIZONTAL
    )
    vertical_score = orientation_score(vertical_lines, CompositionMode.VERTICAL)
    if focus is not None and focus.source == "saliency":
        focus_score *= min(1.0, max(horizontal_score, vertical_score) / 40.0)

    gray = np.asarray(features.gray, dtype=np.uint8)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    vertical_gradient = np.abs(
        cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
    )
    horizontal_gradient = np.abs(
        cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
    )
    gradient_cutoff = max(8.0, float(np.percentile(vertical_gradient, 80)))
    row_strength = vertical_gradient.mean(axis=1)
    row_coverage = (vertical_gradient > gradient_cutoff).mean(axis=1)
    normalized_rows = row_strength / (float(np.percentile(row_strength, 95)) + 1e-6)
    normalized_rows *= np.sqrt(row_coverage)
    third_profiles: list[tuple[float, int]] = []
    for third in (1 / 3, 2 / 3):
        lower = max(0, int((third - 0.10) * len(normalized_rows)))
        upper = min(len(normalized_rows), int((third + 0.10) * len(normalized_rows)) + 1)
        local_index = int(np.argmax(normalized_rows[lower:upper])) + lower
        third_profiles.append((float(normalized_rows[local_index]), local_index))
    best_index = int(third_profiles[1][0] > third_profiles[0][0])
    best_profile, best_row = third_profiles[best_index]
    opposing_profile = third_profiles[1 - best_index][0]
    if best_profile and opposing_profile >= best_profile * 0.6:
        best_profile *= max(0.0, 1.0 - opposing_profile / best_profile)
    profile_support = min(1.0, float(row_coverage[best_row]) / 0.15)
    horizontal_support = max(
        min(1.0, horizontal_score / 40.0), profile_support
    )
    structural_score = min(100.0, 60.0 * best_profile) * horizontal_support
    col_cutoff = max(8.0, float(np.percentile(horizontal_gradient, 80)))
    col_strength = horizontal_gradient.mean(axis=0)
    col_coverage = (horizontal_gradient > col_cutoff).mean(axis=0)
    normalized_cols = col_strength / (float(np.percentile(col_strength, 95)) + 1e-6)
    normalized_cols *= np.sqrt(col_coverage)
    third_col_profiles: list[tuple[float, int]] = []
    for third in (1 / 3, 2 / 3):
        lower = max(0, int((third - 0.10) * len(normalized_cols)))
        upper = min(len(normalized_cols), int((third + 0.10) * len(normalized_cols)) + 1)
        local_index = int(np.argmax(normalized_cols[lower:upper])) + lower
        third_col_profiles.append((float(normalized_cols[local_index]), local_index))
    best_col_index = int(third_col_profiles[1][0] > third_col_profiles[0][0])
    best_col_profile, best_col = third_col_profiles[best_col_index]
    opposing_col_profile = third_col_profiles[1 - best_col_index][0]
    if best_col_profile and opposing_col_profile >= best_col_profile * 0.6:
        best_col_profile *= max(0.0, 1.0 - opposing_col_profile / best_col_profile)
    col_profile_support = min(1.0, float(col_coverage[best_col]) / 0.15)
    vertical_support = max(
        min(1.0, vertical_score / 40.0), col_profile_support
    )
    vertical_structural_score = (
        min(100.0, 68.0 * best_col_profile) * vertical_support
    )
    structural_score = max(structural_score, vertical_structural_score)
    lower_start = int(0.78 * len(normalized_rows))
    lower_stop = max(lower_start + 1, int(0.93 * len(normalized_rows)))
    lower_local = int(np.argmax(normalized_rows[lower_start:lower_stop])) + lower_start
    lower_profile = float(normalized_rows[lower_local])
    upper_edge_density = float(
        np.count_nonzero(features.edges[: int(0.55 * features.edges.shape[0])])
    ) / max(1, features.edges[: int(0.55 * features.edges.shape[0])].size)
    if (
        upper_edge_density < 0.01
        and row_coverage[lower_local] >= 0.55
        and lower_profile >= 0.85
    ):
        structural_score = max(
            structural_score,
            min(100.0, 58.0 * lower_profile),
        )
    centered_enclosure = any(
        0.10 <= contour.area <= 0.60
        and contour.rectangularity >= 0.65
        and math.dist(
            (
                float((contour.points[:, 0].min() + contour.points[:, 0].max()) / 2),
                float((contour.points[:, 1].min() + contour.points[:, 1].max()) / 2),
            ),
            (0.5, 0.5),
        )
        <= 0.15
        for contour in features.contours
    )
    if centered_enclosure:
        structural_score *= 0.25

    histogram, _ = np.histogram(gray, bins=32, range=(0, 256))
    probabilities = histogram[histogram > 0] / histogram.sum()
    entropy = float(-np.sum(probabilities * np.log2(probabilities)))
    texture_reliability = float(np.clip((entropy - 1.5) / 2.0, 0.0, 1.0))
    full_span = max(
        (
            abs(line.x2 - line.x1)
            for line in horizontal_lines
            if min(
                abs((line.y1 + line.y2) / 2 - 1 / 3),
                abs((line.y1 + line.y2) / 2 - 2 / 3),
            )
            <= 0.12
        ),
        default=0.0,
    )
    texture_reliability = max(
        texture_reliability,
        float(np.clip((full_span - 0.7) / 0.2, 0.0, 1.0)),
    )
    if focus is not None and focus.source == "subject":
        texture_reliability = 1.0
    elif focus is not None and focus.source == "saliency":
        salient_anchor_reliability = min(1.0, focus.weight / 0.2) * float(
            np.clip((0.16 - node_distance) / 0.10, 0.0, 1.0)
        )
        texture_reliability = max(
            texture_reliability,
            salient_anchor_reliability,
        )
    score = max(focus_score, structural_score) * texture_reliability
    target_y = best_row / max(1, len(normalized_rows))
    target_x = best_col / max(1, len(normalized_cols))
    if vertical_structural_score > min(100.0, 60.0 * best_profile) * horizontal_support:
        structural_line = min(
            vertical_lines,
            key=lambda line: abs((line.x1 + line.x2) / 2 - target_x),
            default=None,
        )
    else:
        structural_line = min(
            horizontal_lines,
            key=lambda line: abs((line.y1 + line.y2) / 2 - target_y),
            default=None,
        )
    strength = max(0.0, min(1.0, score / 100))
    evidence_items = []
    if focus is not None and focus_score >= structural_score:
        evidence_items.append(
            evidence(
                CompositionEvidenceType.SUBJECT_POSITION,
                strength,
                "主焦点接近三分线/交点",
                points=[point(focus.x, focus.y), point(*node)],
            )
        )
    elif structural_line is not None:
        evidence_items.append(
            evidence(
                CompositionEvidenceType.LINE,
                strength,
                "主结构线接近三分线",
                lines=[normalized_line(structural_line)],
            )
        )
    return result(
        CompositionMode.RULE_OF_THIRDS,
        score,
        features,
        evidence_items,
    )


def _mass_balance_strength(features: CompositionFeatures) -> float:
    cx, cy = features.mass_centroid
    center_distance = math.dist((cx, cy), (0.5, 0.5))
    q1, q2, q3, q4 = features.quadrant_mass
    horizontal_difference = abs((q1 + q3) - (q2 + q4))
    vertical_difference = abs((q1 + q2) - (q3 + q4))
    return (
        evidence_weight(CompositionMode.BALANCED, "centroid")
        * max(0.0, 1.0 - center_distance / 0.5)
        * evidence_weight(CompositionMode.BALANCED, "mass_symmetry")
        * max(0.0, 1.0 - (horizontal_difference + vertical_difference) / 1.2)
    )


def _balance_strength(features: CompositionFeatures) -> float:
    mass_strength = _mass_balance_strength(features)
    if features.primary_focus is not None and features.primary_focus.source == "subject":
        return mass_strength
    gray = np.asarray(features.gray, dtype=np.float32)
    resized = cv2.resize(gray, (96, 96), interpolation=cv2.INTER_AREA)
    contrast = float(resized.std())
    if contrast < 8.0:
        return mass_strength
    normalized = (resized - float(resized.mean())) / (float(resized.std()) + 1e-6)
    mirror_scores = (
        1.0 - float(np.mean(np.abs(normalized - np.fliplr(normalized)))) / 2.0,
        1.0 - float(np.mean(np.abs(normalized - np.flipud(normalized)))) / 2.0,
        1.0
        - float(np.mean(np.abs(normalized - np.flipud(np.fliplr(normalized))))) / 2.0,
    )
    mirror_strength = float(np.clip((max(mirror_scores) - 0.58) / 0.30, 0.0, 1.0))
    edges = np.asarray(features.edges) > 0
    height, width = edges.shape
    center_density = float(
        edges[
            int(0.30 * height) : int(0.70 * height),
            int(0.35 * width) : int(0.65 * width),
        ].mean()
    )
    side_density = float(
        (
            edges[:, : int(0.25 * width)].mean()
            + edges[:, int(0.75 * width) :].mean()
        )
        / 2.0
    )
    top_density = float(edges[: int(0.25 * height), :].mean())
    center_prominence = min(1.0, center_density / max(side_density + 0.025, 1e-6))
    calm_top = float(np.clip((0.035 - top_density) / 0.035, 0.0, 1.0))
    low_line_clutter = float(np.clip((18 - len(features.lines)) / 15.0, 0.0, 1.0))
    quiet_tunnel_strength = center_prominence * calm_top * low_line_clutter
    return max(mass_strength, mirror_strength, quiet_tunnel_strength)


def _balanced(features: CompositionFeatures):
    cx, cy = features.mass_centroid
    score = 100 * _balance_strength(features)
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
    score *= 1.0 - 0.6 * _mass_balance_strength(features)
    fallback_lines: list = []
    if score < 40:
        edges = np.asarray(features.edges) > 0
        height, width = edges.shape
        top_density = float(edges[: int(0.25 * height), :].mean())
        center_density = float(
            edges[
                int(0.30 * height) : int(0.70 * height),
                int(0.35 * width) : int(0.65 * width),
            ].mean()
        )
        side_density = float(
            (
                edges[:, : int(0.25 * width)].mean()
                + edges[:, int(0.75 * width) :].mean()
            )
            / 2.0
        )
        fallback_lines = [
            line
            for line in features.lines
            if 8 <= line.angle <= 28 and (line.y1 + line.y2) / 2 >= 0.40
        ]
        shallow_strength = min(1.0, sum(line.length for line in fallback_lines) / 1.0)
        side_enclosure = min(
            1.0,
            side_density / max(center_density, 0.02),
        )
        calm_canopy = float(np.clip((0.035 - top_density) / 0.035, 0.0, 1.0))
        corridor_strength = shallow_strength * side_enclosure * calm_canopy
        score = max(score, 76.0 * corridor_strength)
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
                lines=[normalized_line(line) for line in (matching or fallback_lines)[:4]],
            )
        ] if matching or fallback_lines else [],
    )


def _triangle(features: CompositionFeatures):
    gray = np.asarray(features.gray, dtype=np.float32)
    height, width = gray.shape
    border_width = max(2, int(0.08 * min(height, width)))
    border = np.concatenate(
        (
            gray[:border_width].ravel(),
            gray[-border_width:].ravel(),
            gray[:, :border_width].ravel(),
            gray[:, -border_width:].ravel(),
        )
    )
    background = float(np.median(border))
    distance = np.abs(gray - background)
    threshold = max(18.0, float(np.percentile(distance, 65)))
    foreground = (distance > threshold).astype(np.uint8) * 255
    foreground = cv2.morphologyEx(
        foreground, cv2.MORPH_OPEN, np.ones((3, 3), dtype=np.uint8)
    )
    raw_contours, _ = cv2.findContours(
        foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    silhouette_strength = 0.0
    largest_solidity = 0.0
    best_triangle = None
    for contour in raw_contours:
        area = float(cv2.contourArea(contour))
        area_ratio = area / (width * height)
        if area_ratio < 0.0005:
            continue
        hull = cv2.convexHull(contour)
        hull_area = float(cv2.contourArea(hull))
        solidity = area / hull_area if hull_area > 0 else 0.0
        if area_ratio >= 0.005:
            largest_solidity = max(largest_solidity, solidity)
        perimeter = float(cv2.arcLength(contour, True))
        approximation = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        if len(approximation) != 3:
            continue
        strength = min(1.0, area_ratio / 0.08) * solidity
        if strength > silhouette_strength:
            silhouette_strength = strength
            best_triangle = approximation.reshape(-1, 2).astype(np.float32)

    total_line_length = sum(line.length for line in features.lines)
    oblique_length = sum(
        line.length for line in features.lines if 12 <= line.angle <= 78
    )
    oblique_strength = 0.0
    if total_line_length > 0:
        oblique_strength = (
            oblique_length
            / total_line_length
            * evidence_weight(CompositionMode.OBLIQUE, "dominance")
            + min(1.0, oblique_length / 1.4)
            * evidence_weight(CompositionMode.OBLIQUE, "coverage")
        )
    structure_strength = oblique_strength * largest_solidity
    strength = max(silhouette_strength, structure_strength)

    # Line-triangle: 3 oblique lines whose pairwise intersections form a
    # closed triangle.  Requires meaningful line lengths and a central,
    # well-proportioned triangle — avoids the false-positive problem of
    # the earlier intersection-exhaustive approach.
    line_triangle_strength = 0.0
    line_triangle_pts = None
    oblique_lines = [
        line for line in features.lines
        if 15 <= line.angle <= 75 and line.length >= 0.18
    ]
    if len(oblique_lines) >= 3:
        # Build intersection map for oblique lines only
        line_intersections: dict[int, list[tuple[int, tuple[float, float]]]] = {}
        for i, li in enumerate(oblique_lines):
            for j, lj in enumerate(oblique_lines):
                if j <= i:
                    continue
                    # compute line-line intersection
                x1, y1, x2, y2 = li.x1, li.y1, li.x2, li.y2
                x3, y3, x4, y4 = lj.x1, lj.y1, lj.x2, lj.y2
                denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
                if abs(denom) < 1e-9:
                    continue
                px = ((x1*y2 - y1*x2)*(x3 - x4) - (x1 - x2)*(x3*y4 - y3*x4)) / denom
                py = ((x1*y2 - y1*x2)*(y3 - y4) - (y1 - y2)*(x3*y4 - y3*x4)) / denom
                if not (0.05 <= px <= 0.95 and 0.05 <= py <= 0.95):
                    continue
                line_intersections.setdefault(i, []).append((j, (px, py)))
                line_intersections.setdefault(j, []).append((i, (px, py)))

        # Find triplets (i,j,k) where each pair has an intersection
        for i in line_intersections:
            for j_entry in line_intersections[i]:
                j = j_entry[0]
                if j <= i:
                    continue
                for k_entry in line_intersections[i]:
                    k = k_entry[0]
                    if k <= j:
                        continue
                    # Check j-k intersection exists
                    jk_found = any(e[0] == k for e in line_intersections.get(j, []))
                    if not jk_found:
                        continue
                    # Get the 3 intersection points
                    p_ij = j_entry[1]
                    p_ik = k_entry[1]
                    p_jk = next(e[1] for e in line_intersections[j] if e[0] == k)
                    # Triangle area
                    a = math.dist(p_ij, p_ik)
                    b = math.dist(p_ik, p_jk)
                    c = math.dist(p_jk, p_ij)
                    s = (a + b + c) / 2
                    area = max(0.0, s * (s - a) * (s - b) * (s - c)) ** 0.5
                    if not (0.03 <= area <= 0.22):
                        continue
                    # Centrality
                    cx = (p_ij[0] + p_ik[0] + p_jk[0]) / 3
                    cy = (p_ij[1] + p_ik[1] + p_jk[1]) / 3
                    centrality = max(0.0, 1.0 - math.dist((cx, cy), (0.5, 0.5)) / 0.28)
                    if centrality < 0.3:
                        continue
                    # Line quality: average length of the 3 lines
                    avg_len = (oblique_lines[i].length + oblique_lines[j].length + oblique_lines[k].length) / 3
                    line_quality = min(1.0, avg_len / 0.40)
                    # Shape: avoid degenerate (too thin) triangles
                    shape_ok = min(a, min(b, c)) / max(a, max(b, c)) >= 0.25
                    if not shape_ok:
                        continue
                    candidate = area * centrality * line_quality * 4.0
                    if candidate > line_triangle_strength:
                        line_triangle_strength = candidate
                        line_triangle_pts = (
                            (p_ij[0] * width, p_ij[1] * height),
                            (p_ik[0] * width, p_ik[1] * height),
                            (p_jk[0] * width, p_jk[1] * height),
                        )

    if line_triangle_strength > strength:
        strength = line_triangle_strength
        best_triangle = np.array(line_triangle_pts, dtype=np.float32)

    score = (
        100.0
        * evidence_weight(CompositionMode.TRIANGLE, "area")
        * strength
    )
    if best_triangle is not None:
        best_triangle[:, 0] /= width
        best_triangle[:, 1] /= height
        evidence_points = best_triangle
    else:
        evidence_points = np.asarray(features.corners[:3], dtype=np.float32)
    return result(
        CompositionMode.TRIANGLE,
        score,
        features,
        [
            evidence(
                CompositionEvidenceType.CONTOUR,
                score / 100,
                "闭合三边轮廓或斜线结构形成稳定三角关系",
                contour=[
                    point(float(item[0]), float(item[1]))
                    for item in evidence_points
                ],
            )
        ] if len(evidence_points) >= 3 and score >= 20 else [],
    )


def score_position_modes(features: CompositionFeatures):
    return [_thirds(features), _dynamic_symmetry(features), _balanced(features), _triangle(features)]
