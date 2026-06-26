import cv2
import time
import threading
import sys
import logging
from pathlib import Path

# Add project root to path so we can run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.core.io.camera import CameraStreamManager
from src.core.analyzer import CameraQAnalyzer
from src.ui.overlay import OverlayRenderer
from src.core.settings import SettingsManager

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting CameraQ Real-time Viewfinder...")
    stream = CameraStreamManager(source=0)
    
    if not stream.start():
        logger.warning("Failed to start camera stream.")
        return

    settings = SettingsManager()
    analyzer = CameraQAnalyzer(settings=settings)
    renderer = OverlayRenderer(settings=settings)
    
    # Run analysis in a separate thread to keep UI smooth
    latest_analysis = None
    analysis_lock = threading.Lock()
    
    def analysis_worker():
        nonlocal latest_analysis
        while stream.is_running:
            frame_to_analyze = stream.read()
            if frame_to_analyze is not None:
                # Resize for faster analysis if needed, here we just pass it
                result = analyzer.process_frame(frame_to_analyze)
                with analysis_lock:
                    latest_analysis = result
            time.sleep(0.05) # ~20 FPS max for AI

    analysis_thread = threading.Thread(target=analysis_worker, daemon=True)
    analysis_thread.start()

    cv2.namedWindow("CameraQ Real-time Viewfinder", cv2.WINDOW_AUTOSIZE)
    
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and renderer.is_sidebar_open:
            for key, (bx1, by1, bx2, by2) in renderer.toggle_bounds.items():
                if bx1 <= x <= bx2 and by1 <= y <= by2:
                    settings.toggle(key)
                    return
            for key, (bx1, by1, bx2, by2, base_key, delta) in renderer.numeric_bounds.items():
                if bx1 <= x <= bx2 and by1 <= y <= by2:
                    settings.adjust(base_key, delta)
                    return

    cv2.setMouseCallback("CameraQ Real-time Viewfinder", mouse_callback)

    logger.info("Camera started. Press 'q' to quit, 'TAB' for settings.")
    
    try:
        while True:
            if not stream.is_running:
                logger.warning("Stream stopped unexpectedly. Exiting.")
                break
                
            frame = stream.read()
            if frame is not None:
                with analysis_lock:
                    current_analysis = latest_analysis
                    
                display_frame = renderer.draw(frame, current_analysis, fps=stream.fps)
                cv2.imshow("CameraQ Real-time Viewfinder", display_frame)
                
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == 9: # TAB key
                renderer.is_sidebar_open = not renderer.is_sidebar_open
            elif key == ord('c'):
                # Force AI Coach analysis
                if frame is not None:
                    analyzer.force_analyze(frame)
            
            # To not spin too fast if no frame
            if frame is None:
                time.sleep(0.01)
                
    finally:
        analyzer.ai_coach.stop()
        stream.stop()
        cv2.destroyAllWindows()
        logger.info("Camera stream stopped.")

if __name__ == "__main__":
    main()
