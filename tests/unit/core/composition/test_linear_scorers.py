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


def test_cross_requires_both_axis_families():
    cross = scores(line_image((0, 90)))
    horizontal = scores(line_image((0,)))
    assert cross[CompositionMode.CROSS].match_score > horizontal[CompositionMode.CROSS].match_score


def test_texture_noise_does_not_form_strong_linear_composition():
    noisy = scores(add_noise(line_image(tuple()), amount=80))
    assert max(item.match_score for item in noisy.values()) < 65
