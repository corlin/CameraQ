"""Deterministic threshold calibration primitives for reviewed composition cases."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2

from src.core.composition.engine import CompositionEngine
from src.core.composition.thresholds import MODE_EVIDENCE_WEIGHTS, WEIGHT_CONFIG_VERSION
from src.core.detectors.saliency_detector import SaliencyDetector
from src.core.entities import (
    BoundingBox,
    CompositionMode,
    FusedSubject,
    SourceType,
)


@dataclass(frozen=True)
class ScoredExample:
    case_id: str
    mode: CompositionMode
    score: float
    truth: bool
    split: str


@dataclass(frozen=True)
class ThresholdMetrics:
    tp: int
    fp: int
    fn: int
    tn: int
    precision: float | None
    recall: float | None


@dataclass(frozen=True)
class CalibrationResult:
    mode: CompositionMode
    enter_score: float
    exit_score: float
    precision: float
    recall: float
    tp: int
    fp: int
    fn: int
    tn: int


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def evaluate_threshold(examples: list[ScoredExample], threshold: float) -> ThresholdMetrics:
    tp = fp = fn = tn = 0
    for item in examples:
        predicted = item.score >= threshold
        if item.truth and predicted:
            tp += 1
        elif item.truth:
            fn += 1
        elif predicted:
            fp += 1
        else:
            tn += 1
    return ThresholdMetrics(
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        precision=_rate(tp, tp + fp),
        recall=_rate(tp, tp + fn),
    )


def assert_calibration_ready(
    examples: list[ScoredExample], modes: list[CompositionMode]
) -> None:
    invalid_splits = sorted({item.split for item in examples} - {"calibration", "acceptance"})
    if invalid_splits:
        raise ValueError(f"unsupported calibration splits: {invalid_splits}")
    for mode in modes:
        for split in ("calibration", "acceptance"):
            selected = [item for item in examples if item.mode is mode and item.split == split]
            if not any(item.truth for item in selected):
                raise ValueError(f"{mode.value} missing {split} positive examples")
            if not any(not item.truth for item in selected):
                raise ValueError(f"{mode.value} missing {split} negative examples")


def calibrate_mode(
    examples: list[ScoredExample],
    mode: CompositionMode,
    *,
    minimum_precision: float = 0.8,
    hysteresis_gap: float = 10.0,
) -> CalibrationResult:
    selected = [
        item for item in examples if item.mode is mode and item.split == "calibration"
    ]
    candidates = sorted({item.score for item in selected})
    eligible: list[tuple[float, ThresholdMetrics]] = []
    for threshold in candidates:
        metrics = evaluate_threshold(selected, threshold)
        if metrics.precision is not None and metrics.precision >= minimum_precision:
            eligible.append((threshold, metrics))
    if not eligible:
        raise ValueError(f"{mode.value} cannot reach precision {minimum_precision:.2f}")
    threshold, metrics = max(
        eligible,
        key=lambda item: (
            item[1].recall if item[1].recall is not None else -1.0,
            item[1].precision if item[1].precision is not None else -1.0,
            -item[0],
        ),
    )
    return CalibrationResult(
        mode=mode,
        enter_score=threshold,
        exit_score=max(0.0, threshold - hysteresis_gap),
        precision=float(metrics.precision),
        recall=float(metrics.recall),
        tp=metrics.tp,
        fp=metrics.fp,
        fn=metrics.fn,
        tn=metrics.tn,
    )


def build_calibration_report(
    examples: list[ScoredExample], modes: list[CompositionMode]
) -> dict[str, dict]:
    assert_calibration_ready(examples, modes)
    report: dict[str, dict] = {
        "_metadata": {
            "weight_config_version": WEIGHT_CONFIG_VERSION,
            "evidence_weights": {
                mode.value: dict(MODE_EVIDENCE_WEIGHTS[mode]) for mode in modes
            },
        }
    }
    for mode in modes:
        calibrated = calibrate_mode(examples, mode)
        acceptance = evaluate_threshold(
            [
                item
                for item in examples
                if item.mode is mode and item.split == "acceptance"
            ],
            calibrated.enter_score,
        )
        report[mode.value] = {
            "proposed_enter_score": calibrated.enter_score,
            "proposed_exit_score": calibrated.exit_score,
            "calibration": asdict(calibrated),
            "acceptance": asdict(acceptance),
        }
        report[mode.value]["calibration"]["mode"] = mode.value
    return report


def _subjects(
    case: dict,
    frame_width: int,
    frame_height: int,
    saliency=None,
) -> list[FusedSubject]:
    box = case.get("subject_box_before")
    if box:
        x, y, width, height = box
        return [
            FusedSubject(
                subject_id="calibration-subject",
                class_name="calibration-subject",
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
    if saliency is None or not saliency.bounding_boxes:
        return []
    primary = max(
        saliency.bounding_boxes,
        key=lambda item: item.width * item.height,
    )
    return [
        FusedSubject(
            subject_id=f"calibration-saliency-{index}",
            class_name="salient-region",
            confidence=saliency.max_salient_score,
            bounding_box=salient_box,
            is_primary_subject=salient_box is primary,
            source=SourceType.SALIENCY,
        )
        for index, salient_box in enumerate(saliency.bounding_boxes)
    ]


def score_reviewed_manifest(manifest_path: str | Path) -> list[ScoredExample]:
    path = Path(manifest_path)
    payload = json.loads(path.read_text())
    examples: list[ScoredExample] = []
    saliency_detector = SaliencyDetector()
    for case in payload.get("cases", []):
        if case.get("review_status") != "accepted":
            continue
        if case.get("kind") not in {"positive", "hard_negative"}:
            continue
        frame = cv2.imread(str(path.parent / case["path"]))
        if frame is None:
            raise FileNotFoundError(path.parent / case["path"])
        height, width = frame.shape[:2]
        saliency = saliency_detector.detect(frame)
        analysis = CompositionEngine().analyze(
            frame,
            _subjects(case, width, height, saliency),
            saliency,
            timestamp=0,
        )
        scores = {result.mode: result.match_score for result in analysis.mode_results}
        for value in case.get("labels", []):
            mode = CompositionMode(value)
            examples.append(
                ScoredExample(case["id"], mode, scores[mode], True, case.get("split", ""))
            )
        for value in case.get("negative_for", []):
            mode = CompositionMode(value)
            examples.append(
                ScoredExample(case["id"], mode, scores[mode], False, case.get("split", ""))
            )
    return examples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=Path(__file__).with_name("manifest.json")
    )
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text())
    modes = [CompositionMode(value) for value in payload.get("labels", [])]
    try:
        report = build_calibration_report(score_reviewed_manifest(args.manifest), modes)
    except ValueError as error:
        raise SystemExit(f"calibration blocked: {error}") from error
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
