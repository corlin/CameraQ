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

