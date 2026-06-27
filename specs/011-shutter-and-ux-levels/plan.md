# Implementation Plan: Shutter Feedback & UX Levels

**Branch**: `[011-shutter-and-ux-levels]` | **Date**: 2026-06-27 | **Spec**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/011-shutter-and-ux-levels/spec.md)

**Input**: Feature specification from `/specs/011-shutter-and-ux-levels/spec.md`

## Summary

This plan introduces advanced shutter timing prompts (e.g. perfect shutter moment due to good composition and alignment) and proactive parameter feedback for severe lighting conditions (e.g. suggesting HDR on overexposure). Additionally, it implements a unified `CoachingLevel` UI system (`OFF`, `MINIMAL`, `COACH`, `PRO`) to replace the cluttered sidebar toggles, giving users complete control over AI UI density.

## Technical Context

**Language/Version**: Python 3.12 (managed via uv)

**Primary Dependencies**: OpenCV (cv2), Pillow (PIL)

**Storage**: Local `config.json` via `SettingsManager`

**Testing**: pytest

**Target Platform**: macOS (Desktop app)

**Project Type**: Desktop Camera App

**Constraints**: Overlays must respect the selected Coaching Level instantly.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Must not degrade rendering performance. The `CoachingLevel` actually improves performance by skipping rendering code when `OFF` or `MINIMAL`.
- [x] Must keep UI layer isolated. The `CoachingLevel` is fetched from `SettingsManager`.

## Project Structure

### Documentation

```text
specs/011-shutter-and-ux-levels/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (to be generated)
```

### Source Code

```text
src/
├── core/
│   ├── settings.py                # Add coaching_level
│   ├── entities.py                # Add CoachingLevel enum
│   ├── analyzer.py                # Inject parameter feedback logic based on lighting
│   └── analyzers/
│       └── aesthetics_analyzer.py # Threshold adjustments for severe lighting
└── ui/
    └── overlay.py                 # Filter UI rendering based on coaching_level, add shortcut key 'C' to toggle level
```

## Proposed Changes

### `src/core/entities.py`
- [MODIFY] Add `CoachingLevel` enum.

### `src/core/settings.py`
- [MODIFY] Add `coaching_level` default to `COACH`. Allow toggling string states.

### `src/core/analyzers/aesthetics_analyzer.py`
- [MODIFY] Lower threshold for underexposure or ensure it's easily triggered for testing.

### `src/core/analyzer.py`
- [MODIFY] If `aesthetics.is_overexposed`, add `🤖 AI洞察: 画面过曝，建议开启 HDR 或锁定曝光` to feedback.
- [MODIFY] Make `shutter_opportunity` trigger not only on node intersection but also on high score (>90).

### `src/ui/overlay.py`
- [MODIFY] Wrap the bounding box drawing code in `if level == "PRO"`.
- [MODIFY] Wrap radar chart code in `if level == "PRO"`.
- [MODIFY] Wrap AI Coach text block in `if level in ["COACH", "PRO"]`.
- [MODIFY] Wrap ghost box and arrows in `if level != "OFF"`.
- [MODIFY] Draw a small overlay indicator for the current level (e.g. `[AI: COACH]`).
