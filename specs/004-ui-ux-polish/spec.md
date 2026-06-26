# Feature Specification: UI/UX Aesthetics Polish

**Feature Branch**: `004-ui-ux-polish`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "从uxui,设计美学角度 ,考虑各种提示框线的显示样式和停留时长."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Aesthetically Pleasing UI Overlays (Priority: P1)

Users should see a clean, modern, and aesthetically pleasing interface when using the camera viewfinder. The bounding boxes, tracking vectors, grid lines, and text prompts should feel integrated, using proper typography, colors, and transparencies, rather than harsh primary colors and clunky shapes.

**Why this priority**: The app is a photography assistant; its own UI should reflect good design and aesthetics so it doesn't ruin the framing experience. Visual auxiliary lines must be sleek and non-intrusive.

**Independent Test**: Run the camera app. The UI elements (grid, bounding boxes, tracking vectors) should look visually refined (e.g., using proper alpha blending, smooth styling, harmonious colors).

**Acceptance Scenarios**:

1. **Given** the camera is active, **When** subjects are detected, **Then** the bounding boxes and text labels should use a sleek color palette (e.g., semi-transparent borders, sleek corners if possible) rather than harsh, thick, neon shapes.
2. **Given** the rule of thirds grid and tracking vectors are on, **When** they are drawn on the screen, **Then** the lines should be subtle, elegantly styled, and seamlessly integrated without overwhelming the subject.

---

### User Story 2 - Dynamic Prompt Durations and Fading (Priority: P2)

Users should not be overwhelmed by persistent text. Alerts (like "Overexposed" or "Perfect Shutter Opportunity") and AI Coaching tips should have a well-defined lifespan, fading in or out, or simply disappearing after a reasonable reading duration.

**Why this priority**: Stale or persistent text clutters the viewfinder and confuses the user if the scene has already changed.

**Independent Test**: Trigger an AI coaching tip or a lighting warning. Wait for the designated duration, and verify the text cleanly disappears without jarring artifacts.

**Acceptance Scenarios**:

1. **Given** a new AI Coaching tip arrives, **When** 10 seconds elapse, **Then** the tip should disappear from the screen.
2. **Given** an Aesthetics Warning (e.g., Overexposed) appears, **When** the lighting corrects itself, **Then** the warning should immediately disappear.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST apply a harmonious color palette and thickness to all drawing primitives (lines, rectangles, circles, tracking vectors).
- **FR-002**: System MUST render visual auxiliary lines (like the rule of thirds grid or motion tracking arrows) with elegant design aesthetics, utilizing proper opacity and line weighting to remain non-intrusive.
- **FR-003**: System MUST enforce a maximum duration for transient messages: AI Coaching (e.g. 10 seconds), Shutter Opportunity (while condition holds).
- **FR-004**: System MUST ensure that text labels associated with boxes or vectors fade or disappear logically when they are no longer relevant, preventing visual noise.

### Key Entities

- **UIOverlayTheme**: Defines colors, fonts, thicknesses, and alphas for rendering.
- **PromptMetadata**: Tracks the spawn time and duration of active text prompts for expiration logic.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All text elements remain readable (contrast ratio > 3:1) regardless of the camera feed's brightness (achieved via background plates).
- **SC-002**: Transient text prompts disappear exactly after their assigned duration to prevent screen clutter.
- **SC-003**: The UI layout strictly reserves non-overlapping zones for different types of feedback (e.g., Top Center for AI Coach, Center for Shutter Opportunity, Bottom Left for Scores).

## Assumptions

- Users have a standard display resolution (at least 720p) so UI elements have enough space.
- OpenCV/PIL will be used for rendering; advanced CSS-like styling (blur, complex drop shadows) may be limited by PIL's performance constraints, so we will use simple alpha compositing and geometric backgrounds.
