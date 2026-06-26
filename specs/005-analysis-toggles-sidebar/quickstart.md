# Quickstart: Analysis Toggles Sidebar

## How to test the feature

1. Run the CameraQ application:
   ```bash
   uv run python src/ui/camera_app.py
   ```

2. **Open the Sidebar**:
   - Press the `Tab` key while focused on the CameraQ window.
   - The settings sidebar should animate or draw on the right edge of the screen.

3. **Toggle Features**:
   - Use your mouse to click on the toggle switches for "Pose Detection", "AI Coach", or "Saliency Detection".
   - **Verification**: Observe that the related overlays (e.g., skeletons for pose detection) disappear immediately from the screen without needing to restart the app.

4. **Verify Persistence**:
   - With some features toggled OFF, press `q` to quit the application.
   - Run the application again using `uv run python src/ui/camera_app.py`.
   - **Verification**: Ensure the previously disabled features remain OFF when the application starts up.
