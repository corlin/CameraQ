# Implementation Plan: Analysis Toggles Sidebar

**Branch**: `005-analysis-toggles-sidebar` | **Date**: 2026-06-26 | **Spec**: [specs/005-analysis-toggles-sidebar/spec.md](file:///Users/corlin/2026/CameraQ/specs/005-analysis-toggles-sidebar/spec.md)

**Input**: Feature specification from `specs/005-analysis-toggles-sidebar/spec.md`

## Summary

This feature introduces a dynamically toggleable sidebar menu that allows users to enable or disable specific analysis modules (AI Coach, Pose Detection, Saliency Detection) to declutter the UI and save system resources. State will be persisted between sessions via a local JSON configuration file.

## User Review Required

> [!IMPORTANT]
> **Sidebar UX**: Since OpenCV doesn't have native UI frameworks beyond primitive sliders, we will render a highly aesthetic, semi-transparent sidebar using Pillow (just like our Stage 5 UI upgrades). We will capture mouse clicks using `cv2.setMouseCallback` to toggle the settings dynamically.
> To open the sidebar, the user can press the `Tab` key or click a persistent "⚙️ Settings" button/icon on the screen. **Are you okay with this custom-drawn UI approach instead of using an external UI library like Tkinter or PyQt?**

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: OpenCV, Pillow, json (standard library)

**Storage**: `config.json` file in the project root.

**Target Platform**: macOS (local execution)

**Project Type**: Desktop Python Application (Computer Vision)

## Proposed Changes

---

### Configuration Management

#### [NEW] [settings.py](file:///Users/corlin/2026/CameraQ/src/core/settings.py)
- Create a `SettingsManager` class.
- Will store boolean flags: `ai_coach_enabled`, `pose_detection_enabled`, `saliency_enabled`.
- Methods: `load()`, `save()`, `toggle(setting_name)`.
- Uses standard Python `json` to read/write from `config.json`.

---

### Core Analyzer Logic

#### [MODIFY] [analyzer.py](file:///Users/corlin/2026/CameraQ/src/core/analyzer.py)
- Update `CameraQAnalyzer.__init__` to accept a `SettingsManager` instance.
- In `process_frame`, check `settings.pose_detection_enabled` before running YOLO pose.
- Check `settings.saliency_enabled` before running Saliency.
- Check `settings.ai_coach_enabled` before hitting the `self.ai_coach.enqueue_frame` logic.
- Ensure that the resulting `AnalysisResult` gracefully handles missing data when modules are skipped.

---

### UI Rendering & Interaction

#### [MODIFY] [overlay.py](file:///Users/corlin/2026/CameraQ/src/ui/overlay.py)
- Update `OverlayRenderer` to accept a `SettingsManager` instance.
- Add rendering logic for the **Settings Sidebar**.
  - If `is_sidebar_open` is true, draw a right-aligned, semi-transparent dark panel (`alpha=200`).
  - Draw toggle switches or checkboxes for each setting.
  - Draw a subtle "Press TAB to toggle settings" prompt or a persistent gear icon when the sidebar is closed.

#### [MODIFY] [camera_app.py](file:///Users/corlin/2026/CameraQ/src/ui/camera_app.py)
- Instantiate `SettingsManager`.
- Add a mouse callback using `cv2.setMouseCallback("CameraQ Real-time Viewfinder", mouse_event_handler)`.
- The `mouse_event_handler` will check if the click intersects with the toggle button bounding boxes defined in the UI.
- Bind the `Tab` key in the `cv2.waitKey` loop to toggle the sidebar visibility state.

## Verification Plan

### Manual Verification
1. Run `uv run python src/ui/camera_app.py`.
2. Press `Tab` to open the settings sidebar.
3. Click on the "Pose Detection" toggle. Verify that the skeleton overlays instantly vanish.
4. Click on "AI Coach" toggle. Verify no new Gemini API requests are logged in the console.
5. Close the app (`q`), restart it, and verify that the toggled settings are remembered.
