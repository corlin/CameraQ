# Research Findings: Advanced Photography Heuristics

**Date**: 2026-06-27
**Feature**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/013-advanced-photography-heuristics/spec.md)

## Algorithm Choices

### 1. Lighting Direction Detection
- **Decision**: Split the primary subject's bounding box into left and right halves. Convert to grayscale. Calculate the mean intensity of both halves. If `abs(left_mean - right_mean) > threshold`, classify as "left" or "right" side lighting. If both are low, "backlit". If difference is small and mean is high, "flat".
- **Rationale**: Computationally extremely cheap (just array slicing and mean). Perfectly adequate for real-time mobile heuristic feedback.
- **Alternatives considered**: Neural network facial landmark detection with 3D lighting estimation (too slow, violates 15ms budget).

### 2. Histogram Analysis
- **Decision**: Compute a 256-bin grayscale histogram of the full frame using `cv2.calcHist`. Check the percentage of pixels in the 0 bin (crushed blacks) and 255 bin (clipped highlights).
- **Rationale**: Highly optimized C++ function in OpenCV, runs in < 1ms.
- **Alternatives considered**: None, this is the standard way to analyze exposure.

### 3. Color Contrast & Separation
- **Decision**: Convert subject ROI and background mask to HSV. Compute the mean Hue of the subject and the mean Hue of the background. If the difference is small (e.g., < 20 degrees on the Hue wheel) and saturation is high enough to be relevant, flag as low contrast.
- **Rationale**: Mean Hue is faster than K-Means clustering and robust enough for a quick "camouflage" warning.

### 4. Leading Lines & Geometry
- **Decision**: Apply Canny edge detection to the background, followed by `cv2.HoughLinesP`. Filter for long, strong lines. Calculate their intersection point (vanishing point). Check if this point falls near the subject's bounding box.
- **Rationale**: Standard CV technique for line detection. Can be downsampled heavily before processing to save time.

### 5. Depth of Field Heuristics
- **Decision**: Use the existing Canny edge density background clutter score. If the score is high (busy background) AND the subject bounding box is small (e.g., < 15% of frame area, implying distance), recommend moving closer.
- **Rationale**: Reuses the background clutter computation from Stage 12, adding a simple bounding box area heuristic. Zero extra computation cost.
