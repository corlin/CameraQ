# Tasks: UI/UX Aesthetics Polish

**Input**: Design documents from `specs/004-ui-ux-polish/`

**Prerequisites**: plan.md, spec.md, data-model.md, quickstart.md, research.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- *(No tasks needed for Phase 1 as the project and dependencies are already fully set up.)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T001 Update `AICoachingResult` and `AnalysisResult` in `src/core/entities.py` to support `duration` tracking and `is_active()` logic based on `timestamp`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Aesthetically Pleasing UI Overlays (Priority: P1) 🎯 MVP

**Goal**: Make the grid, bounding boxes, and text prompts visually refined using translucent background plates and sleek colors.

**Independent Test**: Verify the visual rendering of the rule of thirds grid, AI tracking arrows, and text backgrounds in the live feed.

### Implementation for User Story 1

- [x] T002 [US1] Update `draw_rule_of_thirds` in `src/ui/overlay.py` to use a sleek color palette and alpha blending (semi-transparent lines).
- [x] T003 [US1] Update bounding box drawing in `src/ui/overlay.py` to use sleek styling (e.g., translucent backgrounds instead of thick lines).
- [x] T004 [US1] Update `draw_aesthetics` and `draw_tracking` in `src/ui/overlay.py` to draw text labels with semi-transparent background plates for high readability.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dynamic Prompt Durations and Fading (Priority: P2)

**Goal**: Ensure transient text messages fade or disappear when they are no longer relevant or after a set duration.

**Independent Test**: Trigger an AI coach prompt and verify it disappears after 10 seconds. Verify lighting warnings disappear immediately when corrected.

### Implementation for User Story 2

- [x] T005 [US2] Update `draw_ai_coach` in `src/ui/overlay.py` to use the `is_active()` duration check from `entities.py`.
- [x] T006 [US2] Refactor `OverlayRenderer.draw()` in `src/ui/overlay.py` to only render active and relevant UI alerts based on duration metadata.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T007 Run `quickstart.md` validation scenarios.
- [x] T008 Update top-level `README.md` to reflect completion of the UI/UX polish.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: N/A
- **Foundational (Phase 2)**: Starts immediately
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2)

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational
2. Complete Phase 3: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
