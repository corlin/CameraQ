# Quickstart & Validation

## Prerequisites
- macOS system with Python 3.12 (uv)
- CameraQ repository correctly configured with `.env` / `GEMINI_API_KEY`

## Run the Application
1. Start the camera app:
   ```bash
   uv run python src/ui/camera_app.py
   ```

## Validation Scenarios

### Scenario 1: Top Bar Scene Context
1. Place the camera in a distinct scene (e.g., bright lighting).
2. Wait for the LLM to analyze the scene context.
3. **Expect**: The top bar displays minimalist icons + text (e.g., `☀️ Bright | ⛰️ Outdoor`) in a small, rounded badge. It must NOT span the entire width of the screen with verbose text.

### Scenario 2: AI Coach Timeout & Collapse
1. Enable AI Coaching in the Settings panel (Press `TAB`).
2. Point the camera at a scene that triggers feedback.
3. **Expect**: A subtle pop-up or pill notification appears showing the full wrapped text.
4. Wait 5-7 seconds.
5. **Expect**: The text automatically collapses into a small icon/badge (e.g., `💬 Insight`), ensuring the screen returns to a clean state.

### Scenario 3: Bounding Box Aesthetics
1. Show a clear subject (e.g., your face) to the camera.
2. **Expect**: The bounding box uses thin borders (1px or 2px) or corner brackets (reticles) instead of a solid, thick box.

### Scenario 4: Central Area Obstruction
1. Throughout all the above tests, observe the exact center of the screen (the middle 50%).
2. **Expect**: No AI text overlays or opaque boxes ever cover this area.
