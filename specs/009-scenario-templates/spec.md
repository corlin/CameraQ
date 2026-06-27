# Feature Specification: AI Scenario Templates

**Feature Branch**: `[009-scenario-templates]`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "结束当前跌倒.开始 stage 2 (Based on ref1.md Stage 2: Scenario Templates)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ghost Composition Boxes & Directional Arrows (Priority: P1)

As a photographer, I want the AI to provide a semi-transparent ghost composition box and directional edge arrows, so that I know exactly how to adjust my camera intuitively without reading text.

**Why this priority**: This fulfills the core vision from Stage 1 that was missed in the initial UX redesign. Visual guidance (arrows/boxes) is strictly superior to text-based coaching for a fast-paced camera interface.

**Independent Test**: Can be fully tested by pointing the camera at a misaligned subject and verifying that directional arrows and a ghost target box appear.

**Acceptance Scenarios**:

1. **Given** the subject is off-center, **When** the AI analyzes the frame, **Then** a directional arrow (e.g., ←) appears on the edge of the screen and a ghost box appears where the subject should be.
2. **Given** the user moves the camera to align with the ghost box, **When** alignment is reached, **Then** the ghost box and arrows disappear or turn green.

---

### User Story 2 - Scenario-Specific Templates (Priority: P2)

As a user, I want the AI to dynamically switch its compositional rules based on the detected scene (e.g., Portrait vs Landscape vs Food), so that the coaching is highly relevant to what I'm shooting.

**Why this priority**: Not all photos use the rule of thirds. A portrait needs different guidance (eye level, head room) than a landscape (horizon line, foreground).

**Independent Test**: Can be tested by switching between photographing a person and photographing a building, verifying that the coaching logic changes.

**Acceptance Scenarios**:

1. **Given** the camera points at a person, **When** the AI detects a Portrait scene, **Then** it evaluates head room and eye position instead of just general thirds.
2. **Given** the camera points at a landscape, **When** the AI detects a Landscape scene, **Then** it evaluates the horizon line and prompts to keep it level.

---

### User Story 3 - Video Speaking/Vlog Template (Priority: P3)

As a short video creator, I want a specialized "Vlog/Speaking" template that checks face exposure, eye height, and 9:16 aspect ratio, so that my talking-head videos are professional.

**Why this priority**: Vlogging is a massive use case, and its requirements are unique (needs vertical video framing, face lighting, and stability).

**Independent Test**: Can be tested by selecting the Vlog mode and verifying it prompts for 9:16 aspect ratio and face exposure.

**Acceptance Scenarios**:

1. **Given** the user selects the Vlog template, **When** they are framing a shot, **Then** the AI checks for 9:16 framing and highlights if the face is underexposed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render a semi-transparent "ghost" box indicating the recommended crop or subject position.
- **FR-002**: System MUST render directional arrows (Up, Down, Left, Right, Forward, Backward) on the edges of the screen indicating required physical camera movement.
- **FR-003**: System MUST automatically classify the scene into predefined templates (Portrait, Landscape, Food, Architecture, Vlog).
- **FR-004**: System MUST apply unique compositional evaluation logic per template (e.g., rule of thirds for landscape, eye level for portrait, top-down angle for food).
- **FR-005**: System MUST support a 9:16 aspect ratio check specifically for the Vlog template.

### Key Entities

- **SceneTemplate**: Represents a set of compositional rules (e.g., `PortraitTemplate`, `LandscapeTemplate`).
- **CompositionRule**: A specific heuristic to evaluate (e.g., `RuleOfThirds`, `HorizonLevel`, `HeadRoom`).
- **CoachingAction**: The recommended physical movement (e.g., `MoveLeft`, `TiltUp`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can align the camera with the AI's intended composition in under 3 seconds using the ghost box and arrows.
- **SC-002**: System successfully classifies the scene into the correct template (Portrait, Landscape, etc.) with >90% accuracy in typical environments.
- **SC-003**: The UI continues to maintain the >30 FPS performance standard while running the template detection logic.

## Assumptions

- We will start with a small set of templates (Portrait, Landscape, Vlog) before expanding to all niche templates (Pets, Food, etc.).
- OpenCV and existing ML models can accurately detect horizons, faces, and basic scene context locally without cloud latency.
