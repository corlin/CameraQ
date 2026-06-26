# Feature Specification: Generative AI Guide (Stage 4)

**Feature Branch**: `003-generative-ai-guide`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "Gemini multimodal integration for contextual, stylistic photography coaching using Fast/Slow Brain asynchronous architecture."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Contextual Coaching (Priority: P1)

Users receive high-level, artistic photography suggestions (e.g., lighting, emotional tone, posing, composition style) based on the current scene, without experiencing any UI lag or framerate drops in the viewfinder.

**Why this priority**: Core value proposition of Stage 4. It introduces genuine LLM understanding of the scene while validating the "Fast/Slow Brain" asynchronous architecture.

**Independent Test**: Can be fully tested by pointing the camera at a scene and waiting for an AI suggestion bubble to appear after a few seconds, while verifying that the live camera feed remains smooth at 30 FPS.

**Acceptance Scenarios**:

1. **Given** the app is running in continuous tracking mode, **When** 5 seconds elapse (or the camera stabilizes), **Then** a frame is sent to the AI Coach, and its stylistic advice appears in a UI bubble.
2. **Given** the background AI analysis is running, **When** the user pans the camera quickly, **Then** the UI continues rendering smoothly without blocking.

---

### User Story 2 - On-Demand Inspiration (Priority: P2)

Users who are actively setting up a specific shot can manually request the AI to provide inspiration or critique on the current frame.

**Why this priority**: Gives users control over analysis calls (saving usage/costs) and allows them to ask for help precisely when they need it.

**Independent Test**: Can be tested by pressing a "Coach Me" key/button. A specific, contextual response should appear shortly after.

**Acceptance Scenarios**:

1. **Given** the camera feed is live, **When** the user presses the manual trigger key, **Then** the current frame is captured and sent to the AI Coach, returning a dedicated critique.

### Edge Cases

- What happens when network connectivity is lost? The system should fall back to basic real-time composition tracking without crashing, optionally showing an "Offline" badge.
- How does system handle rate limits or API timeouts? It should fail gracefully, dismissing the coaching bubble or displaying a subtle "AI busy" indicator.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST process AI Coach network calls concurrently to prevent blocking the main camera loop.
- **FR-002**: System MUST extract frames for the AI analysis without disrupting the primary viewfinder feed.
- **FR-003**: System MUST provide the AI Coach with instructions to focus on high-level aesthetics (emotion, lighting vibe, posing, framing).
- **FR-004**: System MUST render the text advice in the viewfinder UI as a non-intrusive floating element.
- **FR-005**: System MUST include a throttling mechanism to prevent overwhelming the AI service (e.g., minimum 5 seconds between automated calls).

### Key Entities 

- **AICoachingResult**: Represents the parsed response from the AI, including the generated text advice and the timestamp of the frame it analyzed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The main camera viewfinder MUST maintain a smooth, uninterrupted framerate even while an AI network request is in flight.
- **SC-002**: The AI coaching response MUST appear within 4 seconds of the frame being sampled.
- **SC-003**: The system MUST successfully handle network timeouts or service failures without crashing the application.

## Assumptions

- The user has a valid AI service API key configured in their environment.
- Network connectivity is available; if offline, the application will simply skip the advanced AI coaching and fall back to the basic offline pipeline.
