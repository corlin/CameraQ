import numpy as np
import pytest
from src.core.analyzers.aesthetics_analyzer import AestheticsAnalyzer

def test_aesthetics_analyzer_overexposed():
    analyzer = AestheticsAnalyzer()
    # Create a completely white image (overexposed)
    image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    metrics = analyzer.analyze(image)
    
    assert metrics.is_overexposed is True
    assert metrics.is_underexposed is False
    assert metrics.brightness_level > 240
    assert "过曝" in metrics.lighting_feedback or "Overexposed" in metrics.lighting_feedback

def test_aesthetics_analyzer_underexposed():
    analyzer = AestheticsAnalyzer()
    # Create a completely black image (underexposed)
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    metrics = analyzer.analyze(image)
    
    assert metrics.is_underexposed is True
    assert metrics.is_overexposed is False
    assert metrics.brightness_level < 15
    assert "欠曝" in metrics.lighting_feedback or "Underexposed" in metrics.lighting_feedback

def test_aesthetics_analyzer_normal():
    analyzer = AestheticsAnalyzer()
    # Create a gray image (normal exposure)
    image = np.ones((100, 100, 3), dtype=np.uint8) * 128
    metrics = analyzer.analyze(image)
    
    assert metrics.is_overexposed is False
    assert metrics.is_underexposed is False
    assert 100 < metrics.brightness_level < 150
    assert metrics.lighting_feedback == ""
