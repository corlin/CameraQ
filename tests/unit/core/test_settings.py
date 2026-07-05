import json

from src.core.settings import SettingsManager


def test_composition_settings_have_private_safe_defaults(tmp_path):
    settings = SettingsManager(config_path=tmp_path / "config.json")
    assert settings.composition_detection_enabled is True
    assert settings.composition_analysis_interval_s == 0.15
    assert settings.composition_diagnostics_enabled is False


def test_composition_toggles_and_interval_persist(tmp_path):
    path = tmp_path / "config.json"
    settings = SettingsManager(config_path=path)
    settings.toggle("composition_diagnostics_enabled")
    settings.adjust("composition_analysis_interval_s", -1.0)

    saved = json.loads(path.read_text())
    assert saved["composition_diagnostics_enabled"] is True
    assert saved["composition_analysis_interval_s"] == 0.05

    reloaded = SettingsManager(config_path=path)
    assert reloaded.composition_diagnostics_enabled is True
    assert reloaded.composition_analysis_interval_s == 0.05
