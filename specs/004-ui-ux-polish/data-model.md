# Data Model: UI/UX Aesthetics Polish

## Entities

### UIOverlayTheme
Defines the stylistic properties for drawing.
- **Fields**:
  - `primary_color`: `tuple` (RGB, e.g., `(255, 255, 255)`)
  - `accent_color`: `tuple` (RGB, e.g., `(255, 215, 0)`)
  - `bg_alpha`: `float` (Opacity for text backgrounds, e.g., `0.5`)
  - `line_thickness`: `int` (Default thickness for grid/vectors)
  - `font_path`: `str` (Path to TTF font)

### PromptMetadata (Already partially implemented as `AICoachingResult` and `AnalysisResult`)
Tracks state and lifecycle of transient text prompts.
- **Fields**:
  - `text`: `str`
  - `timestamp`: `float` (Time created)
  - `duration`: `float` (Lifespan in seconds, e.g., `10.0`)
  - `is_active()` -> `bool`: Returns `True` if `current_time < timestamp + duration`.
