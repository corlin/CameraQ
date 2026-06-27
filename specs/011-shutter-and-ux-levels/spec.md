# Feature Specification: Shutter Feedback & UX Levels

**Feature Branch**: `[011-shutter-and-ux-levels]`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "先做选项 3 (更深度的抓拍与参数辅助), 再做选项 2 (AI 辅助等级切换)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Shutter Timing & Parameter Guidance (Priority: P1)

Users often miss the perfect moment because they don't know when to press the shutter (e.g., people blinking) or they shoot in bad lighting without adjusting parameters (e.g., severe backlight). This feature acts as a proactive assistant that prompts the user precisely when to shoot or adjust settings.

**Why this priority**: Directly impacts the final photo quality. A well-composed but blurry or badly exposed photo is still unusable.

**Independent Test**: Can be tested by simulating a backlit scene and observing the parameter prompt ("Turn on HDR"), or simulating a group photo and observing the visual flash when all subjects are looking at the camera.

**Acceptance Scenarios**:

1. **Given** a heavily backlit scene is detected, **When** the AI analyzes the frame, **Then** a high-priority prompt appears: "Tap screen to lock exposure or enable HDR."
2. **Given** a group photo scene, **When** all detected faces have their eyes open and are smiling, **Then** the UI displays a prominent visual flash/border indicating "Perfect Shutter Opportunity!"

---

### User Story 2 - AI Coaching Levels UI (Priority: P2)

Users have different tolerance levels for on-screen UI. Professionals might want deep analytics, while casual users might only want subtle visual cues. This feature replaces the sidebar toggles with a unified "Coaching Level" button on the main UI.

**Why this priority**: Enhances the core UX by putting the user in control of how much "noise" the AI coach generates. Resolves the issue of a cluttered viewfinder.

**Independent Test**: Can be tested by tapping the Coaching Level button and verifying that the UI elements toggle between Off, Minimal, Coach, and Pro modes.

**Acceptance Scenarios**:

1. **Given** the app is in "Off" mode, **When** a perfect composition is achieved, **Then** no AI overlays (boxes, text, arrows) are displayed.
2. **Given** the app is in "Minimal" mode, **When** the AI suggests a composition change, **Then** only the ghost box and arrows appear (no explanatory text).
3. **Given** the app is in "Pro" mode, **When** the user pans the camera, **Then** advanced metrics (e.g., scores, histograms, bounding boxes) are visible alongside the coach.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST evaluate lighting conditions (e.g., backlight, severe underexposure) and emit actionable parameter advice (e.g., "Tap to expose", "Enable HDR").
- **FR-002**: System MUST evaluate facial states (eyes open, smiling) in portrait/group contexts and emit a "Perfect Shutter Opportunity" boolean state when conditions are optimal.
- **FR-003**: System MUST provide a main UI toggle to cycle through 4 AI Coaching Levels: Off, Minimal, Coach, Pro.
- **FR-004**: System MUST suppress all AI overlays when the level is "Off".
- **FR-005**: System MUST render only visual guides (ghost boxes, arrows) and suppress text advice when the level is "Minimal".
- **FR-006**: System MUST render visual guides AND one-line text advice when the level is "Coach".
- **FR-007**: System MUST render all available debugging and analytical overlays (bounding boxes, scores, debug text) when the level is "Pro".

### Key Entities *(include if feature involves data)*

- **CoachingLevel**: An Enum representing the current UI state (`OFF`, `MINIMAL`, `COACH`, `PRO`).
- **AestheticsMetrics**: Extended to include precise exposure/backlight boolean flags.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users capture 20% fewer photos with closed eyes when the shutter opportunity feature is active.
- **SC-002**: 90% of users discover and use the Coaching Level button within their first 3 sessions, compared to the previously hidden sidebar.
- **SC-003**: The UI rendering performance remains strictly above 30 FPS across all 4 coaching levels.

## Assumptions

- Facial state analysis (eyes/smile) can be reasonably approximated using the existing YOLO pose/keypoint detector or a lightweight heuristic, without needing a heavy new neural network.
- The user's device has a functional HDR or exposure lock mechanism that the app can suggest using, even if the app doesn't automatically trigger it on the hardware level yet.
