import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Resolve config path relative to project root (3 levels up from this file)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config.json"


class SettingsManager:
    """Manages application settings and persists them to a local JSON config file.
    Thread-safe: all reads/writes are protected by a lock."""
    
    # Registry of all settings with their defaults and types
    _DEFAULTS = {
        # Detection module toggles
        "ai_coach_enabled": True,
        "pose_detection_enabled": True,
        "saliency_enabled": True,
        "object_detection_enabled": True,
        # Performance parameters
        "ai_sampling_interval": 5.0,     # seconds between AI Coach calls
        "analysis_throttle_n": 5,         # run expensive analysis every N frames
        # Display options
        "overlay_opacity": 0.7,           # 0.0–1.0
    }

    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
        self._lock = threading.Lock()
        
        # Initialize all settings with defaults
        for key, default_val in self._DEFAULTS.items():
            setattr(self, key, default_val)
        
        # Load from disk if available
        self.load()

    def load(self) -> None:
        """Load settings from the JSON config file."""
        with self._lock:
            if self.config_path.exists():
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    for key, default_val in self._DEFAULTS.items():
                        if key in data:
                            val = data[key]
                            # Type validation
                            if isinstance(default_val, bool) and isinstance(val, bool):
                                setattr(self, key, val)
                            elif isinstance(default_val, float) and isinstance(val, (int, float)):
                                setattr(self, key, float(val))
                            elif isinstance(default_val, int) and isinstance(val, int):
                                setattr(self, key, val)
                            else:
                                logger.warning(f"Invalid type for setting '{key}' in config, using default")
                    
                    logger.info(f"Loaded configuration from {self.config_path}")
                except Exception as e:
                    logger.warning(f"Failed to load configuration: {e}. Using defaults.")

    def save(self) -> None:
        """Save current settings to the JSON config file."""
        with self._lock:
            data = {}
            for key in self._DEFAULTS:
                data[key] = getattr(self, key)
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                logger.debug(f"Saved configuration to {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")

    def toggle(self, setting_name: str) -> None:
        """Toggle a boolean setting by its name and save."""
        with self._lock:
            if setting_name not in self._DEFAULTS:
                logger.warning(f"Unknown setting: {setting_name}")
                return
            current_val = getattr(self, setting_name)
            if isinstance(current_val, bool):
                setattr(self, setting_name, not current_val)
            else:
                logger.warning(f"Cannot toggle non-boolean setting: {setting_name}")
                return
        self.save()  # save() acquires its own lock

    def adjust(self, setting_name: str, delta: float) -> None:
        """Adjust a numeric setting by a delta value and save."""
        with self._lock:
            if setting_name not in self._DEFAULTS:
                logger.warning(f"Unknown setting: {setting_name}")
                return
            current_val = getattr(self, setting_name)
            if isinstance(current_val, bool):
                logger.warning(f"Cannot adjust boolean setting: {setting_name}")
                return
            new_val = current_val + delta
            # Clamp based on known ranges
            if setting_name == "overlay_opacity":
                new_val = max(0.1, min(1.0, new_val))
            elif setting_name == "ai_sampling_interval":
                new_val = max(2.0, min(30.0, new_val))
            elif setting_name == "analysis_throttle_n":
                new_val = max(1, min(15, int(new_val)))
            setattr(self, setting_name, new_val)
        self.save()

    def get(self, setting_name: str):
        """Thread-safe getter."""
        with self._lock:
            return getattr(self, setting_name, None)
