# Feature Specification: Alignment and Clutter

**Feature Branch**: `[012-alignment-and-clutter]`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "只考虑2,3 (Background Clutter Detection and Progressive Alignment Feedback)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Background Clutter Detection (Priority: P1)

As a user taking photos of subjects, I want the AI to proactively warn me when the background is too messy or cluttered, so I can adjust my camera angle or zoom level before taking the shot.

**Why this priority**: A clean background is one of the most fundamental principles of good photography. Warning users about high background interference directly increases the aesthetic quality of their photos.

**Independent Test**: Can be fully tested by pointing the camera at a subject in front of a busy bookshelf vs. a plain wall, and verifying the AI correctly triggers the clutter warning.

**Acceptance Scenarios**:

1. **Given** the camera is pointing at a subject, **When** the background edge density or clutter exceeds the acceptable threshold, **Then** the AI suggests "背景较乱，建议切 2x 焦段" (Background is cluttered, suggest switching to 2x zoom).
2. **Given** the camera is pointing at a subject with a clean background, **When** the clutter is low, **Then** no background clutter warning is triggered.

---

### User Story 2 - Progressive Alignment Feedback (Priority: P1)

As a user following the AI's "Ghost Box" composition suggestions, I want a clear visual and tactile "snap" when I align the subject perfectly with the target box, so I know exactly when to take the photo without staring at numbers.

**Why this priority**: Helps users quickly and intuitively find the optimal framing without cognitive overload. Translates composition math into physical/visual muscle memory.

**Independent Test**: Can be fully tested by deliberately misaligning the subject with the AI Ghost Box, then moving the camera to perfectly overlap the subject and the box, observing the UI transition into the "locked/snapped" golden state.

**Acceptance Scenarios**:

1. **Given** an AI coaching target box is active, **When** the subject's bounding box has an IoU (Intersection over Union) > 0.65 with the target box, **Then** the target box visually highlights (e.g., solid gold border) and the system emits a "perfect alignment" haptic/log event.
2. **Given** an AI coaching target box is active, **When** the subject is outside the target box (IoU <= 0.65), **Then** the target box remains in its default semi-transparent tracking state.

### Edge Cases

- What happens when there are multiple subjects in the frame? (The alignment and clutter checks will default to the *primary* tracked subject).
- How does system handle rapid camera movement causing motion blur? (Edge detection for clutter might spike or drop unpredictably; smoothing or throttling the clutter warning over a few frames might be necessary).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute a background clutter/frequency score for the region outside the primary subject's bounding box.
- **FR-002**: System MUST append a specific proactive advice message if the background clutter score exceeds a predefined threshold.
- **FR-003**: System MUST calculate the overlap (IoU) between the active scenario template's `target_box` and the primary subject's bounding box in real-time.
- **FR-004**: System MUST transition the UI rendering of the `target_box` to a highly visible "snapped" state when the IoU exceeds 65%.
- **FR-005**: System MUST log a simulated haptic vibration event when the alignment state transitions from false to true.

### Key Entities *(include if feature involves data)*

- **AestheticsMetrics**: Extended to include `is_background_cluttered`.
- **AICoachingResult**: Extended to include `perfect_alignment` boolean flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The background clutter detection logic executes in under 10ms per frame to maintain real-time performance.
- **SC-002**: The alignment IoU calculation successfully triggers the UI "snap" state exactly when the subject is visually within the target box, providing zero-latency visual confirmation.
- **SC-003**: The background clutter warning correctly suppresses itself when the user switches to a cleaner background, proving real-time responsiveness.

## Assumptions

- Users have the AI Coaching Level set to `COACH` or `PRO` to see the target box and alignment feedback.
- We will use standard Canny Edge detection or variance of Laplacian on the grayscale image to approximate visual clutter.
- Simulated haptic feedback via console logging is acceptable for the MVP desktop environment.
