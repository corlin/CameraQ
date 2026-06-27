import subprocess
import threading
import logging

logger = logging.getLogger(__name__)

class VoiceSynthesizer:
    def __init__(self):
        self._lock = threading.Lock()
        self._current_process = None
        self.is_speaking = False

    def speak(self, text: str):
        """Non-blocking text-to-speech using macOS 'say' command."""
        # Stop current speech if playing
        self.stop()
        
        def worker():
            with self._lock:
                self.is_speaking = True
                
            try:
                # Use 'say' command on macOS
                self._current_process = subprocess.Popen(['say', text])
                self._current_process.wait()
            except Exception as e:
                logger.error(f"TTS error: {e}")
            finally:
                with self._lock:
                    self.is_speaking = False
                    self._current_process = None

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def stop(self):
        with self._lock:
            if self._current_process and self._current_process.poll() is None:
                self._current_process.terminate()
                self._current_process = None
            self.is_speaking = False
