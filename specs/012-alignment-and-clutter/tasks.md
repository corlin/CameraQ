# Tasks: Alignment and Clutter

**Branch**: `[012-alignment-and-clutter]` | **Date**: 2026-06-27 | **Plan**: [plan.md](file:///Users/corlin/2026/CameraQ/specs/012-alignment-and-clutter/plan.md)

- [x] 1. Update `src/core/entities.py` to add `background_clutter_score`, `is_background_cluttered` to `AestheticsMetrics`, and `perfect_alignment` to `AICoachingResult`.
- [x] 2. Update `src/core/analyzers/aesthetics_analyzer.py` to accept `primary_box` and compute Canny edge density on the background mask.
- [x] 3. Update `src/core/analyzer.py` to pass the `primary_box` to `aesthetics_analyzer.analyze()` and calculate IoU between `primary_box` and `ai_coaching.target_box`.
- [x] 4. Update `src/ui/overlay.py` to render the `perfect_alignment` glowing gold state.
- [x] 5. Update `src/ui/camera_app.py` to track the `perfect_alignment` state and log `[HAPTIC VIBRATION]` on edge triggers.
- [x] 6. Test with `uv run python -m py_compile` and manually verify.
