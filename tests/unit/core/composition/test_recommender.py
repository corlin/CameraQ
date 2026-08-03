from src.core.composition.extractor import CompositionFeatureExtractor
from src.core.composition.recommender import CompositionRecommender
from src.core.entities import (
    BoundingBox,
    CompositionAction,
    CompositionConfidence,
    CompositionMode,
    CompositionModeResult,
    FusedSubject,
    SourceType,
)
from tests.fixtures.composition.factory import canvas, line_image


def subject(x, y, width=30, height=40):
    return FusedSubject(
        subject_id="s",
        class_name="person",
        confidence=0.95,
        bounding_box=BoundingBox(x=x, y=y, width=width, height=height),
        is_primary_subject=True,
        source=SourceType.YOLO,
    )


def mode_results(mode=CompositionMode.RULE_OF_THIRDS, score=55, confidence=CompositionConfidence.HIGH):
    return [
        CompositionModeResult(
            mode=item,
            match_score=score if item is mode else 10,
            confidence=confidence if item is mode else CompositionConfidence.LOW,
            evidence=[],
        )
        for item in CompositionMode
    ]


def test_near_thirds_returns_horizontal_pan_direction():
    frame = canvas()
    features = CompositionFeatureExtractor().extract(frame, [subject(60, 40, 100, 80)], None)
    recommendation = CompositionRecommender().recommend(features, mode_results())
    assert recommendation is not None
    assert recommendation.target_mode is CompositionMode.RULE_OF_THIRDS
    assert recommendation.action in {CompositionAction.MOVE_LEFT, CompositionAction.MOVE_RIGHT}


def test_small_and_large_subjects_map_to_distance_actions():
    frame = canvas()
    small = CompositionFeatureExtractor().extract(frame, [subject(150, 110, 15, 20)], None)
    large = CompositionFeatureExtractor().extract(frame, [subject(0, 0, 250, 230)], None)
    recommender = CompositionRecommender()
    assert recommender.recommend(small, mode_results()).action is CompositionAction.MOVE_CLOSER
    assert recommender.recommend(large, mode_results()).action is CompositionAction.MOVE_BACK


def test_strong_current_composition_returns_keep():
    frame = canvas()
    features = CompositionFeatureExtractor().extract(frame, [subject(90, 60, 40, 50)], None)
    recommendation = CompositionRecommender().recommend(features, mode_results(score=92))
    assert recommendation.action is CompositionAction.KEEP
    assert recommendation.aligned


def test_clipping_overrides_keep_but_strong_small_subject_can_stay():
    frame = canvas()
    small = CompositionFeatureExtractor().extract(frame, [subject(150, 110, 15, 20)], None)
    clipped = CompositionFeatureExtractor().extract(frame, [subject(0, 0, 300, 230)], None)
    recommender = CompositionRecommender()

    assert recommender.recommend(small, mode_results(score=92)).action is CompositionAction.KEEP
    assert recommender.recommend(clipped, mode_results(score=92)).action is CompositionAction.MOVE_BACK


def test_clipped_subject_with_saturated_only_candidate_does_not_fabricate_improvement():
    frame = canvas()
    clipped = CompositionFeatureExtractor().extract(frame, [subject(0, 0, 300, 230)], None)

    recommendation = CompositionRecommender().recommend(clipped, mode_results(score=100))

    assert recommendation.action is CompositionAction.KEEP
    assert recommendation.projected_score == recommendation.current_score == 100


def test_low_confidence_result_does_not_generate_advice():
    features = CompositionFeatureExtractor().extract(canvas(), [subject(90, 60)], None)
    recommendation = CompositionRecommender().recommend(
        features, mode_results(score=55, confidence=CompositionConfidence.LOW)
    )
    assert recommendation is None


def test_medium_display_result_does_not_generate_directional_advice():
    features = CompositionFeatureExtractor().extract(canvas(), [subject(90, 60)], None)
    recommendation = CompositionRecommender().recommend(
        features, mode_results(score=55, confidence=CompositionConfidence.MEDIUM)
    )
    assert recommendation is None


def test_dominant_tilt_can_generate_rotation():
    features = CompositionFeatureExtractor().extract(line_image((8,)), [subject(110, 80, 100, 80)], None)
    recommendation = CompositionRecommender().recommend(
        features, mode_results(CompositionMode.HORIZONTAL, score=58)
    )
    assert recommendation.action in {
        CompositionAction.ROTATE_CLOCKWISE,
        CompositionAction.ROTATE_COUNTERCLOCKWISE,
    }


def test_rotation_direction_is_invariant_to_hough_endpoint_order():
    positive = CompositionFeatureExtractor().extract(
        line_image((18,)), [subject(55, 75, 100, 80)], None
    )
    negative = CompositionFeatureExtractor().extract(
        line_image((-18,)), [subject(55, 75, 100, 80)], None
    )
    recommender = CompositionRecommender()

    assert (
        recommender.recommend(positive, mode_results(CompositionMode.OBLIQUE, score=70)).action
        is CompositionAction.ROTATE_COUNTERCLOCKWISE
    )
    assert (
        recommender.recommend(negative, mode_results(CompositionMode.OBLIQUE, score=70)).action
        is CompositionAction.ROTATE_CLOCKWISE
    )


def test_no_focus_line_rotation_suggests_rotate_or_keep():
    """T063/F6: line-mode rotation without primary_focus."""
    features = CompositionFeatureExtractor().extract(line_image((18,)), [], None)
    recommender = CompositionRecommender()
    recommendation = recommender.recommend(features, mode_results(CompositionMode.OBLIQUE, score=70))
    assert recommendation is not None
    assert recommendation.action in {
        CompositionAction.ROTATE_CLOCKWISE,
        CompositionAction.ROTATE_COUNTERCLOCKWISE,
        CompositionAction.KEEP,
    }


def test_no_focus_near_max_score_returns_keep():
    """T063: near-max line score without focus → KEEP (can't project improvement)."""
    features = CompositionFeatureExtractor().extract(line_image((8,)), [], None)
    recommender = CompositionRecommender()
    recommendation = recommender.recommend(features, mode_results(CompositionMode.HORIZONTAL, score=99))
    assert recommendation is not None
    assert recommendation.action is CompositionAction.KEEP
