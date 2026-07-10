from pathlib import Path

import cv2
import numpy as np

from src.core.composition.extractor import CompositionFeatureExtractor
from src.core.composition.scorers.linear import score_linear_modes
from src.core.entities import CompositionMode
from tests.fixtures.composition.factory import add_noise, line_image


def scores(frame):
    features = CompositionFeatureExtractor().extract(frame, [], None)
    return {item.mode: item for item in score_linear_modes(features)}


def test_horizontal_and_vertical_are_distinguished():
    horizontal = scores(line_image((0,)))
    vertical = scores(line_image((90,)))
    assert horizontal[CompositionMode.HORIZONTAL].match_score > horizontal[CompositionMode.VERTICAL].match_score
    assert vertical[CompositionMode.VERTICAL].match_score > vertical[CompositionMode.HORIZONTAL].match_score


def test_diagonal_requires_corner_spanning_direction():
    diagonal = scores(line_image((36,)))
    oblique = scores(line_image((20,)))
    assert diagonal[CompositionMode.DIAGONAL].match_score > oblique[CompositionMode.DIAGONAL].match_score
    assert oblique[CompositionMode.OBLIQUE].match_score > oblique[CompositionMode.DIAGONAL].match_score


def test_diagonal_uses_repeated_short_directional_edges_as_fallback():
    diagonal = np.zeros((240, 320, 3), dtype=np.uint8)
    horizontal = np.zeros_like(diagonal)
    for x, y in ((35, 45), (90, 70), (150, 120), (215, 155), (265, 190)):
        cv2.line(diagonal, (x, y), (x + 24, y + 18), (255, 255, 255), 3)
        cv2.line(horizontal, (x, y), (x + 30, y), (255, 255, 255), 3)

    diagonal_score = scores(diagonal)[CompositionMode.DIAGONAL]
    horizontal_score = scores(horizontal)[CompositionMode.DIAGONAL]

    assert diagonal_score.match_score >= 20
    assert diagonal_score.match_score > horizontal_score.match_score


def test_cross_requires_both_axis_families():
    cross = scores(line_image((0, 90)))
    horizontal = scores(line_image((0,)))
    assert cross[CompositionMode.CROSS].match_score > horizontal[CompositionMode.CROSS].match_score


def test_cross_recognizes_connected_orthogonal_arms_not_a_solid_rectangle():
    cross_shape = line_image(tuple())
    rectangle = line_image(tuple())
    cv2.rectangle(cross_shape, (140, 35), (180, 205), (255, 255, 255), -1)
    cv2.rectangle(cross_shape, (70, 100), (250, 140), (255, 255, 255), -1)
    cv2.rectangle(rectangle, (70, 35), (250, 205), (255, 255, 255), -1)

    cross_score = scores(cross_shape)[CompositionMode.CROSS]
    rectangle_score = scores(rectangle)[CompositionMode.CROSS]

    assert cross_score.match_score >= 50
    assert rectangle_score.match_score < cross_score.match_score


def test_cross_recognizes_disconnected_tonal_arms_in_real_fixture():
    fixture = (
        Path(__file__).parents[3]
        / "fixtures/composition/images/real_candidates"
        / "commons-triangle-negative-19.jpg"
    )
    frame = cv2.imread(str(fixture))

    cross_score = scores(frame)[CompositionMode.CROSS]

    assert cross_score.match_score >= 50


def test_horizontal_recognizes_broad_landscape_bands_without_hough_lines():
    fixtures = Path(__file__).parents[3] / "fixtures/composition/images/real_candidates"
    landscape = cv2.imread(str(fixtures / "commons-horizontal-photo-positive-00.jpg"))
    bridge = cv2.imread(str(fixtures / "commons-horizontal-negative-12.jpg"))

    landscape_score = scores(landscape)[CompositionMode.HORIZONTAL]
    bridge_score = scores(bridge)[CompositionMode.HORIZONTAL]

    assert landscape_score.match_score >= 65
    assert landscape_score.match_score > bridge_score.match_score


def test_texture_noise_does_not_form_strong_linear_composition():
    noisy = scores(add_noise(line_image(tuple()), amount=80))
    assert max(item.match_score for item in noisy.values()) < 65
