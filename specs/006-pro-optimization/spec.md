# Feature Specification: Professional Performance & UX Deep Optimization

**Feature Branch**: `006-pro-optimization`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "思考一下优化点,往专业性和用户体验上深度思考"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Render Pipeline Performance Optimization (Priority: P1)

As a photographer using CameraQ in the field, I need the viewfinder to run at a consistently smooth frame rate (≥25 FPS on a MacBook) without visible stuttering or lag, so that I can see real-time composition feedback while composing a shot.

**Why this priority**: The current render pipeline performs 3 full-image pixel copies and 2 color-space conversions (BGR→RGBA→composite→RGB→BGR) every single frame, plus redundant font file lookups on every frame. This is the #1 bottleneck that directly degrades the core user experience. Without a smooth viewfinder, all other features lose their value.

**Independent Test**: Run the application, observe FPS counter stays above 25 FPS consistently. Compare before/after FPS with profiling data.

**Acceptance Scenarios**:

1. **Given** the camera is running at 30 FPS input, **When** all analysis modules are enabled, **Then** the displayed frame rate remains ≥ 20 FPS with no visible lag between camera movement and display update.
2. **Given** the application has just started, **When** the first frame renders, **Then** fonts are loaded once at initialization and reused for all subsequent frames (no per-frame filesystem access).
3. **Given** the analysis pipeline is processing, **When** a computationally expensive rule (e.g., horizon detection) runs, **Then** it should be throttled to run at a reduced cadence (e.g., every 5th frame) rather than every frame, with cached results used in between.

---

### User Story 2 - Professional Multi-Dimensional Composition Scoring (Priority: P2)

As a photography learner, I want to see a breakdown of my composition score across multiple dimensions (subject placement, structural alignment, balance, interference, style), not just a single deduction-based number, so that I can understand which specific aspects of my composition need improvement.

**Why this priority**: The current scoring system starts at 100 and only subtracts points. There is no positive reinforcement for good technique. The existing `CompositionScore` entity (with subject/structure/balance/interference/style sub-scores) was designed but never implemented. A multi-dimensional score is the cornerstone of professional-grade coaching.

**Independent Test**: Frame a shot with good rule-of-thirds placement but a tilted horizon. Verify that the subject placement score is high while the structural score is low, and the feedback message explains both.

**Acceptance Scenarios**:

1. **Given** a subject is perfectly aligned on a rule-of-thirds intersection, **When** the score is calculated, **Then** the subject placement sub-score reflects a positive bonus (not just "no penalty").
2. **Given** any frame is analyzed, **When** the score is displayed, **Then** the user can see a visual breakdown of at least 3 distinct scoring dimensions (e.g., via a small radar/bar chart or segmented progress bar in the overlay).
3. **Given** the composition has a specific weakness, **When** the user reads the feedback, **Then** the feedback message explicitly names the weakest dimension and offers a targeted improvement tip.

---

### User Story 3 - Expanded & Intelligent Settings Panel (Priority: P3)

As a power user, I want the settings sidebar to expose more configurable parameters beyond simple on/off toggles (e.g., AI sampling interval, image quality for Gemini, scoring sensitivity), and I want the sidebar to feel alive with smooth animations, so that I feel in control of a professional tool.

**Why this priority**: The current sidebar only has 3 boolean toggles and appears/disappears instantly. YOLO object detection cannot be disabled. Many critical parameters (AI sampling interval, image resize dimensions, scoring thresholds) are hardcoded. Expanding configurability and adding micro-animations elevates the experience from "debug tool" to "professional application".

**Independent Test**: Open the sidebar, adjust the "AI Sampling Interval" slider from 5s to 15s, and verify that Gemini API calls now occur every 15 seconds. Close and reopen the app; verify the 15s setting persists.

**Acceptance Scenarios**:

1. **Given** the sidebar is opened, **When** the user views the settings, **Then** they see categorized groups: "Detection Modules" (toggles), "Performance" (sliders/values), and "Display" (overlay opacity, etc.).
2. **Given** the user adjusts a slider value, **When** the next analysis cycle runs, **Then** the adjusted parameter is immediately reflected in the system behavior without restart.
3. **Given** the sidebar is closed, **When** the user presses Tab, **Then** the sidebar smoothly slides in from the right edge over ~200ms (not an instant pop-in).

---

### User Story 4 - Graceful Resource Management & Error Resilience (Priority: P4)

As a user who runs CameraQ for extended sessions, I want the application to handle errors gracefully (camera disconnection, API failures, resource exhaustion) without crashing, and to cleanly release all resources on exit, so that I can trust the tool during a real photo shoot.

**Why this priority**: The current code lacks `ai_coach.stop()` on shutdown, has no handling for camera disconnection, shares mutable settings across threads without synchronization, and uses `print()` instead of structured logging. These are reliability fundamentals that distinguish a prototype from a tool you can depend on.

**Independent Test**: Unplug the webcam while the app is running; verify the app displays a "Camera disconnected" message and does not crash. Press `q` to quit and verify all threads terminate within 2 seconds.

**Acceptance Scenarios**:

1. **Given** the application is running, **When** the user presses 'q' to quit, **Then** the AI Coach background thread is properly stopped, the camera stream is released, and all OpenCV windows are destroyed within 2 seconds.
2. **Given** the Gemini API returns a 429 rate limit error, **When** the error is handled, **Then** the user sees a calm, non-alarming message (e.g., "AI 教练休息中...") instead of raw error text.
3. **Given** settings are shared between the UI thread and analysis thread, **When** a toggle is clicked, **Then** the state change is thread-safe and cannot cause a race condition.

---

### Edge Cases

- What happens when `config.json` is corrupted or manually edited with invalid values? → Should fall back to defaults with a warning.
- What happens when the camera provides frames at a rate much lower than expected (e.g., 10 FPS)? → Analysis cadence should adapt rather than assuming 30 FPS.
- What happens if the YOLO model file is missing from disk? → Should display a clear error message rather than an unhandled exception.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST cache font objects at initialization time and reuse them across all frames (eliminating per-frame filesystem access).
- **FR-002**: System MUST throttle expensive analysis operations (horizon detection, saliency detection) to run at a configurable reduced cadence (e.g., every N frames), using cached results for intermediate frames.
- **FR-003**: System MUST implement the multi-dimensional `CompositionScore` model (subject, structure, balance, interference, style) with both positive and negative scoring factors.
- **FR-004**: System MUST display the multi-dimensional score breakdown visually in the overlay (e.g., segmented bar, radar chart, or labeled sub-scores).
- **FR-005**: System MUST support toggling YOLO object detection on/off in the settings sidebar, consistent with the existing pose/saliency/AI coach toggles.
- **FR-006**: System MUST support configurable numeric parameters in the settings sidebar (e.g., AI sampling interval via slider or numeric input).
- **FR-007**: System MUST properly stop the AI Coach background thread on application exit.
- **FR-008**: System MUST use Python's `logging` module instead of `print()` for all operational messages.
- **FR-009**: System MUST ensure thread-safe access to shared `SettingsManager` state between UI and analysis threads.
- **FR-010**: System MUST remove dead/unused code: unused imports in `analyzer.py`, unused entity classes, unused `drawing.py` utilities.

### Key Entities

- **CompositionScore**: Multi-dimensional score object with sub-scores for subject placement, structural alignment, balance, interference, and style. Already defined in `entities.py` but currently unused.
- **SettingsManager** (enhanced): Extended to support numeric parameters (float ranges) in addition to boolean toggles, with thread-safe access.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Average frame rate improves by at least 30% compared to the current baseline with all modules enabled (measured via the on-screen FPS counter).
- **SC-002**: Composition score displays at least 3 distinct sub-dimensions, each with its own visual indicator.
- **SC-003**: All operational log messages use Python's `logging` module with appropriate log levels (DEBUG, INFO, WARNING, ERROR).
- **SC-004**: Application exits cleanly within 2 seconds of the user pressing 'q', with no orphaned threads.
- **SC-005**: Settings sidebar displays at least 2 configurable numeric parameters beyond the existing boolean toggles.

## Assumptions

- The existing PIL-based overlay rendering approach will be retained (no migration to a different GUI framework).
- Performance improvements will be achieved through caching, throttling, and reducing redundant work — not through GPU acceleration or native code rewrites.
- The multi-dimensional scoring system will be rule-based (extending the existing feedback/rule engine), not ML-based.
- Thread safety will be achieved via simple `threading.Lock` rather than more complex concurrency primitives.
