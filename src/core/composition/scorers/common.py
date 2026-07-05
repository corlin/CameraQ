from __future__ import annotations

from src.core.composition.features import CompositionFeatures, LineFeature
from src.core.entities import (
    CompositionConfidence,
    CompositionEvidence,
    CompositionEvidenceType,
    CompositionMode,
    CompositionModeResult,
    NormalizedLine,
    NormalizedPoint,
)


def clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def confidence_for(score: float, features: CompositionFeatures) -> CompositionConfidence:
    if score >= 70 and features.evidence_quality >= 0.18:
        return CompositionConfidence.HIGH
    if score >= 40 and features.evidence_quality >= 0.18:
        return CompositionConfidence.MEDIUM
    return CompositionConfidence.LOW


def point(x: float, y: float) -> NormalizedPoint:
    return NormalizedPoint(x=max(0.0, min(1.0, x)), y=max(0.0, min(1.0, y)))


def normalized_line(line: LineFeature) -> NormalizedLine:
    return NormalizedLine(p1=point(line.x1, line.y1), p2=point(line.x2, line.y2))


def evidence(
    kind: CompositionEvidenceType,
    strength: float,
    description: str,
    *,
    points: list[NormalizedPoint] | None = None,
    lines: list[NormalizedLine] | None = None,
    contour: list[NormalizedPoint] | None = None,
) -> CompositionEvidence:
    return CompositionEvidence(
        evidence_type=kind,
        strength=max(0.0, min(1.0, strength)),
        description=description,
        points=points or [],
        lines=lines or [],
        contour=contour or [],
    )


def result(
    mode: CompositionMode,
    score: float,
    features: CompositionFeatures,
    evidence_items: list[CompositionEvidence] | None = None,
) -> CompositionModeResult:
    bounded = clamp_score(score)
    return CompositionModeResult(
        mode=mode,
        match_score=bounded,
        confidence=confidence_for(bounded, features),
        evidence=evidence_items or [],
        is_visible=False,
        stable_for_ms=0,
    )
