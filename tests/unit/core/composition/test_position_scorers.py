import numpy as np

from src.core.composition.extractor import CompositionFeatureExtractor
from src.core.composition.scorers.position import score_position_modes
from src.core.entities import BoundingBox, CompositionMode, FusedSubject, SourceType
from tests.fixtures.composition.factory import line_image, triangle_image


def subject_at(x: float, y: float, size: float = 30) -> FusedSubject:
    return FusedSubject(
        subject_id="s",
        class_name="person",
        confidence=0.95,
        bounding_box=BoundingBox(x=x - size / 2, y=y - size / 2, width=size, height=size),
        is_primary_subject=True,
        source=SourceType.YOLO,
    )


def scores(frame, subjects):
    features = CompositionFeatureExtractor().extract(frame, subjects, None)
    return {item.mode: item for item in score_position_modes(features)}


def test_rule_of_thirds_prefers_third_intersection_over_arbitrary_position():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    thirds = scores(frame, [subject_at(320 / 3, 240 / 3)])[CompositionMode.RULE_OF_THIRDS]
    arbitrary = scores(frame, [subject_at(0.47 * 320, 0.42 * 240)])[CompositionMode.RULE_OF_THIRDS]
    assert thirds.match_score >= 70
    assert thirds.match_score > arbitrary.match_score


def test_balanced_prefers_mass_centroid_near_frame_center():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    centered = scores(frame, [subject_at(160, 120, 60)])[CompositionMode.BALANCED]
    edge = scores(frame, [subject_at(25, 120, 60)])[CompositionMode.BALANCED]
    assert centered.match_score > edge.match_score


def test_triangle_requires_non_collinear_three_point_structure():
    triangular = scores(triangle_image(), [])[CompositionMode.TRIANGLE]
    straight = scores(line_image((0,)), [])[CompositionMode.TRIANGLE]
    assert triangular.match_score >= 60
    assert triangular.match_score > straight.match_score


def test_dynamic_symmetry_uses_diagonal_structure_and_focus():
    diagonal = line_image((36, 144))
    aligned = scores(diagonal, [subject_at(160, 120)])[CompositionMode.DYNAMIC_SYMMETRY]
    blank = scores(np.zeros_like(diagonal), [subject_at(160, 120)])[CompositionMode.DYNAMIC_SYMMETRY]
    assert aligned.match_score > blank.match_score
