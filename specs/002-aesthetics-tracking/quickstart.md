# Quickstart & Validation: Advanced Aesthetics & Dynamic Tracking

## Setup
No new external dependencies are strictly required since we rely on `cv2` and `numpy`.
Ensure the environment is ready:
```bash
uv sync
```

## Scenario 1: Lighting & Color Evaluation
**Goal**: Verify that extreme lighting conditions trigger UI feedback.

1. Run the app:
   ```bash
   uv run python src/ui/camera_app.py
   ```
2. **Action**: Point the camera directly at a bright light source (e.g., a lamp or a window on a sunny day).
3. **Expected**: The UI should display a warning like "过曝" (Overexposed) or "逆光" (Backlit) instead of standard composition feedback.
4. **Action**: Cover the camera lens slightly to simulate a dark room.
5. **Expected**: The UI should display "欠曝" (Underexposed).

## Scenario 2: Dynamic Tracking & Shutter Prompt
**Goal**: Verify that moving objects are tracked and trigger a shutter opportunity.

1. Run the app:
   ```bash
   uv run python src/ui/camera_app.py
   ```
2. **Action**: Have a person or an object (e.g., a phone) move steadily across the camera's field of view from left to right.
3. **Expected**: The UI should draw a motion vector/arrow showing the object's predicted path.
4. **Action**: As the object approaches the left/right third intersection line, observe the UI.
5. **Expected**: The screen briefly highlights or flashes a "绝佳抓拍时机!" (Perfect Shutter Opportunity!) message before the object crosses the line.
