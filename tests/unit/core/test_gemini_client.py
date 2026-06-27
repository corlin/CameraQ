import pytest
from unittest.mock import MagicMock, patch
import json
from src.core.gemini_client import GeminiClient
from src.core.settings import SettingsManager
from src.core.entities import SceneContext

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=SettingsManager)
    settings.gemini_api_key = "fake_key"
    return settings

@patch("src.core.gemini_client.genai.Client")
def test_analyze_scene_success(mock_client_class, mock_settings):
    # Setup mock response
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "scene_type": "Portrait",
        "lighting_condition": "Backlit",
        "recommended_iso": 400,
        "recommended_shutter": "1/200",
        "proactive_advice": "Turn around"
    })
    mock_client.models.generate_content.return_value = mock_response
    
    client = GeminiClient(mock_settings)
    result = client.analyze_scene(b"fake_image_bytes")
    
    assert isinstance(result, SceneContext)
    assert result.scene_type == "Portrait"
    assert result.lighting_condition == "Backlit"
    assert result.recommended_iso == 400
    assert result.recommended_shutter == "1/200"
    assert result.proactive_advice == "Turn around"

@patch("src.core.gemini_client.genai.Client")
def test_analyze_scene_json_error(mock_client_class, mock_settings):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "invalid json"
    mock_client.models.generate_content.return_value = mock_response
    
    client = GeminiClient(mock_settings)
    result = client.analyze_scene(b"fake_image_bytes")
    
    assert result is None
