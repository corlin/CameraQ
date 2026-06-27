# Implementation Plan: AI UX Redesign

**Branch**: `[008-ai-ux-redesign]` | **Date**: 2026-06-27 | **Spec**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/008-ai-ux-redesign/spec.md)

**Input**: Feature specification from `/specs/008-ai-ux-redesign/spec.md`

## Summary

Redesign the AI coaching and scene context UI overlays to be non-intrusive and professional. Use minimalistic visual paradigms (toast notifications, thin lines, icon + short text, auto-collapse) to ensure the central 50% of the viewfinder remains unobstructed.

## Technical Context

**Language/Version**: Python 3.12 (managed via uv)

**Primary Dependencies**: OpenCV (cv2), Pillow (PIL) for overlay rendering

**Storage**: N/A

**Testing**: pytest

**Target Platform**: macOS (Desktop app)

**Project Type**: Desktop Camera App

**Performance Goals**: Overlay rendering must take < 5ms to maintain 30+ FPS

**Constraints**: Must not block the OpenCV video rendering thread

**Scale/Scope**: Local UI overlay modifications

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] UI updates must not degrade rendering performance
- [x] UI updates must be isolated to the presentation layer (`src/ui/overlay.py`)

## Project Structure

### Documentation (this feature)

```text
specs/008-ai-ux-redesign/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
└── ui/
    └── overlay.py       # Primary file to be modified for UI redesign

assets/
└── icons/               # [NEW] Directory for UI icons (Sun, Mountain, etc.) - or we can use Emoji/Text for MVP
```

**Structure Decision**: Single project desktop application. Modifications isolated to the UI overlay module (`src/ui/overlay.py`).

## Complexity Tracking

N/A - No major architectural complexity added. This is a refactoring of presentation logic.
