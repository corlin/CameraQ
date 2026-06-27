# Data Model: deep-ai-assist

## `SceneContext` (Data Class)

Represents the high-level understanding of the current scene provided by the cloud AI model.

- `scene_type` (str): E.g., "Portrait", "Landscape", "Action", "Macro", "Night".
- `lighting_condition` (str): E.g., "Backlit", "Low light", "Overexposed", "Even".
- `recommended_iso` (int): Suggested ISO (e.g., 100, 400, 1600).
- `recommended_shutter` (str): Suggested shutter speed (e.g., "1/200", "1/60").
- `proactive_advice` (str): A short, actionable sentence to speak to the user (e.g., "Try moving to the left to avoid the harsh backlight.").
- `confidence` (float): AI confidence score (0.0 to 1.0).
- `timestamp` (float): When this context was generated.

## `AIInteraction` (Data Class)

Represents a single proactive or reactive interaction with the user.

- `timestamp` (float): Time of interaction.
- `message` (str): The text content of the alert/advice.
- `type` (Enum): `PROACTIVE_VOICE`, `PROACTIVE_POPUP`, `REACTIVE_CHAT`.
- `acknowledged` (bool): Whether the user dismissed or responded to it.

## System State Extensions

The `AnalysisResult` (from `entities.py`) will be extended to include:
- `current_scene_context`: Optional[`SceneContext`] - the most recently fetched scene context.
- `active_interactions`: List[`AIInteraction`] - current alerts to display on the overlay.
