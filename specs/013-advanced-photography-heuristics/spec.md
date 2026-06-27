# Feature Specification: Advanced Photography Heuristics

**Feature Branch**: `[013-advanced-photography-heuristics]`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "基于专业摄影师角度,继续深入优化照片AI辅助能力 - 全选 (光影方向、引导线、色彩对比、景深评估、直方图分析)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lighting Direction & Quality Analysis (Priority: P1)

As a user taking portraits, I want the AI to analyze the light falling on the subject's face and suggest how to turn to get more flattering, three-dimensional lighting (like side lighting or Rembrandt lighting).

**Why this priority**: Lighting is the soul of photography. Flat lighting or severe backlighting ruins portraits. Knowing *where* to turn the subject provides immediate, highly actionable value.

**Independent Test**: Can be fully tested by placing a subject near a window. Point the camera so they are in flat light (window behind camera), and the AI suggests turning them. Move to side-lighting and the AI stops warning or praises the lighting.

**Acceptance Scenarios**:

1. **Given** a portrait scene, **When** the subject's face has zero shadow gradient (flat lighting), **Then** the AI suggests "光线太平，尝试让人物侧向光源以增加立体感".
2. **Given** a portrait scene, **When** one side of the face is brightly lit and the other in deep shadow, **Then** the AI confirms "优秀的侧面立体光影".

---

### User Story 2 - Histogram & Dynamic Range Diagnosis (Priority: P1)

As a photographer, I want the AI to analyze the exposure histogram in real-time to warn me if I am crushing blacks or clipping highlights, so I can adjust exposure compensation (EV) before shooting.

**Why this priority**: Replaces the need for users to manually read a histogram graph, translating technical data into simple "EV+ / EV-" instructions.

**Independent Test**: Can be fully tested by pointing the camera at a very bright window (clipping) or a dark room (crushing blacks) and observing the EV suggestions.

**Acceptance Scenarios**:

1. **Given** a high-contrast scene, **When** the histogram shows >5% of pixels at pure white (255), **Then** the AI suggests "高光溢出，建议降低曝光 (EV-)".

---

### User Story 3 - Color Contrast & Subject Separation (Priority: P2)

As a photographer, I want the AI to check if my subject's clothing blends into the background color, so I can be prompted to find a contrasting background.

**Why this priority**: Helps users avoid "camouflage" photos where the subject is lost in the background.

**Independent Test**: Point camera at a person wearing green standing in front of green bushes. The AI should trigger a color separation warning.

**Acceptance Scenarios**:

1. **Given** a tracked primary subject, **When** the dominant hue of the subject's bounding box matches the dominant hue of the background mask, **Then** the AI suggests "主体与背景颜色接近，建议更换对比色背景".

---

### User Story 4 - Leading Lines & Geometry Detection (Priority: P2)

As a landscape/street photographer, I want the AI to detect strong architectural or natural lines and advise me to position the camera so these lines point toward my subject.

**Why this priority**: Leading lines are a classic composition technique that creates depth.

**Independent Test**: Stand on a path or road. If the vanishing point is far from the subject, the AI suggests moving to align the subject with the path.

**Acceptance Scenarios**:

1. **Given** strong straight lines detected via Hough Transform, **When** the lines do not intersect near the primary subject, **Then** the AI suggests "尝试利用背景线条指向主体".

---

### User Story 5 - Depth of Field (DoF) Heuristics (Priority: P2)

As a portrait photographer, I want the AI to warn me if the background is too sharp and cluttered, advising me to create more background blur.

**Why this priority**: Simulates optical depth-of-field awareness, encouraging users to physically move closer for natural bokeh or switch to portrait mode.

**Independent Test**: Point the camera at a subject 3 meters away with a busy background 4 meters away.

**Acceptance Scenarios**:

1. **Given** a cluttered background, **When** the subject occupies < 20% of the frame (user is far away), **Then** the AI suggests "靠近主体以虚化背景，或开启人像模式".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute a luminance histogram per frame and detect if the 0 (black) or 255 (white) bins exceed a 5% threshold.
- **FR-002**: System MUST analyze the left vs right side brightness of the primary subject's bounding box to detect directional lighting.
- **FR-003**: System MUST extract dominant colors (using K-Means or Hue histograms) for both the subject and the background mask to check for hue proximity.
- **FR-004**: System MUST apply Hough Line Transform to the background mask to find the primary vanishing point or dominant line angles.
- **FR-005**: System MUST evaluate the ratio of subject bounding box area to total frame area to trigger DoF advice when background clutter is high.

### Key Entities 

- **AestheticsMetrics**: Extended to include `histogram_clipping` (str: "highlights", "shadows", None), `lighting_direction` (str: "flat", "left", "right", "backlit"), `color_contrast_low` (bool), `vanishing_point_aligned` (bool).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 5 new analytical modules (Histogram, Light Direction, Color, Lines, DoF) combined MUST execute in under 15ms per frame to maintain 25+ FPS real-time performance.
- **SC-002**: The UI gracefully handles multiple concurrent advice triggers by prioritizing P1 feedback (Lighting, Exposure) over P2 feedback (Color, Lines) using the existing feedback selection logic.

## Assumptions

- We will rely on classical Computer Vision (OpenCV) for these heuristics to guarantee performance, avoiding heavy neural networks for line and lighting detection.
- Histogram analysis will use grayscale luminance.
