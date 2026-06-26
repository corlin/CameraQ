from typing import List, Tuple
from ..entities import DetectedSubject, CropRecommendation, CropStyle, BoundingBox

def generate_crops(subjects: List[DetectedSubject], image_width: int, image_height: int) -> List[CropRecommendation]:
    """
    Generates recommended crops based on the primary subject.
    For MVP, we generate a Rule of Thirds crop, a Centered square crop, and a Social Vertical crop.
    """
    crops = []
    
    primary = next((s for s in subjects if s.is_primary_subject), None)
    if not primary and subjects:
        primary = subjects[0] # Fallback to first
        
    if not primary:
        return crops # No subjects, no crops recommended
        
    # Simplified logic: ensure the crop contains the primary subject
    cx = primary.bounding_box.x + primary.bounding_box.width / 2
    cy = primary.bounding_box.y + primary.bounding_box.height / 2
    
    # 1. Centered 1:1
    size_11 = min(image_width, image_height) * 0.8
    crops.append(CropRecommendation(
        crop_style=CropStyle.CENTERED,
        bounding_box=BoundingBox(
            x=max(0, cx - size_11 / 2),
            y=max(0, cy - size_11 / 2),
            width=min(size_11, image_width - max(0, cx - size_11 / 2)),
            height=min(size_11, image_height - max(0, cy - size_11 / 2))
        ),
        reasoning="中心对称构图，突出主体。"
    ))
    
    # 2. Social Vertical (9:16)
    w_916 = min(image_width, image_height * 9 / 16) * 0.8
    h_916 = w_916 * 16 / 9
    crops.append(CropRecommendation(
        crop_style=CropStyle.SOCIAL_VERTICAL,
        bounding_box=BoundingBox(
            x=max(0, cx - w_916 / 2),
            y=max(0, cy - h_916 / 2),
            width=min(w_916, image_width - max(0, cx - w_916 / 2)),
            height=min(h_916, image_height - max(0, cy - h_916 / 2))
        ),
        reasoning="适合社交媒体(9:16)的竖屏构图。"
    ))
    
    return crops
