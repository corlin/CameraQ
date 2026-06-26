# Implementation Plan: Professional Performance & UX Deep Optimization

**Branch**: `006-pro-optimization` | **Date**: 2026-06-26 | **Spec**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/006-pro-optimization/spec.md)

**Input**: Feature specification from `specs/006-pro-optimization/spec.md`

## Summary

A comprehensive optimization pass that tackles the four pillars identified by deep codebase audit: (1) render pipeline performance, (2) professional multi-dimensional composition scoring, (3) expanded intelligent settings panel, and (4) graceful resource management & error resilience.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: OpenCV, Pillow (PIL), ultralytics (YOLO11), google-genai, Pydantic, logging (stdlib)

**Storage**: `config.json` (local JSON file via `SettingsManager`)

**Target Platform**: macOS (local execution)

**Project Type**: Desktop Python Application (Computer Vision)

**Performance Goals**: ≥25 FPS with all modules enabled on a MacBook

**Constraints**: No GPU acceleration or native code rewrites; improvements via caching, throttling, and architecture cleanup

## Project Structure

### Documentation (this feature)

```text
specs/006-pro-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── core/
│   ├── settings.py          # [MODIFY] Enhanced with numeric params, thread safety, logging
│   ├── analyzer.py          # [MODIFY] Throttled analysis, YOLO toggle, dead code removal
│   ├── ai_coach.py          # [MODIFY] Graceful shutdown, logging, move import re to top
│   ├── entities.py          # [MODIFY] Remove duplicate imports, remove unused classes
│   ├── models/
│   │   ├── yolo_wrapper.py  # [MODIFY] Remove dead _mark_primary_subject code
│   │   └── pose_wrapper.py  # (minor cleanup)
│   ├── detectors/
│   │   └── saliency_detector.py  # (throttled via analyzer)
│   ├── analyzers/
│   │   └── aesthetics_analyzer.py  # [MODIFY] Implement color_harmony_score
│   ├── trackers/
│   │   └── object_tracker.py  # [MODIFY] deque for history, smoothed velocity
│   ├── rules/
│   │   ├── scoring.py       # [MODIFY] Multi-dimensional CompositionScore with positive factors
│   │   ├── horizon_rule.py  # (throttled via analyzer)
│   │   ├── position_rule.py # [MODIFY] Add positive scoring for thirds alignment
│   │   └── ...
│   ├── utils/
│   │   └── drawing.py       # [DELETE] Dead code — unused since PIL migration
│   └── io/
│       └── camera.py        # [MODIFY] Error resilience for disconnect
├── ui/
│   ├── overlay.py           # [MODIFY] Font caching, score visualization, sidebar animation
│   └── camera_app.py        # [MODIFY] Clean shutdown, thread-safe settings, logging
```

## Proposed Changes

---

### P1: Render Pipeline Performance

#### [MODIFY] [overlay.py](file:///Users/corlin/2026/CameraQ/src/ui/overlay.py)
- **Font caching**: Move font discovery and loading into `__init__`. Store `self.font` and `self.small_font` as instance attributes. Eliminate per-frame `os.path.exists()` calls.
- **Reduce PIL overhead**: Reuse the overlay `Image` object where possible instead of creating a new one every frame. Move `import os` to module level.
- **Score visualization**: Add a `_draw_score_breakdown()` method that renders the multi-dimensional `CompositionScore` as a compact horizontal bar or labeled sub-scores near the bottom of the screen.
- **Sidebar animation**: Add a `sidebar_offset` float field (0.0 = closed, 1.0 = open) that interpolates by ~0.15 per frame toward the target state, creating a smooth slide-in/out effect.

#### [MODIFY] [analyzer.py](file:///Users/corlin/2026/CameraQ/src/core/analyzer.py)
- **Throttled analysis**: Add a frame counter. Run `detect_horizon()` and `saliency_detector.detect()` only every Nth frame (default N=5), caching results for intermediate frames.
- **YOLO object detection toggle**: Add `settings.object_detection_enabled` check, consistent with existing toggles.
- **Remove dead imports**: Remove `draw_rule_of_thirds_grid`, `draw_line` imports.
- **Remove redundant copy**: Remove `out_img = img.copy()` — the overlay renderer already copies the frame.

---

### P2: Professional Multi-Dimensional Scoring

#### [MODIFY] [scoring.py](file:///Users/corlin/2026/CameraQ/src/core/rules/scoring.py)
- Rewrite `calculate_composition_score` to return a `CompositionScore` object (already defined in entities.py) instead of a plain `int`.
- Implement sub-scores:
  - **subject_score**: Positive bonus for rule-of-thirds alignment, penalty for edge placement.
  - **structure_score**: Positive for level horizon, penalty for tilt.
  - **balance_score**: Assess visual weight distribution across frame quadrants.
  - **interference_score**: Penalty from background interference feedbacks.
  - **style_score**: Bonus from aesthetics (good lighting, color harmony).
- `total_score` is a weighted sum of sub-scores, clamped to 0–100.

#### [MODIFY] [position_rule.py](file:///Users/corlin/2026/CameraQ/src/core/rules/position_rule.py)
- Add a `thirds_alignment_bonus` feedback when a subject center is within 5% of a thirds intersection — this feeds into the positive scoring in `scoring.py`.

#### [MODIFY] [aesthetics_analyzer.py](file:///Users/corlin/2026/CameraQ/src/core/analyzers/aesthetics_analyzer.py)
- Implement `color_harmony_score` using the already-computed HSV saturation std deviation (currently computed but unused).

#### [MODIFY] [entities.py](file:///Users/corlin/2026/CameraQ/src/core/entities.py)
- Remove duplicate `from typing import Any` / `from pydantic import BaseModel, Field` at line 100-101.
- Remove unused classes: `CameraStream`, `StructuralAnalysis` (not referenced anywhere).
- Update `AnalysisResult.score` type from `int` to `CompositionScore`.

---

### P3: Expanded Settings Panel

#### [MODIFY] [settings.py](file:///Users/corlin/2026/CameraQ/src/core/settings.py)
- Add new settings: `object_detection_enabled` (bool), `ai_sampling_interval` (float, default 5.0), `overlay_opacity` (float, 0.0–1.0, default 0.7).
- Add `threading.Lock` for thread-safe reads/writes.
- Use an absolute path for `config_path` (resolve relative to project root using `__file__`).
- Replace `print()` with `logging.getLogger(__name__)`.

#### [MODIFY] [overlay.py](file:///Users/corlin/2026/CameraQ/src/ui/overlay.py) (sidebar enhancements)
- Organize sidebar into groups: "检测模块", "性能参数", "显示选项".
- Render numeric parameter displays (read-only for MVP — clickable +/- buttons for adjustment).
- Display `settings.ai_sampling_interval` and `settings.overlay_opacity` in the sidebar.

---

### P4: Graceful Resource Management

#### [MODIFY] [camera_app.py](file:///Users/corlin/2026/CameraQ/src/ui/camera_app.py)
- Add `analyzer.ai_coach.stop()` in the `finally` block.
- Wrap `stream.read()` with error handling for camera disconnection.
- Replace `print()` with `logging`.

#### [MODIFY] [ai_coach.py](file:///Users/corlin/2026/CameraQ/src/core/ai_coach.py)
- Move `import re` to module level.
- Ensure `stop()` properly joins the thread (increase timeout or use a `threading.Event` for clean shutdown).
- Replace `print()` with `logging`.
- Sanitize error messages shown to user (replace raw API error with friendly Chinese message).

#### [MODIFY] [camera.py](file:///Users/corlin/2026/CameraQ/src/core/io/camera.py)
- Add try/except around `cap.read()` to handle camera disconnection gracefully.
- Replace `print()` with `logging`.

#### [MODIFY] [object_tracker.py](file:///Users/corlin/2026/CameraQ/src/core/trackers/object_tracker.py)
- Replace `list.pop(0)` with `collections.deque(maxlen=10)` for history.
- Add simple exponential smoothing to velocity to reduce jitter.

#### [DELETE] [drawing.py](file:///Users/corlin/2026/CameraQ/src/core/utils/drawing.py)
- Completely unused since the PIL migration in Stage 5. Remove file and its import from `analyzer.py`.

---

## Verification Plan

### Manual Verification
1. Run `uv run python src/ui/camera_app.py`.
2. **Performance**: Compare on-screen FPS before and after optimization. Target: ≥30% improvement.
3. **Scoring**: Frame a well-composed shot — verify multi-dimensional sub-scores are displayed. Frame a poor shot — verify the weakest dimension is highlighted.
4. **Settings**: Press `Tab`, verify sidebar slides in smoothly. Verify new settings categories ("检测模块", "性能参数") are visible.
5. **Shutdown**: Press `q`, verify clean exit in terminal logs (no orphaned thread warnings). Verify `[AICoach] Stopped.` message appears.
6. **Resilience**: Cover the camera lens — verify no crash. Check that all console output uses structured logging format.
