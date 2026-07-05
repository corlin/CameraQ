"""Small deterministic BGR fixtures used by composition tests."""

from __future__ import annotations

import cv2
import numpy as np


def canvas(width: int = 320, height: int = 240, value: int = 0) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


def line_image(
    angles: tuple[float, ...], width: int = 320, height: int = 240, thickness: int = 4
) -> np.ndarray:
    image = canvas(width, height)
    center = np.array([width / 2.0, height / 2.0])
    radius = float(np.hypot(width, height))
    for angle in angles:
        direction = np.array([np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))])
        p1 = tuple(np.round(center - direction * radius).astype(int))
        p2 = tuple(np.round(center + direction * radius).astype(int))
        cv2.line(image, p1, p2, (255, 255, 255), thickness)
    return image


def radial_image(spokes: int = 8, width: int = 320, height: int = 240) -> np.ndarray:
    angles = tuple(np.linspace(0.0, 180.0, spokes, endpoint=False))
    return line_image(angles, width=width, height=height, thickness=3)


def grid_image(rows: int = 5, cols: int = 7, width: int = 320, height: int = 240) -> np.ndarray:
    image = canvas(width, height)
    for x in np.linspace(20, width - 20, cols, dtype=int):
        cv2.line(image, (int(x), 10), (int(x), height - 10), (255, 255, 255), 3)
    for y in np.linspace(20, height - 20, rows, dtype=int):
        cv2.line(image, (10, int(y)), (width - 10, int(y)), (255, 255, 255), 3)
    return image


def nested_rectangles(levels: int = 4, width: int = 320, height: int = 240) -> np.ndarray:
    image = canvas(width, height)
    for inset in np.linspace(10, min(width, height) * 0.35, levels, dtype=int):
        cv2.rectangle(image, (inset, inset), (width - inset, height - inset), (255, 255, 255), 3)
    return image


def triangle_image(width: int = 320, height: int = 240) -> np.ndarray:
    image = canvas(width, height)
    points = np.array([[width // 2, 25], [35, height - 30], [width - 35, height - 30]])
    cv2.polylines(image, [points], True, (255, 255, 255), 4)
    for x, y in points:
        cv2.circle(image, (int(x), int(y)), 9, (255, 255, 255), -1)
    return image


def curve_image(width: int = 320, height: int = 240) -> np.ndarray:
    image = canvas(width, height)
    points = np.array(
        [[10, height - 30], [70, 20], [145, height - 25], [230, 25], [width - 10, height - 35]],
        dtype=np.int32,
    )
    curve = cv2.approxPolyDP(points.reshape(-1, 1, 2), 1.0, False)
    cv2.polylines(image, [curve], False, (255, 255, 255), 5)
    return image


def add_noise(image: np.ndarray, seed: int = 7, amount: int = 30) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.integers(-amount, amount + 1, image.shape, dtype=np.int16)
    return np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
