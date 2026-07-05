"""Capture one CameraQ live-view frame with the production overlay renderer."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.analyzer import CameraQAnalyzer  # noqa: E402
from src.core.io.camera import CameraStreamManager  # noqa: E402
from src.core.settings import SettingsManager  # noqa: E402
from src.ui.overlay import OverlayRenderer  # noqa: E402


def capture(output: Path, *, source: int = 0, warmup_seconds: float = 2.0) -> None:
    stream = CameraStreamManager(source=source)
    if not stream.start():
        raise RuntimeError(f"camera source {source} could not be started")

    settings = SettingsManager()
    analyzer = CameraQAnalyzer(settings=settings)
    renderer = OverlayRenderer(settings=settings)
    deadline = time.monotonic() + warmup_seconds
    frame = None
    analysis = None

    try:
        while time.monotonic() < deadline or frame is None or analysis is None:
            frame = stream.read()
            if frame is None:
                time.sleep(0.02)
                continue
            analysis = analyzer.process_frame(frame)
            time.sleep(0.05)

        rendered = renderer.draw(frame, analysis, fps=stream.fps)
        output.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(output), rendered):
            raise RuntimeError(f"failed to write screenshot: {output}")
    finally:
        analyzer.ai_coach.stop()
        stream.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source", type=int, default=0)
    parser.add_argument("--warmup-seconds", type=float, default=2.0)
    args = parser.parse_args()
    capture(args.output, source=args.source, warmup_seconds=args.warmup_seconds)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
