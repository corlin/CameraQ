# Implementation Plan: CameraQ Stage 1 Offline Demo

**Branch**: `main` | **Date**: 2026-06-26 | **Spec**: [spec.md](file:///Users/corlin/2026/CameraQ/spec.md)

**Input**: Feature specification from `spec.md`

## Summary

Build an offline image analysis demo (Stage 1) to validate the core composition rules of CameraQ. The demo allows a user to upload an image and receive a single actionable composition tip, a score, and 3 recommended crops.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: FastAPI, Gradio, OpenCV, Ultralytics YOLO11

**Storage**: None (in-memory processing for MVP)

**Testing**: Pytest

**Target Platform**: Local Desktop/Web App (Offline Demo)

**Project Type**: Web Service / Demo App

**Performance Goals**: <2s inference time per image on CPU

**Constraints**: Must run locally without requiring a dedicated GPU (CPU fallback).

**Scale/Scope**: Single user, offline demo.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Test-First (NON-NEGOTIABLE)**: Tests for core composition rules (e.g., horizon detection, head room calculation) will be written before implementing the actual rules.
- **Simplicity**: Starting with an offline Python+Gradio demo before moving to mobile ensures rapid iteration and keeps the architecture simple for validation.

## Project Structure

### Documentation (this feature)

```text
.
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── core/
│   ├── analyzer.py       # Main orchestration logic
│   ├── rules/            # Individual composition rules (horizon, headroom, etc.)
│   └── models/           # YOLO wrappers
├── ui/
│   └── gradio_app.py     # Gradio Web UI
└── utils/

tests/
├── unit/
│   └── test_rules.py
└── integration/
    └── test_analyzer.py
```

**Structure Decision**: Option 1: Single project (Python application). Using `src/` to separate core logic from UI, allowing later reuse of `core/` in a FastAPI backend if the mobile app requires cloud processing.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
