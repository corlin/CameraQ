---
description: "Task list for Stage 3 Advanced Aesthetics & Dynamic Tracking"
---

# Tasks: Advanced Aesthetics & Dynamic Tracking

**Input**: Design documents from `/specs/002-aesthetics-tracking/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify project structure and OpenCV dependencies in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T002 Update core models `AestheticsMetrics` and `TrackedSubject` in `src/core/entities.py`
- [x] T003 Update `AnalysisResult` model in `src/core/entities.py` to include aesthetics and tracked subjects

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Lighting & Color Evaluation (Priority: P1) 🎯 MVP

**Goal**: Identify extreme lighting conditions (overexposed/underexposed) and evaluate color harmony to provide real-time UI feedback.

**Independent Test**: Point camera at a bright light source; UI should display "过曝" or "逆光". Cover lens; UI should display "欠曝".

### Tests for User Story 1

- [x] T004 [P] [US1] Unit test for AestheticsAnalyzer in `tests/unit/core/analyzers/test_aesthetics_analyzer.py`

### Implementation for User Story 1

- [x] T005 [US1] Implement `AestheticsAnalyzer` using OpenCV histograms in `src/core/analyzers/aesthetics_analyzer.py`
- [x] T006 [US1] Integrate `AestheticsAnalyzer` into `CameraQAnalyzer` in `src/core/analyzer.py`
- [x] T007 [US1] Update `OverlayRenderer` in `src/ui/overlay.py` to display lighting warnings on screen

**Checkpoint**: At this point, User Story 1 should be fully functional (lighting and color feedback works).

---

## Phase 4: User Story 2 - Dynamic Subject Tracking (Priority: P2)

**Goal**: Predict the trajectory of moving subjects and suggest the optimal shutter timing when they intersect with compositional nodes.

**Independent Test**: Move an object across the camera frame; UI should draw a motion vector and briefly flash a "绝佳抓拍时机!" (Perfect Shutter Opportunity) message.

### Tests for User Story 2

- [x] T008 [P] [US2] Unit test for ObjectTracker in `tests/unit/core/trackers/test_object_tracker.py`

### Implementation for User Story 2

- [x] T009 [US2] Implement lightweight Centroid/IoU tracking logic in `src/core/trackers/object_tracker.py`
- [x] T010 [US2] Integrate `ObjectTracker` into `CameraQAnalyzer` in `src/core/analyzer.py` to calculate `shutter_opportunity`
- [x] T011 [US2] Update `OverlayRenderer` in `src/ui/overlay.py` to draw motion vectors and display the shutter prompt

**Checkpoint**: At this point, User Story 2 is integrated and full dynamic tracking works independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T012 Run validation scenarios from `quickstart.md`
- [x] T013 Update top-level `README.md` to document the new Stage 3 features

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - Sequentially in priority order: US1 -> US2

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Entities -> Analyzers/Trackers -> UI/Integration

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2.
2. Complete Phase 3 (US1) and verify the lighting feedback is stable.

### Incremental Delivery

1. Foundation ready.
2. Add US1 -> Test independently -> Aesthetics logic works.
3. Add US2 -> Test independently -> Tracking and shutter timing works.
