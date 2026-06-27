# Implementation Plan: AI Scenario Templates

**Branch**: `[009-scenario-templates]` | **Date**: 2026-06-27 | **Spec**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/009-scenario-templates/spec.md)

**Input**: Feature specification from `/specs/009-scenario-templates/spec.md`

## Summary

Implement Stage 2 of the AI UX vision by introducing Scenario Templates (Portrait, Landscape, Vlog) that dynamically dictate compositional rules. More importantly, fulfill the core UX vision by rendering "ghost composition boxes" (semi-transparent target rectangles) and directional edge arrows to guide users without forcing them to read text.

## Technical Context

**Language/Version**: Python 3.12 (managed via uv)

**Primary Dependencies**: OpenCV (cv2), Pillow (PIL) for overlay rendering

**Storage**: N/A

**Testing**: pytest

**Target Platform**: macOS (Desktop app)

**Project Type**: Desktop Camera App

**Performance Goals**: Overlay rendering must take < 5ms to maintain 30+ FPS

**Constraints**: Must not block the OpenCV video rendering thread

**Scale/Scope**: Local UI overlay modifications and core entity extensions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] UI updates must not degrade rendering performance (PIL drawing for ghost boxes and text arrows is extremely fast).
- [x] UI updates must be isolated to the presentation layer (`src/ui/overlay.py`). Template logic injected via `AnalysisResult`.

## Project Structure

### Documentation (this feature)

```text
specs/009-scenario-templates/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (to be generated)
```

### Source Code (repository root)

```text
src/
├── core/
│   └── entities.py      # Extend AICoaching to hold target_box and directional_arrows
└── ui/
    └── overlay.py       # Render the ghost boxes and edge arrows using PIL
```

**Structure Decision**: Single project desktop application. Data model changes go to `src/core/entities.py`, presentation logic goes to `src/ui/overlay.py`.

## Complexity Tracking

No major architectural complexity added. This builds upon the existing PIL overlay rendering pipeline.
