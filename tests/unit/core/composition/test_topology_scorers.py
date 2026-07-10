from pathlib import Path

import cv2
import numpy as np

from src.core.composition.extractor import CompositionFeatureExtractor
from src.core.composition.scorers.topology import score_topology_modes
from src.core.entities import BoundingBox, CompositionMode, FusedSubject, SourceType
from tests.fixtures.composition.factory import canvas, curve_image, grid_image, nested_rectangles, radial_image


def centered_subject() -> FusedSubject:
    return FusedSubject(
        subject_id="center",
        class_name="person",
        confidence=0.95,
        bounding_box=BoundingBox(x=145, y=95, width=30, height=50),
        is_primary_subject=True,
        source=SourceType.YOLO,
    )


def scores(frame, subjects=None):
    features = CompositionFeatureExtractor().extract(frame, subjects or [], None)
    return {item.mode: item for item in score_topology_modes(features)}


def test_curve_requires_long_curved_contour():
    curve = scores(curve_image())[CompositionMode.CURVE]
    blank = scores(canvas())[CompositionMode.CURVE]
    assert curve.match_score > blank.match_score


def test_curve_penalizes_dense_straight_line_structure():
    curve = scores(curve_image())[CompositionMode.CURVE]
    straight_grid = scores(grid_image())[CompositionMode.CURVE]

    assert curve.match_score > straight_grid.match_score
    assert straight_grid.match_score < 30


def test_curve_recognizes_centered_arch_tunnel():
    fixtures = Path(__file__).parents[3] / "fixtures/composition/images/real_candidates"
    arch = cv2.imread(str(fixtures / "commons-tunnel-positive-14.jpg"))
    facade = cv2.imread(str(fixtures / "commons-vertical-photo-positive-01.jpg"))

    arch_score = scores(arch)[CompositionMode.CURVE]
    facade_score = scores(facade)[CompositionMode.CURVE]

    assert arch_score.match_score >= 35
    assert arch_score.match_score > facade_score.match_score


def test_radial_and_centripetal_are_distinguished_by_focus():
    radial_without_focus = scores(radial_image())
    radial_with_focus = scores(radial_image(), [centered_subject()])
    assert radial_without_focus[CompositionMode.RADIAL].match_score >= 60
    assert radial_with_focus[CompositionMode.CENTRIPETAL].match_score > radial_without_focus[CompositionMode.CENTRIPETAL].match_score


def test_centripetal_can_use_a_geometric_vanishing_point_without_subject():
    perspective = canvas()
    vanishing_point = (160, 115)
    for endpoint in (
        (10, 10),
        (10, 230),
        (310, 10),
        (310, 230),
        (30, 70),
        (290, 70),
    ):
        cv2.line(perspective, endpoint, vanishing_point, (255, 255, 255), 3)
    for y in (25, 205):
        cv2.line(perspective, (0, y), (319, y), (160, 160, 160), 2)

    centripetal = scores(perspective)[CompositionMode.CENTRIPETAL]

    assert centripetal.match_score >= 20


def test_radial_recognizes_curved_petals_without_hough_intersections():
    petals = canvas()
    for angle in range(0, 360, 45):
        x = int(160 + 55 * np.cos(np.deg2rad(angle)))
        y = int(120 + 55 * np.sin(np.deg2rad(angle)))
        cv2.ellipse(
            petals,
            (x, y),
            (18, 35),
            float(angle),
            0,
            360,
            (255, 255, 255),
            3,
        )

    radial = scores(petals)[CompositionMode.RADIAL]

    assert radial.match_score >= 30


def test_radial_requires_multiple_spoke_directions():
    many_spokes = scores(radial_image(spokes=8))[CompositionMode.RADIAL]
    single_line = scores(radial_image(spokes=1))[CompositionMode.RADIAL]

    assert many_spokes.match_score >= 60
    assert single_line.match_score < 30


def test_radial_recognizes_dense_radial_textile_pattern():
    fixtures = Path(__file__).parents[3] / "fixtures/composition/images/real_candidates"
    textile = cv2.imread(str(fixtures / "commons-radial-positive-08.jpg"))
    stools = cv2.imread(str(fixtures / "commons-radial-negative-15.jpg"))

    textile_score = scores(textile)[CompositionMode.RADIAL]
    stools_score = scores(stools)[CompositionMode.RADIAL]

    assert textile_score.match_score >= 48
    assert textile_score.match_score > stools_score.match_score


def test_radial_rejects_distant_perspective_vanishing_point():
    petals = canvas()
    petals_center = (200, 105)
    for angle in range(0, 360, 45):
        x = int(petals_center[0] + 50 * np.cos(np.deg2rad(angle)))
        y = int(petals_center[1] + 50 * np.sin(np.deg2rad(angle)))
        cv2.ellipse(
            petals,
            (x, y),
            (16, 32),
            float(angle),
            0,
            360,
            (255, 255, 255),
            3,
        )
    perspective_frame = canvas()
    vanishing_point = (260, 105)
    for endpoint in (
        (20, 20),
        (20, 220),
        (300, 20),
        (300, 220),
        (80, 55),
        (80, 185),
    ):
        cv2.line(
            perspective_frame,
            endpoint,
            vanishing_point,
            (255, 255, 255),
            3,
        )
    cv2.rectangle(perspective_frame, (25, 25), (295, 215), (255, 255, 255), 3)

    radial_petals = scores(petals)[CompositionMode.RADIAL]
    radial_frame = scores(perspective_frame)[CompositionMode.RADIAL]

    assert radial_petals.match_score >= 25
    assert radial_frame.match_score < radial_petals.match_score


def test_checkerboard_requires_two_repeating_orthogonal_families():
    checker = scores(grid_image())[CompositionMode.CHECKERBOARD]
    single_family = scores(radial_image(spokes=1))[CompositionMode.CHECKERBOARD]
    assert checker.match_score > single_family.match_score


def test_checkerboard_uses_short_horizontal_repetition_on_vertical_structure():
    facade = canvas()
    horizon = canvas()
    for x in range(50, 290, 40):
        cv2.line(facade, (x, 20), (x, 220), (255, 255, 255), 3)
        for y in range(45, 210, 35):
            cv2.line(facade, (x - 9, y), (x + 9, y), (200, 200, 200), 2)
    for y in range(45, 210, 35):
        cv2.line(horizon, (15, y), (305, y), (255, 255, 255), 3)

    facade_score = scores(facade)[CompositionMode.CHECKERBOARD]
    horizon_score = scores(horizon)[CompositionMode.CHECKERBOARD]

    assert facade_score.match_score >= 30
    assert facade_score.match_score > horizon_score.match_score


def test_checkerboard_ranks_full_grid_over_vertical_fallback():
    facade = canvas()
    for x in range(50, 290, 40):
        cv2.line(facade, (x, 20), (x, 220), (255, 255, 255), 3)
        for y in range(45, 210, 35):
            cv2.line(facade, (x - 9, y), (x + 9, y), (200, 200, 200), 2)

    grid_score = scores(grid_image())[CompositionMode.CHECKERBOARD]
    facade_score = scores(facade)[CompositionMode.CHECKERBOARD]

    assert grid_score.match_score > facade_score.match_score


def test_checkerboard_prefers_regular_grid_spacing_over_irregular_crossings():
    irregular = canvas()
    for x in (35, 91, 158, 283):
        cv2.line(irregular, (x, 20), (x, 220), (255, 255, 255), 3)
    for y in (42, 77, 151, 213):
        cv2.line(irregular, (20, y), (300, y), (255, 255, 255), 3)

    grid_score = scores(grid_image())[CompositionMode.CHECKERBOARD]
    irregular_score = scores(irregular)[CompositionMode.CHECKERBOARD]

    assert grid_score.match_score > irregular_score.match_score


def test_tunnel_requires_nested_depth_but_frame_does_not():
    nested = scores(nested_rectangles(), [centered_subject()])
    single = canvas()
    cv2.rectangle(single, (30, 25), (290, 215), (255, 255, 255), 5)
    framed = scores(single, [centered_subject()])
    assert nested[CompositionMode.TUNNEL].match_score > framed[CompositionMode.TUNNEL].match_score
    assert framed[CompositionMode.FRAME_WITHIN_FRAME].match_score >= 50


def test_tunnel_accepts_low_clutter_interior_depth_without_nested_rectangles():
    corridor = canvas(value=150)
    framed_window = canvas(value=20)
    cv2.rectangle(corridor, (95, 55), (225, 185), (35, 35, 35), -1)
    for offset in range(0, 100, 20):
        cv2.line(
            corridor,
            (105 + offset, 75),
            (105 + offset, 165),
            (110, 110, 110),
            2,
        )
    cv2.rectangle(
        framed_window,
        (95, 55),
        (225, 185),
        (230, 230, 230),
        -1,
    )

    corridor_score = scores(corridor)[CompositionMode.TUNNEL]
    frame_score = scores(framed_window)[CompositionMode.TUNNEL]

    assert corridor_score.match_score >= 30
    assert corridor_score.match_score > frame_score.match_score


def test_frame_requires_a_textured_scene_inside_the_enclosure():
    scene = canvas(value=20)
    blank = canvas(value=20)
    rng = np.random.default_rng(7)
    scene[40:200, 50:270] = rng.integers(
        40, 220, (160, 220, 3), dtype=np.uint8
    )
    blank[40:200, 50:270] = 255

    scene_score = scores(scene)[CompositionMode.FRAME_WITHIN_FRAME]
    blank_score = scores(blank)[CompositionMode.FRAME_WITHIN_FRAME]

    assert scene_score.match_score >= 60
    assert scene_score.match_score > blank_score.match_score


def test_perspective_convergence_supports_tunnel_and_spatial_frame_fallback():
    perspective = radial_image(spokes=6)
    blank = canvas()

    converging = scores(perspective)
    empty = scores(blank)

    assert converging[CompositionMode.TUNNEL].match_score >= 30
    assert (
        converging[CompositionMode.FRAME_WITHIN_FRAME].match_score
        > empty[CompositionMode.FRAME_WITHIN_FRAME].match_score
    )
