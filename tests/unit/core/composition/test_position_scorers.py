from pathlib import Path

import cv2
import numpy as np

from src.core.composition.extractor import CompositionFeatureExtractor
from src.core.composition.scorers.position import score_position_modes
from src.core.detectors.saliency_detector import SaliencyDetector
from src.core.entities import (
    BoundingBox,
    CompositionMode,
    FusedSubject,
    SaliencyMap,
    SourceType,
)
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


def scores_with_saliency(frame):
    saliency = SaliencyDetector().detect(frame)
    height, width = frame.shape[:2]
    primary = max(
        saliency.bounding_boxes,
        key=lambda item: item.width * item.height,
        default=None,
    )
    subjects = [
        FusedSubject(
            subject_id=f"saliency-{index}",
            class_name="salient-region",
            confidence=saliency.max_salient_score,
            bounding_box=box,
            is_primary_subject=box is primary,
            source=SourceType.SALIENCY,
        )
        for index, box in enumerate(saliency.bounding_boxes)
        if width and height
    ]
    features = CompositionFeatureExtractor().extract(frame, subjects, saliency)
    return {item.mode: item for item in score_position_modes(features)}


def test_rule_of_thirds_prefers_third_intersection_over_arbitrary_position():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    thirds = scores(frame, [subject_at(320 / 3, 240 / 3)])[CompositionMode.RULE_OF_THIRDS]
    arbitrary = scores(frame, [subject_at(0.47 * 320, 0.42 * 240)])[CompositionMode.RULE_OF_THIRDS]
    assert thirds.match_score >= 70
    assert thirds.match_score > arbitrary.match_score


def test_rule_of_thirds_recognizes_dominant_line_on_a_third():
    thirds_frame = np.zeros((240, 320, 3), dtype=np.uint8)
    centered_frame = np.zeros_like(thirds_frame)
    cv2 = __import__("cv2")
    cv2.line(thirds_frame, (0, 80), (319, 80), (255, 255, 255), 5)
    cv2.line(centered_frame, (0, 120), (319, 120), (255, 255, 255), 5)

    thirds = scores(thirds_frame, [])[CompositionMode.RULE_OF_THIRDS]
    centered = scores(centered_frame, [])[CompositionMode.RULE_OF_THIRDS]

    assert thirds.match_score >= 30
    assert thirds.match_score > centered.match_score


def test_rule_of_thirds_ignores_zero_confidence_saliency_focus():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    heatmap = np.zeros((240, 320), dtype=np.uint8)
    heatmap[80, 106] = 255
    saliency = SaliencyMap(
        heatmap=heatmap, bounding_boxes=[], max_salient_score=0.0
    )
    features = CompositionFeatureExtractor().extract(frame, [], saliency)

    result = {
        item.mode: item for item in score_position_modes(features)
    }[CompositionMode.RULE_OF_THIRDS]

    assert result.match_score == 0


def test_rule_of_thirds_detects_textured_horizon_boundary():
    rng = np.random.default_rng(11)
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    for x in range(frame.shape[1]):
        horizon = 80 + int(8 * np.sin(x / 17))
        frame[:horizon, x] = np.clip(
            170 + rng.integers(-20, 21, (horizon, 3)), 0, 255
        )
        frame[horizon:, x] = np.clip(
            70 + rng.integers(-20, 21, (240 - horizon, 3)), 0, 255
        )

    result = scores(frame, [])[CompositionMode.RULE_OF_THIRDS]

    assert result.match_score >= 50


def test_rule_of_thirds_detects_smooth_landscape_horizon_on_a_third():
    fixture = (
        Path(__file__).parents[3]
        / "fixtures/composition/images/real_candidates"
        / "commons-horizontal-photo-positive-06.jpg"
    )
    frame = cv2.imread(str(fixture))

    result = scores_with_saliency(frame)[CompositionMode.RULE_OF_THIRDS]

    assert result.match_score >= 50


def test_rule_of_thirds_detects_vertical_structure_on_a_third():
    fixture = (
        Path(__file__).parents[3]
        / "fixtures/composition/images/real_candidates"
        / "commons-rule-of-thirds-positive-08.jpg"
    )
    frame = cv2.imread(str(fixture))

    result = scores_with_saliency(frame)[CompositionMode.RULE_OF_THIRDS]

    assert result.match_score >= 55


def test_rule_of_thirds_suppresses_a_centered_rectangular_enclosure():
    fixture = (
        Path(__file__).parents[3]
        / "fixtures/composition/images/real_candidates"
        / "commons-rule-of-thirds-negative-11.jpg"
    )
    frame = cv2.imread(str(fixture))

    result = scores(frame, [])[CompositionMode.RULE_OF_THIRDS]

    assert result.match_score < 60


def test_balanced_prefers_mass_centroid_near_frame_center():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    centered = scores(frame, [subject_at(160, 120, 60)])[CompositionMode.BALANCED]
    edge = scores(frame, [subject_at(25, 120, 60)])[CompositionMode.BALANCED]
    assert centered.match_score > edge.match_score


def test_balanced_ranks_centered_visual_structure_over_perspective_repetition():
    fixtures = Path(__file__).parents[3] / "fixtures/composition/images/real_candidates"
    balanced_frame = cv2.imread(str(fixtures / "commons-dynamic-symmetry-negative-07.jpg"))
    perspective_frame = cv2.imread(
        str(fixtures / "commons-balanced-perspective-negative-09.jpg")
    )

    balanced = scores_with_saliency(balanced_frame)[CompositionMode.BALANCED]
    perspective = scores_with_saliency(perspective_frame)[CompositionMode.BALANCED]

    assert balanced.match_score > perspective.match_score


def test_balanced_recognizes_quiet_centered_tunnel_over_busy_perspective():
    fixtures = Path(__file__).parents[3] / "fixtures/composition/images/real_candidates"
    tunnel_frame = cv2.imread(str(fixtures / "commons-tunnel-positive-05.jpg"))
    perspective_frame = cv2.imread(
        str(fixtures / "commons-balanced-perspective-negative-09.jpg")
    )

    tunnel = scores_with_saliency(tunnel_frame)[CompositionMode.BALANCED]
    perspective = scores_with_saliency(perspective_frame)[CompositionMode.BALANCED]

    assert tunnel.match_score >= 78
    assert tunnel.match_score > perspective.match_score


def test_triangle_requires_non_collinear_three_point_structure():
    triangular = scores(triangle_image(), [])[CompositionMode.TRIANGLE]
    straight = scores(line_image((0,)), [])[CompositionMode.TRIANGLE]
    assert triangular.match_score >= 60
    assert triangular.match_score > straight.match_score


def test_triangle_rejects_cross_shaped_corner_layout():
    cross = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2 = __import__("cv2")
    cv2.line(cross, (40, 120), (280, 120), (255, 255, 255), 20)
    cv2.line(cross, (160, 30), (160, 210), (255, 255, 255), 20)

    triangular = scores(triangle_image(), [])[CompositionMode.TRIANGLE]
    crossed = scores(cross, [])[CompositionMode.TRIANGLE]

    assert triangular.match_score > crossed.match_score
    assert crossed.match_score < 60


def test_dynamic_symmetry_uses_diagonal_structure_and_focus():
    diagonal = line_image((36, 144))
    aligned = scores(diagonal, [subject_at(160, 120)])[CompositionMode.DYNAMIC_SYMMETRY]
    blank = scores(np.zeros_like(diagonal), [subject_at(160, 120)])[CompositionMode.DYNAMIC_SYMMETRY]
    assert aligned.match_score > blank.match_score


def test_dynamic_symmetry_penalizes_static_centered_balance():
    diagonal = line_image((36, 144))
    dynamic = scores(diagonal, [subject_at(100, 75)])[
        CompositionMode.DYNAMIC_SYMMETRY
    ]
    static = scores(diagonal, [subject_at(160, 120)])[
        CompositionMode.DYNAMIC_SYMMETRY
    ]

    assert dynamic.match_score > static.match_score


def test_dynamic_symmetry_recognizes_shallow_perspective_corridor():
    fixtures = Path(__file__).parents[3] / "fixtures/composition/images/real_candidates"
    corridor_frame = cv2.imread(str(fixtures / "commons-tunnel-positive-06.jpg"))
    radial_frame = cv2.imread(str(fixtures / "commons-radial-positive-03.jpg"))

    corridor = scores_with_saliency(corridor_frame)[CompositionMode.DYNAMIC_SYMMETRY]
    radial = scores_with_saliency(radial_frame)[CompositionMode.DYNAMIC_SYMMETRY]

    assert corridor.match_score >= 40
    assert corridor.match_score > radial.match_score
