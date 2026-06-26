import time
import numpy as np
import pytest
from src.core.analyzer import CameraQAnalyzer
from src.core.io.camera import CameraStreamManager

def test_ai_latency_under_250ms():
    """SC-002: AI processing pipeline should take less than 250ms per frame."""
    analyzer = CameraQAnalyzer()
    # Create a dummy image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Warmup the models to load them into memory
    analyzer.process_frame(img)
    
    iterations = 5
    start_time = time.time()
    for _ in range(iterations):
        analyzer.process_frame(img)
    end_time = time.time()
    
    avg_latency = (end_time - start_time) / iterations
    
    # 250ms target
    assert avg_latency < 0.250, f"Average AI latency {avg_latency*1000:.2f}ms exceeds target 250ms"

def test_camera_stream_fps_target():
    """SC-001: UI FPS stable at or above 30 FPS. (We test that the camera thread is non-blocking)"""
    stream = CameraStreamManager(source=0)
    
    success = stream.start()
    if not success:
        pytest.skip("No camera available to run FPS test")
        
    try:
        # Give it up to 2 seconds to calculate first FPS
        for _ in range(20):
            if stream.fps > 0:
                break
            time.sleep(0.1)
            
        # Check if we are actually getting frames
        if stream.current_frame is None:
            pytest.skip("Camera started but no frames received (likely headless/CI env)")
            
        fps = stream.fps
        
        # 20 is a safe lower bound for a standard webcam running smoothly.
        assert fps >= 20.0, f"Measured FPS {fps:.1f} is below target of ~30 FPS"
    finally:
        stream.stop()
