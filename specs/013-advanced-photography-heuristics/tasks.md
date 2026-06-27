# Tasks: Advanced Photography Heuristics

**Branch**: `[013-advanced-photography-heuristics]` | **Date**: 2026-06-27 | **Plan**: [plan.md](file:///Users/corlin/2026/CameraQ/specs/013-advanced-photography-heuristics/plan.md)

## Implementation Strategy
- **MVP Scope**: Complete Phase 1 and 2 (Lighting Direction and Histogram) as they are P1 priorities providing the highest immediate value.
- **Incremental Delivery**: Each User Story phase is self-contained and testable independently.
- **Parallel Execution**: US3, US4, and US5 heuristic algorithms can be developed in parallel as they don't depend on each other.

## Phase 1: Setup

- [x] T001 Update `AestheticsMetrics` in `src/core/entities.py` with `histogram_clipping`, `lighting_direction`, `color_contrast_low`, and `vanishing_point_aligned`.

## Phase 2: User Story 1 (Lighting Direction - P1)
*Goal: Detect flat, side, or backlighting.*
*Tests: Point at a backlit window, then turn 90 degrees.*

- [x] T002 [US1] Implement face bounding box intensity slicing in `src/core/analyzers/aesthetics_analyzer.py`.
- [x] T003 [US1] Update `src/core/rules/scene_rule.py` to provide lighting direction UI advice.

## Phase 3: User Story 2 (Histogram & Dynamic Range - P1)
*Goal: Warn on clipped highlights and crushed blacks.*
*Tests: Point at a very bright bulb, then cover lens.*

- [x] T004 [US2] Implement full-frame grayscale histogram calculation using `cv2.calcHist` in `src/core/analyzers/aesthetics_analyzer.py`.
- [x] T005 [US2] Update `src/core/rules/scene_rule.py` to trigger EV+/- warnings based on clipping percentages.

## Phase 4: User Story 3 (Color Contrast - P2)
*Goal: Detect if subject blends into the background.*
*Tests: Subject in green shirt against green wall.*

- [x] T006 [P] [US3] Implement HSV mean comparison for subject vs background mask in `src/core/analyzers/aesthetics_analyzer.py`.
- [x] T007 [US3] Update `src/core/rules/scene_rule.py` for color separation warnings.

## Phase 5: User Story 4 (Leading Lines - P2)
*Goal: Advise using background geometry pointing to subject.*
*Tests: Stand on a road, subject off-center from vanishing point.*

- [x] T008 [P] [US4] Implement Canny + `cv2.HoughLinesP` geometry detection in `src/core/analyzers/aesthetics_analyzer.py`.
- [x] T009 [US4] Update `src/core/rules/scene_rule.py` for leading lines alignment advice.

## Phase 6: User Story 5 (Depth of Field - P2)
*Goal: Suggest DoF blur when background is busy and far.*
*Tests: Small subject bounding box with high Canny edge density background.*

- [x] T010 [P] [US5] Implement DoF area heuristic using clutter score in `src/core/analyzers/aesthetics_analyzer.py`.
- [x] T011 [US5] Update `src/core/rules/scene_rule.py` for DoF warnings.
- [x] T012 Run performance profiling script on `aesthetics_analyzer.py` to ensure `<15ms` execution time.

## Final Phase: Polish & Cross-Cutting Concerns

- [x] T013 Verify 15ms budget in `tests/integration/test_performance.py`.
