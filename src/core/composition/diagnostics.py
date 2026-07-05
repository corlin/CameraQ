from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import threading
import time
import uuid

from src.core.entities import CompositionAnalysis

logger = logging.getLogger(__name__)


class CompositionDiagnostics:
    def __init__(
        self,
        directory: str | Path | None = None,
        *,
        enabled: bool = False,
        max_records: int = 300,
        max_file_bytes: int = 20 * 1024 * 1024,
        retention_days: int = 7,
    ):
        self.directory = Path(directory) if directory else Path.home() / ".cameraq" / "diagnostics" / "composition"
        self.enabled = enabled
        self.max_file_bytes = max_file_bytes
        self.retention_seconds = retention_days * 24 * 60 * 60
        self._records = deque(maxlen=max_records)
        self._session_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
        self._file_index = 0
        self._lock = threading.Lock()
        self._cleanup_expired()

    @property
    def records(self) -> list[dict]:
        with self._lock:
            return list(self._records)

    def add(self, analysis: CompositionAnalysis, scene_changed: bool = False) -> None:
        record = self._to_record(analysis, scene_changed)
        with self._lock:
            self._records.append(record)
            if not self.enabled:
                return
            try:
                self.directory.mkdir(parents=True, exist_ok=True)
                self._cleanup_expired_locked()
                line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
                encoded = line.encode("utf-8")
                path = self._current_path()
                if path.exists() and path.stat().st_size + len(encoded) > self.max_file_bytes:
                    self._file_index += 1
                    path = self._current_path()
                with path.open("ab") as handle:
                    handle.write(encoded)
            except Exception as exc:
                logger.warning("Composition diagnostics write failed: %s", exc)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
            if self.directory.exists():
                for path in self.directory.glob("*.ndjson"):
                    try:
                        path.unlink()
                    except OSError as exc:
                        logger.warning("Failed to clear composition diagnostic %s: %s", path, exc)

    def _current_path(self) -> Path:
        return self.directory / f"{self._session_id}-{self._file_index:03d}.ndjson"

    def _cleanup_expired(self) -> None:
        with self._lock:
            self._cleanup_expired_locked()

    def _cleanup_expired_locked(self) -> None:
        if not self.directory.exists():
            return
        cutoff = time.time() - self.retention_seconds
        for path in self.directory.glob("*.ndjson"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
            except OSError as exc:
                logger.warning("Failed to inspect composition diagnostic %s: %s", path, exc)

    @staticmethod
    def _to_record(analysis: CompositionAnalysis, scene_changed: bool) -> dict:
        visible = [item for item in analysis.mode_results if item.is_visible]
        recommendation = None
        if analysis.recommendation is not None:
            recommendation = {
                "target_mode": analysis.recommendation.target_mode.value,
                "action": analysis.recommendation.action.value,
                "reason": analysis.recommendation.reason,
            }
        return {
            "timestamp": analysis.timestamp,
            "visible_modes": [mode.value for mode in analysis.top_modes],
            "mode_summaries": [
                {
                    "mode": item.mode.value,
                    "match_score": item.match_score,
                    "confidence": item.confidence.value,
                    "evidence": [entry.description for entry in item.evidence],
                }
                for item in visible
            ],
            "recommendation": recommendation,
            "evidence_quality": analysis.evidence_quality,
            "scene_changed": scene_changed,
        }
