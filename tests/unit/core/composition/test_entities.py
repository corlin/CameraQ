import pytest
from pydantic import ValidationError

from src.core.entities import (
    CompositionAction,
    CompositionAnalysis,
    CompositionConfidence,
    CompositionEvidence,
    CompositionEvidenceType,
    CompositionMode,
    CompositionModeResult,
    NormalizedLine,
    NormalizedPoint,
    TargetCompositionRecommendation,
)


def evidence() -> CompositionEvidence:
    return CompositionEvidence(
        evidence_type=CompositionEvidenceType.LINE,
        strength=0.8,
        description="主线",
        lines=[NormalizedLine(p1=NormalizedPoint(x=0, y=0), p2=NormalizedPoint(x=1, y=1))],
    )


def result(mode: CompositionMode, *, visible: bool = False) -> CompositionModeResult:
    return CompositionModeResult(
        mode=mode,
        match_score=80,
        confidence=CompositionConfidence.HIGH,
        evidence=[evidence()] if visible else [],
        is_visible=visible,
        stable_for_ms=500,
    )


def test_contract_defines_exactly_fifteen_modes():
    assert len(CompositionMode) == 15
    assert len({mode.value for mode in CompositionMode}) == 15


def test_normalized_coordinates_reject_out_of_range_values():
    with pytest.raises(ValidationError):
        NormalizedPoint(x=1.1, y=0.5)


def test_analysis_requires_every_mode_once_and_top_three_visible():
    results = [result(mode, visible=idx < 3) for idx, mode in enumerate(CompositionMode)]
    analysis = CompositionAnalysis(
        timestamp=1.0,
        frame_width=320,
        frame_height=240,
        evidence_quality=0.9,
        mode_results=results,
        top_modes=[item.mode for item in results[:3]],
        recommendation=None,
        insufficient_evidence=False,
        processing_time_ms=3.0,
    )
    assert len(analysis.mode_results) == 15

    with pytest.raises(ValidationError):
        CompositionAnalysis(
            timestamp=1.0,
            frame_width=320,
            frame_height=240,
            evidence_quality=0.9,
            mode_results=results[:-1] + [results[0]],
            top_modes=[],
            recommendation=None,
            insufficient_evidence=False,
            processing_time_ms=3.0,
        )


def test_directional_recommendation_is_forbidden_when_evidence_is_insufficient():
    results = [result(mode) for mode in CompositionMode]
    recommendation = TargetCompositionRecommendation(
        target_mode=CompositionMode.RULE_OF_THIRDS,
        action=CompositionAction.MOVE_LEFT,
        reason="向左",
        current_score=50,
        projected_score=70,
        adjustment_cost=0.2,
        priority=0.8,
    )
    with pytest.raises(ValidationError):
        CompositionAnalysis(
            timestamp=1.0,
            frame_width=320,
            frame_height=240,
            evidence_quality=0.1,
            mode_results=results,
            top_modes=[],
            recommendation=recommendation,
            insufficient_evidence=True,
            processing_time_ms=3.0,
        )
