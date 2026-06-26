# Implementation Plan: UI/UX Aesthetics Polish

**Branch**: `004-ui-ux-polish` | **Date**: 2026-06-26 | **Spec**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/004-ui-ux-polish/spec.md)

**Input**: Feature specification from `specs/004-ui-ux-polish/spec.md`

## Summary

This feature refines the aesthetics of the CameraQ viewfinder UI by transitioning from harsh, solid-color lines to elegant, semi-transparent overlays. It also introduces lifecycle management for text prompts (such as a 10-second fade for AI coaching). This will be achieved using PIL for styled text/backgrounds and OpenCV for alpha-blended geometric lines, governed by tracking metadata timestamps.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: OpenCV (`cv2`), Pillow (`PIL`), numpy

**Storage**: N/A

**Testing**: Manual Visual Verification via `uv run python src/ui/camera_app.py`

**Target Platform**: macOS / Desktop OpenCV Windows

**Project Type**: Python CLI / OpenCV GUI Application

**Performance Goals**: Maintain 30 FPS rendering loop with PIL/OpenCV overlays.

**Constraints**: OpenCV GUI has limited styling capabilities, requiring conversion between OpenCV BGR matrices and PIL Images to draw high-quality text and translucent panels efficiently.

**Scale/Scope**: Impacts `src/ui/overlay.py` and `src/core/entities.py`.

## Constitution Check

*GATE: Passed. No new architectural complexity introduced. Modifies existing UI rendering classes to support alpha/translucency and duration checks.*

## Project Structure

### Documentation (this feature)

```text
specs/004-ui-ux-polish/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── quickstart.md        # Phase 1 output
```

### Source Code (repository root)

```text
src/
├── core/
│   └── entities.py      # Add duration and is_active logic to result classes
└── ui/
    └── overlay.py       # Re-implement draw functions using PIL alpha compositing
```

**Structure Decision**: The logic will reside entirely in `overlay.py` (which currently handles all drawing) and `entities.py` (which holds state). No new files or modules are required.

## Complexity Tracking

N/A
