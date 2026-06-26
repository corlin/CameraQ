# Data Model: Professional Performance & UX Deep Optimization

## Modified Entities

### `CompositionScore` (existing, now fully implemented)
Multi-dimensional score replacing the plain `int` in `AnalysisResult`.

**Fields** (all `int`, range 0–100):
- `total_score`: Weighted aggregate, clamped 0–100
- `subject_score`: Subject placement quality (thirds alignment bonus, edge penalty)
- `structure_score`: Structural alignment (horizon level bonus, tilt penalty)
- `balance_score`: Visual weight distribution across quadrants
- `interference_score`: Penalty from background interference
- `style_score`: Aesthetics (lighting quality, color harmony)

### `SettingsManager` (enhanced)
Extended with numeric parameters and thread safety.

**New Fields**:
- `object_detection_enabled`: bool (default: True)
- `ai_sampling_interval`: float (default: 5.0, range: 2.0–30.0)
- `overlay_opacity`: float (default: 0.7, range: 0.1–1.0)
- `analysis_throttle_n`: int (default: 5, range: 1–15) — run expensive analysis every N frames
- `_lock`: threading.Lock (internal, not persisted)

**Modified Methods**:
- `toggle(key)` and all getters/setters now acquire `_lock`
- `save()` excludes `_lock` from serialization

### `AnalysisResult` (modified)
- `score`: type changes from `int` to `CompositionScore`

## Removed Entities
- `CameraStream`: defined but never used anywhere
- `StructuralAnalysis`: defined but never used anywhere

## Removed Files
- `src/core/utils/drawing.py`: Dead code since PIL migration in Stage 5
