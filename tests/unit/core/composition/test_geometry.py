import numpy as np

from src.core.composition.geometry import (
    angle_degrees,
    line_intersection,
    normalize_point,
    orientation_histogram,
    point_line_distance,
    point_within_polygon,
)


def test_normalize_point_uses_frame_dimensions():
    assert normalize_point((160, 120), width=320, height=240) == (0.5, 0.5)


def test_angle_degrees_is_undirected():
    assert angle_degrees((0, 0, 10, 0)) == 0
    assert angle_degrees((0, 0, 0, 10)) == 90
    assert angle_degrees((10, 10, 0, 0)) == 45


def test_line_intersection_rejects_parallel_and_out_of_bounds():
    assert line_intersection((0, 0, 10, 10), (0, 10, 10, 0), bounds=(10, 10)) == (5.0, 5.0)
    assert line_intersection((0, 0, 10, 0), (0, 1, 10, 1), bounds=(10, 10)) is None
    assert line_intersection((0, 0, 1, 0), (2, -1, 2, 1), bounds=(1, 1)) is None


def test_point_line_distance_is_normalized_by_line_length():
    assert point_line_distance((5, 5), (0, 0, 10, 0)) == 5


def test_orientation_histogram_weights_long_lines_more():
    lines = np.array([[0, 0, 100, 0], [0, 0, 0, 10]], dtype=float)
    hist = orientation_histogram(lines, bins=18)
    assert hist[0] > hist[9]
    assert np.isclose(hist.sum(), 1.0)


def test_point_within_polygon_handles_rectangles():
    polygon = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float32)
    assert point_within_polygon((5, 5), polygon)
    assert not point_within_polygon((20, 20), polygon)
