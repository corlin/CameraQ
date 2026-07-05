import pytest
import numpy as np
from src.core.entities import DetectedSubject, BoundingBox, SaliencyMap, FusedSubject, SourceType
from src.core.analyzer import CameraQAnalyzer

def test_saliency_fusion():
    analyzer = CameraQAnalyzer()
    
    # Mocking YOLO output
    yolo_subjects = [
        DetectedSubject(subject_id="1", class_name="car", confidence=0.8, 
                       bounding_box=BoundingBox(x=10, y=10, width=50, height=50),
                       is_primary_subject=True)
    ]
    
    # Mocking Saliency output (a huge salient blob, e.g., a cloud)
    saliency_map = SaliencyMap(
        heatmap=np.zeros((1,1)), 
        bounding_boxes=[BoundingBox(x=100, y=100, width=300, height=300)],
        max_salient_score=0.9
    )
    
    # Fuse
    fused_subjects = analyzer._fuse_subjects(yolo_subjects, saliency_map, img_area=800*600)
    
    # The salient blob is much larger (90,000 area) vs car (2,500 area).
    # The salient blob should become the primary subject.
    assert len(fused_subjects) == 2
    
    primary = next((s for s in fused_subjects if s.is_primary_subject), None)
    assert primary is not None
    assert primary.source == SourceType.SALIENCY
    assert primary.class_name == "显著主体"
    
def test_yolo_wins_if_saliency_small():
    analyzer = CameraQAnalyzer()
    
    yolo_subjects = [
        DetectedSubject(subject_id="1", class_name="person", confidence=0.9, 
                       bounding_box=BoundingBox(x=100, y=100, width=200, height=400),
                       is_primary_subject=True)
    ]
    
    saliency_map = SaliencyMap(
        heatmap=np.zeros((1,1)), 
        bounding_boxes=[BoundingBox(x=10, y=10, width=20, height=20)],
        max_salient_score=0.2
    )
    
    fused_subjects = analyzer._fuse_subjects(yolo_subjects, saliency_map, img_area=800*600)
    
    primary = next((s for s in fused_subjects if s.is_primary_subject), None)
    assert primary is not None
    assert primary.source == SourceType.YOLO
    assert primary.class_name == "person"


def test_multiple_detected_subjects_have_one_deterministic_primary():
    analyzer = CameraQAnalyzer()
    yolo_subjects = [
        DetectedSubject(
            subject_id="small",
            class_name="person",
            confidence=0.95,
            bounding_box=BoundingBox(x=20, y=20, width=40, height=60),
        ),
        DetectedSubject(
            subject_id="large",
            class_name="person",
            confidence=0.85,
            bounding_box=BoundingBox(x=180, y=80, width=120, height=160),
        ),
    ]
    saliency_map = SaliencyMap(
        heatmap=np.zeros((1, 1)),
        bounding_boxes=[],
        max_salient_score=0.0,
    )

    fused = analyzer._fuse_subjects(yolo_subjects, saliency_map, img_area=320 * 240)

    primaries = [subject for subject in fused if subject.is_primary_subject]
    assert len(primaries) == 1
    assert primaries[0].subject_id == "large"

from unittest.mock import patch, MagicMock

@patch("src.core.gemini_client.genai.Client")
def test_analyzer_scene_context_async(mock_client_class):
    # Just test that process_frame doesn't block and enqueues the frame
    analyzer = CameraQAnalyzer()
    analyzer.settings.gemini_api_key = "fake_key"
    
    # Fast forward time to trigger enqueue
    import time
    analyzer._last_scene_time = time.time() - 11.0
    
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Process frame
    result = analyzer.process_frame(frame)
    
    # Result shouldn't have scene context yet (it's async)
    assert result.current_scene_context is None
    
    # Check that _last_scene_time was updated, indicating we enqueued
    import time
    assert analyzer._last_scene_time > time.time() - 1.0


def test_process_frame_populates_optional_composition_analysis():
    from src.core.settings import SettingsManager

    settings = SettingsManager()
    settings.object_detection_enabled = False
    settings.pose_detection_enabled = False
    settings.ai_coach_enabled = False
    analyzer = CameraQAnalyzer(settings)
    frame = np.zeros((240, 320, 3), dtype=np.uint8)

    result = analyzer.process_frame(frame)

    assert result.composition_analysis is not None
    assert len(result.composition_analysis.mode_results) == 15
    assert result.score.total_score >= 0


def test_composition_engine_receives_fused_subjects_and_saliency(monkeypatch):
    from src.core.settings import SettingsManager

    settings = SettingsManager()
    settings.pose_detection_enabled = False
    settings.ai_coach_enabled = False
    analyzer = CameraQAnalyzer(settings)
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    captured = {}
    original = analyzer.composition_engine.analyze

    def capture(frame_arg, subjects_arg, saliency_arg, **kwargs):
        captured["subjects"] = subjects_arg
        captured["saliency"] = saliency_arg
        return original(frame_arg, subjects_arg, saliency_arg, **kwargs)

    monkeypatch.setattr(analyzer.composition_engine, "analyze", capture)
    analyzer.process_frame(frame)

    assert isinstance(captured["subjects"], list)
    assert captured["saliency"] is not None


def test_composition_analysis_uses_monotonic_time_gate_and_cache(monkeypatch):
    from src.core.settings import SettingsManager

    settings = SettingsManager()
    settings.object_detection_enabled = False
    settings.pose_detection_enabled = False
    settings.saliency_enabled = False
    settings.ai_coach_enabled = False
    settings.composition_detection_enabled = True
    settings.composition_analysis_interval_s = 0.15
    analyzer = CameraQAnalyzer(settings)
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    now = [0.0]
    analyzer._composition_clock = lambda: now[0]
    calls = 0
    original = analyzer.composition_engine.analyze

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(analyzer.composition_engine, "analyze", counted)
    first = analyzer.process_frame(frame).composition_analysis
    now[0] = 0.10
    cached = analyzer.process_frame(frame).composition_analysis
    now[0] = 0.16
    refreshed = analyzer.process_frame(frame).composition_analysis
    assert calls == 2
    assert cached is first
    assert refreshed is not None


def test_composition_gate_achieves_five_updates_per_second(monkeypatch):
    from src.core.settings import SettingsManager

    settings = SettingsManager()
    settings.object_detection_enabled = False
    settings.pose_detection_enabled = False
    settings.saliency_enabled = False
    settings.ai_coach_enabled = False
    settings.composition_analysis_interval_s = 0.15
    analyzer = CameraQAnalyzer(settings)
    frame = np.zeros((60, 80, 3), dtype=np.uint8)
    now = [0.0]
    analyzer._composition_clock = lambda: now[0]
    calls = 0
    original = analyzer.composition_engine.analyze

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(analyzer.composition_engine, "analyze", counted)
    for step in range(201):
        now[0] = step * 0.05
        analyzer.process_frame(frame)
    assert calls >= 50


def test_composition_can_be_disabled_and_failure_keeps_cached_result(monkeypatch):
    from src.core.settings import SettingsManager

    settings = SettingsManager()
    settings.object_detection_enabled = False
    settings.pose_detection_enabled = False
    settings.saliency_enabled = False
    settings.ai_coach_enabled = False
    analyzer = CameraQAnalyzer(settings)
    frame = np.zeros((60, 80, 3), dtype=np.uint8)
    first = analyzer.process_frame(frame).composition_analysis
    analyzer._composition_clock = lambda: 999.0
    monkeypatch.setattr(analyzer.composition_engine, "analyze", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    assert analyzer.process_frame(frame).composition_analysis is first
    settings.composition_detection_enabled = False
    assert analyzer.process_frame(frame).composition_analysis is None
