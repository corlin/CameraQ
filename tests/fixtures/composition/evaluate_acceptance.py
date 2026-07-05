from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2

from src.core.composition.engine import CompositionEngine
from src.core.composition.thresholds import enter_score
from src.core.entities import BoundingBox, CompositionConfidence, CompositionMode, FusedSubject, SourceType


@dataclass(frozen=True)
class AcceptanceEvaluation:
    per_mode: dict[str, dict[str, float | int | None]]
    positive_cases: int
    hard_negative_cases: int
    top3_hits: int
    top3_coverage: float | None
    degraded_total: int
    degraded_abstentions: int
    degraded_abstention_rate: float | None
    recommendation_total: int
    recommendation_improvements: int
    recommendation_improvement_rate: float | None
    recommendation_action_matches: int
    recommendation_action_match_rate: float | None
    strong_composition_checks: int
    strong_composition_preserved: int
    strong_composition_preservation_rate: float | None


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _subjects(case: dict, key: str, frame_width: int, frame_height: int) -> list[FusedSubject]:
    box = case.get(key)
    if not box:
        return []
    x, y, width, height = box
    return [
        FusedSubject(
            subject_id="acceptance-subject",
            class_name="acceptance-subject",
            confidence=0.95,
            bounding_box=BoundingBox(
                x=x * frame_width,
                y=y * frame_height,
                width=width * frame_width,
                height=height * frame_height,
            ),
            is_primary_subject=True,
            source=SourceType.YOLO,
        )
    ]


def _read_image(path: Path):
    frame = cv2.imread(str(path))
    if frame is None:
        raise FileNotFoundError(path)
    return frame


def evaluate_manifest(path: str | Path) -> AcceptanceEvaluation:
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text())
    labels = [CompositionMode(value) for value in payload.get("labels", [])]
    confusion = {mode: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for mode in labels}
    positive_cases = hard_negative_cases = top3_hits = 0
    degraded_total = degraded_abstentions = 0
    recommendation_total = recommendation_improvements = recommendation_action_matches = 0
    strong_checks = strong_preserved = 0

    for case in payload.get("cases", []):
        if case.get("review_status") != "accepted":
            continue
        frame = _read_image(manifest_path.parent / case["path"])
        height, width = frame.shape[:2]
        analysis = CompositionEngine().analyze(
            frame,
            _subjects(case, "subject_box_before", width, height),
            None,
            timestamp=0,
        )
        predictions = {
            result.mode
            for result in analysis.mode_results
            if result.confidence is CompositionConfidence.HIGH
            and result.match_score >= enter_score(result.mode)
        }
        kind = case["kind"]
        truths = {CompositionMode(value) for value in case.get("labels", [])}
        negatives = {CompositionMode(value) for value in case.get("negative_for", [])}

        if kind == "positive":
            positive_cases += 1
            if truths & set(analysis.top_modes):
                top3_hits += 1
        elif kind == "hard_negative":
            hard_negative_cases += 1

        for mode in labels:
            if mode in truths:
                confusion[mode]["tp" if mode in predictions else "fn"] += 1
            if mode in negatives:
                confusion[mode]["fp" if mode in predictions else "tn"] += 1

        if kind == "degraded":
            degraded_total += 1
            strong_visible = any(
                result.is_visible and result.confidence is CompositionConfidence.HIGH
                for result in analysis.mode_results
            )
            if analysis.insufficient_evidence or not strong_visible:
                degraded_abstentions += 1
        elif kind == "recommendation":
            recommendation_total += 1
            target_mode = CompositionMode(case["target_mode"])
            before_score = next(
                result.match_score for result in analysis.mode_results if result.mode is target_mode
            )
            after_frame = _read_image(manifest_path.parent / case["after_path"])
            after_height, after_width = after_frame.shape[:2]
            after = CompositionEngine().analyze(
                after_frame,
                _subjects(case, "subject_box_after", after_width, after_height),
                None,
                timestamp=0,
            )
            after_score = next(
                result.match_score for result in after.mode_results if result.mode is target_mode
            )
            if after_score > before_score:
                recommendation_improvements += 1
            action = analysis.recommendation.action.value if analysis.recommendation else None
            if action == case["recommendation_action"]:
                recommendation_action_matches += 1
            after_scores = {result.mode: result.match_score for result in after.mode_results}
            strong_before = [
                result
                for result in analysis.mode_results
                if result.confidence is CompositionConfidence.HIGH and result.match_score >= 88
            ]
            for result in strong_before:
                strong_checks += 1
                if after_scores[result.mode] >= result.match_score:
                    strong_preserved += 1

    per_mode: dict[str, dict[str, float | int | None]] = {}
    for mode, values in confusion.items():
        precision_denominator = values["tp"] + values["fp"]
        recall_denominator = values["tp"] + values["fn"]
        per_mode[mode.value] = {
            **values,
            "precision": _rate(values["tp"], precision_denominator),
            "recall": _rate(values["tp"], recall_denominator),
        }

    return AcceptanceEvaluation(
        per_mode=per_mode,
        positive_cases=positive_cases,
        hard_negative_cases=hard_negative_cases,
        top3_hits=top3_hits,
        top3_coverage=_rate(top3_hits, positive_cases),
        degraded_total=degraded_total,
        degraded_abstentions=degraded_abstentions,
        degraded_abstention_rate=_rate(degraded_abstentions, degraded_total),
        recommendation_total=recommendation_total,
        recommendation_improvements=recommendation_improvements,
        recommendation_improvement_rate=_rate(recommendation_improvements, recommendation_total),
        recommendation_action_matches=recommendation_action_matches,
        recommendation_action_match_rate=_rate(recommendation_action_matches, recommendation_total),
        strong_composition_checks=strong_checks,
        strong_composition_preserved=strong_preserved,
        strong_composition_preservation_rate=_rate(strong_preserved, strong_checks),
    )


if __name__ == "__main__":
    default_manifest = Path(__file__).with_name("manifest.json")
    print(json.dumps(asdict(evaluate_manifest(default_manifest)), indent=2, ensure_ascii=False))
