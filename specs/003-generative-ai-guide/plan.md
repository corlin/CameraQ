# Implementation Plan: Generative AI Guide (Stage 4)

**Branch**: `003-generative-ai-guide` | **Date**: 2026-06-26 | **Spec**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/003-generative-ai-guide/spec.md)

**Input**: Feature specification from `/specs/003-generative-ai-guide/spec.md`

## Summary

Implement Stage 4 of CameraQ: Integrating a Generative AI Multimodal Guide. To maintain 30 FPS for real-time OpenCV tracking, we will introduce a "Fast/Slow Brain" asynchronous architecture using a background thread and concurrent queue. The AI Coach will process keyframes asynchronously and return stylistic and emotional photography suggestions without blocking the main viewfinder feed.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: OpenCV, `google-genai` (Google GenAI SDK), Pillow

**Storage**: N/A

**Testing**: pytest

**Target Platform**: macOS

**Project Type**: Python Application

**Performance Goals**: > 20 fps during inference, ideally 30 fps

**Constraints**: Asynchronous decoupling required

**Scale/Scope**: Local application calling external API

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
N/A - Project principles uninitialized.

## Project Structure

### Documentation (this feature)

```text
specs/003-generative-ai-guide/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── core/
│   ├── ai_coach.py      # Background thread and queue manager
│   ├── entities.py      # Updated with AICoachingResult
│   └── analyzer.py      # Updated to enqueue frames
├── ui/
│   ├── overlay.py       # Updated to draw AI advice bubble
│   └── camera_app.py    # Updated to initialize AICoach
```

**Structure Decision**: Extending the existing architecture. `src/core/ai_coach.py` will encapsulate the asynchronous logic.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A       | N/A        | N/A                                 |
