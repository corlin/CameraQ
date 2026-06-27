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
    import argparse
    parser = argparse.ArgumentParser(description="CameraQ Real-time Viewfinder")
    parser.add_argument("--deep-ai-enabled", action="store_true", help="Enable deep AI assistant features by default")
    args = parser.parse_args()

    logger.info("Starting CameraQ Real-time Viewfinder...")
    stream = CameraStreamManager(source=0)
    
    if not stream.start():
        logger.warning("Failed to start camera stream.")
        return

    settings = SettingsManager()
    if args.deep_ai_enabled:
        settings.ai_coach_enabled = True
        
    analyzer = CameraQAnalyzer(settings=settings)
    renderer = OverlayRenderer(settings=settings)
    
    from src.core.io.voice import VoiceSynthesizer
    voice_synth = VoiceSynthesizer()
    last_spoken_advice = ""
    last_alignment_state = False
    
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
        if event == cv2.EVENT_LBUTTONDOWN:
            # Handle potential Retina/DPI scaling by mapping coordinates
            try:
                rect = cv2.getWindowImageRect("CameraQ Real-time Viewfinder")
                if rect[2] > 0 and hasattr(renderer, 'last_frame_size'):
                    fw, fh = renderer.last_frame_size
                    dw, dh = rect[2], rect[3]
                    if dw != fw:
                        x = int(x * (fw / dw))
                        y = int(y * (fh / dh))
            except Exception as e:
                pass

            logger.info(f"Mouse click mapped to ({x}, {y}), sidebar_open={renderer.is_sidebar_open}")
            if renderer.is_sidebar_open:
                # Copy bounds to prevent dictionary changed size during iteration error
                toggles = list(renderer.toggle_bounds.items())
                numerics = list(renderer.numeric_bounds.items())
                
                for key, (bx1, by1, bx2, by2) in toggles:
                    if bx1 <= x <= bx2 and by1 <= y <= by2:
                        settings.toggle(key)
                        return
                for key, (bx1, by1, bx2, by2, base_key, delta) in numerics:
                    if bx1 <= x <= bx2 and by1 <= y <= by2:
                        settings.adjust(base_key, delta)
                        return

    cv2.setMouseCallback("CameraQ Real-time Viewfinder", mouse_callback)

    logger.info("Camera started. Press 'q' to quit, 'TAB' for settings.")
    logger.info("Press 'i' to ask the AI coach a specific question.")
    
    try:
        while True:
            if not stream.is_running:
                logger.warning("Stream stopped unexpectedly. Exiting.")
                break
                
            frame = stream.read()
            if frame is not None:
                with analysis_lock:
                    current_analysis = latest_analysis
                    
                if current_analysis and current_analysis.current_scene_context:
                    ctx = current_analysis.current_scene_context
                    if getattr(ctx, '_last_applied_time', 0.0) != ctx.timestamp:
                        stream.set_iso(ctx.recommended_iso)
                        exp_val = 0.0
                        if ctx.recommended_iso >= 800:
                            exp_val = 1.0
                        elif ctx.recommended_iso <= 100:
                            exp_val = -1.0
                        stream.set_exposure(exp_val)
                        ctx._last_applied_time = ctx.timestamp
                        
                # Handle Voice Feedback
                level = getattr(settings, "coaching_level", "COACH")
                if current_analysis and current_analysis.ai_coaching and level in ["COACH", "PRO"]:
                    ai = current_analysis.ai_coaching
                    current_time = time.time()
                    if not ai.is_error and ai.is_active(current_time):
                        if ai.advice_text != last_spoken_advice and ai.interaction_type == "PROACTIVE_VOICE":
                            voice_synth.speak(ai.advice_text)
                            last_spoken_advice = ai.advice_text
                    
                    # Handle Haptic / Alignment State
                    current_alignment_state = getattr(ai, 'perfect_alignment', False)
                    if current_alignment_state and not last_alignment_state:
                        logger.info("[HAPTIC VIBRATION] Perfect alignment snap!")
                    last_alignment_state = current_alignment_state
                else:
                    last_alignment_state = False
                    
                display_frame = renderer.draw(frame, current_analysis, fps=stream.fps)
                cv2.imshow("CameraQ Real-time Viewfinder", display_frame)
                
            key = cv2.waitKey(1)
            if key != -1:
                if renderer.input_mode:
                    # In input mode, append standard characters to query
                    if key == 13 or key == 10: # Enter
                        if frame is not None and renderer.user_query.strip():
                            analyzer.force_analyze(frame, query=renderer.user_query.strip())
                        renderer.input_mode = False
                        renderer.user_query = ""
                    elif key == 27: # Esc
                        renderer.input_mode = False
                        renderer.user_query = ""
                    elif key == 8 or key == 127: # Backspace
                        renderer.user_query = renderer.user_query[:-1]
                    elif 32 <= key <= 126:
                        renderer.user_query += chr(key)
                else:
                    key = key & 0xFF
                    if key == ord('q'):
                        break
                    elif key == 9: # TAB key
                        renderer.is_sidebar_open = not renderer.is_sidebar_open
                    elif key == ord('f'):
                        # Force AI Coach analysis
                        if frame is not None:
                            analyzer.force_analyze(frame)
                    elif key == ord('c'):
                        settings.cycle_coaching_level()
                    elif key == ord('i'):
                        renderer.input_mode = True
                        renderer.user_query = ""
            
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
