import cv2

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


def test_radial_and_centripetal_are_distinguished_by_focus():
    radial_without_focus = scores(radial_image())
    radial_with_focus = scores(radial_image(), [centered_subject()])
    assert radial_without_focus[CompositionMode.RADIAL].match_score >= 60
    assert radial_with_focus[CompositionMode.CENTRIPETAL].match_score > radial_without_focus[CompositionMode.CENTRIPETAL].match_score


def test_checkerboard_requires_two_repeating_orthogonal_families():
    checker = scores(grid_image())[CompositionMode.CHECKERBOARD]
    single_family = scores(radial_image(spokes=1))[CompositionMode.CHECKERBOARD]
    assert checker.match_score > single_family.match_score


def test_tunnel_requires_nested_depth_but_frame_does_not():
    nested = scores(nested_rectangles(), [centered_subject()])
    single = canvas()
    cv2.rectangle(single, (30, 25), (290, 215), (255, 255, 255), 5)
    framed = scores(single, [centered_subject()])
    assert nested[CompositionMode.TUNNEL].match_score > framed[CompositionMode.TUNNEL].match_score
    assert framed[CompositionMode.FRAME_WITHIN_FRAME].match_score >= 50
