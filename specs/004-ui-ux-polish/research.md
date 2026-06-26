# Research: UI/UX Aesthetics Polish

## Decisions

### Rendering Engine
- **Decision**: Use a hybrid of OpenCV and PIL (Pillow) for rendering.
- **Rationale**: OpenCV is fast for basic geometric lines (grid, tracking vectors), but lacks native support for antialiased rounded rectangles, drop shadows, and complex alpha blending on text backgrounds. PIL will be used for text rendering with semi-transparent background plates, while OpenCV can still draw basic lines with alpha blending using `cv2.addWeighted()` or directly drawing on an overlay layer.
- **Alternatives considered**: Entirely moving to Pygame or another GUI toolkit. Rejected because CameraQ is an OpenCV `imshow` app and rewriting the rendering pipeline is out of scope.

### UI Element Fading and Duration
- **Decision**: Use timestamps to track when transient UI elements were created, and compute their alpha/opacity dynamically based on elapsed time.
- **Rationale**: Tracking `(start_time, duration)` allows us to cleanly calculate exactly what opacity a text prompt should have (e.g., fading out in the last 1 second of its life).
- **Alternatives considered**: Frame counting. Rejected because frame rate can fluctuate (especially when AI inference occurs), making time-based tracking more accurate.
