# Feature Specification: AI UX Redesign

**Feature Branch**: `[008-ai-ux-redesign]`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "AI相关辅助性的设计,需要参考其他专业软件完成. 目前ux体验太差"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Non-intrusive AI Assistance (Priority: P1)

As a photographer, I want AI suggestions to be visually integrated and non-intrusive (similar to professional camera apps like Halide or DJI Go), so that I can focus on composing my shot without being distracted by large text blocks.

**Why this priority**: The core complaint is poor UX. Text blocking the viewfinder ruins the camera experience. Moving to a professional, non-intrusive design is the highest priority.

**Independent Test**: Can be fully tested by launching the camera and verifying that AI suggestions appear as subtle UI elements (e.g., pill badges, toast notifications) rather than large text overlays.

**Acceptance Scenarios**:

1. **Given** the camera is active and AI generates a suggestion, **When** the suggestion is displayed, **Then** it appears in a subtle, non-blocking UI component (e.g., bottom edge or top corner).
2. **Given** a long AI suggestion is generated, **When** it is displayed, **Then** it does not cover the central composition area of the viewfinder.

---

### User Story 2 - Professional Visual Language (Priority: P2)

As a user, I want the AI scene context, scoring, and bounding boxes to use standard professional camera iconography and minimalistic layout (e.g., thin lines, semi-transparent dark backgrounds, clear typography), so the interface feels premium and familiar.

**Why this priority**: Aesthetics play a massive role in perceived UX quality. Adopting professional visual paradigms will directly address the "poor UX" complaint.

**Independent Test**: Can be fully tested by comparing the new UI elements (fonts, colors, line weights, icons) against a standard professional reference (e.g., Apple Camera app).

**Acceptance Scenarios**:

1. **Given** the AI detects a subject, **When** the bounding box is drawn, **Then** it uses thin, professional-looking reticles or corners instead of thick, bright green boxes.
2. **Given** the AI displays scene context (e.g., lighting, ISO), **When** rendered, **Then** it uses clean iconography and minimalistic typography rather than emoji-heavy or cluttered text.

---

### Edge Cases

- What happens when multiple AI suggestions (e.g., lighting warning + composition advice) are generated simultaneously? (Do they queue, stack, or does one override?)
- How does the UI adapt if the user resizes the window to a very small dimension where even minimal UI might overlap?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display AI feedback and coaching using minimalistic, non-blocking UI components (e.g., toast notifications, pill-shaped badges, or collapsible panels).
- **FR-002**: System MUST ensure that the central 50% of the viewfinder area remains completely unobstructed by any text or opaque UI overlays.
- **FR-003**: System MUST update bounding box rendering to use professional camera styles (e.g., corner brackets, thin lines, or focus reticles) instead of default OpenCV-style thick boxes.
- **FR-004**: System MUST use a professional color palette and typography (e.g., monochrome with subtle accent colors for specific alerts) for all AI-generated overlays.
- **FR-005**: System MUST truncate long AI advice (providing a "tap to expand" or visual indicator of more text) and MUST automatically hide/dismiss the advice after a defined timeout if not interacted with.
- **FR-006**: System MUST replace verbose text-heavy scene context with an "Icon + Short Text" layout (e.g., [Sun Icon] Bright, [Mountain Icon] Outdoor).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The AI overlay (text, badges, panels) occupies no more than 15% of the total screen area during normal operation.
- **SC-002**: The central 50% of the screen remains 100% free of text overlays at all times.
- **SC-003**: Qualitative user testing feedback indicates the UI feels "professional" and "non-intrusive."

## Assumptions

- Users prefer a minimalist UI akin to iOS Camera, Halide, or professional DSLR displays over verbose text output.
- The underlying AI analysis logic (latency, accuracy, rate limiting) remains unchanged; this feature is strictly a UI/UX presentation layer redesign.
- Users are familiar with standard camera iconography (e.g., a sun icon for exposure/lighting).
