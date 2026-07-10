import cv2
import numpy as np
import time
import threading
import sys
import logging
from pathlib import Path

# Add project root to path so we can run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.core.io.camera import CameraStreamManager
from src.ui.overlay import OverlayRenderer
from src.core.settings import SettingsManager

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

WINDOW_NAME = "CameraQ Real-time Viewfinder"


def _status_frame(message: str, width: int = 960, height: int = 540) -> np.ndarray:
    """Render a visible status page while camera/models are starting."""
    from PIL import Image, ImageDraw, ImageFont

    font_paths = (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/LanguageSupport/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    )
    font_path = next((path for path in font_paths if Path(path).exists()), None)
    try:
        title_font = ImageFont.truetype(font_path, 42) if font_path else ImageFont.load_default()
        message_font = ImageFont.truetype(font_path, 25) if font_path else ImageFont.load_default()
    except OSError:
        title_font = ImageFont.load_default()
        message_font = ImageFont.load_default()

    image = Image.new("RGB", (width, height), (24, 28, 36))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((32, 32, width - 32, height - 32), radius=16,
                           fill=(31, 37, 48), outline=(0, 190, 235), width=2)
    draw.text((64, 78), "CameraQ", font=title_font, fill=(70, 220, 255))
    draw.text((64, 160), message, font=message_font, fill=(240, 240, 240))
    draw.text((64, height - 92), "CameraQ local viewfinder", font=message_font,
              fill=(155, 165, 180))
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CameraQ Real-time Viewfinder")
    parser.add_argument("--deep-ai-enabled", action="store_true", help="Enable deep AI assistant features by default")
    args = parser.parse_args()

    logger.info("Starting CameraQ Real-time Viewfinder...")
    stream = CameraStreamManager(source=0)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    cv2.imshow(WINDOW_NAME, _status_frame("正在打开摄像头..."))
    cv2.waitKey(1)
    
    if not stream.start():
        message = stream.last_error or "摄像头不可用；请在系统设置中允许当前终端/IDE访问摄像头。"
        logger.error(message)
        cv2.imshow(WINDOW_NAME, _status_frame(message))
        cv2.waitKey(1800)
        cv2.destroyAllWindows()
        return

    settings = SettingsManager()
    if args.deep_ai_enabled:
        settings.ai_coach_enabled = True
        
    cv2.imshow(WINDOW_NAME, _status_frame("正在加载本地视觉模型，请稍候..."))
    cv2.waitKey(1)
    # Import the heavy analyzer only after the status window is visible. The
    # YOLO/torch import path can take tens of seconds on a cold start.
    from src.core.analyzer import CameraQAnalyzer

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

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # Handle potential Retina/DPI scaling by mapping coordinates
            try:
                rect = cv2.getWindowImageRect(WINDOW_NAME)
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
                actions = list(renderer.action_bounds.items())
                
                for key, (bx1, by1, bx2, by2) in toggles:
                    if bx1 <= x <= bx2 and by1 <= y <= by2:
                        settings.toggle(key)
                        return
                for key, (bx1, by1, bx2, by2, base_key, delta) in numerics:
                    if bx1 <= x <= bx2 and by1 <= y <= by2:
                        settings.adjust(base_key, delta)
                        return
                for key, (bx1, by1, bx2, by2) in actions:
                    if bx1 <= x <= bx2 and by1 <= y <= by2:
                        if key == "clear_composition_diagnostics":
                            analyzer.clear_composition_diagnostics()
                        return

    cv2.setMouseCallback(WINDOW_NAME, mouse_callback)

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
                cv2.imshow(WINDOW_NAME, display_frame)
            else:
                message = stream.last_error or "正在等待摄像头帧..."
                cv2.imshow(WINDOW_NAME, _status_frame(message))
                
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
