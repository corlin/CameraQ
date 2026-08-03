from __future__ import annotations

import math

import cv2
import numpy as np

from src.core.composition.features import CompositionFeatures, LineFeature
from src.core.composition.thresholds import evidence_weight
from src.core.entities import CompositionEvidenceType, CompositionMode

from .common import evidence, normalized_line, point, result


def _cross_silhouette_strength(gray: np.ndarray) -> tuple[float, tuple[float, float] | None]:
    blurred = cv2.GaussianBlur(np.asarray(gray), (5, 5), 0)
    _, binary = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )
    height, width = binary.shape
    image_area = height * width
    best_strength = 0.0
    best_center = None
    for mask in (binary, cv2.bitwise_not(binary)):
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        for contour in contours:
            area_ratio = cv2.contourArea(contour) / image_area
            if not 0.015 <= area_ratio <= 0.6:
                continue
            x, y, box_width, box_height = cv2.boundingRect(contour)
            if box_width < 0.15 * width or box_height < 0.15 * height:
                continue
            center_x = (x + box_width / 2.0) / width
            center_y = (y + box_height / 2.0) / height
            centrality = max(
                0.0,
                1.0 - math.dist((center_x, center_y), (0.5, 0.5)) / 0.35,
            )
            if not centrality:
                continue
            component = np.zeros_like(mask)
            cv2.drawContours(component, [contour], -1, 1, thickness=-1)
            crop = component[y : y + box_height, x : x + box_width]
            vertical_start = int(0.4 * box_width)
            vertical_end = max(vertical_start + 1, int(0.6 * box_width))
            horizontal_start = int(0.4 * box_height)
            horizontal_end = max(horizontal_start + 1, int(0.6 * box_height))
            vertical = float(
                crop[:, vertical_start:vertical_end].mean()
            )
            horizontal = float(
                crop[horizontal_start:horizontal_end, :].mean()
            )
            corner_height = max(1, int(0.28 * box_height))
            corner_width = max(1, int(0.28 * box_width))
            corners = np.concatenate(
                [
                    crop[:corner_height, :corner_width].ravel(),
                    crop[:corner_height, -corner_width:].ravel(),
                    crop[-corner_height:, :corner_width].ravel(),
                    crop[-corner_height:, -corner_width:].ravel(),
                ]
            )
            corner_penalty = float(corners.mean())
            strength = min(vertical, horizontal) * (1.0 - corner_penalty) * centrality
            if strength > best_strength:
                best_strength = strength
                best_center = (center_x, center_y)
    normalized = cv2.resize(blurred, (100, 100), interpolation=cv2.INTER_AREA)
    best_contrast = 0.0
    for lower, upper in ((0.15, 0.85), (0.25, 0.75), (0.30, 0.70)):
        start = int(lower * 100)
        end = int(upper * 100)
        span = end - start
        arm_half_width = max(2, int(0.18 * span))
        plus_mask = np.zeros((100, 100), dtype=bool)
        plus_mask[start:end, 50 - arm_half_width : 50 + arm_half_width] = True
        plus_mask[50 - arm_half_width : 50 + arm_half_width, start:end] = True
        corner_mask = np.zeros_like(plus_mask)
        corner_size = int(0.28 * span)
        corner_mask[start : start + corner_size, start : start + corner_size] = True
        corner_mask[start : start + corner_size, end - corner_size : end] = True
        corner_mask[end - corner_size : end, start : start + corner_size] = True
        corner_mask[end - corner_size : end, end - corner_size : end] = True
        contrast = abs(
            float(normalized[plus_mask].mean())
            - float(normalized[corner_mask].mean())
        ) / 255.0
        best_contrast = max(best_contrast, contrast)
    tonal_strength = min(1.0, best_contrast / 0.33)
    if tonal_strength > best_strength:
        best_strength = tonal_strength
        best_center = (0.5, 0.5)
    return best_strength, best_center


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


def _horizontal_band_strength(features: CompositionFeatures) -> float:
    gradient_angles = np.asarray(features.gradient_angle) % 180.0
    gradient_magnitude = np.asarray(features.gradient_magnitude)
    strong = gradient_magnitude > np.percentile(gradient_magnitude, 80)
    if not np.any(strong):
        return 0.0
    horizontal_normal = np.minimum(
        np.abs(gradient_angles - 90.0),
        180.0 - np.abs(gradient_angles - 90.0),
    )
    vertical_normal = np.minimum(np.abs(gradient_angles), 180.0 - np.abs(gradient_angles))
    horizontal_energy = float(
        gradient_magnitude[strong & (horizontal_normal <= 12.0)].sum()
    )
    vertical_energy = float(
        gradient_magnitude[strong & (vertical_normal <= 12.0)].sum()
    )
    energy_ratio = horizontal_energy / max(vertical_energy, 1e-6)
    gray = np.asarray(features.gray, dtype=np.uint8)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    row_gradient = np.abs(cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3))
    row_strength = row_gradient.mean(axis=1)
    cutoff = max(8.0, float(np.percentile(row_gradient, 80)))
    row_coverage = (row_gradient > cutoff).mean(axis=1)
    normalized_rows = row_strength / (float(np.percentile(row_strength, 95)) + 1e-6)
    normalized_rows *= np.sqrt(row_coverage)
    band_peak = float(np.percentile(normalized_rows, 95))
    band_span = float(np.mean(normalized_rows > 0.35))
    return (
        float(np.clip((energy_ratio - 1.35) / 1.2, 0.0, 1.0))
        * min(1.0, band_peak / 0.62)
        * min(1.0, band_span / 0.20)
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
    gradient_angles = np.asarray(features.gradient_angle) % 180.0
    gradient_magnitude = np.asarray(features.gradient_magnitude)
    strong_gradient = gradient_magnitude > np.percentile(gradient_magnitude, 80)
    normal_targets = (90.0 - diagonal_angle, 90.0 + diagonal_angle)
    differences = [
        np.minimum(
            np.abs(gradient_angles - target),
            180.0 - np.abs(gradient_angles - target),
        )
        for target in normal_targets
    ]
    diagonal_gradient = strong_gradient & (np.minimum(*differences) <= 10.0)
    total_gradient = float(gradient_magnitude[strong_gradient].sum())
    gradient_strength = (
        float(gradient_magnitude[diagonal_gradient].sum()) / total_gradient
        if total_gradient
        else 0.0
    )
    gradient_score = 100.0 * gradient_strength
    if gradient_score > diagonal.match_score:
        representative = LineFeature(
            x1=0.05,
            y1=0.05,
            x2=0.95,
            y2=0.95,
            angle=diagonal_angle,
            length=1.0,
        )
        diagonal = result(
            CompositionMode.DIAGONAL,
            gradient_score,
            features,
            [
                evidence(
                    CompositionEvidenceType.LINE,
                    gradient_strength,
                    "短边缘在画面中重复形成对角主方向",
                    lines=[normalized_line(representative)],
                )
            ],
        )
    oblique = _mode(
        features,
        CompositionMode.OBLIQUE,
        lambda line: 12 <= line.angle <= 78 and abs(line.angle - diagonal_angle) > 8,
        "倾斜主方向形成动势",
    )
    band_strength = _horizontal_band_strength(features)
    if (
        band_strength
        and oblique.match_score <= horizontal.match_score
        and vertical.match_score <= horizontal.match_score + 15
    ):
        band_score = 75.0 * band_strength
        if band_score > horizontal.match_score:
            representative = LineFeature(
                x1=0.05,
                y1=0.50,
                x2=0.95,
                y2=0.50,
                angle=0.0,
                length=0.9,
            )
            horizontal = result(
                CompositionMode.HORIZONTAL,
                band_score,
                features,
                [
                    evidence(
                        CompositionEvidenceType.LINE,
                        band_strength,
                        "宽幅水平层带主导画面",
                        lines=[normalized_line(representative)],
                    )
                ],
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
    silhouette_strength, silhouette_center = _cross_silhouette_strength(features.gray)
    # Silhouette fallback: strong cross patterns (≥0.4) pass through at
    # full strength; weaker ones are scaled down to suppress noise.
    silhouette_contribution = (
        silhouette_strength if silhouette_strength >= 0.40
        else silhouette_strength * 0.35
    )
    # Gradient-based cross: two perpendicular dominant gradient directions
    # with similar energy, concentrated near center.
    gradient_cross = 0.0
    gradient_angles = np.asarray(features.gradient_angle) % 180.0
    gradient_magnitude = np.asarray(features.gradient_magnitude)
    strong = gradient_magnitude > np.percentile(gradient_magnitude, 75)
    if np.any(strong):
        vertical_mask = strong & ((gradient_angles <= 10) | (gradient_angles >= 170))
        horizontal_mask = strong & (np.abs(gradient_angles - 90) <= 10)
        v_energy = float(gradient_magnitude[vertical_mask].sum())
        h_energy = float(gradient_magnitude[horizontal_mask].sum())
        total_energy = float(gradient_magnitude[strong].sum())
        if total_energy > 0 and v_energy > 0 and h_energy > 0:
            # Both directions must have significant presence
            balance = min(v_energy, h_energy) / max(v_energy, h_energy)
            combined = (v_energy + h_energy) / total_energy
            gradient_cross = combined * balance * 0.65
    cross_strength = max(cross_strength, silhouette_contribution, gradient_cross)
    cross = result(
        CompositionMode.CROSS,
        cross_strength * 100,
        features,
        [
            evidence(
                CompositionEvidenceType.LINE_INTERSECTION,
                cross_strength,
                "主水平与垂直结构形成交叉",
                points=(
                    [point(*silhouette_center)]
                    if silhouette_contribution >= cross_strength * 0.9
                    and silhouette_center is not None
                    else [
                        point(float(value[0]), float(value[1]))
                        for value in intersections[:3]
                    ]
                ),
                lines=[normalized_line(line) for line in (h_lines[:2] + v_lines[:2])],
            )
        ] if (h_lines and v_lines) or (silhouette_contribution > 0.15 and silhouette_center is not None) else [],
    )
    return [diagonal, horizontal, oblique, cross, vertical]
