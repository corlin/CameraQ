# Implementation Plan: Alignment and Clutter

**Branch**: `[012-alignment-and-clutter]` | **Date**: 2026-06-27 | **Spec**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/012-alignment-and-clutter/spec.md)

**Input**: Feature specification from `/specs/012-alignment-and-clutter/spec.md`

## Summary

This plan outlines the implementation of Background Clutter Detection and Progressive Alignment Feedback (IoU-based snapping) for CameraQ's AI Coaching system. We will leverage OpenCV's Canny edge detection on masked image regions for clutter scoring and bounding box intersection logic for alignment snapping.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: OpenCV (cv2), numpy, pydantic

**Storage**: N/A

**Testing**: N/A

**Target Platform**: Desktop (macOS/Windows)

**Project Type**: AI Camera CLI / Viewfinder

**Performance Goals**: < 10ms per frame overhead

**Constraints**: Must not interrupt the UI thread; real-time performance.

## Constitution Check

*GATE: Passed. All features adhere to the "Presentation layer isolation" and "Avoid heavy DL inference when classical CV suffices" principles.*

## Project Structure

### Documentation (this feature)

```text
specs/012-alignment-and-clutter/
├── plan.md              
└── tasks.md             
```

### Source Code (repository root)

```text
src/
├── core/
│   ├── analyzer.py
│   ├── entities.py
│   └── analyzers/
│       └── aesthetics_analyzer.py
├── ui/
│   ├── overlay.py
│   └── camera_app.py
```

**Structure Decision**: The logic perfectly slots into the existing `CameraQAnalyzer`, `AestheticsAnalyzer`, and `OverlayRenderer`. No new project structures or files are required.

## Technical Approach

### 1. Clutter Detection (AestheticsAnalyzer)
- The `AestheticsAnalyzer` will accept an optional `primary_box` parameter.
- If provided, we create a mask ignoring the primary subject, run `cv2.Canny` on the grayscale image, and count the number of edge pixels in the background.
- If the ratio of edge pixels to background area exceeds `0.15` (15%), we trigger `is_background_cluttered = True`.

### 2. Alignment Snapping (CameraQAnalyzer)
- After obtaining the `target_box` from the Scenario Templates, we will calculate the IoU (Intersection over Union) with the primary subject's bounding box.
- If IoU > 0.65, `ai_coaching.perfect_alignment = True`.

### 3. Haptic UI Simulation (CameraApp & Overlay)
- `OverlayRenderer` will detect `perfect_alignment`. If `True`, it draws a golden thick solid border `(255, 215, 0, 255)` for the target box and adds "✨ ALIGNED".
- `CameraApp` will track the state transition. If transitioning from `False` to `True`, it logs `logger.info("[HAPTIC VIBRATION] Perfect alignment snap!")`.
