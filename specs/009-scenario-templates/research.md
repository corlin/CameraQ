# Phase 0: Outline & Research

## Technical Decisions

**Decision 1: Ghost Composition Box Rendering**
- **Decision**: Use PIL `ImageDraw.rectangle` with a semi-transparent `fill` color (e.g., `(255, 255, 255, 50)`) and a dashed or thin solid border to represent the "ghost" target box.
- **Rationale**: PIL is already used in `OverlayRenderer` for alpha compositing. Rendering a semi-transparent box is highly efficient and aligns perfectly with the current architecture.
- **Alternatives**: OpenCV `cv2.rectangle` with `cv2.addWeighted`, but since we already maintain a PIL `ui_overlay` layer, doing it in PIL is cleaner and avoids an extra OpenCV layer blend.

**Decision 2: Directional Arrows Rendering**
- **Decision**: Render arrows using Unicode text (e.g., `←`, `↑`, `→`, `↓`) combined with a background pill/plate, anchored to the edges of the screen.
- **Rationale**: Easy to implement using the existing `ImageFont` system, highly visible, and very low performance overhead compared to rendering custom polygon vectors or loading image assets.
- **Alternatives**: Using `assets/icons/` PNG files or drawing manual polygons with `ImageDraw.polygon`. Unicode text is chosen for the MVP as it's the fastest path to value and looks clean.

**Decision 3: Scene Template Logic Location**
- **Decision**: The template logic (detecting Portrait vs Landscape and emitting the target Ghost Box + Arrows) will be added to the AI Coaching module, which will output a `CoachingAction` containing the `target_box` and `directional_arrows`.
- **Rationale**: The UI layer should remain "dumb". The `OverlayRenderer` should just draw what the `AnalysisResult` tells it to draw.
- **Alternatives**: Putting the rule engine inside the UI renderer (rejected because UI should not contain business/analysis logic).
