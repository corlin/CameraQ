# Quickstart: Validation Guide for Real-time Saliency MVP

This guide outlines how to validate the end-to-end functionality of the real-time viewfinder and saliency integration once implementation is complete.

## Setup
Ensure you have activated the environment and installed the dependencies (including any new Saliency library):
```bash
uv sync
```

## Running the Real-time Viewfinder
Start the new real-time camera app:
```bash
uv run python src/ui/camera_app.py
```
*(Note: A new entry point `camera_app.py` using OpenCV `cv2.imshow` or Gradio's WebRTC plugin will be created during implementation).*

## Validation Scenarios

### 1. Frame Rate Check
- **Action**: Wave your hand in front of the camera.
- **Expectation**: The video stream should feel smooth and responsive. The terminal or UI overlay should report ~30 FPS for the render loop, while the AI inference might run at ~5-10 FPS in the background.

### 2. Saliency Override (The "Heart-shaped Cloud" Test)
- **Action**: Point the camera at a scene containing a standard COCO object (e.g., a toy car) AND a highly salient but non-standard object (e.g., a bright glowing shape on a screen, or a brightly colored abstract item).
- **Expectation**: The system should highlight the non-standard object as the `Primary Subject` (with a `saliency_blob` label) instead of defaulting to the car, and center/composition rules should be calculated relative to this salient blob.

### 3. Dynamic UI Feedback
- **Action**: Move the camera so the primary subject is pushed to the far left edge of the frame.
- **Expectation**: A clean text prompt like "向右微调机位" appears dynamically. When you center the subject, the text changes to "构图完美" and then disappears.
