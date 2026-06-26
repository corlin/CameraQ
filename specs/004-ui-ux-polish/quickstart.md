# Quickstart: UI/UX Aesthetics Polish Validation

This guide explains how to validate the newly styled visual auxiliary lines and prompt durations in CameraQ.

## Prerequisites

- CameraQ installed with its dependencies (`uv run`).

## Validation Scenarios

### Scenario 1: Verify Aesthetics of Grid and Bounding Boxes
1. Run the app: `uv run python src/ui/camera_app.py`
2. Present a subject (e.g., a person or cup) to the camera.
3. Observe the rule of thirds grid (if enabled) and the object bounding box.
4. **Expected Outcome**: The lines should be elegant (e.g., semi-transparent white or sleek colors) instead of stark, thick RGB lines. The text labels should have a background plate for high contrast readability.

### Scenario 2: Verify AI Coaching Text Fading
1. Run the app.
2. Press the `c` key to force an AI coaching request.
3. Wait for the advice bubble to appear at the top center of the screen.
4. Count to 10 seconds.
5. **Expected Outcome**: The advice bubble should completely disappear from the screen exactly 10 seconds after it appeared, preventing screen clutter.
