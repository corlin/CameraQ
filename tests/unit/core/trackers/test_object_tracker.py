import pytest
from src.core.entities import DetectedSubject, BoundingBox, TrackedSubject
from src.core.trackers.object_tracker import ObjectTracker

def test_object_tracker_new_subject():
    tracker = ObjectTracker()
    subject = DetectedSubject(
        subject_id="yolo_1",
        class_name="person",
        confidence=0.9,
        bounding_box=BoundingBox(x=10, y=10, width=50, height=100)
    )
    tracked = tracker.update([subject])
    assert len(tracked) == 1
    assert tracked[0].track_id == 0
    assert len(tracked[0].history) == 1

def test_object_tracker_velocity():
    tracker = ObjectTracker()
    # Frame 1
    tracker.update([DetectedSubject(
        subject_id="1", class_name="person", confidence=0.9,
        bounding_box=BoundingBox(x=10, y=10, width=50, height=100)
    )])
    # Frame 2
    tracked = tracker.update([DetectedSubject(
        subject_id="2", class_name="person", confidence=0.9,
        bounding_box=BoundingBox(x=20, y=10, width=50, height=100) # Moved right by 10
    )])
    
    assert len(tracked) == 1
    assert tracked[0].track_id == 0 # Should match the same track
    assert tracked[0].velocity_x == 10.0
    assert tracked[0].velocity_y == 0.0
