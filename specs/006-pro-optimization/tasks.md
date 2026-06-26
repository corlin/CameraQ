# Implementation Tasks: Professional Performance & UX Deep Optimization

## Phase 1: Setup (Code Cleanup)

**Purpose**: Remove dead code and fix structural issues before any optimization work begins.

- [x] T001 Remove duplicate imports (`from typing import Any`, `from pydantic import BaseModel, Field`) at line 100-101 in `src/core/entities.py`
- [x] T002 [P] Remove unused classes `CameraStream` and `StructuralAnalysis` from `src/core/entities.py`
- [x] T003 [P] Remove dead imports (`draw_rule_of_thirds_grid`, `draw_line`) from `src/core/analyzer.py`
- [x] T004 [P] Delete unused file `src/core/utils/drawing.py`
- [x] T005 [P] Move `import re` from inside except block to module level in `src/core/ai_coach.py`
- [x] T006 [P] Move `import os` from inside `draw()` method to module level in `src/ui/overlay.py`

---

## Phase 2: Foundational (Logging & Thread Safety)

**Purpose**: Replace all `print()` with `logging` and add thread safety to `SettingsManager`. These are cross-cutting concerns that MUST be in place before feature work.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Add `import logging` and configure `logger = logging.getLogger(__name__)` in `src/core/settings.py`, replace all `print()` calls with appropriate log levels
- [x] T008 [P] Replace all `print()` with `logging` in `src/core/ai_coach.py`
- [x] T009 [P] Replace all `print()` with `logging` in `src/core/io/camera.py`
- [x] T010 [P] Replace all `print()` with `logging` in `src/ui/camera_app.py`
- [x] T011 Add `threading.Lock` to `SettingsManager` in `src/core/settings.py` — wrap all getattr/setattr/toggle/save/load with lock acquisition
- [x] T012 Add new settings fields to `SettingsManager` in `src/core/settings.py`: `object_detection_enabled` (bool, default True), `ai_sampling_interval` (float, default 5.0), `overlay_opacity` (float, default 0.7), `analysis_throttle_n` (int, default 5)
- [x] T013 Resolve `config_path` to an absolute path using `Path(__file__).resolve().parent.parent.parent / "config.json"` in `src/core/settings.py`

**Checkpoint**: Foundation ready — all logging consistent, settings thread-safe, new config fields available.

---

## Phase 3: User Story 1 - Render Pipeline Performance (Priority: P1) 🎯 MVP

**Goal**: Achieve ≥30% FPS improvement by caching, throttling, and eliminating redundant work.

**Independent Test**: Run the app, compare FPS counter before/after. Target: ≥25 FPS with all modules on.

### Implementation for User Story 1

- [x] T014 [US1] Cache font objects in `OverlayRenderer.__init__` in `src/ui/overlay.py` — move font discovery loop from `draw()` to `__init__`, store as `self.font` and `self.small_font`
- [x] T015 [US1] Remove redundant `out_img = img.copy()` from `process_frame` in `src/core/analyzer.py` — the overlay renderer already copies the frame
- [x] T016 [US1] Add frame counter `self._frame_count` to `CameraQAnalyzer` in `src/core/analyzer.py` and throttle `detect_horizon()` to run every `settings.analysis_throttle_n` frames, caching the result between runs
- [x] T017 [US1] Throttle `saliency_detector.detect()` in `src/core/analyzer.py` to run every `settings.analysis_throttle_n` frames (same cadence as horizon), caching the saliency_map between runs
- [x] T018 [US1] Add `object_detection_enabled` toggle check before YOLO object detection in `src/core/analyzer.py`, returning empty subjects list when disabled
- [x] T019 [US1] Replace `list.pop(0)` with `collections.deque(maxlen=10)` for `history` field in `src/core/trackers/object_tracker.py`
- [x] T020 [US1] Add exponential smoothing to velocity calculation in `src/core/trackers/object_tracker.py` (alpha=0.3 blending of new velocity with previous)

**Checkpoint**: FPS should be noticeably improved. Verify with the on-screen counter.

---

## Phase 4: User Story 2 - Professional Multi-Dimensional Scoring (Priority: P2)

**Goal**: Replace the simplistic deduction-only scoring with a 5-dimensional `CompositionScore` and visual breakdown.

**Independent Test**: Frame a shot with good subject placement but tilted horizon — verify subject_score is high and structure_score is low.

### Implementation for User Story 2

- [x] T021 [US2] Rewrite `calculate_composition_score` in `src/core/rules/scoring.py` to return `CompositionScore` instead of `int`, implementing all 5 sub-scores (subject, structure, balance, interference, style)
- [x] T022 [US2] Add positive `thirds_alignment_bonus` feedback in `src/core/rules/position_rule.py` when subject center is within 5% of a thirds intersection point
- [x] T023 [US2] Implement `color_harmony_score` in `src/core/analyzers/aesthetics_analyzer.py` using the already-computed HSV saturation std deviation (currently computed but value discarded)
- [x] T024 [US2] Update `AnalysisResult.score` type from `int` to `CompositionScore` in `src/core/entities.py`
- [x] T025 [US2] Update `process_frame` in `src/core/analyzer.py` to pass aesthetics metrics and subjects list to the new `calculate_composition_score` function
- [x] T026 [US2] Update `feedback_str` construction in `src/core/analyzer.py` to display `total_score` from `CompositionScore` and include weakest dimension name
- [x] T027 [US2] Add `_draw_score_breakdown` method to `OverlayRenderer` in `src/ui/overlay.py` that renders sub-scores as compact labeled values or a segmented horizontal bar near the bottom-left

**Checkpoint**: Multi-dimensional score should be visible on screen with sub-score breakdown.

---

## Phase 5: User Story 3 - Expanded Settings Panel (Priority: P3)

**Goal**: Expand the sidebar with categorized groups, numeric parameter displays, and smooth animation.

**Independent Test**: Open sidebar, see categorized groups. Close/open sidebar and observe smooth slide animation.

### Implementation for User Story 3

- [x] T028 [US3] Add `sidebar_offset` float field to `OverlayRenderer` in `src/ui/overlay.py` (0.0=closed, 1.0=open), interpolate by 0.15 per frame toward target state for smooth animation
- [x] T029 [US3] Refactor `_draw_sidebar` in `src/ui/overlay.py` to organize toggles under a "🔍 检测模块" header group, including the new `object_detection_enabled` toggle
- [x] T030 [US3] Add "⚡ 性能参数" section in `_draw_sidebar` in `src/ui/overlay.py` displaying `ai_sampling_interval` and `analysis_throttle_n` as read-only values with +/- clickable buttons
- [x] T031 [US3] Register click bounds for numeric +/- buttons in `src/ui/overlay.py` and handle clicks in `mouse_callback` in `src/ui/camera_app.py` to increment/decrement numeric settings
- [x] T032 [US3] Use `settings.ai_sampling_interval` instead of hardcoded `5.0` in AI Coach sampling check in `src/core/analyzer.py`

**Checkpoint**: Sidebar should have categorized sections and smooth animation.

---

## Phase 6: User Story 4 - Graceful Resource Management (Priority: P4)

**Goal**: Clean shutdown, error resilience, and friendly error messages.

**Independent Test**: Press 'q' to quit — verify all threads terminate cleanly within 2 seconds.

### Implementation for User Story 4

- [x] T033 [US4] Add `analyzer.ai_coach.stop()` call in the `finally` block of `main()` in `src/ui/camera_app.py`
- [x] T034 [US4] Improve `AICoach.stop()` in `src/core/ai_coach.py` — use `threading.Event` as stop signal instead of boolean, increase join timeout
- [x] T035 [US4] Sanitize AI error messages in `src/core/ai_coach.py` — replace raw API error text with friendly Chinese messages (e.g., "AI 教练休息中，稍后自动恢复...")
- [x] T036 [US4] Add try/except around `cap.read()` in `src/core/io/camera.py` to handle camera disconnection gracefully, set `is_running = False` and log warning
- [x] T037 [US4] Remove dead `_mark_primary_subject` method from `src/core/models/yolo_wrapper.py` (its result is always overwritten by `_fuse_subjects` in analyzer)
- [x] T038 [US4] Configure `logging.basicConfig` at application entry point in `src/ui/camera_app.py` with format `[%(name)s] %(levelname)s: %(message)s`

**Checkpoint**: Application exits cleanly, logs are structured, errors are user-friendly.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation.

- [x] T039 [P] Update `README.md` with Stage 6 optimization notes
- [x] T040 Run quickstart.md validation locally

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 Performance (Phase 3)**: Depends on Phase 2 (needs new settings fields + logging)
- **US2 Scoring (Phase 4)**: Depends on Phase 2 (needs entities cleanup)
- **US3 Settings (Phase 5)**: Depends on Phase 2 + Phase 3 (needs new settings + throttle fields)
- **US4 Resilience (Phase 6)**: Depends on Phase 2 (needs logging)
- **Polish (Phase 7)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2. No dependency on other stories.
- **US2 (P2)**: Can start after Phase 2. No dependency on US1.
- **US3 (P3)**: Depends on US1 (needs `analysis_throttle_n` and `object_detection_enabled` fields active).
- **US4 (P4)**: Can start after Phase 2. No dependency on other stories.

### Parallel Opportunities

- Phase 1: All T001–T006 are independent file edits — fully parallelizable.
- Phase 2: T007–T010 (logging) are independent files — parallelizable. T011–T013 are sequential within settings.py.
- Phase 3: T014 (overlay) and T015–T018 (analyzer) touch different files — parallelizable.
- Phase 4: T021 (scoring) and T022 (position_rule) and T023 (aesthetics) touch different files — parallelizable.
- US1, US2, and US4 can be worked on in parallel after Phase 2.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup cleanup
2. Complete Phase 2: Logging + thread safety
3. Complete Phase 3: Performance optimization (US1)
4. **STOP and VALIDATE**: Check FPS improvement
5. Proceed to US2 → US3 → US4

### Incremental Delivery

1. Setup + Foundational → Clean codebase
2. Add US1 → Test FPS → Validate (MVP!)
3. Add US2 → Test scoring → Validate
4. Add US3 → Test sidebar → Validate
5. Add US4 → Test shutdown → Validate
6. Polish → Final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- T001–T006 are pure cleanup — zero risk of regression
- T014 (font caching) is the single highest-impact performance fix
- T021 (scoring rewrite) is the most complex task — requires careful testing

## Phase 8: Convergence

- [x] T041 Remove `_mark_primary_subject` method and its usage per T037 / US4 (missing)
- [x] T042 Add `try/except` around YOLO initialization to handle missing model file gracefully per spec: Edge Cases (missing)
- [x] T043 Use `threading.Event` for clean shutdown in `AICoach` per T034 / US4 (partial)
- [x] T044 Update `AICoach` error strings to be friendly Chinese messages per T035 / US4 (partial)
