# Tasks: AI UX Redesign

**Input**: Design documents from `/specs/008-ai-ux-redesign/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

*(No setup tasks needed for this UI refactor)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

*(No foundational tasks needed)*

---

## Phase 3: User Story 1 - Non-intrusive AI Assistance (Priority: P1) 🎯 MVP

**Goal**: Make AI suggestions visually integrated and non-intrusive so they don't distract from composing the shot.

**Independent Test**: Can be fully tested by launching the camera and verifying that AI suggestions appear as subtle UI elements with time-based decay.

### Implementation for User Story 1

- [X] T001 [US1] Add state variables `ai_coach_last_update` and `ai_coach_message` to `OverlayRenderer` init in `src/ui/overlay.py`
- [X] T002 [US1] Implement time-based decay (auto-collapse after 5s) for AI Coaching overlay in `src/ui/overlay.py`
- [X] T003 [US1] Update AI Coaching rendering to use rounded rectangles and professional styling in `src/ui/overlay.py`

**Checkpoint**: At this point, User Story 1 should be fully functional.

---

## Phase 4: User Story 2 - Professional Visual Language (Priority: P2)

**Goal**: Use standard professional camera iconography and minimalistic layout (icon + short text, thin bounding boxes).

**Independent Test**: Can be tested by verifying bounding boxes use thin lines and scene context uses icons.

### Implementation for User Story 2

- [X] T004 [US2] Update bounding box rendering to use professional thin lines or corner brackets in `src/ui/overlay.py`
- [X] T005 [US2] Add `SCENE_ICONS` dictionary mapping to `OverlayRenderer` in `src/ui/overlay.py`
- [X] T006 [US2] Update Scene Context rendering to use the `SCENE_ICONS` mapping instead of verbose text in `src/ui/overlay.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T007 Run quickstart.md validation scenarios to ensure central 50% is unobscured

---

## Dependencies & Execution Order

- **Phase 3 (US1)**: Can start immediately.
- **Phase 4 (US2)**: Can start in parallel or sequentially.
- **Phase 5**: Depends on all user stories.
