import cv2
import threading
import time
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class CameraStreamManager:
    def __init__(self, source=0):
        self.source = source
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self._lock = threading.Lock()
        self._thread = None
        self.fps = 0.0

    def start(self):
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            logger.warning(f"Warning: Could not open camera source {self.source}")
            return False
            
        self.is_running = True
        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()
        return True

    def _update(self):
        frame_count = 0
        start_time = time.time()
        
        while self.is_running:
            if not self.cap:
                break
                
            try:
                ret, frame = self.cap.read()
            except Exception as e:
                logger.warning(f"Camera read error/disconnect: {e}")
                self.is_running = False
                break
                
            if ret:
                with self._lock:
                    self.current_frame = frame
                
                frame_count += 1
                elapsed = time.time() - start_time
                if elapsed >= 1.0:
                    self.fps = frame_count / elapsed
                    frame_count = 0
                    start_time = time.time()
            else:
                time.sleep(0.01) # Sleep briefly if no frame

    def read(self) -> Optional[Any]:
        with self._lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def stop(self):
        self.is_running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            
        if self.cap is not None:
            self.cap.release()
            self.cap = None
