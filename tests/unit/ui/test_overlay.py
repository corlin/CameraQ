import pytest
import numpy as np
from src.ui.overlay import OverlayRenderer
from src.core.entities import (
    AnalysisResult,
    CompositionAnalysis,
    CompositionConfidence,
    CompositionEvidence,
    CompositionEvidenceType,
    CompositionMode,
    CompositionModeResult,
    CompositionAction,
    CompositionScore,
    NormalizedLine,
    NormalizedPoint,
    TargetCompositionRecommendation,
)

def test_overlay_renderer():
    renderer = OverlayRenderer()
    
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    
    # Mock analysis result
    result = AnalysisResult(
        image_with_overlays=img,
        feedback_message="测试反馈: 向左移动",
        score=CompositionScore(total_score=85, subject_score=80, structure_score=90, balance_score=85, interference_score=90, style_score=80),
        recommended_crops=[]
    )
    
    out_img = renderer.draw(img, result, fps=30.0)
    
    assert out_img is not None
    assert out_img.shape == (400, 600, 3)
    # The output image should have been modified (text drawn)
    # but exact pixel check is brittle, so just verifying it returns a valid image.


def composition_analysis(top_modes=(), insufficient=False):
    evidence = CompositionEvidence(
        evidence_type=CompositionEvidenceType.LINE,
        strength=0.9,
        description="主线",
        lines=[NormalizedLine(p1=NormalizedPoint(x=0, y=0), p2=NormalizedPoint(x=1, y=1))],
    )
    results = []
    for mode in CompositionMode:
        visible = mode in top_modes
        results.append(
            CompositionModeResult(
                mode=mode,
                match_score=90 if visible else 10,
                confidence=CompositionConfidence.HIGH if visible else CompositionConfidence.LOW,
                evidence=[evidence] if visible else [],
                is_visible=visible,
                stable_for_ms=500 if visible else 0,
            )
        )
    return CompositionAnalysis(
        timestamp=1,
        frame_width=600,
        frame_height=400,
        evidence_quality=0.9 if not insufficient else 0.0,
        mode_results=results,
        top_modes=list(top_modes),
        recommendation=None,
        insufficient_evidence=insufficient,
        processing_time_ms=2,
    )


def test_composition_summary_handles_absent_and_insufficient_states():
    renderer = OverlayRenderer()
    assert renderer._composition_summary(None, "COACH") == []
    assert renderer._composition_summary(composition_analysis(insufficient=True), "COACH") == ["构图：证据不足"]


def test_composition_summary_is_bounded_by_coaching_level():
    renderer = OverlayRenderer()
    analysis = composition_analysis(
        (CompositionMode.RULE_OF_THIRDS, CompositionMode.DIAGONAL, CompositionMode.BALANCED)
    )
    minimal = renderer._composition_summary(analysis, "MINIMAL")
    coach = renderer._composition_summary(analysis, "COACH")
    assert len(minimal) == 1
    assert "三分法" in minimal[0]
    assert len(coach) == 3


def test_recommendation_text_handles_move_keep_and_none():
    renderer = OverlayRenderer()
    analysis = composition_analysis((CompositionMode.RULE_OF_THIRDS,))
    assert renderer._composition_recommendation_text(analysis) is None

    analysis.recommendation = TargetCompositionRecommendation(
        target_mode=CompositionMode.RULE_OF_THIRDS,
        action=CompositionAction.MOVE_LEFT,
        reason="向左微调",
        current_score=55,
        projected_score=75,
        adjustment_cost=0.2,
        priority=0.8,
    )
    assert "向左" in renderer._composition_recommendation_text(analysis)

    analysis.recommendation = TargetCompositionRecommendation(
        target_mode=CompositionMode.RULE_OF_THIRDS,
        action=CompositionAction.KEEP,
        reason="保持",
        current_score=90,
        projected_score=90,
        adjustment_cost=0,
        priority=0.9,
        aligned=True,
    )
    assert "保持" in renderer._composition_recommendation_text(analysis)


def test_pro_evidence_geometry_maps_normalized_coordinates_to_frame():
    renderer = OverlayRenderer()
    analysis = composition_analysis((CompositionMode.DIAGONAL,))
    geometry = renderer._composition_evidence_geometry(analysis, width=600, height=400)
    assert geometry["lines"] == [((0, 0), (600, 400))]
    assert geometry["points"] == []


def test_non_visible_mode_evidence_is_not_rendered():
    renderer = OverlayRenderer()
    analysis = composition_analysis(())
    geometry = renderer._composition_evidence_geometry(analysis, width=600, height=400)
    assert geometry == {"points": [], "lines": [], "contours": []}


def test_sidebar_exposes_composition_controls_and_clear_action():
    renderer = OverlayRenderer()
    renderer.is_sidebar_open = True
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    renderer.draw(frame, None)
    assert "composition_detection_enabled" in renderer.toggle_bounds
    assert "composition_diagnostics_enabled" in renderer.toggle_bounds
    assert "composition_analysis_interval_s_minus" in renderer.numeric_bounds
    assert "clear_composition_diagnostics" in renderer.action_bounds


def test_sidebar_composition_labels_fit_controls_and_chrome_avoids_missing_emoji():
    renderer = OverlayRenderer()

    assert renderer.small_font.getlength(renderer.CLEAR_COMPOSITION_LABEL) <= 180
    assert renderer.small_font.getlength(renderer.COMPOSITION_INTERVAL_LABEL) <= 155
    assert renderer.SETTINGS_TITLE.isascii()
    assert renderer.SETTINGS_PROMPT.isascii()
