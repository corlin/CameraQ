import pytest
import numpy as np
import time
import cv2
from src.core.io.camera import CameraStreamManager

def test_camera_stream_manager():
    # We can't really test a real camera without hardware, but we can test the structure
    # by passing a mock source or doing a quick setup
    
    # Use a blank video file or just verify initialization
    manager = CameraStreamManager(source=0)
    assert not manager.is_running
    
    # Start and stop quickly
    # Note: cv2.VideoCapture(0) might fail on CI/servers without a camera, 
    # so we'll wrap it and handle gracefully if camera is unavailable.
    try:
        success = manager.start()
        time.sleep(0.1)
        if success:
            assert manager.is_running
            frame = manager.read()
            # frame could be None if camera is unavailable
        else:
            assert not manager.is_running
    finally:
        manager.stop()
        assert not manager.is_running

def test_camera_software_exposure():
    camera = CameraStreamManager(source=0)
    
    # Fake a frame
    fake_frame = np.ones((100, 100, 3), dtype=np.uint8) * 100
    camera.current_frame = fake_frame
    
    # Test setting exposure
    camera.set_exposure(1.0)
    assert camera.software_exposure_compensation == 1.0
    
    # Read frame and verify it's brighter
    frame = camera.read()
    assert frame is not None
    assert frame.mean() > 100
    
    # Test negative exposure
    camera.set_exposure(-1.0)
    assert camera.software_exposure_compensation == -1.0
    frame = camera.read()
    assert frame.mean() < 100


def test_camera_start_reports_capture_initialization_error(monkeypatch):
    def raise_on_open(_source):
        raise RuntimeError("permission denied")

    monkeypatch.setattr(cv2, "VideoCapture", raise_on_open)
    camera = CameraStreamManager(source=0)

    assert not camera.start()
    assert "摄像头初始化失败" in camera.last_error
    assert camera.cap is None
