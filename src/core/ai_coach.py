import time
import os
import queue
import threading
import cv2
import numpy as np
import re
import logging
from PIL import Image
from typing import Optional
from google import genai

from .entities import AICoachingResult

logger = logging.getLogger(__name__)

class AICoach:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client()
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client: {e}")
                self.client = None
        
        self.frame_queue = queue.Queue(maxsize=1)
        self.latest_advice: Optional[AICoachingResult] = None
        self._stop_event = threading.Event()
        self.worker_thread: Optional[threading.Thread] = None
        self.consecutive_errors = 0

    def start(self):
        """Starts the background worker thread."""
        if not self._stop_event.is_set() and self.worker_thread is None and self.client:
            self._stop_event.clear()
            self.worker_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.worker_thread.start()

    def stop(self):
        """Stops the background worker thread."""
        self._stop_event.set()
        if self.worker_thread:
            # Wake up the queue if it's blocking
            try:
                self.frame_queue.put_nowait(None)
            except queue.Full:
                pass
            self.worker_thread.join(timeout=1.0)

    def enqueue_frame(self, frame: np.ndarray, force: bool = False):
        """
        Attempts to enqueue a frame for background processing.
        If the queue is full (i.e. the worker is busy), the frame is dropped
        to ensure we don't build up a backlog of outdated frames, unless 'force' is True,
        in which case we override the queue.
        """
        if self._stop_event.is_set() or not self.client:
            return

        if force:
            try:
                # empty the queue first
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass
            self.frame_queue.put(frame.copy())
        else:
            try:
                self.frame_queue.put_nowait(frame.copy())
            except queue.Full:
                # Worker is busy, just drop the frame
                pass

    def get_latest_advice(self) -> Optional[AICoachingResult]:
        """Returns the most recent coaching advice."""
        return self.latest_advice

    def _process_loop(self):
        """The background loop that pulls frames and calls Gemini API."""
        prompt = (
            "You are a professional photography coach. Look at this camera frame. "
            "Give a short (1-2 sentences), highly stylistic and emotional coaching tip. "
            "Focus on aesthetics, vibe, lighting, and posing. "
            "Output the advice directly in Chinese, without quotes or conversational filler."
        )

        while not self._stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if frame is None:
                continue

            # Resize image to save bandwidth and latency (max dimension 512)
            h, w = frame.shape[:2]
            max_dim = 512
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # Convert OpenCV BGR frame to PIL Image for Gemini
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)

            try:
                logger.info(f"Calling Gemini {self.model_name} with {pil_image.width}x{pil_image.height} image...")
                start_time = time.time()
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[prompt, pil_image]
                )
                elapsed = time.time() - start_time
                
                advice_text = response.text.strip()
                logger.info(f"Received response in {elapsed:.2f}s: {advice_text}")
                self.latest_advice = AICoachingResult(
                    advice_text=advice_text,
                    timestamp=time.time(),
                    is_error=False
                )
                self.consecutive_errors = 0  # Reset on success
            except Exception as e:
                err_str = str(e)
                
                # Check if API explicitly provided a retry delay (e.g. for 429 RESOURCE_EXHAUSTED)
                match = re.search(r"Please retry in ([\d\.]+)s", err_str)
                if match:
                    backoff_time = float(match.group(1)) + 1.0  # Add 1s buffer
                    logger.error(f"AI Coaching Error: 429 RESOURCE_EXHAUSTED")
                    logger.warning(f"Rate limited. API requested exact wait. Backing off for {backoff_time:.2f} seconds before retrying...")
                    error_msg = "💡 AI 教练喝口水，稍后继续..."
                else:
                    self.consecutive_errors += 1
                    backoff_time = min(60.0, (2 ** self.consecutive_errors))
                    logger.error(f"AI Coaching Error: {e}")
                    logger.warning(f"API is busy/unavailable. Backing off for {backoff_time} seconds before retrying...")
                    error_msg = "🔌 网络信号弱，教练暂时掉线"
                
                self.latest_advice = AICoachingResult(
                    advice_text=error_msg,
                    timestamp=time.time(),
                    is_error=True
                )
                time.sleep(backoff_time)
            finally:
                self.frame_queue.task_done()
