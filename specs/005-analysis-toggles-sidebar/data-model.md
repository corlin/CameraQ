# Data Model: Analysis Toggles Sidebar

## Entities

### `SettingsManager`
Handles persistence and toggling of application settings.

**Fields**:
- `ai_coach_enabled`: bool (default: True)
- `pose_detection_enabled`: bool (default: True)
- `saliency_enabled`: bool (default: True)
- `config_path`: str (path to JSON file)

**Methods**:
- `load()` -> None: Loads from JSON.
- `save()` -> None: Saves to JSON.
- `toggle(setting_name: str)` -> None: Flips the boolean and saves.

### `SidebarUI` (Logical Entity within OverlayRenderer)
Represents the state of the interactive sidebar.

**Fields**:
- `is_open`: bool
- `bounds`: Tuple[int, int, int, int] (x1, y1, x2, y2)
- `toggle_buttons`: List[Dict] (metadata mapping setting names to clickable bounding boxes on screen)
