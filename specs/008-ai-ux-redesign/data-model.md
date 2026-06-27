# Phase 1: Data Model

## State Tracking (in `OverlayRenderer`)
To support the new UI interactions (timeout/collapse), the following state variables need to be tracked in `OverlayRenderer`:

- `self.ai_coach_last_update`: Timestamp of when the last AI coaching message arrived.
- `self.ai_coach_message`: The current message string.
- `COACH_DISPLAY_DURATION`: Constant (e.g., 5.0 seconds). If `time.time() - self.ai_coach_last_update < COACH_DISPLAY_DURATION`, display the full expanded text. Otherwise, display the collapsed icon badge.

## Scene Context Mapping
We will need a mapping function or dictionary to convert textual scene contexts from the LLM into professional UI icons + short text.

```python
SCENE_ICONS = {
    "Outdoor": "⛰️ Outdoor",
    "Indoor": "🏠 Indoor",
    "Portrait": "👤 Portrait",
    "Landscape": "🌄 Landscape",
    "Night": "🌙 Night",
    # Lighting
    "Bright": "☀️ Bright",
    "Dark": "🌑 Dark",
    "Backlit": "✨ Backlit"
}
```
