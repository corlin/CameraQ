# Quickstart: Shutter Feedback & UX Levels

## Validation Scenarios

### Scenario 1: Toggling Coaching Levels
1. Run the app: `uv run python src/ui/camera_app.py`
2. The UI should display a new button for "Coaching Level" or map it to a keybinding (e.g., press 'C').
3. **Verify [OFF]**: All AI boxes, arrows, and texts disappear. The scene context top bar is still visible but nothing else.
4. **Verify [MINIMAL]**: The ghost target box and directional arrows appear, but the text "🤖 提示: ..." is hidden.
5. **Verify [COACH]**: The ghost box, arrows, and one-line text advice appear.
6. **Verify [PRO]**: The coach overlays appear PLUS the green YOLO bounding boxes, the radar sub-scores, and FPS metrics.

### Scenario 2: Perfect Shutter Flash
1. Ensure Coaching Level is COACH or PRO.
2. Point the camera at a scene.
3. Simulate a "perfect shutter" moment by triggering `shutter_opportunity = True` (e.g. by intercepting a composition node).
4. **Verify**: A prominent visual flash or text appears ("✨ 绝佳抓拍时机!").

### Scenario 3: Parameter Feedback
1. Simulate a severely overexposed/backlit image input.
2. **Verify**: A high-priority warning message appears in the coach UI or center screen: "建议开启 HDR 或点击锁定曝光".
