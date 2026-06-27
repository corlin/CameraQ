# Implementation Plan: deep-ai-assist

**Branch**: `[007-deep-ai-assist]` | **Date**: 2026-06-27 | **Spec**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/007-deep-ai-assist/spec.md)

**Input**: Feature specification from `/specs/007-deep-ai-assist/spec.md`

## Summary

Implement a hybrid AI architecture for CameraQ that performs deep scene understanding to automatically adjust camera parameters and proactively alert users via voice/popups during optimal shooting moments.

## Technical Context

**Language/Version**: Python 3.12 (managed via uv)

**Primary Dependencies**: OpenCV, Ultralytics YOLO, Google GenAI SDK (Gemini), `pyttsx3` or macOS `say` for TTS.

**Storage**: Local `config.json` via existing `SettingsManager`.

**Testing**: `pytest`

**Target Platform**: macOS Desktop

**Project Type**: Computer Vision Desktop App

**Performance Goals**: >= 25 FPS local processing; < 2.0s latency for cloud-based deep AI insights.

**Constraints**: Webcam API limitations on macOS for hardware parameter control (Exposure/ISO); requires graceful degradation to software simulated parameters if hardware control fails.

**Scale/Scope**: Real-time single user application.

## Constitution Check

*GATE: Passed. (No specific constraints in the placeholder constitution file).*

## Project Structure

### Documentation (this feature)

```text
specs/007-deep-ai-assist/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── core/
│   ├── ai_coach.py           # Enhance for voice and proactive prompts
│   ├── analyzer.py           # Implement scene detection logic and edge cases fallback
│   ├── io/
│   │   └── camera.py         # Add exposure/ISO hardware control interfaces
│   ├── rules/
│   │   └── scene_rule.py     # Deep scene context rules & conflicting subjects resolution
│   └── entities.py           # Add SceneContext entity
└── ui/
    ├── camera_app.py         # Handle proactive popup alerts
    └── overlay.py            # Render new UI elements
tests/
└── integration/
    └── test_performance.py   # NEW: Enforce < 2.0s latency SLA for SC-002
```

**Structure Decision**: Extending the existing single project structure. Adding specific rules for scene understanding, resolving conflicting subjects based on bounding box size, applying low-confidence fallbacks in `analyzer.py`, and implementing an explicit performance test for the 2-second SLA.
