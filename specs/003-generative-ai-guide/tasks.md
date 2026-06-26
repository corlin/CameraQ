# Tasks: Generative AI Guide (Stage 4)

**Input**: Design documents from `/specs/003-generative-ai-guide/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify or install `google-genai` dependency in the environment.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T002 [P] Extend `AnalysisResult` and create `AICoachingResult` model in `src/core/entities.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Automated Contextual Coaching (Priority: P1) 🎯 MVP

**Goal**: Users receive high-level, artistic photography suggestions based on the current scene, without UI lag.

**Independent Test**: Can be fully tested by pointing the camera at a scene and waiting for an AI suggestion bubble to appear after a few seconds, while verifying that the live camera feed remains smooth at 30 FPS.

### Implementation for User Story 1

- [x] T003 [P] [US1] Create `AICoach` class with `threading.Thread` and `queue.Queue` in `src/core/ai_coach.py`
- [x] T004 [US1] Implement background `_process_loop`, `enqueue_frame()`, and `get_latest_advice()` in `src/core/ai_coach.py`
- [x] T005 [US1] Initialize `AICoach` within `CameraQAnalyzer.__init__` in `src/core/analyzer.py`
- [x] T006 [US1] Add a 5-second sampling logic to push frames to the AI Coach in `src/core/analyzer.py`
- [x] T007 [US1] Extract the latest `ai_coaching` result into `AnalysisResult` inside `src/core/analyzer.py`
- [x] T008 [US1] Update `OverlayRenderer.draw` in `src/ui/overlay.py` to render the AI coaching text using Pillow (`ImageDraw`)

**Checkpoint**: At this point, User Story 1 should be fully functional. Background coaching works autonomously.

---

## Phase 4: User Story 2 - On-Demand Inspiration (Priority: P2)

**Goal**: Users who are actively setting up a specific shot can manually request the AI to provide inspiration or critique on the current frame.

**Independent Test**: Can be tested by pressing a "Coach Me" key/button. A specific, contextual response should appear shortly after.

### Implementation for User Story 2

- [x] T009 [US2] Expose a `force_analyze()` method on `CameraQAnalyzer` in `src/core/analyzer.py`
- [x] T010 [US2] Map a keyboard event (e.g., pressing 'c' for coach) in the main loop of `src/ui/camera_app.py` to trigger `force_analyze()`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T011 Run quickstart.md validation scenarios to ensure 30 FPS stability during Gemini calls
- [x] T012 Update top-level `README.md` to check off Stage 4 completion

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2).
- **User Story 2 (P2)**: Integrates into US1's underlying `AICoach` thread, so must be implemented after US1.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2
2. Complete Phase 3: User Story 1
3. **STOP and VALIDATE**: Test background coaching independently without breaking the camera framerate.
4. If successful, proceed to US2.
