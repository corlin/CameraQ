from __future__ import annotations

import cv2
import numpy as np


def normalize_point(point: tuple[float, float], width: int, height: int) -> tuple[float, float]:
    if width <= 0 or height <= 0:
        raise ValueError("dimensions must be positive")
    return float(point[0]) / width, float(point[1]) / height


def angle_degrees(line: tuple[float, float, float, float]) -> float:
    x1, y1, x2, y2 = line
    angle = abs(float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))) % 180.0
    return min(angle, 180.0 - angle)


def line_intersection(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
    bounds: tuple[float, float] | None = None,
) -> tuple[float, float] | None:
    x1, y1, x2, y2 = first
    x3, y3, x4, y4 = second
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denominator) < 1e-8:
        return None
    determinant1 = x1 * y2 - y1 * x2
    determinant2 = x3 * y4 - y3 * x4
    px = (determinant1 * (x3 - x4) - (x1 - x2) * determinant2) / denominator
    py = (determinant1 * (y3 - y4) - (y1 - y2) * determinant2) / denominator
    if bounds and not (0 <= px <= bounds[0] and 0 <= py <= bounds[1]):
        return None
    return round(float(px), 6), round(float(py), 6)


def point_line_distance(
    point: tuple[float, float], line: tuple[float, float, float, float]
) -> float:
    px, py = point
    x1, y1, x2, y2 = line
    denominator = float(np.hypot(x2 - x1, y2 - y1))
    if denominator == 0:
        return float(np.hypot(px - x1, py - y1))
    return abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1) / denominator


def orientation_histogram(lines: np.ndarray, bins: int = 18) -> np.ndarray:
    histogram = np.zeros(bins, dtype=np.float32)
    if lines.size == 0:
        return histogram
    for x1, y1, x2, y2 in np.asarray(lines, dtype=float).reshape(-1, 4):
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180.0
        index = min(int(angle / 180.0 * bins), bins - 1)
        histogram[index] += float(np.hypot(x2 - x1, y2 - y1))
    total = float(histogram.sum())
    if total:
        histogram /= total
    return histogram


def point_within_polygon(point: tuple[float, float], polygon: np.ndarray) -> bool:
    return cv2.pointPolygonTest(np.asarray(polygon, dtype=np.float32), point, False) >= 0
