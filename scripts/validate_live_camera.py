"""Run a no-save, CPU-only live CameraQ composition validation."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.composition.engine import CompositionEngine
from src.core.entities import AnalysisResult, CompositionScore
from src.core.io.camera import CameraStreamManager
from src.core.settings import SettingsManager
from src.ui.overlay import OverlayRenderer


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, int(len(ordered) * fraction) - 1))]


def validate(duration_s: float) -> dict:
    stream = CameraStreamManager(source=0)
    if not stream.start():
        raise RuntimeError("camera source 0 could not be opened")
    config = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    config.write(b"{}")
    config.flush()
    config.close()
    settings = SettingsManager(config_path=config.name)
    settings.ai_coach_enabled = False
    settings.object_detection_enabled = False
    settings.pose_detection_enabled = False
    engine = CompositionEngine()
    renderer = OverlayRenderer(settings=settings)
    score = CompositionScore(
        total_score=0,
        subject_score=0,
        structure_score=0,
        balance_score=0,
        interference_score=0,
        style_score=0,
    )
    started = time.perf_counter()
    last_analysis = -1.0
    last_top_modes: tuple[str, ...] | None = None
    analysis = None
    analysis_latencies: list[float] = []
    frame_intervals: list[float] = []
    capture_fps_samples: list[float] = []
    next_fps_sample = started + 1.0
    last_frame_time = started
    frames = analyses = label_transitions = results_with_evidence = 0
    try:
        while time.perf_counter() - started < duration_s:
            frame = stream.read()
            if frame is None:
                time.sleep(0.005)
                continue
            now = time.perf_counter()
            if analysis is None or now - last_analysis >= 0.15:
                analysis_started = time.perf_counter()
                analysis = engine.analyze(frame, [], None, timestamp=now)
                analysis_latencies.append((time.perf_counter() - analysis_started) * 1000.0)
                last_analysis = now
                analyses += 1
                top_modes = tuple(mode.value for mode in analysis.top_modes)
                if last_top_modes is not None and top_modes != last_top_modes:
                    label_transitions += 1
                last_top_modes = top_modes
                if any(result.is_visible and result.evidence for result in analysis.mode_results):
                    results_with_evidence += 1
            payload = AnalysisResult(
                feedback_message="",
                score=score,
                composition_analysis=analysis,
            )
            renderer.draw(frame, payload, fps=stream.fps)
            finished = time.perf_counter()
            frame_intervals.append(finished - last_frame_time)
            last_frame_time = finished
            frames += 1
            if finished >= next_fps_sample:
                if stream.fps > 0:
                    capture_fps_samples.append(stream.fps)
                next_fps_sample += 1.0
    finally:
        stream.stop()
    elapsed = time.perf_counter() - started
    return {
        "duration_s": round(elapsed, 3),
        "input": "live camera source 0; frames not saved",
        "frames_rendered": frames,
        "analyses": analyses,
        "render_loop_fps": round(frames / elapsed, 3),
        "capture_fps_average": round(sum(capture_fps_samples) / len(capture_fps_samples), 3),
        "analysis_hz": round(analyses / elapsed, 3),
        "analysis_average_ms": round(sum(analysis_latencies) / len(analysis_latencies), 3),
        "analysis_p95_ms": round(percentile(analysis_latencies, 0.95), 3),
        "frame_interval_p95_ms": round(percentile(frame_intervals, 0.95) * 1000.0, 3),
        "label_transitions": label_transitions,
        "analyses_with_visible_evidence": results_with_evidence,
        "final_top_modes": list(last_top_modes or ()),
        "raw_frames_persisted": False,
        "network_required": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=30.0)
    arguments = parser.parse_args()
    print(json.dumps(validate(arguments.duration), ensure_ascii=False, indent=2))
