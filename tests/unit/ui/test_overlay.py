import pytest
import numpy as np
from src.ui.overlay import OverlayRenderer
from src.core.entities import AnalysisResult, CompositionScore

def test_overlay_renderer():
    renderer = OverlayRenderer()
    
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    
    # Mock analysis result
    result = AnalysisResult(
        image_with_overlays=img,
        feedback_message="测试反馈: 向左移动",
        score=CompositionScore(total_score=85, subject_score=80, structure_score=90, balance_score=85, interference_score=90, style_score=80),
        recommended_crops=[]
    )
    
    out_img = renderer.draw(img, result, fps=30.0)
    
    assert out_img is not None
    assert out_img.shape == (400, 600, 3)
    # The output image should have been modified (text drawn)
    # but exact pixel check is brittle, so just verifying it returns a valid image.
