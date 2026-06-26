import pytest
from src.core.entities import DetectedSubject, BoundingBox, CropStyle
from src.core.rules.cropping import generate_crops

def test_generate_crops():
    subject = DetectedSubject(
        subject_id="1",
        class_name="person",
        confidence=0.9,
        bounding_box=BoundingBox(x=100, y=100, width=200, height=200),
        is_primary_subject=True
    )
    crops = generate_crops([subject], 1000, 1000)
    
    assert len(crops) == 2
    assert crops[0].crop_style == CropStyle.CENTERED
    assert crops[1].crop_style == CropStyle.SOCIAL_VERTICAL
    
    # Check boundaries for centered crop
    # Center of subject is (200, 200). Image is 1000x1000.
    # size = 1000 * 0.8 = 800
    # Center crop should try to be around 200,200.
    assert crops[0].bounding_box.width <= 800
    assert crops[0].bounding_box.height <= 800

def test_generate_crops_no_subject():
    crops = generate_crops([], 1000, 1000)
    assert len(crops) == 0
