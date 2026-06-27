import pytest
from src.core.entities import AICoachingResult
from src.core.io.voice import VoiceSynthesizer
from unittest.mock import patch, MagicMock
import time

def test_interaction_type_assignment():
    ai = AICoachingResult(
        advice_text="Test advice",
        timestamp=time.time(),
        interaction_type="PROACTIVE_VOICE"
    )
    assert ai.interaction_type == "PROACTIVE_VOICE"

@patch('src.core.io.voice.subprocess.Popen')
def test_voice_synthesizer_non_blocking(mock_popen):
    mock_process = MagicMock()
    # Make wait block briefly so we can test is_speaking
    def mock_wait():
        time.sleep(0.2)
    mock_process.wait.side_effect = mock_wait
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    
    synth = VoiceSynthesizer()
    synth.speak("Hello world")
    
    # Wait briefly for thread to start
    time.sleep(0.05)
    
    assert mock_popen.called
    assert synth.is_speaking
    
    synth.stop()
    assert not synth.is_speaking
    assert mock_process.terminate.called
