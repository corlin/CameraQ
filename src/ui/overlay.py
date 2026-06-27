import cv2
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
from src.core.entities import AnalysisResult
from src.core.settings import SettingsManager

class OverlayRenderer:
    def __init__(self, debounce_interval=0.3, settings: SettingsManager = None):
        # We use PIL for rendering text because cv2.putText does not support Chinese out of the box nicely
        self.debounce_interval = debounce_interval
        self.last_feedback = ""
        self.last_update_time = 0.0
        self.settings = settings if settings else SettingsManager()
        self.is_sidebar_open = False
        self.sidebar_offset = 320.0 # start fully hidden
        self.toggle_bounds = {}
        self.numeric_bounds = {}
        self.input_mode = False
        self.user_query = ""
        self.ai_coach_last_update = 0.0
        self.ai_coach_message = None
        self.scene_icons = {
            "Outdoor": "⛰️ Outdoor",
            "Indoor": "🏠 Indoor",
            "Portrait": "👤 Portrait",
            "Landscape": "🌄 Landscape",
            "Night": "🌙 Night",
            "Bright": "☀️ Bright",
            "Dark": "🌑 Dark",
            "Backlit": "✨ Backlit"
        }
        
        # Pre-load fonts to avoid loading them per-frame
        try:
            import os
            font_paths = [
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "/System/Library/Fonts/LanguageSupport/PingFang.ttc",
                "/System/Library/Fonts/PingFang.ttc"
            ]
            font_path = None
            for p in font_paths:
                if os.path.exists(p):
                    font_path = p
                    break
                    
            if font_path:
                self.font = ImageFont.truetype(font_path, 30)
                self.small_font = ImageFont.truetype(font_path, 20)
            else:
                self.font = ImageFont.load_default()
                self.small_font = ImageFont.load_default()
        except IOError:
            self.font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()

    def draw(self, frame: np.ndarray, analysis: Optional[AnalysisResult], fps: float = 0.0) -> np.ndarray:
        if frame is None:
            return frame
            
        # Draw base overlays (from analyzer if available, or just raw frame)
        if analysis and analysis.image_with_overlays is not None:
            out_frame = analysis.image_with_overlays.copy()
        else:
            out_frame = frame.copy()
            
        h, w = out_frame.shape[:2]
        self.last_frame_size = (w, h)

        # Use PIL to draw Chinese text and translucent shapes
        img_pil = Image.fromarray(cv2.cvtColor(out_frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
        
        # Create a translucent overlay layer for UI elements
        ui_overlay = Image.new('RGBA', img_pil.size, (255, 255, 255, 0))
        draw_ov = ImageDraw.Draw(ui_overlay)

        # Draw Rule of Thirds Grid
        grid_color = (200, 200, 200, 90) # Soft translucent white
        x1, x2 = w // 3, 2 * w // 3
        y1, y2 = h // 3, 2 * h // 3
        draw_ov.line([(x1, 0), (x1, h)], fill=grid_color, width=1)
        draw_ov.line([(x2, 0), (x2, h)], fill=grid_color, width=1)
        draw_ov.line([(0, y1), (w, y1)], fill=grid_color, width=1)
        draw_ov.line([(0, y2), (w, y2)], fill=grid_color, width=1)

        # Draw FPS with a subtle background plate
        fps_text = f"FPS: {fps:.1f}"
        bbox = draw_ov.textbbox((10, 10), fps_text, font=self.small_font)
        draw_ov.rectangle([bbox[0]-4, bbox[1]-4, bbox[2]+4, bbox[3]+4], fill=(0, 0, 0, 100))
        draw_ov.text((10, 10), fps_text, font=self.small_font, fill=(0, 255, 0, 255))
        
        if analysis:
            current_time = time.time()
            level = getattr(self.settings, "coaching_level", "COACH")
            
            # Draw Coaching Level Indicator
            level_text = f"AI: {level}"
            bbox = draw_ov.textbbox((w//2 - 40, 10), level_text, font=self.small_font)
            lw = bbox[2] - bbox[0]
            draw_ov.rectangle([w//2 - lw//2 - 10, 10, w//2 + lw//2 + 10, 40], fill=(0, 0, 0, 150))
            draw_ov.text((w//2 - lw//2, 12), level_text, font=self.small_font, fill=(200, 200, 200, 255))
            
            # Draw subject bounding boxes and labels
            if level == "PRO" and hasattr(analysis, 'subjects') and analysis.subjects:
                for sub in analysis.subjects:
                    color = (0, 255, 0, 160) if sub.is_primary_subject else (200, 200, 200, 120)
                    thickness = 2 if sub.is_primary_subject else 1
                    
                    sx1 = int(sub.bounding_box.x)
                    sy1 = int(sub.bounding_box.y)
                    sx2 = int(sx1 + sub.bounding_box.width)
                    sy2 = int(sy1 + sub.bounding_box.height)
                    
                    # Draw translucent box (T004: professional thin lines)
                    thickness = 1 # Thin lines
                    draw_ov.rectangle([sx1, sy1, sx2, sy2], outline=color, width=thickness)
                    
                    # Corner brackets (reticles)
                    length = min(30, max(5, (sx2-sx1)//4), max(5, (sy2-sy1)//4))
                    for point in [(sx1, sy1), (sx2, sy1), (sx1, sy2), (sx2, sy2)]:
                        px, py = point
                        dx = 1 if px == sx1 else -1
                        dy = 1 if py == sy1 else -1
                        draw_ov.line([(px, py), (px + dx * length, py)], fill=color, width=2)
                        draw_ov.line([(px, py), (px, py + dy * length)], fill=color, width=2)
                    
                    # Text label with background plate
                    text = f"{sub.class_name} {sub.confidence:.2f}"
                    bbox = draw_ov.textbbox((0, 0), text, font=self.small_font)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    
                    plate_y1 = max(0, sy1 - th - 8)
                    plate_y2 = max(0, sy1)
                    draw_ov.rectangle([sx1, plate_y1, sx1 + tw + 8, plate_y2], fill=(0, 0, 0, 150))
                    draw_ov.text((sx1 + 4, plate_y1 + 2), text, font=self.small_font, fill=(255, 255, 255, 255))

            # Draw tracked motion vectors
            if level == "PRO" and getattr(analysis, 'tracked_subjects', None):
                for ts in analysis.tracked_subjects:
                    if abs(ts.velocity_x) > 1 or abs(ts.velocity_y) > 1:
                        cx = ts.bounding_box.x + ts.bounding_box.width / 2.0
                        cy = ts.bounding_box.y + ts.bounding_box.height / 2.0
                        end_x = cx + ts.velocity_x * 5  # scale vector for visibility
                        end_y = cy + ts.velocity_y * 5
                        draw_ov.line([(cx, cy), (end_x, end_y)], fill=(0, 165, 255, 180), width=3)
                        # Draw arrowhead (simple point)
                        draw_ov.ellipse([(end_x-4, end_y-4), (end_x+4, end_y+4)], fill=(0, 165, 255, 220))

            # Draw Aesthetics Warning
            if level in ["COACH", "PRO"] and getattr(analysis, 'aesthetics', None) and analysis.aesthetics.lighting_feedback:
                warning_text = analysis.aesthetics.lighting_feedback
                bbox = draw_ov.textbbox((0, 0), warning_text, font=self.font)
                w_text = bbox[2] - bbox[0]
                h_text = bbox[3] - bbox[1]
                x_warn = max((w - w_text) // 2, 10)
                
                draw_ov.rectangle([x_warn - 10, 50 - 5, x_warn + w_text + 10, 50 + h_text + 5], fill=(0, 0, 0, 180), outline=(255, 50, 50, 200), width=1)
                draw_ov.text((x_warn, 50), warning_text, font=self.font, fill=(255, 100, 100, 255))

            # Draw Shutter Opportunity
            if level in ["COACH", "PRO"] and getattr(analysis, 'shutter_opportunity', False):
                shutter_text = "✨ 绝佳抓拍时机! (Perfect Shutter Opportunity!) ✨"
                bbox = draw_ov.textbbox((0, 0), shutter_text, font=self.font)
                s_w = bbox[2] - bbox[0]
                s_h = bbox[3] - bbox[1]
                x_shutter = max((w - s_w) // 2, 10)
                y_shutter = h // 2
                
                draw_ov.rectangle([x_shutter - 15, y_shutter - 10, x_shutter + s_w + 15, y_shutter + s_h + 10], fill=(0, 0, 0, 160), outline=(0, 255, 255, 200), width=2)
                draw_ov.text((x_shutter, y_shutter), shutter_text, font=self.font, fill=(0, 255, 255, 255))

            # Debounce feedback text updates
            if analysis.feedback_message != self.last_feedback:
                if current_time - self.last_update_time >= self.debounce_interval:
                    self.last_feedback = analysis.feedback_message
                    self.last_update_time = current_time

            # Pre-calculate feedback layout to avoid overlap with sub-scores
            wrapped_lines = []
            if level in ["COACH", "PRO"] and self.last_feedback:
                max_text_width = w - 40
                for p in self.last_feedback.split('\n'):
                    line = ""
                    for char in p:
                        test_line = line + char
                        bbox = draw_ov.textbbox((0,0), test_line, font=self.small_font)
                        tw = bbox[2] - bbox[0]
                        if tw > max_text_width and line != "":
                            wrapped_lines.append(line)
                            line = char
                        else:
                            line = test_line
                    if line:
                        wrapped_lines.append(line)
                        
            total_text_height = len(wrapped_lines) * 35 if wrapped_lines else 0
            feedback_y_offset = h - 30 - total_text_height if wrapped_lines else h - 30

            # Draw Sub-scores (Radar/Bar Chart)
            if level == "PRO" and hasattr(analysis, 'score') and analysis.score:
                # Dynamic positioning above the feedback text (bg_h is approx 135)
                subscore_h = 5 * 20 + 35
                subscores_y = feedback_y_offset - subscore_h - 15
                self._draw_subscores(draw_ov, analysis.score, 10, subscores_y)

            # Draw feedback (which already includes the score in Chinese)
            if wrapped_lines:
                y_offset = feedback_y_offset
                max_width = max([draw_ov.textbbox((0,0), line, font=self.small_font)[2] - draw_ov.textbbox((0,0), line, font=self.small_font)[0] for line in wrapped_lines]) if wrapped_lines else 0
                draw_ov.rectangle([10, y_offset - 10, 10 + max_width + 20, y_offset + total_text_height], fill=(0, 0, 0, 150), outline=(200, 200, 200, 100), width=1)
                
                for line in wrapped_lines:
                    draw_ov.text((20, y_offset), line, font=self.small_font, fill=(255, 255, 255, 255))
                    y_offset += 35
            
            # Draw AI Coaching (US2: Use duration/is_active logic)
            if level != "OFF" and getattr(analysis, 'ai_coaching', None):
                ai = analysis.ai_coaching
                if not ai.is_error and ai.is_active(current_time):
                    # Style based on interaction type
                    if ai.interaction_type == "PROACTIVE_VOICE":
                        coach_text = f"🔊 语音: {ai.advice_text}"
                        outline_color = (100, 255, 100, 200) # Green for voice
                        fill_color = (100, 255, 100, 255)
                    else:
                        coach_text = f"🤖 提示: {ai.advice_text}"
                        outline_color = (255, 215, 0, 200) # Gold for popup
                        fill_color = (255, 215, 0, 255)
                        
                    if self.ai_coach_message != coach_text:
                        self.ai_coach_message = coach_text
                        self.ai_coach_last_update = current_time
                        
                    time_since_update = current_time - self.ai_coach_last_update
                    y_ai = 100
                    
                    if level in ["COACH", "PRO"]:
                        if time_since_update < 5.0:
                            max_text_width = w - 40
                            wrapped_coach_lines = []
                            line = ""
                            for char in coach_text:
                                test_line = line + char
                                bbox = draw_ov.textbbox((0,0), test_line, font=self.font)
                                tw = bbox[2] - bbox[0]
                                if tw > max_text_width and line != "":
                                    wrapped_coach_lines.append(line)
                                    line = char
                                else:
                                    line = test_line
                            if line:
                                wrapped_coach_lines.append(line)
                            
                            total_h_ai = len(wrapped_coach_lines) * 40
                            
                            max_w_ai = max([draw_ov.textbbox((0,0), l, font=self.font)[2] - draw_ov.textbbox((0,0), l, font=self.font)[0] for l in wrapped_coach_lines]) if wrapped_coach_lines else 0
                            x_ai = max((w - max_w_ai) // 2, 10)
                            
                            draw_ov.rounded_rectangle([x_ai - 15, y_ai - 10, x_ai + max_w_ai + 15, y_ai + total_h_ai + 10], radius=10, fill=(0, 0, 0, 180), outline=outline_color, width=1)
                            
                            for i, l in enumerate(wrapped_coach_lines):
                                draw_ov.text((x_ai, y_ai + i * 40), l, font=self.font, fill=fill_color)
                        else:
                            # Collapsed pill view
                            collapsed_text = "💬 AI Insight (Tab)"
                            bbox = draw_ov.textbbox((0,0), collapsed_text, font=self.small_font)
                            cw = bbox[2] - bbox[0]
                            ch = bbox[3] - bbox[1]
                            x_ai = max((w - cw) // 2, 10)
                            
                            draw_ov.rounded_rectangle([x_ai - 10, y_ai - 5, x_ai + cw + 10, y_ai + ch + 5], radius=15, fill=(0, 0, 0, 150), outline=(200, 200, 200, 100), width=1)
                            draw_ov.text((x_ai, y_ai), collapsed_text, font=self.small_font, fill=(200, 200, 200, 255))
                    
                    # T003: Render Ghost Composition Box
                    target_box = getattr(ai, 'target_box', None)
                    if target_box:
                        tx1, ty1, tx2, ty2 = target_box
                        if getattr(ai, 'perfect_alignment', False):
                            # Solid golden border for perfect alignment "snap"
                            draw_ov.rectangle([tx1, ty1, tx2, ty2], fill=(255, 215, 0, 40), outline=(255, 215, 0, 255), width=3)
                            # Add "✨ ALIGNED" text below the box
                            snap_text = "✨ ALIGNED"
                            draw_ov.text((tx1 + (tx2-tx1)//2 - 40, ty2 + 10), snap_text, font=self.small_font, fill=(255, 215, 0, 255))
                        else:
                            # Semi-transparent fill with dashed-like border
                            draw_ov.rectangle([tx1, ty1, tx2, ty2], fill=(255, 255, 255, 40), outline=(255, 255, 255, 180), width=2)
                        
                    # T004: Render Directional Arrows
                    arrows = getattr(ai, 'directional_arrows', [])
                    if arrows:
                        arrow_map = {
                            "LEFT": ("←", 30, h//2),
                            "RIGHT": ("→", w - 60, h//2),
                            "UP": ("↑", w//2, 80),
                            "DOWN": ("↓", w//2, h - 120),
                            "FORWARD": ("⇡", w//2 - 40, h//2),
                            "BACKWARD": ("⇣", w//2 + 40, h//2)
                        }
                        for arrow in arrows:
                            if arrow in arrow_map:
                                symbol, ax, ay = arrow_map[arrow]
                                draw_ov.rectangle([ax - 10, ay - 10, ax + 40, ay + 40], fill=(0, 0, 0, 150), outline=(200, 200, 200, 100), width=1)
                                draw_ov.text((ax, ay), symbol, font=self.font, fill=(255, 255, 255, 255))
                    
            # Draw Scene Context
            if getattr(analysis, 'current_scene_context', None):
                ctx = analysis.current_scene_context
                
                # Use scene icons
                st = self.scene_icons.get(ctx.scene_type, ctx.scene_type)
                lc = self.scene_icons.get(ctx.lighting_condition, ctx.lighting_condition)
                
                active_tpl = getattr(getattr(analysis, 'ai_coaching', None), 'active_template', "Default")
                scene_info = f"{st} | {lc} | Tpl: {active_tpl} | ISO {ctx.recommended_iso} | 1/{int(ctx.recommended_shutter*1000) if ctx.recommended_shutter and ctx.recommended_shutter < 1 else ctx.recommended_shutter}"
                
                # Top bar badge
                bbox = draw_ov.textbbox((0,0), scene_info, font=self.small_font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                
                x_scene = max((w - tw) // 2, 10)
                y_scene = 40
                
                draw_ov.rounded_rectangle([x_scene - 15, y_scene - 5, x_scene + tw + 15, y_scene + th + 5], radius=15, fill=(0, 0, 0, 150), outline=(200, 200, 200, 80), width=1)
                draw_ov.text((x_scene, y_scene), scene_info, font=self.small_font, fill=(200, 255, 200, 255))

        # Update sidebar animation state
        target_offset = 0.0 if self.is_sidebar_open else 320.0
        self.sidebar_offset += (target_offset - self.sidebar_offset) * 0.3
        
        # Draw Sidebar
        if self.sidebar_offset < 319.0:
            self._draw_sidebar(draw_ov, w, h)
            
        if self.sidebar_offset > 5.0:
            prompt_text = "⚙️ Press TAB for Settings"
            bbox = draw_ov.textbbox((0, 0), prompt_text, font=self.small_font)
            pw = bbox[2] - bbox[0]
            draw_ov.rectangle([w - pw - 20, 10, w - 10, 10 + 30], fill=(0, 0, 0, 150))
            draw_ov.text((w - pw - 15, 15), prompt_text, font=self.small_font, fill=(200, 200, 200, 255))
            if not self.is_sidebar_open:
                self.toggle_bounds.clear()
                self.numeric_bounds.clear()

        # Draw input box if in input mode
        if self.input_mode:
            input_text = f"向AI提问: {self.user_query}_"
            bbox = draw_ov.textbbox((0, 0), input_text, font=self.font)
            iw = bbox[2] - bbox[0]
            ih = bbox[3] - bbox[1]
            ix = max((w - iw) // 2, 20)
            iy = h - ih - 50
            draw_ov.rectangle([ix - 15, iy - 10, ix + iw + 15, iy + ih + 10], fill=(0, 0, 0, 200), outline=(200, 200, 255, 255), width=2)
            draw_ov.text((ix, iy), input_text, font=self.font, fill=(255, 255, 255, 255))
            
            # Helper text
            helper_text = "按 Enter 发送, Esc 取消"
            draw_ov.text((ix, iy + ih + 15), helper_text, font=self.small_font, fill=(150, 150, 150, 255))

        # Composite the UI layer over the image
        img_pil = Image.alpha_composite(img_pil, ui_overlay).convert('RGB')
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def _draw_sidebar(self, draw_ov, w, h):
        sidebar_w = 320
        sidebar_x = w - sidebar_w + int(self.sidebar_offset)
        
        # Draw dark panel
        draw_ov.rectangle([sidebar_x, 0, w + int(self.sidebar_offset), h], fill=(0, 0, 0, 220))
        
        # Draw title
        title = "🛠️ Analysis Settings (TAB)"
        draw_ov.text((sidebar_x + 15, 20), title, font=self.small_font, fill=(255, 255, 255, 255))
        draw_ov.line([(sidebar_x + 10, 55), (sidebar_x + sidebar_w - 10, 55)], fill=(100, 100, 100, 255), width=1)
        
        y_offset = 80
        self.toggle_bounds.clear()
        self.numeric_bounds.clear()
        
        # Group 1: Detection Toggles
        draw_ov.text((sidebar_x + 15, y_offset), "--- Detection Modules ---", font=self.small_font, fill=(150, 150, 150, 255))
        y_offset += 40
        
        toggles = [
            ("AI Coach", "ai_coach_enabled"),
            ("Pose Detection", "pose_detection_enabled"),
            ("Saliency Detection", "saliency_enabled")
        ]
        
        for label, key in toggles:
            is_enabled = getattr(self.settings, key, False)
            draw_ov.text((sidebar_x + 20, y_offset), label, font=self.small_font, fill=(200, 200, 200, 255))
            
            btn_w, btn_h = 70, 30
            btn_x = sidebar_x + sidebar_w - btn_w - 20
            btn_y = y_offset - 2
            
            color = (0, 180, 0, 200) if is_enabled else (180, 0, 0, 200)
            text = "ON" if is_enabled else "OFF"
            
            draw_ov.rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h], fill=color, outline=(255, 255, 255, 100))
            draw_ov.text((btn_x + 15, btn_y + 3), text, font=self.small_font, fill=(255, 255, 255, 255))
            self.toggle_bounds[key] = (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h)
            y_offset += 50
            
        # Group 2: Performance Parameters
        y_offset += 10
        draw_ov.text((sidebar_x + 15, y_offset), "--- Performance ---", font=self.small_font, fill=(150, 150, 150, 255))
        y_offset += 40
        
        numerics = [
            ("AI Interval (s)", "ai_sampling_interval", 1.0, "{:.1f}"),
            ("Analysis Throttle", "analysis_throttle_n", 1, "{:d}")
        ]
        
        for label, key, delta, fmt in numerics:
            val = getattr(self.settings, key, 0)
            draw_ov.text((sidebar_x + 20, y_offset), label, font=self.small_font, fill=(200, 200, 200, 255))
            
            val_text = fmt.format(val)
            # Minus button
            btn_y = y_offset - 2
            btn_h = 30
            mx = sidebar_x + sidebar_w - 110
            px = sidebar_x + sidebar_w - 40
            
            draw_ov.rectangle([mx, btn_y, mx + 30, btn_y + btn_h], fill=(80, 80, 80, 200), outline=(255, 255, 255, 100))
            draw_ov.text((mx + 10, btn_y + 3), "-", font=self.small_font, fill=(255, 255, 255, 255))
            self.numeric_bounds[key + "_minus"] = (mx, btn_y, mx + 30, btn_y + btn_h, key, -delta)
            
            # Value
            draw_ov.text((mx + 35, y_offset), val_text, font=self.small_font, fill=(255, 255, 0, 255))
            
            # Plus button
            draw_ov.rectangle([px, btn_y, px + 30, btn_y + btn_h], fill=(80, 80, 80, 200), outline=(255, 255, 255, 100))
            draw_ov.text((px + 8, btn_y + 3), "+", font=self.small_font, fill=(255, 255, 255, 255))
            self.numeric_bounds[key + "_plus"] = (px, btn_y, px + 30, btn_y + btn_h, key, delta)
            
            y_offset += 50

    def _draw_subscores(self, draw_ov, score, x, y):
        # Draw a small bar chart for the 5 sub-scores
        labels = [
            ("主体 Subject", score.subject_score),
            ("结构 Structure", score.structure_score),
            ("平衡 Balance", score.balance_score),
            ("干扰 Interference", score.interference_score),
            ("风格 Style", score.style_score)
        ]
        
        bg_w = 200
        bg_h = len(labels) * 20 + 35
        # Background plate
        draw_ov.rectangle([x, y, x + bg_w, y + bg_h], fill=(0, 0, 0, 180), outline=(100, 100, 100, 150))
        draw_ov.text((x + 10, y + 5), f"综合评分: {score.total_score}", font=self.small_font, fill=(255, 215, 0, 255))
        
        bar_x = x + 10
        bar_y = y + 30
        max_bar_w = bg_w - 20
        
        for name, val in labels:
            # text label (very small, maybe just first char or English? let's just print name)
            # using small font but scaled down? PIL text is tricky without a tinier font, so just draw bar and value
            draw_ov.text((bar_x, bar_y - 2), f"{name[:2]}:{val}", font=self.small_font, fill=(200, 200, 200, 255))
            
            # draw bar
            bar_len = int((val / 100.0) * (max_bar_w - 80))
            if bar_len < 1: bar_len = 1
            color = (0, 255, 0, 200) if val >= 80 else ((255, 165, 0, 200) if val >= 60 else (255, 0, 0, 200))
            draw_ov.rectangle([bar_x + 80, bar_y + 4, bar_x + 80 + bar_len, bar_y + 16], fill=color)
            
            bar_y += 20

