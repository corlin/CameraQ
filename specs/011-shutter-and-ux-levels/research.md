# Phase 0: Outline & Research

## Technical Decisions

**Decision 1: Evaluating Shutter Opportunity (Facial State)**
- **Decision**: We will simulate/check for "eyes open" and "smiling" by adding a mock/heuristic check inside `CameraQAnalyzer` over YOLO pose keypoints, or more simply, we will emit "Perfect Shutter Opportunity" when `is_primary_subject` is True and the bounding box is in a good compositional spot (score > 85), adding a `shutter_opportunity` boolean to `AnalysisResult`. Wait, we already have `shutter_opportunity` based on intersection. We will extend it or add a specific "Perfect Portrait Shutter" based on a mock state for MVP.
- **Rationale**: Full facial expression recognition requires a heavy model (e.g., MediaPipe Face Mesh). For this UI/UX demo, we will use a simplified heuristic to trigger the feedback, focusing on the UI delivery.

**Decision 2: Coaching Level Architecture**
- **Decision**: Add `coaching_level` string enum (`OFF`, `MINIMAL`, `COACH`, `PRO`) to `SettingsManager`.
- **Rationale**: Centralized state management. 
- **Implementation**:
  - `OFF`: Hide all `ai_coaching` and structural lines.
  - `MINIMAL`: Show `ai_coaching.target_box` and `directional_arrows`, but suppress `advice_text`.
  - `COACH`: Show `ai_coaching` text, boxes, arrows.
  - `PRO`: Show everything in `COACH` plus bounding boxes, scores, and debug histograms.

**Decision 3: Parameter Prompting**
- **Decision**: `AestheticsAnalyzer` already detects `is_overexposed` and `is_underexposed`. We will bubble this up to `CameraQAnalyzer` and if severe (e.g. `brightness_level > 240`), we will trigger a high-priority proactive interaction (e.g., "Tap screen to lock exposure or enable HDR").
