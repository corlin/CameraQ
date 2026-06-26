# Implementation Tasks: Analysis Toggles Sidebar

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

 - [x] T001 Initialize `src/core/settings.py` file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

 - [x] T002 Implement `SettingsManager` skeleton in `src/core/settings.py` with default boolean flags

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Toggle Individual Analysis Modules (Priority: P1) 🎯 MVP

**Goal**: Allow users to dynamically toggle specific analysis modules (like AI Coach, Pose Detection, Saliency Detection) on or off from a sidebar.

**Independent Test**: Can be fully tested by opening the sidebar, toggling "Pose Detection" off, and observing that the skeletons stop appearing and YOLO pose processing halts.

### Implementation for User Story 1

 - [x] T003 [US1] Update `CameraQAnalyzer.__init__` in `src/core/analyzer.py` to accept and store `SettingsManager`.
 - [x] T004 [P] [US1] Wrap YOLO pose execution with `if self.settings.pose_detection_enabled` in `src/core/analyzer.py`.
 - [x] T005 [P] [US1] Wrap Saliency map execution with `if self.settings.saliency_enabled` in `src/core/analyzer.py`.
 - [x] T006 [P] [US1] Wrap Gemini API enqueueing with `if self.settings.ai_coach_enabled` in `src/core/analyzer.py`.
 - [x] T007 [US1] Update `OverlayRenderer` in `src/ui/overlay.py` to accept `SettingsManager` and store sidebar state (`is_sidebar_open`).
 - [x] T008 [US1] Add `draw_sidebar` logic in `src/ui/overlay.py` to render toggle buttons based on current settings state.
 - [x] T009 [US1] Update `main` in `src/ui/camera_app.py` to instantiate `SettingsManager` and pass it to Analyzer/Renderer.
 - [x] T010 [US1] Implement `cv2.setMouseCallback` in `src/ui/camera_app.py` to map clicks to sidebar toggle state updates.
 - [x] T011 [US1] Bind the `Tab` key in `src/ui/camera_app.py` to open/close the sidebar.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (but settings won't persist on restart).

---

## Phase 4: User Story 2 - Persist Settings (Priority: P2)

**Goal**: Remember module toggle preferences between sessions.

**Independent Test**: Can be fully tested by turning off a feature, closing the application, restarting it, and verifying the feature is still turned off.

### Implementation for User Story 2

 - [x] T012 [US2] Implement `load()` logic in `SettingsManager` (`src/core/settings.py`) to read from `config.json`.
 - [x] T013 [US2] Implement `save()` logic in `SettingsManager` (`src/core/settings.py`) to write to `config.json`.
 - [x] T014 [US2] Hook up `save()` to be called whenever a setting is toggled via the UI in `src/ui/camera_app.py`.
 - [x] T015 [US2] Ensure `load()` is called upon initialization in `src/ui/camera_app.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Settings will now persist across application restarts.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

 - [x] T016 [P] Verify `config.json` is added to `.gitignore` to avoid committing local user preferences.
 - [x] T017 Run quickstart.md validation locally.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 UI being available to hook the save callback.

### Parallel Opportunities

- AI Coach, YOLO, and Saliency analyzers skipping logic updates in `analyzer.py` (T004, T005, T006) can run in parallel.
- Adding `config.json` to `.gitignore` (T016) can happen anytime.

---

## Parallel Example: User Story 1

```bash
# Update analyzer skipping logic in parallel:
Task: "Wrap YOLO pose execution with if self.settings.pose_detection_enabled in src/core/analyzer.py."
Task: "Wrap Saliency map execution with if self.settings.saliency_enabled in src/core/analyzer.py."
Task: "Wrap Gemini API enqueueing with if self.settings.ai_coach_enabled in src/core/analyzer.py."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test the toggle functionality and UI rendering.
5. Proceed to US2.
