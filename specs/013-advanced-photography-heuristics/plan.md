# Implementation Plan: Advanced Photography Heuristics

**Branch**: `[013-advanced-photography-heuristics]` | **Date**: 2026-06-27 | **Spec**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/013-advanced-photography-heuristics/spec.md)

**Input**: Feature specification covering Lighting Direction, Histogram, Color Contrast, Leading Lines, and DoF.

## Technical Context
- **Dependencies**: OpenCV, Numpy
- **Status**: Research complete. Algorithms selected for performance (< 15ms total overhead).

## Constitution Check
- **Library-First**: All algorithms encapsulate nicely into `AestheticsAnalyzer`.
- **Test-First**: Unit tests must be written for the new heuristic functions.
- **Simplicity**: Kept to classical CV (histograms, slicing, means) to avoid NN overhead.

## Phase 0: Research
[x] Done. See [research.md](file:///Users/corlin/2026/CameraQ/specs/013-advanced-photography-heuristics/research.md). No open questions.

## Phase 1: Design & Contracts
[x] Done. See [data-model.md](file:///Users/corlin/2026/CameraQ/specs/013-advanced-photography-heuristics/data-model.md) and [quickstart.md](file:///Users/corlin/2026/CameraQ/specs/013-advanced-photography-heuristics/quickstart.md).

## Phase 2: Proposed Changes

### Domain & Data Model
#### [MODIFY] [entities.py](file:///Users/corlin/2026/CameraQ/src/core/entities.py)
- Add `histogram_clipping`, `lighting_direction`, `color_contrast_low`, `vanishing_point_aligned` to `AestheticsMetrics`.

### Analyzer Engine
#### [MODIFY] [aesthetics_analyzer.py](file:///Users/corlin/2026/CameraQ/src/core/analyzers/aesthetics_analyzer.py)
- Import `cv2.calcHist` for exposure check.
- Add lighting direction logic (slice `primary_box` left/right).
- Add color contrast logic (HSV mean of `primary_box` vs background).
- Add DoF logic (use `clutter_score` + area ratio).
- Add leading lines logic using `cv2.HoughLinesP`.

#### [MODIFY] [scene_rule.py](file:///Users/corlin/2026/CameraQ/src/core/rules/scene_rule.py)
- Expand the rule engine to process the new `AestheticsMetrics` fields and generate localized UI advice (e.g. "高光溢出，建议降低曝光").

## Post-Design Constitution Check
- [x] Simple and Fast? Yes, avoids deep learning.
- [x] Extensible? Yes, `AestheticsMetrics` scales well.

## Verification Plan
### Automated Tests
- Unit tests for `AestheticsAnalyzer` with mock frames (all black, all white, half white/half black).
- Unit tests for `SceneRule` to verify priority ordering of feedback.

### Manual Verification
- Run `uv run python src/ui/camera_app.py` and test the scenarios defined in [quickstart.md](file:///Users/corlin/2026/CameraQ/specs/013-advanced-photography-heuristics/quickstart.md).
