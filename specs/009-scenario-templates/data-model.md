# Data Model: AI Scenario Templates

## Core Entities

### 1. `AICoaching` (Updated)
We need to extend the existing `AICoaching` entity in `src/core/entities.py` to support ghost boxes and arrows.

```python
@dataclass
class AICoaching:
    # Existing fields
    advice_text: str
    interaction_type: str  # "POPUP", "PROACTIVE_VOICE"
    is_error: bool = False
    
    # New fields for Scenario Templates
    target_box: Optional[Tuple[int, int, int, int]] = None  # (x1, y1, x2, y2) for the ghost box
    directional_arrows: List[str] = None  # List of required movements: "LEFT", "RIGHT", "UP", "DOWN", "FORWARD", "BACKWARD"
    active_template: str = "Default"  # "Portrait", "Landscape", "Vlog", "Food", etc.
```

### 2. Scene Context (No Data Model changes needed)
The scene context logic already identifies `Portrait`, `Landscape`, etc., in `SceneContext`. We will use this to drive the `active_template` logic.
