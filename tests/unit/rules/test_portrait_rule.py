import pytest
from src.core.entities import DetectedSubject, BoundingBox, Keypoint, PriorityLevel, ActionType
from src.core.rules.portrait_rule import analyze_portrait

def test_analyze_portrait_headroom_too_small():
    # Setup
    subject = DetectedSubject(
        subject_id="1",
        class_name="person",
        confidence=0.9,
        bounding_box=BoundingBox(x=100, y=10, width=200, height=800), # y=10 is very small, 10/1000 = 0.01
        is_primary_subject=True,
        keypoints=[Keypoint(x=100, y=100, confidence=0.9)] # Just one valid keypoint
    )
    feedbacks = analyze_portrait(subject, 1000, 1000)
    assert len(feedbacks) >= 1
    assert feedbacks[0].action_type == ActionType.TILT_UP

def test_analyze_portrait_headroom_too_large():
    # Setup
    subject = DetectedSubject(
        subject_id="2",
        class_name="person",
        confidence=0.9,
        bounding_box=BoundingBox(x=100, y=400, width=200, height=500), # y=400, 400/1000 = 0.4
        is_primary_subject=True,
        keypoints=[Keypoint(x=100, y=100, confidence=0.9)] 
    )
    feedbacks = analyze_portrait(subject, 1000, 1000)
    assert len(feedbacks) >= 1
    assert feedbacks[0].action_type == ActionType.TILT_DOWN

def test_analyze_portrait_awkward_crop_wrist():
    # Setup
    # COCO keypoints: 9: L_Wrist
    kpts = [Keypoint(x=0, y=0, confidence=0.0)] * 17
    kpts[9] = Keypoint(x=10, y=500, confidence=0.9) # x=10 is < 5% of 1000
    subject = DetectedSubject(
        subject_id="3",
        class_name="person",
        confidence=0.9,
        bounding_box=BoundingBox(x=10, y=100, width=200, height=800),
        is_primary_subject=True,
        keypoints=kpts
    )
    feedbacks = analyze_portrait(subject, 1000, 1000)
    # The wrist is close to the edge
    assert any(fb.action_type == ActionType.MOVE_BACK and "手部边缘" in fb.message for fb in feedbacks)

def test_analyze_portrait_awkward_crop_ankle():
    # Setup
    # COCO keypoints: 15: L_Ankle
    kpts = [Keypoint(x=0, y=0, confidence=0.0)] * 17
    kpts[15] = Keypoint(x=500, y=980, confidence=0.9) # y=980 is > 95% of 1000
    subject = DetectedSubject(
        subject_id="4",
        class_name="person",
        confidence=0.9,
        bounding_box=BoundingBox(x=100, y=100, width=200, height=880),
        is_primary_subject=True,
        keypoints=kpts
    )
    feedbacks = analyze_portrait(subject, 1000, 1000)
    assert any(fb.action_type == ActionType.MOVE_BACK and "脚部边缘" in fb.message for fb in feedbacks)
