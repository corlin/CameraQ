# CameraQ - Research & Decisions

## 1. Demo Frontend Framework
- **Decision**: Use **Gradio** for the Stage 1 offline image analysis demo.
- **Rationale**: Gradio is built for Python and perfectly integrates with machine learning models (YOLO, OpenCV). It allows rapid building of an image upload -> inference -> result display UI without needing a separate frontend team or complex React/Vue setups.
- **Alternatives considered**: 
  - Streamlit: Good, but Gradio is slightly more tailored for computer vision image in/out pipelines.
  - React + FastAPI: Too heavy for the Stage 1 4-6 weeks prototype.

## 2. Model Pipeline Orchestration
- **Decision**: Combine Ultralytics YOLOv11 for object detection/segmentation with traditional OpenCV algorithms for lines/horizon.
- **Rationale**: YOLO11 is state-of-the-art for real-time edge/server inference. OpenCV `HoughLinesP` is computationally cheap and robust enough for horizon and architectural line detection.
- **Alternatives considered**: 
  - Deep learning models for horizon detection: Unnecessary overhead for MVP.

## 3. Pose/Face Detection
- **Decision**: Use YOLO11-Pose for human body keypoints.
- **Rationale**: Reusing the YOLO family keeps the dependency tree smaller and allows unified ONNX export later. It also provides bounding boxes and keypoints simultaneously.
- **Alternatives considered**: MediaPipe Pose. MediaPipe is great but requires a separate pipeline alongside YOLO. Can be reconsidered for the mobile-native version.
