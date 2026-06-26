# Data Model: Advanced Aesthetics & Dynamic Tracking

## Entities

### `AestheticsMetrics`
Represents the lighting and color analysis of a frame.
- `brightness_level`: Float (0-255 average luminance).
- `is_overexposed`: Boolean.
- `is_underexposed`: Boolean.
- `color_harmony_score`: Float (0-1.0).
- `lighting_feedback`: String (e.g., "Too bright, adjust angle").

### `TrackedSubject` (Extends `DetectedSubject`)
Represents an object over time.
- `track_id`: Integer (unique ID assigned by tracker).
- `history`: List of `BoundingBox` (last N frames).
- `velocity_x`: Float (pixels per frame).
- `velocity_y`: Float (pixels per frame).
- `will_intersect_composition_node`: Boolean.
- `time_to_intersection`: Float (seconds).

### `AnalysisResult` (Updated)
- `aesthetics`: `AestheticsMetrics`.
- `tracked_subjects`: List of `TrackedSubject`.
- `shutter_opportunity`: Boolean (True if a tracked subject is entering an optimal position).
