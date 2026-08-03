from __future__ import annotations

import time

import cv2
import numpy as np

from src.core.entities import CompositionAnalysis, CompositionConfidence, CompositionMode

from .extractor import CompositionFeatureExtractor
from .scorers.linear import score_linear_modes
from .scorers.position import score_position_modes
from .scorers.topology import score_topology_modes
from .recommender import CompositionRecommender
from .temporal import CompositionTemporalFilter
from .thresholds import INSUFFICIENT_EVIDENCE_QUALITY, SCENE_CHANGE_THRESHOLD, TOP_MODE_RANKING_BONUS


def _top_mode_rank_score(item) -> float:
    bonus = TOP_MODE_RANKING_BONUS.get(item.mode, 0.0)
    if item.mode is CompositionMode.CENTRIPETAL and item.match_score >= 40.0:
        bonus += 15.0
    return item.match_score + bonus


class CompositionEngine:
    def __init__(self, extractor: CompositionFeatureExtractor | None = None):
        self.extractor = extractor or CompositionFeatureExtractor()
        self.recommender = CompositionRecommender()
        self.temporal = CompositionTemporalFilter()
        self._previous_gray = None

    def analyze(self, frame, subjects, saliency, timestamp: float | None = None) -> CompositionAnalysis:
        started = time.perf_counter()
        features = self.extractor.extract(frame, subjects, saliency)
        results = (
            score_position_modes(features)
            + score_linear_modes(features)
            + score_topology_modes(features)
        )
        if {result.mode for result in results} != set(CompositionMode):
            raise RuntimeError("composition scorer registry is incomplete")
        insufficient = features.evidence_quality < INSUFFICIENT_EVIDENCE_QUALITY
        current_gray = np.asarray(features.gray)
        scene_changed = False
        if self._previous_gray is not None and self._previous_gray.shape == current_gray.shape:
            scene_changed = float(np.mean(cv2.absdiff(self._previous_gray, current_gray))) > SCENE_CHANGE_THRESHOLD
        self._previous_gray = current_gray.copy()
        results = self.temporal.update(
            results,
            timestamp=time.monotonic() if timestamp is None else timestamp,
            scene_changed=scene_changed,
        )
        visible_candidates = [item for item in results if item.is_visible and item.evidence]
        if insufficient:
            visible_candidates = []
            results = [item.model_copy(update={"is_visible": False}) for item in results]
        elif sum(item.confidence is CompositionConfidence.HIGH for item in visible_candidates) >= 3:
            # Medium-confidence cues expand an under-filled Top 3, but never
            # displace three already-stable high-confidence modes.
            visible_candidates = [
                item
                for item in visible_candidates
                if item.confidence is CompositionConfidence.HIGH
            ]
        visible_candidates.sort(
            key=lambda item: (
                _top_mode_rank_score(item),
                item.confidence is CompositionConfidence.HIGH,
                item.match_score,
            ),
            reverse=True,
        )
        top_modes = [item.mode for item in visible_candidates[:3]]
        top_set = set(top_modes)
        results = [item.model_copy(update={"is_visible": item.mode in top_set}) for item in results]
        recommendation = None
        if not insufficient:
            recommendation = self.recommender.recommend(
                features, [item for item in results if item.is_visible]
            )
        return CompositionAnalysis(
            timestamp=time.monotonic() if timestamp is None else timestamp,
            frame_width=features.frame_width,
            frame_height=features.frame_height,
            evidence_quality=features.evidence_quality,
            mode_results=results,
            top_modes=top_modes,
            recommendation=recommendation,
            insufficient_evidence=insufficient,
            processing_time_ms=(time.perf_counter() - started) * 1000.0,
        )
