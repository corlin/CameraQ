# Research & Technical Decisions: Advanced Aesthetics & Dynamic Tracking

## Decision: OpenCV Histograms for Lighting and Color
- **Decision**: Use OpenCV's `cv2.calcHist` and HSV color space conversions.
- **Rationale**: extremely fast, easily integrated with the existing OpenCV pipeline, sufficient for basic over/underexposure detection and color harmony heuristics (e.g. tracking dominant hues).
- **Alternatives considered**: PyTorch-based image quality assessment models (NIMA). Rejected because it adds significant latency (violating the <250ms constraint) and increases dependencies.

## Decision: SORT/Centroid Tracking for Dynamic Tracking
- **Decision**: Implement a lightweight SORT (Simple Online and Realtime Tracking) or Centroid-based tracker.
- **Rationale**: Since we already have bounding boxes from YOLO/Saliency, we can track them across frames using IoU (Intersection over Union) matching and simple Kalman filtering (or just centroid distance) to keep object IDs consistent and predict short-term trajectories.
- **Alternatives considered**: `cv2.TrackerCSRT_create()` or DeepSORT. OpenCV's built-in trackers are decent but require initializing per object and don't natively ingest YOLO outputs. DeepSORT requires an extra Re-ID network. Simple IoU/Centroid tracker is faster and adequate for our shutter timing predictions.

## Decision: Shutter Timing Prediction
- **Decision**: Calculate velocity of the tracked centroid. If the centroid is moving towards a "Rule of Thirds" intersection and will arrive within the next 300ms, trigger a "Shutter Opportunity" prompt.
- **Rationale**: Simple vector math is fast.
- **Alternatives considered**: Reinforcement learning for timing prediction. Too complex for MVP.
