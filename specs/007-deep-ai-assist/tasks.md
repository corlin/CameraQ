---
description: "Task list template for feature implementation"
---

# Tasks: deep-ai-assist

**Input**: Design documents from `/specs/007-deep-ai-assist/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as unit testing is a core requirement of the project's quality standard.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify `google-genai` is added to project dependencies (via `uv`)
- [x] T002 Ensure `GEMINI_API_KEY` loading is handled in `src/core/settings.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create `SceneContext` and `AIInteraction` data classes in `src/core/entities.py`
- [x] T004 Extend `AnalysisResult` in `src/core/entities.py` to include `current_scene_context` and `active_interactions`
- [x] T005 [P] Implement Gemini API client service in `src/core/gemini_client.py` using `llm_schema.json` constraint
- [x] T006 [P] Add exposure and ISO control interfaces (with software fallback) to `src/core/io/camera.py`
- [x] T007 [P] Create `tests/unit/core/test_gemini_client.py` mock tests
- [x] T008 [P] Create `tests/unit/core/io/test_camera.py` for exposure control

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Context-Aware Scene Analysis (Priority: P1) 🎯 MVP

**Goal**: Scene understanding and automatic camera parameter adjustment.

**Independent Test**: Can be fully tested by pointing the camera at various distinct scenes (e.g., a person, a landscape) and verifying the AI correctly identifies the context and applies settings.

### Implementation for User Story 1

- [x] T009 [US1] Create deep scene context rule in `src/core/rules/scene_rule.py`
- [x] T010 [US1] Integrate `gemini_client` into `src/core/analyzer.py` with asynchronous polling (2s interval)
- [x] T011 [US1] Apply `SceneContext` recommended ISO and shutter via `camera.py` in the main analyzer loop
- [x] T012 [P] [US1] Render `SceneContext` data in the UI overlay in `src/ui/overlay.py`
- [x] T013 [P] [US1] Write unit tests for `scene_rule.py` in `tests/unit/rules/test_scene_rule.py`
- [x] T014 [US1] Write unit tests for async analyzer behavior in `tests/unit/core/test_analyzer.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Interactive AI Photography Assistant (Priority: P2)

**Goal**: Proactive voice and text interactions acting as a photography coach.

**Independent Test**: Can be fully tested by triggering the interactive assistant and hearing the macOS `say` voice prompt.

### Implementation for User Story 2

- [x] T015 [US2] Update `src/core/ai_coach.py` to support `InteractionType` (Voice, Popup, Chat).
- [x] T016 [US2] Create non-blocking voice synthesis function using `subprocess` and `say` in macOS.
- [x] T017 [US2] Integrate voice feedback dispatch in the `CameraQAnalyzer` loop based on AI coaching logic.
- [x] T018 [P] [US2] Update `src/ui/overlay.py` to differentiate between popup styles and chat interfaces.
- [x] T019 [US2] Add unit tests for interaction routing in `tests/unit/core/test_interaction.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T020 Code cleanup and error handling for network timeouts in Gemini API
- [ ] T021 Validate End-to-End flow via `specs/007-deep-ai-assist/quickstart.md`
- [ ] T022 Document new configuration flags (`--deep-ai-enabled`) in CLI entrypoint

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P2)

### Parallel Opportunities

- Gemini client implementation and Camera I/O enhancements can be done in parallel (T005, T006).
- Unit tests can be written in parallel with their implementations.
- UI overlay rendering (T012, T018) can be developed independently of the backend logic if mocked.

## Phase 6: Convergence

- [x] T023 Implement interactive query mechanism (e.g., text input or voice recording) for users to ask specific questions per FR-005 and US2/AC1 (missing)
- [x] T024 Add exponential backoff and timeout handling in `gemini_client.py` per T020 (partial)
- [x] T025 Validate End-to-End flow and update `quickstart.md` per T021 (missing)
- [x] T026 Document or add `--deep-ai-enabled` configuration flag in CLI entrypoint per T022 (missing)

---

## Phase 7: Edge Cases & Performance

- [x] T027 Handle "Low Confidence" fallback and conflicting subjects in `src/core/analyzer.py` and `scene_rule.py` per U1.
- [x] T028 Create `tests/integration/test_performance.py` to enforce the <2.0s latency SLA (SC-002) per C1.
