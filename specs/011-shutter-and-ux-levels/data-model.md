# Data Model: Shutter Feedback & UX Levels

## Core Entities

### 1. `CoachingLevel` (New)
A new Enum in `src/core/entities.py` (or just string constants in `SettingsManager`) representing the UI density state.

```python
class CoachingLevel(str, Enum):
    OFF = "OFF"
    MINIMAL = "MINIMAL"
    COACH = "COACH"
    PRO = "PRO"
```

### 2. `SettingsManager` (Updated)
Add `coaching_level` to the managed settings.

```python
class SettingsManager:
    _DEFAULTS = {
        # ...
        "coaching_level": "COACH", # Default to coach
        # ...
    }
```

### 3. `AestheticsMetrics` (Updated)
Extend for severe lighting flags.
```python
class AestheticsMetrics(BaseModel):
    # ... existing ...
    is_severe_backlight: bool = False
```
