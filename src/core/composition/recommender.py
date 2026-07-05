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
            return None
        candidates = [
            item
            for item in mode_results
            if item.mode in self.ACTIONABLE and item.confidence is not CompositionConfidence.LOW
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: item.match_score, reverse=True)
        strongest = candidates[0]
        if features.subject_clipped or features.subject_area_ratio > 0.45:
            distance_candidate = next(
                (item for item in candidates if item.match_score < 100), None
            )
            if distance_candidate is not None:
                return self._build(
                    distance_candidate,
                    CompositionAction.MOVE_BACK,
                    min(100, distance_candidate.match_score + 18),
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
            return self._build(strongest, CompositionAction.MOVE_CLOSER, min(100, strongest.match_score + 16), 0.2, "靠近以增强主体视觉质量")

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
            return self._build(strongest, action, min(100, strongest.match_score + 15), 0.25, "小幅旋转以对齐主方向")

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
