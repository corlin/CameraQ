# Quickstart: AI Scenario Templates

## Prerequisites
- UV installed and CameraQ environment set up.
- Mac camera access granted.

## Validation Scenarios

### Scenario 1: Ghost Target Box and Arrows (Mock Data)
**Purpose**: Verify the UI renderer correctly draws the ghost box and arrows.
1. Run the app: `uv run python src/ui/camera_app.py`
2. Force the analyzer (or mock it) to return an `AICoaching` object with:
   - `target_box = (100, 100, 300, 400)`
   - `directional_arrows = ["LEFT", "UP"]`
3. **Verify**: A translucent box appears at the specified coordinates.
4. **Verify**: Arrows `←` and `↑` appear prominently on the left and top edges of the screen.

### Scenario 2: Portrait Template Active
**Purpose**: Verify that pointing the camera at a person switches the active template to Portrait.
1. Run the app: `uv run python src/ui/camera_app.py`
2. Point the camera at a person's face.
3. **Verify**: The AI Coach UI pill indicates `Template: Portrait`.
4. **Verify**: The ghost box suggests a standard headroom and rule-of-thirds eye placement.

### Scenario 3: Vlog Mode Aspect Ratio (9:16)
**Purpose**: Verify the Vlog template enforces vertical video framing.
1. Run the app: `uv run python src/ui/camera_app.py`
2. Point the camera at a scene.
3. If the analyzer sets `active_template = "Vlog"`, **Verify** that the ghost box draws a 9:16 vertical rectangle in the center of the screen, even if the camera feed is 16:9.
