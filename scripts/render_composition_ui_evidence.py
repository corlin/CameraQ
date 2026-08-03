from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.entities import (  # noqa: E402
    AnalysisResult,
    CompositionAction,
    CompositionAnalysis,
    CompositionConfidence,
    CompositionEvidence,
    CompositionEvidenceType,
    CompositionMode,
    CompositionModeResult,
    CompositionScore,
    NormalizedLine,
    NormalizedPoint,
    TargetCompositionRecommendation,
)
from src.core.settings import SettingsManager  # noqa: E402
from src.ui.overlay import OverlayRenderer  # noqa: E402


def _synthetic_scene() -> np.ndarray:
    frame = np.full((720, 1280, 3), (42, 34, 28), dtype=np.uint8)
    cv2.rectangle(frame, (170, 90), (1110, 650), (78, 67, 56), -1)
    cv2.rectangle(frame, (300, 160), (980, 610), (25, 31, 39), -1)
    cv2.line(frame, (0, 480), (1280, 480), (190, 150, 90), 8)
    cv2.line(frame, (80, 690), (780, 50), (210, 210, 210), 10)
    cv2.circle(frame, (430, 245), 54, (70, 170, 235), -1)
    return frame


def _analysis() -> CompositionAnalysis:
    evidence_by_mode = {
        CompositionMode.RULE_OF_THIRDS: CompositionEvidence(
            evidence_type=CompositionEvidenceType.SUBJECT_POSITION,
            strength=0.92,
            description="主体靠近左上三分点",
            points=[NormalizedPoint(x=1 / 3, y=1 / 3)],
        ),
        CompositionMode.DIAGONAL: CompositionEvidence(
            evidence_type=CompositionEvidenceType.LINE,
            strength=0.88,
            description="主线沿画面对角线延伸",
            lines=[
                NormalizedLine(
                    p1=NormalizedPoint(x=0.06, y=0.96),
                    p2=NormalizedPoint(x=0.61, y=0.07),
                )
            ],
        ),
        CompositionMode.FRAME_WITHIN_FRAME: CompositionEvidence(
            evidence_type=CompositionEvidenceType.CONTOUR,
            strength=0.84,
            description="边界包围内部主体",
            contour=[
                NormalizedPoint(x=0.23, y=0.22),
                NormalizedPoint(x=0.77, y=0.22),
                NormalizedPoint(x=0.77, y=0.85),
                NormalizedPoint(x=0.23, y=0.85),
            ],
        ),
    }
    scores = {
        CompositionMode.RULE_OF_THIRDS: 91,
        CompositionMode.DIAGONAL: 86,
        CompositionMode.FRAME_WITHIN_FRAME: 82,
    }
    results = []
    for mode in CompositionMode:
        visible = mode in evidence_by_mode
        results.append(
            CompositionModeResult(
                mode=mode,
                match_score=scores.get(mode, 12),
                confidence=(CompositionConfidence.HIGH if visible else CompositionConfidence.LOW),
                evidence=[evidence_by_mode[mode]] if visible else [],
                is_visible=visible,
                stable_for_ms=850 if visible else 0,
            )
        )
    top_modes = list(evidence_by_mode)
    return CompositionAnalysis(
        timestamp=1.0,
        frame_width=1280,
        frame_height=720,
        evidence_quality=0.91,
        mode_results=results,
        top_modes=top_modes,
        recommendation=TargetCompositionRecommendation(
            target_mode=CompositionMode.RULE_OF_THIRDS,
            action=CompositionAction.MOVE_LEFT,
            reason="向左微调主体至三分交点",
            current_score=61,
            projected_score=78,
            adjustment_cost=0.18,
            priority=0.9,
        ),
        processing_time_ms=2.4,
    )


def _result(frame: np.ndarray, composition: CompositionAnalysis | None) -> AnalysisResult:
    return AnalysisResult(
        image_with_overlays=frame,
        feedback_message="保持画面稳定",
        score=CompositionScore(
            total_score=86,
            subject_score=88,
            structure_score=91,
            balance_score=82,
            interference_score=90,
            style_score=80,
        ),
        composition_analysis=composition,
    )


def render_ui_evidence(output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    frame = _synthetic_scene()
    composition = _analysis()
    settings = SettingsManager(config_path=output / "nonexistent-validation-config.json")
    settings.ai_coach_enabled = False
    report: dict[str, object] = {
        "uses_camera_frame": False,
        "source": "deterministic synthetic UI validation scene",
    }
    paths: dict[str, Path] = {}

    for state, level in (("minimal", "MINIMAL"), ("coach", "COACH"), ("pro", "PRO")):
        settings.coaching_level = level
        renderer = OverlayRenderer(settings=settings)
        rendered = renderer.draw(frame, _result(frame, composition), fps=30.0)
        path = output / f"composition-ui-{state}.png"
        if not cv2.imwrite(str(path), rendered):
            raise RuntimeError(f"failed to write {path}")
        paths[state] = path
        # Match overlay.draw() behaviour: recommendation only in COACH/PRO,
        # evidence geometry only in PRO (lines 136–141, 166 of overlay.py)
        has_recommendation = level in ("COACH", "PRO") and renderer._composition_recommendation_text(composition) is not None
        if level == "PRO":
            geometry = renderer._composition_evidence_geometry(composition, 1280, 720)
            total_lines = sum(len(geo["lines"]) for geo in geometry.values())
            total_points = sum(len(geo["points"]) for geo in geometry.values())
            total_contours = sum(len(geo["contours"]) for geo in geometry.values())
        else:
            total_lines = total_points = total_contours = 0
        report[state] = {
            "composition_lines": len(renderer._composition_summary(composition, level)),
            "has_recommendation": has_recommendation,
            "evidence_lines": total_lines,
            "evidence_points": total_points,
            "evidence_contours": total_contours,
        }

    settings.coaching_level = "COACH"
    renderer = OverlayRenderer(settings=settings)
    disabled = renderer.draw(frame, _result(frame, None), fps=30.0)
    disabled_path = output / "composition-ui-disabled.png"
    if not cv2.imwrite(str(disabled_path), disabled):
        raise RuntimeError(f"failed to write {disabled_path}")
    paths["disabled"] = disabled_path
    report["disabled"] = {
        "composition_lines": len(renderer._composition_summary(None, "COACH")),
        "has_recommendation": False,
    }

    sidebar_renderer = OverlayRenderer(settings=settings)
    sidebar_renderer.is_sidebar_open = True
    sidebar_renderer.sidebar_offset = 0.0
    sidebar = sidebar_renderer.draw(frame, _result(frame, composition), fps=30.0)
    sidebar_path = output / "composition-ui-sidebar.png"
    if not cv2.imwrite(str(sidebar_path), sidebar):
        raise RuntimeError(f"failed to write {sidebar_path}")
    paths["sidebar"] = sidebar_path
    controls = sorted(
        key
        for key in (
            list(sidebar_renderer.toggle_bounds)
            + list(sidebar_renderer.numeric_bounds)
            + list(sidebar_renderer.action_bounds)
        )
        if key.startswith("composition") or key == "clear_composition_diagnostics"
    )
    report["sidebar"] = {"composition_controls": controls}

    report_path = output / "composition-ui-evidence.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    paths["report"] = report_path
    return paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render non-camera composition UI evidence")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/014-composition-pattern-recognition/evidence/ui"),
    )
    args = parser.parse_args()
    generated = render_ui_evidence(args.output)
    print(f"generated {len(generated) - 1} UI images and {generated['report']}")
