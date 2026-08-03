from __future__ import annotations

import math

from src.core.composition.features import CompositionFeatures
from src.core.entities import (
    CompositionAction,
    CompositionConfidence,
    CompositionMode,
    CompositionModeResult,
    NormalizedPoint,
    TargetCompositionRecommendation,
)


class CompositionRecommender:
    ACTIONABLE = {
        CompositionMode.RULE_OF_THIRDS,
        CompositionMode.BALANCED,
        CompositionMode.DYNAMIC_SYMMETRY,
        CompositionMode.HORIZONTAL,
        CompositionMode.VERTICAL,
        CompositionMode.DIAGONAL,
        CompositionMode.OBLIQUE,
        CompositionMode.RADIAL,
        CompositionMode.CENTRIPETAL,
        CompositionMode.TUNNEL,
        CompositionMode.FRAME_WITHIN_FRAME,
    }

    def recommend(
        self,
        features: CompositionFeatures,
        mode_results: list[CompositionModeResult],
    ) -> TargetCompositionRecommendation | None:
        if features.primary_focus is None:
            # Without a focus point we cannot suggest position-based movements,
            # but dominant line modes can still trigger rotation suggestions.
            line_candidates = [
                item
                for item in mode_results
                if item.mode in {
                    CompositionMode.HORIZONTAL,
                    CompositionMode.VERTICAL,
                    CompositionMode.DIAGONAL,
                    CompositionMode.OBLIQUE,
                }
                and item.confidence is CompositionConfidence.HIGH
            ]
            if line_candidates and features.lines:
                best = max(line_candidates, key=lambda item: item.match_score)
                if best.match_score >= 99:
                    return self._build(best, CompositionAction.KEEP, best.match_score, 0, "当前线构已达最佳，保持", True)
                dominant = max(features.lines, key=lambda line: line.length)
                action = (
                    CompositionAction.ROTATE_COUNTERCLOCKWISE
                    if dominant.y2 >= dominant.y1
                    else CompositionAction.ROTATE_CLOCKWISE
                )
                return self._build(best, action, min(100.0,best.match_score + 15), 0.25, "小幅旋转以对齐主方向")
            return None
        candidates = [
            item
            for item in mode_results
            if item.mode in self.ACTIONABLE and item.confidence is CompositionConfidence.HIGH
        ]
        if not candidates:
            # Check for strong non-actionable modes — prefer KEEP over
            # suggesting movement when the frame is already well-composed.
            non_actionable = [
                item
                for item in mode_results
                if item.mode not in self.ACTIONABLE
                and item.confidence is CompositionConfidence.HIGH
            ]
            non_actionable.sort(key=lambda item: item.match_score, reverse=True)
            if non_actionable and non_actionable[0].match_score >= 88:
                return self._build(
                    non_actionable[0],
                    CompositionAction.KEEP,
                    non_actionable[0].match_score,
                    0,
                    "当前构图稳定（非可执行模式），保持",
                    True,
                )
            return None
        candidates.sort(key=lambda item: item.match_score, reverse=True)
        strongest = candidates[0]
        # Cannot project improvement above 100; use KEEP for scores near ceiling.
        if strongest.match_score >= 99:
            return self._build(strongest, CompositionAction.KEEP, strongest.match_score, 0, "当前构图已达最佳，保持", True)
        if features.subject_clipped or features.subject_area_ratio > 0.45:
            distance_candidate = next(
                (item for item in candidates if item.match_score < 100), None
            )
            if distance_candidate is not None:
                return self._build(
                    distance_candidate,
                    CompositionAction.MOVE_BACK,
                    min(100.0,distance_candidate.match_score + 18),
                    0.25,
                    "后退以保留主体和结构边界",
                )
            return self._build(
                strongest,
                CompositionAction.KEEP,
                strongest.match_score,
                0,
                "当前候选已达分数上限，保持并重新取景后再评估",
                True,
            )
        if strongest.match_score >= 88:
            return self._build(strongest, CompositionAction.KEEP, strongest.match_score, 0, "当前构图稳定，保持", True)
        if 0 < features.subject_area_ratio < 0.08:
            # Guard: MOVE_CLOSER would destroy strong enclosure/tunnel/balance
            # evidence.  Check whether a high-confidence structural mode is
            # already active before suggesting a distance change.
            structural_modes = {
                item.mode
                for item in mode_results
                if item.confidence is CompositionConfidence.HIGH
                and item.match_score >= 85
                and item.mode
                in {
                    CompositionMode.FRAME_WITHIN_FRAME,
                    CompositionMode.TUNNEL,
                    CompositionMode.BALANCED,
                }
            }
            if not structural_modes:
                return self._build(strongest, CompositionAction.MOVE_CLOSER, min(100.0,strongest.match_score + 16), 0.2, "靠近以增强主体视觉质量")

        if strongest.mode in {
            CompositionMode.HORIZONTAL,
            CompositionMode.VERTICAL,
            CompositionMode.DIAGONAL,
            CompositionMode.OBLIQUE,
        } and features.lines:
            dominant = max(features.lines, key=lambda line: line.length)
            action = (
                CompositionAction.ROTATE_COUNTERCLOCKWISE
                if dominant.y2 >= dominant.y1
                else CompositionAction.ROTATE_CLOCKWISE
            )
            return self._build(strongest, action, min(100.0,strongest.match_score + 15), 0.25, "小幅旋转以对齐主方向")

        focus = features.primary_focus
        nodes = [(x, y) for x in (1 / 3, 2 / 3) for y in (1 / 3, 2 / 3)]
        target = min(nodes, key=lambda value: math.dist((focus.x, focus.y), value))
        dx, dy = target[0] - focus.x, target[1] - focus.y
        if abs(dx) >= abs(dy):
            action = CompositionAction.MOVE_LEFT if dx > 0 else CompositionAction.MOVE_RIGHT
        else:
            action = CompositionAction.TILT_UP if dy > 0 else CompositionAction.TILT_DOWN
        cost = min(1.0, math.dist((focus.x, focus.y), target) / 0.5)
        projected = min(100.0, strongest.match_score + max(8.0, 25.0 * (1.0 - cost)))
        return self._build(strongest, action, projected, cost, "微调取景使主焦点贴近目标锚点", target=target)

    @staticmethod
    def _build(
        result: CompositionModeResult,
        action: CompositionAction,
        projected: float,
        cost: float,
        reason: str,
        aligned: bool = False,
        target: tuple[float, float] | None = None,
    ) -> TargetCompositionRecommendation:
        improvement = max(0.0, projected - result.match_score)
        priority = min(1.0, (improvement / 30.0) * 0.7 + (1.0 - cost) * 0.3)
        if action is CompositionAction.KEEP:
            priority = max(priority, 0.8)
        return TargetCompositionRecommendation(
            target_mode=result.mode,
            action=action,
            reason=reason,
            current_score=result.match_score,
            projected_score=projected,
            adjustment_cost=cost,
            priority=priority,
            target_points=[NormalizedPoint(x=target[0], y=target[1])] if target else [],
            aligned=aligned,
        )
