from __future__ import annotations

from dataclasses import dataclass

from src.core.entities import CompositionConfidence, CompositionMode, CompositionModeResult

from .thresholds import enter_score, exit_score


@dataclass
class ModeTemporalRecord:
    state: str = "ABSENT"
    above_enter_count: int = 0
    below_exit_count: int = 0
    state_since: float = 0.0


class CompositionTemporalFilter:
    def __init__(self):
        self.records = {mode: ModeTemporalRecord() for mode in CompositionMode}
        self._has_seen_frame = False

    def reset(self):
        self.records = {mode: ModeTemporalRecord() for mode in CompositionMode}
        self._has_seen_frame = False

    def update(
        self,
        mode_results: list[CompositionModeResult],
        timestamp: float,
        scene_changed: bool = False,
    ) -> list[CompositionModeResult]:
        if scene_changed:
            self.reset()
        first_frame = not self._has_seen_frame
        output = []
        for item in mode_results:
            record = self.records[item.mode]
            enter_threshold = enter_score(item.mode)
            exit_threshold = exit_score(item.mode)
            high_evidence = item.confidence is CompositionConfidence.HIGH
            if first_frame and high_evidence and item.match_score >= enter_threshold:
                record.state = "ACTIVE"
                record.state_since = timestamp
                record.above_enter_count = 3
            elif record.state == "ACTIVE":
                if item.match_score < exit_threshold:
                    record.below_exit_count += 1
                    if record.below_exit_count >= 3:
                        record.state = "ABSENT"
                        record.state_since = timestamp
                        record.above_enter_count = 0
                else:
                    record.below_exit_count = 0
            elif high_evidence and item.match_score >= enter_threshold:
                record.state = "CANDIDATE"
                record.above_enter_count += 1
                record.below_exit_count = 0
                if record.above_enter_count >= 3:
                    record.state = "ACTIVE"
                    record.state_since = timestamp
            elif item.match_score < exit_threshold:
                record.state = "ABSENT"
                record.above_enter_count = 0
                record.below_exit_count = 0

            visible = record.state == "ACTIVE"
            stable_ms = max(0, int((timestamp - record.state_since) * 1000)) if visible else 0
            output.append(item.model_copy(update={"is_visible": visible, "stable_for_ms": stable_ms}))
        self._has_seen_frame = True
        return output
