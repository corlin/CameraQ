---
description: "Task list for Stage 2 Real-time Saliency MVP"
---

# Tasks: Real-time Saliency MVP

**Input**: Design documents from `/specs/001-realtime-saliency-mvp/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Setup Saliency dependencies (if external lightweight models are needed beyond OpenCV) in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T002 Update core models `CameraStream`, `SaliencyMap`, and `FusedSubject` in `src/core/entities.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 实时摄像头推流感知 (Priority: P1) 🎯 MVP

**Goal**: System can capture real-time video stream from device camera and maintain high FPS with AI processing decoupled.

**Independent Test**: Running the camera stream module independently displays the feed at ~30FPS.

### Tests for User Story 1

- [x] T003 [P] [US1] Unit test for CameraStream in `tests/unit/core/io/test_camera.py`

### Implementation for User Story 1

- [x] T004 [US1] Implement `CameraStream` with background thread fetching in `src/core/io/camera.py`
- [x] T005 [US1] Create a basic runner script `src/ui/camera_app.py` to display the raw stream using `cv2.imshow`

**Checkpoint**: At this point, User Story 1 should be fully functional (raw camera preview works smoothly).

---

## Phase 4: User Story 2 - 非标准主体识别 (显著性检测) (Priority: P2)

**Goal**: System introduces Saliency model to detect visually attractive non-standard objects and fuse them with YOLO results.

**Independent Test**: Provide an image with a heart-shaped cloud and a car; the analyzer should flag the cloud as the primary subject.

### Tests for User Story 2

- [x] T006 [P] [US2] Unit test for Saliency detector in `tests/unit/core/detectors/test_saliency.py`
- [x] T007 [P] [US2] Unit test for fusion logic in `tests/unit/core/test_analyzer.py`

### Implementation for User Story 2

- [x] T008 [US2] Implement `SaliencyDetector` (using OpenCV or U2Net) in `src/core/detectors/saliency_detector.py`
- [x] T009 [US2] Update `CameraQAnalyzer.analyze_frame()` in `src/core/analyzer.py` to run SaliencyDetector and fuse outputs to determine `is_primary_subject`

**Checkpoint**: At this point, Analyzer correctly prioritizes salient blobs over standard YOLO classes if they are visually dominant.

---

## Phase 5: User Story 3 - 取景器实时反馈交互 (Priority: P3)

**Goal**: Display dynamic, non-intrusive UI overlays (composition grids and short textual advice) on the real-time stream.

**Independent Test**: Run `camera_app.py`, place an object far left, verify the app overlays "向右微调机位".

### Tests for User Story 3

- [x] T010 [P] [US3] Unit test for overlay drawing functions in `tests/unit/ui/test_overlay.py`

### Implementation for User Story 3

- [x] T011 [US3] Implement dynamic overlay rendering (text and grids) in `src/ui/overlay.py`
- [x] T012 [US3] Integrate `CameraQAnalyzer` and `overlay.py` into the main loop of `src/ui/camera_app.py` (ensure AI logic runs without blocking the `cv2.imshow` thread)

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T013 Code cleanup and ensure clean separation of UI thread and AI loop
- [x] T014 Run validation scenarios from `quickstart.md`
- [x] T015 Update top-level `README.md` to document the new Real-time Viewfinder MVP

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - Sequentially in priority order: US1 -> US2 -> US3

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Entities -> Detectors -> UI/Integration

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2.
2. Complete Phase 3 (US1) and verify the pure camera stream is stable.

### Incremental Delivery

1. Foundation ready.
2. Add US1 -> Test independently -> Real-time pipeline works.
3. Add US2 -> Test independently -> Saliency logic proves accurate.
4. Add US3 -> Test independently -> Full real-time CameraQ app is ready!

---

## Phase 7: Convergence

**Purpose**: Address gaps identified during convergence analysis

- [x] T016 Add UI debounce mechanism to stabilize feedback text updates per spec.md (Edge Cases / SC-004) (missing)
- [x] T017 Implement automated performance benchmarking tests for 30FPS and 250ms latency targets per spec.md (SC-001/SC-002) (missing)
