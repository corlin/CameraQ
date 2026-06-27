# Feature Specification: Video Shooting Assistant (Stage 3)

**Feature Branch**: `[010-video-assistant]`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Stage 3: Video Shooting Assistant. Features: Camera movement path, Shot duration, Shot group completeness, Stability score, Subject tracking, Auto-recommend next shot, Shooting script card, Auto-rough-cut after shooting."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Smart Video Stabilization & Pacing (Priority: P1)

Users recording video often struggle with camera shake and holding shots long enough to be useful in editing. This story introduces real-time stability feedback and minimum duration tracking.

**Why this priority**: Shaky, overly brief footage is the most common reason video clips become unusable. Solving this provides immediate value to all video shooters.

**Independent Test**: Can be fully tested by simulating camera shake and checking if the "stability score" warns the user, and if a "duration progress bar" fills up indicating a usable clip length.

**Acceptance Scenarios**:

1. **Given** the user is recording a video, **When** they hold the camera steady for 3 seconds, **Then** a subtle UI indicator confirms the shot is "Stable" and "Usable length reached."
2. **Given** the user is panning, **When** the pan is too fast or jittery, **Then** the UI warns "Move slower / Stabilize."

---

### User Story 2 - Subject Tracking & Camera Movement Path (Priority: P2)

Users struggle with dynamic tracking shots (e.g., following a moving person). This story introduces a path overlay and tracking lock to guide smooth camera motion.

**Why this priority**: Elevates the app from a passive recorder to an active "director of photography," guiding complex movements like tracking or orbiting.

**Independent Test**: Can be fully tested by locking onto a moving subject and verifying that a movement trajectory line/arrow guides the user to maintain framing.

**Acceptance Scenarios**:

1. **Given** a moving subject is locked, **When** the subject moves right, **Then** a semi-transparent path line indicates the user should pan right smoothly to maintain the subject in the golden ratio.
2. **Given** the user is attempting an orbit shot, **When** they move around the subject, **Then** the UI shows a trajectory path to maintain constant distance.

---

### User Story 3 - Shooting Script Card & Shot Group Completeness (Priority: P3)

Vloggers and content creators often forget to capture B-roll or transition shots. This story provides a "script card" checklist overlay during shooting to ensure a complete narrative sequence (e.g., Wide, Medium, Close-up, Cutaway).

**Why this priority**: Extremely valuable for creators, acting as an AI producer. It's P3 because it targets a slightly more advanced user segment than basic stabilization.

**Independent Test**: Can be fully tested by selecting a "Vlog Script" and verifying that as shots are recorded, the checklist updates, and the AI recommends the next required shot type.

**Acceptance Scenarios**:

1. **Given** an active "Event Recap" script, **When** the user records a wide establishing shot, **Then** the script marks it complete and recommends "Now get a close-up detail shot."
2. **Given** the user has recorded 3 out of 4 required shots, **When** they finish the 3rd shot, **Then** a checklist overlay shows "1 shot remaining: Subject Reaction."

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate and display a real-time stability score during video recording.
- **FR-002**: System MUST display a shot duration indicator suggesting a minimum usable length (e.g., 3-5 seconds for static shots).
- **FR-003**: System MUST identify and lock onto a primary moving subject across frames.
- **FR-004**: System MUST render a semi-transparent camera movement path (trajectory overlay) when performing dynamic movements (pan, tilt, track).
- **FR-005**: System MUST allow users to select predefined "Shooting Script Cards" (e.g., Vlog, Interview, Event).
- **FR-006**: System MUST track the completion of shot types against the active Script Card and recommend the next shot.
- **FR-007**: System MUST generate an automatic "rough cut" timeline data structure combining the recorded clips from a completed Script Card. [NEEDS CLARIFICATION: Does the app need to physically render the compiled video file locally, or just generate an edit decision list (EDL)/metadata structure for third-party editors?]

### Key Entities *(include if feature involves data)*

- **VideoClip**: Represents a single recorded take, including metadata like duration, stability score, and shot type classification.
- **ShootingScript**: A template containing a list of required `ShotRequirement` objects (e.g., 1 Wide, 2 Mediums, 1 Close-up).
- **ShotRequirement**: Defines the criteria for a clip to fulfill a slot in a script (e.g., minimum duration, specific framing/subject).
- **TrajectoryState**: Tracks the real-time velocity and intended path of camera movement for rendering UI overlays.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users using the Shooting Script feature produce usable video sequences with at least 80% completeness (all required shots captured).
- **SC-002**: The stability scoring and duration prompting result in a 30% reduction in clips shorter than 2 seconds (which are typically unusable in editing).
- **SC-003**: Real-time trajectory overlay rendering maintains a strict 30+ FPS performance target without dropping frames during video recording.

## Assumptions

- Users have enough local storage to record multiple video clips in a session.
- Real-time video processing (especially multi-object tracking) might run at a slightly lower internal resolution to maintain frame rates, with the actual recording being high-resolution.
- Audio recording is handled by the default OS pipeline and doesn't require complex AI intervention in this specific feature slice.
