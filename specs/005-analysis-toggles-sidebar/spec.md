# Feature Specification: Analysis Toggles Sidebar

**Feature Branch**: `005-analysis-toggles-sidebar`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "增加一个可以动态开关各项分析功能（例如关闭 AI 教练或关闭骨骼检测）的侧边栏菜单"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Toggle Individual Analysis Modules (Priority: P1)

As a photographer using CameraQ, I want to dynamically toggle specific analysis modules (like AI Coach, Pose Detection, Saliency Detection) on or off from a sidebar, so that I can customize the viewfinder experience and reduce visual clutter or save CPU resources.

**Why this priority**: Core value of the feature. Without the ability to turn off heavy models or distracting visuals, the app can feel overwhelming.

**Independent Test**: Can be fully tested by opening the sidebar, toggling "AI Coach" off, and observing that AI coaching prompts stop appearing and the API stops being called.

**Acceptance Scenarios**:

1. **Given** the user is viewing the live camera feed, **When** they click/press to open the settings sidebar, **Then** a menu appears showing a list of toggleable modules.
2. **Given** the Pose Detection module is currently ON, **When** the user toggles it OFF, **Then** all skeleton/keypoint overlays immediately disappear from the screen and the YOLO pose model stops executing on subsequent frames.

---

### User Story 2 - Persist Settings (Priority: P2)

As a regular user, I want the system to remember my module toggle preferences between sessions, so I don't have to reconfigure the sidebar every time I launch the app.

**Why this priority**: Improves user experience significantly, but the app is still functional without it.

**Independent Test**: Can be fully tested by turning off a feature, closing the application, restarting it, and verifying the feature is still turned off.

**Acceptance Scenarios**:

1. **Given** the user has turned off the Saliency Detection module, **When** the application is restarted, **Then** the Saliency Detection module defaults to OFF on startup.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a UI sidebar or panel that overlays or sits beside the camera feed.
- **FR-002**: System MUST provide a mechanism (e.g., keyboard shortcut or UI button) to open/close the sidebar.
- **FR-003**: System MUST allow toggling the "AI Coach" module on and off.
- **FR-004**: System MUST allow toggling the "Pose Detection" (skeletons) module on and off.
- **FR-005**: System MUST allow toggling the "Saliency Detection" module on and off.
- **FR-006**: System MUST immediately reflect the toggle state in the realtime feed without requiring an application restart.
- **FR-007**: System MUST pause or skip the background thread execution / inference for disabled modules (e.g., stop calling Gemini API if AI Coach is disabled, saving network quota and compute).
- **FR-008**: System MUST persist the state of the toggles across application restarts.

### Key Entities

- **SettingsConfig**: A persistent data structure mapping feature names (e.g., `ai_coach_enabled`, `pose_detection_enabled`) to boolean values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can open the sidebar and toggle features within 2 clicks or key presses.
- **SC-002**: Disabling a feature immediately (within 1 frame) hides its visual overlays and prevents its processing logic from running.
- **SC-003**: CPU/GPU usage is measurably reduced when heavy modules (like YOLO Pose or Gemini) are toggled off.
- **SC-004**: Settings are persisted and restored accurately 100% of the time upon app restart.

## Assumptions

- We assume the existing UI framework (e.g., OpenCV's `imshow` or a lightweight GUI overlay on top of it) can support a basic sidebar or settings menu. (If OpenCV `imshow` is purely used, the sidebar might be implemented via a separate small OpenCV window, or an integrated drawn menu, or by migrating to a more robust GUI like PyQt/Tkinter. We assume a simple drawn UI or trackbars will suffice for the MVP).
- The toggle settings will be saved to a local JSON or INI file.
