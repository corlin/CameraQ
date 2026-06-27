# Data Model: Advanced Photography Heuristics

**Feature**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/013-advanced-photography-heuristics/spec.md)

## Modified Entities

### `AestheticsMetrics` (in `src/core/entities.py`)

New fields to support advanced heuristics:

```python
    histogram_clipping: Optional[str] = None # "highlights", "shadows", or None
    lighting_direction: Optional[str] = None # "flat", "left", "right", "backlit", or None
    color_contrast_low: bool = False
    vanishing_point_aligned: bool = False
```

## Data Flow

1. **Camera Frame** -> `Analyzer` -> `AestheticsAnalyzer`
2. **AestheticsAnalyzer**:
   - Computes histogram on full grayscale frame (`histogram_clipping`).
   - If `primary_box` exists, crops box, computes mean intensities for left/right halves (`lighting_direction`).
   - If `primary_box` exists, computes mean Hue of box and background mask (`color_contrast_low`).
   - Runs HoughLinesP on Canny edges, finds intersections (`vanishing_point_aligned`).
3. **Analyzer** passes metrics to `SceneRule`.
4. **SceneRule** generates UI feedback based on the new metrics, prioritizing Exposure and Lighting over Color and Lines.
