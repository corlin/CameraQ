# Quickstart: Professional Performance & UX Deep Optimization

## Prerequisites
- macOS with webcam access
- Python 3.12 with `uv` installed
- GEMINI_API_KEY environment variable set (for AI Coach)

## How to Validate

### 1. Performance Improvement
```bash
uv run python src/ui/camera_app.py
```
- Observe the FPS counter in the top-left corner.
- **Before**: Expect ~15-20 FPS with all modules enabled.
- **After**: Expect ≥20-25 FPS with all modules enabled (≥30% improvement).

### 2. Multi-Dimensional Score
- Point the camera at a well-composed scene (subject on a thirds line, level horizon).
- **Verification**: The bottom overlay should show sub-score breakdowns (e.g., "主体: 85 | 结构: 90 | 平衡: 75").
- Point at a poorly composed scene (subject centered, tilted camera).
- **Verification**: The weakest dimension should be highlighted differently.

### 3. Expanded Settings
- Press `Tab` to open the settings sidebar.
- **Verification**: The sidebar should slide in smoothly (~200ms).
- **Verification**: You should see categorized sections: "检测模块" (toggles), "性能参数" (numeric values).
- Toggle "Object Detection" off — verify bounding boxes vanish.

### 4. Clean Shutdown
- Press `q` to quit.
- **Verification**: Terminal should show structured log messages (not raw print).
- **Verification**: `[AICoach] Stopped.` should appear.
- **Verification**: Process exits within 2 seconds with no Python warnings about orphaned threads.
