# Tasks: AI Scenario Templates

**Input**: Design documents from `/specs/009-scenario-templates/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

*(No setup tasks needed for this UI refactor)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T001 Update `AICoaching` entity in `src/core/entities.py` to add `target_box` (tuple), `directional_arrows` (list), and `active_template` (str) fields with default values.
- [x] T002 Update `src/ui/overlay.py` to cleanly read `target_box` and `directional_arrows` from the coaching object without crashing if missing.

---

## Phase 3: User Story 1 - Ghost Composition Boxes & Directional Arrows (Priority: P1) 🎯 MVP

**Goal**: Make AI suggestions visually integrated and non-intrusive so they don't distract from composing the shot.

**Independent Test**: Can be fully tested by verifying that ghost target boxes and edge arrows appear when a simulated coaching object is present.

### Implementation for User Story 1

- [x] T003 [US1] In `src/ui/overlay.py`, implement rendering of the `target_box` using PIL `ImageDraw.rectangle` with a semi-transparent fill.
- [x] T004 [US1] In `src/ui/overlay.py`, implement rendering of `directional_arrows` on the screen edges (Left, Right, Top, Bottom) using Unicode symbols and `ImageDraw.text`.

**Checkpoint**: At this point, the UI layer can render boxes and arrows if passed to it.

---

## Phase 4: User Story 2 - Scenario-Specific Templates (Priority: P2)

**Goal**: Dynamically switch compositional rules based on the scene (Portrait vs Landscape).

**Independent Test**: Can be tested by feeding different scene contexts and verifying the `active_template` and coaching advice changes.

### Implementation for User Story 2

- [x] T005 [US2] In `src/core/analyzer.py` (or wherever AI coaching logic resides), add a rule to set `active_template = "Portrait"` if `current_scene_context.scene_type == "Portrait"`, and emit a portrait-specific target box and arrows.
- [x] T006 [US2] In `src/core/analyzer.py`, add a rule to set `active_template = "Landscape"` if `current_scene_context.scene_type == "Landscape"`, emitting a horizon-based target box and arrows.
- [x] T007 [US2] In `src/ui/overlay.py`, display the `active_template` text in the scene context badge (e.g. `Template: Portrait`).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Video Speaking/Vlog Template (Priority: P3)

**Goal**: Support Vlog scenarios with 9:16 aspect ratio logic.

**Independent Test**: Test by simulating Vlog mode and checking if the ghost box outlines a 9:16 area in the center.

### Implementation for User Story 3

- [x] T008 [US3] In `src/core/analyzer.py`, add logic for `active_template = "Vlog"`, outputting a 9:16 centered `target_box` regardless of the camera's actual aspect ratio.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T009 Run quickstart.md validation scenarios to ensure UI scales correctly with different screen sizes.

---

## Dependencies & Execution Order

- **Phase 2 (Foundational)**: MUST be completed first.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 3.
- **Phase 5 (US3)**: Depends on Phase 4.
- **Phase 6**: Depends on all user stories.
