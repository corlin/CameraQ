# Tasks: Shutter Feedback & UX Levels

**Branch**: `[011-shutter-and-ux-levels]` | **Date**: 2026-06-27 | **Plan**: [plan.md](file:///Users/corlin/2026/CameraQ/specs/011-shutter-and-ux-levels/plan.md)

- [x] 1. Define `CoachingLevel` enum in `src/core/entities.py`.
- [x] 2. Add `coaching_level` string setting to `src/core/settings.py` and modify `toggle` or add a specific cycle method to support string cycling.
- [x] 3. Refine `AestheticsAnalyzer` in `src/core/analyzers/aesthetics_analyzer.py` to ensure lighting limits trigger overexposure feedback more frequently during testing.
- [x] 4. Inject parameter feedback logic and shutter opportunity checks inside `process_frame` in `src/core/analyzer.py`.
- [x] 5. Implement UI masking logic inside `OverlayRenderer.draw` in `src/ui/overlay.py` to respect the active `CoachingLevel`.
- [x] 6. Add 'C' keybinding in `CameraApp.run` to cycle the `CoachingLevel`.
- [x] 7. Update `walkthrough.md` with the new changes and screenshots.
