import cv2
import numpy as np
from pathlib import Path
from typing import Union, Optional

from .entities import AnalysisResult, CropRecommendation, CropStyle, BoundingBox, FusedSubject, SourceType
from .models.yolo_wrapper import YoloObjectDetector
from .models.pose_wrapper import YoloPoseDetector
from .detectors.saliency_detector import SaliencyDetector
from .rules.horizon_rule import detect_horizon
from .rules.portrait_rule import analyze_portrait
from .rules.scoring import calculate_composition_score
from .rules.cropping import generate_crops
from .rules.feedback import select_primary_feedback
from .analyzers.aesthetics_analyzer import AestheticsAnalyzer
from .trackers.object_tracker import ObjectTracker
from .rules.background_rule import analyze_background_interference
from .rules.position_rule import analyze_position
from .ai_coach import AICoach
from .settings import SettingsManager
import time
import queue

class CameraQAnalyzer:
    """
    Main orchestration class for CameraQ Stage 1 Offline Demo.
    It combines subject detection, structural analysis, and composition scoring.
    """
    
    def __init__(self, settings: SettingsManager = None):
        self.settings = settings if settings else SettingsManager()
        self.object_detector = YoloObjectDetector(model_size="n")
        self.pose_detector = YoloPoseDetector(model_size="n")
        self.saliency_detector = SaliencyDetector()
        self.aesthetics_analyzer = AestheticsAnalyzer()
        self.object_tracker = ObjectTracker()
        self.ai_coach = AICoach()
        self.ai_coach.start()
        
        from .gemini_client import GeminiClient
        import threading, queue
        self.gemini_client = GeminiClient(self.settings)
        self.scene_context_queue = queue.Queue(maxsize=1)
        self._cached_scene_context = None
        self._scene_thread = threading.Thread(target=self._scene_context_loop, daemon=True)
        self._scene_thread.start()
        
        self.last_ai_sample_time = 0.0
        self._frame_count = 0
        self._cached_horizon = None
        self._cached_saliency = None

    def _scene_context_loop(self):
        while True:
            try:
                frame = self.scene_context_queue.get()
                if frame is None:
                    continue
                # Compress image
                h, w = frame.shape[:2]
                max_dim = 512
                if max(h, w) > max_dim:
                    scale = max_dim / max(h, w)
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                
                # Encode to jpeg
                success, encoded_image = cv2.imencode('.jpg', frame)
                if success:
                    image_bytes = encoded_image.tobytes()
                    context = self.gemini_client.analyze_scene(image_bytes)
                    if context:
                        self._cached_scene_context = context
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Scene context loop error: {e}")
            finally:
                self.scene_context_queue.task_done()
                
    def process_frame(self, image_source: Union[str, Path, np.ndarray]) -> AnalysisResult:
        """
        Process a single image frame and return composition feedback.
        
        Args:
            image_source: Path to image file or a numpy array (BGR format from cv2).
            
        Returns:
            AnalysisResult containing feedback, score, and recommended crops.
        """
        if isinstance(image_source, (str, Path)):
            img = cv2.imread(str(image_source))
            if img is None:
                raise ValueError(f"Could not read image from {image_source}")
        else:
            img = image_source
            
        image_height, image_width = img.shape[:2]
        
        # Enqueue frame for AI Coach every 10 seconds, and Scene Context every 10 seconds
        current_time = time.time()
        if self.settings.ai_coach_enabled and current_time - self.last_ai_sample_time > 10.0:
            self.ai_coach.enqueue_frame(img)
            self.last_ai_sample_time = current_time
            
        # Offload scene analysis to background thread (limit to every 10s to avoid hitting 15 RPM rate limit)
        if self.settings.gemini_api_key and current_time - getattr(self, '_last_scene_time', 0.0) > 10.0:
            try:
                self.scene_context_queue.put_nowait(img)
                self._last_scene_time = current_time
            except queue.Full:
                pass
        
        # Run YOLO object detection
        if self.settings.object_detection_enabled:
            yolo_subjects = self.object_detector.detect(img)
        else:
            yolo_subjects = []
        
        # Run Saliency detection
        if self.settings.saliency_enabled:
            if self._frame_count % self.settings.analysis_throttle_n == 0 or self._cached_saliency is None:
                self._cached_saliency = self.saliency_detector.detect(img)
            saliency_map = self._cached_saliency
        else:
            from .entities import SaliencyMap
            saliency_map = SaliencyMap(heatmap=np.zeros((image_height, image_width), dtype=np.uint8), bounding_boxes=[], max_salient_score=0.0)
        
        # Fuse subjects
        subjects = self._fuse_subjects(yolo_subjects, saliency_map, image_width * image_height)
        
        # Track subjects
        tracked_subjects = self.object_tracker.update(subjects, image_width=image_width)
        
        # Shutter opportunity will be checked after scoring
        
        # Run YOLO pose detection
        if self.settings.pose_detection_enabled:
            pose_subjects = self.pose_detector.detect(img)
        else:
            pose_subjects = []
        
        # Run portrait rules
        all_feedbacks = []
        for p_sub in pose_subjects:
            feedbacks = analyze_portrait(p_sub, image_height, image_width)
            all_feedbacks.extend(feedbacks)
            
        # Run background interference rule
        bg_feedbacks = analyze_background_interference(subjects)
        all_feedbacks.extend(bg_feedbacks)
        
        # Run positional rule
        pos_feedbacks = analyze_position(subjects, image_width, image_height)
        all_feedbacks.extend(pos_feedbacks)
            
        # Run structural analysis (horizon)
        if self._frame_count % self.settings.analysis_throttle_n == 0 or self._cached_horizon is None:
            self._cached_horizon = detect_horizon(img)
        horizon = self._cached_horizon
        
        horizon_angle = 0.0
        if horizon is not None:
            # Calculate angle relative to absolute horizontal
            angle = np.abs(np.degrees(np.arctan2(horizon.p2.y - horizon.p1.y, horizon.p2.x - horizon.p1.x)))
            if angle > 90:
                angle = 180 - angle
            horizon_angle = angle
            horizon_text = f"地平线倾斜: {angle:.1f}度"
        else:
            horizon_text = "未检测到明显地平线"
            
        primary_subject_name = "无"
        
        for sub in subjects:
            if sub.is_primary_subject:
                primary_subject_name = sub.class_name
        
        # Scoring & Crops
        score = calculate_composition_score(all_feedbacks, horizon_angle)
        crops = generate_crops(subjects, image_width, image_height)
        
        # Check shutter opportunity
        shutter_opportunity = score.total_score >= 90 or any(ts.will_intersect_composition_node for ts in tracked_subjects)
        
        # Primary Feedback Selection
        primary_feedback = select_primary_feedback(all_feedbacks)
        
        primary_box = None
        for sub in subjects:
            if sub.is_primary_subject:
                primary_box = sub.bounding_box
                break

        # Aesthetics analysis
        aesthetics_metrics = self.aesthetics_analyzer.analyze(img, primary_box)
        
        # Combine text feedback
        feedback_str = f"得分: {score.total_score}/100. 主要目标: {primary_subject_name}。\n{horizon_text}。"
        if primary_feedback:
            feedback_str += f"\n👉 构图建议: {primary_feedback.message}"
            
        # Additional logic: if score is very high
        if score.total_score > 90:
            feedback_str += "\n✨ 完美构图！保持稳定！"
            
        if aesthetics_metrics.is_severe_backlight:
            feedback_str += "\n🤖 AI洞察: 画面严重过曝，建议开启 HDR 或锁定曝光"
            
        if aesthetics_metrics.is_background_cluttered:
            feedback_str += "\n🌿 背景较乱，建议切 2x 焦段或靠近主体"
        
        # Extract latest AI coaching
        ai_coaching = self.ai_coach.get_latest_advice() if self.settings.ai_coach_enabled else None
        
        # Scenario Templates logic (US2, US3)
        if ai_coaching and self._cached_scene_context:
            scene_type = self._cached_scene_context.scene_type
            cx, cy = image_width // 2, image_height // 2
            
            if "Portrait" in scene_type:
                ai_coaching.active_template = "Portrait"
                w_box, h_box = int(image_width * 0.4), int(image_height * 0.6)
                ai_coaching.target_box = (cx - w_box//2, cy - h_box//2 - 50, cx + w_box//2, cy + h_box//2 - 50)
                ai_coaching.directional_arrows = ["UP"]
            elif "Landscape" in scene_type:
                ai_coaching.active_template = "Landscape"
                h_third = image_height // 3
                ai_coaching.target_box = (int(image_width*0.1), h_third*2 - 20, int(image_width*0.9), h_third*2 + 20)
                ai_coaching.directional_arrows = ["DOWN"]
            elif "Vlog" in scene_type:
                ai_coaching.active_template = "Vlog"
                v_height = int(image_height * 0.8)
                v_width = int(v_height * (9/16))
                ai_coaching.target_box = (cx - v_width//2, cy - v_height//2, cx + v_width//2, cy + v_height//2)
                ai_coaching.directional_arrows = ["FORWARD"]
                
            # IoU Alignment calculation
            if primary_box and ai_coaching.target_box:
                tx1, ty1, tx2, ty2 = ai_coaching.target_box
                px1, py1 = primary_box.x, primary_box.y
                px2, py2 = primary_box.x + primary_box.width, primary_box.y + primary_box.height
                
                intersect_x = max(0, min(tx2, px2) - max(tx1, px1))
                intersect_y = max(0, min(ty2, py2) - max(ty1, py1))
                intersect_area = intersect_x * intersect_y
                
                target_area = (tx2 - tx1) * (ty2 - ty1)
                primary_area = primary_box.width * primary_box.height
                union_area = target_area + primary_area - intersect_area
                
                iou = intersect_area / float(union_area) if union_area > 0 else 0
                if iou > 0.65:
                    ai_coaching.perfect_alignment = True
                
        self._frame_count += 1
        
        result = AnalysisResult(
            image_with_overlays=None, # Clean frame, rendering moved entirely to overlay.py
            feedback_message=feedback_str,
            score=score,
            recommended_crops=crops,
            subjects=subjects,
            aesthetics=aesthetics_metrics,
            tracked_subjects=tracked_subjects,
            shutter_opportunity=shutter_opportunity,
            ai_coaching=ai_coaching,
            current_scene_context=self._cached_scene_context,
            debug_data={"num_subjects": len(subjects), "num_poses": len(pose_subjects)}
        )
        
        from .rules.scene_rule import SceneContextRule
        scene_rule = SceneContextRule()
        scene_feedbacks = scene_rule.evaluate(result)
        
        # Just append proactive advice to feedback string for now if it exists
        for fb in scene_feedbacks:
            if fb.message not in feedback_str:
                result.feedback_message += f"\n🤖 AI洞察: {fb.message}"
                
        return result

    def force_analyze(self, frame: np.ndarray, query: Optional[str] = None):
        """Forces the AI coach to analyze the current frame, overriding the queue."""
        if self.ai_coach:
            self.ai_coach.enqueue_frame(frame, force=True, query=query)
            self.last_ai_sample_time = time.time()

    def _fuse_subjects(self, yolo_subjects, saliency_map, img_area) -> list:
        fused = []
        for s in yolo_subjects:
            fs = FusedSubject(
                subject_id=s.subject_id,
                class_name=s.class_name,
                confidence=s.confidence,
                bounding_box=s.bounding_box,
                keypoints=s.keypoints,
                is_primary_subject=False,
                source=SourceType.YOLO
            )
            fused.append(fs)
            
        salient_boxes = saliency_map.bounding_boxes
        for i, box in enumerate(salient_boxes):
            # If saliency box heavily overlaps with a YOLO box, skip it to avoid duplicates
            is_duplicate = False
            for y_sub in fused:
                yx = y_sub.bounding_box.x
                yy = y_sub.bounding_box.y
                yw = y_sub.bounding_box.width
                yh = y_sub.bounding_box.height
                
                # simple IoU approx or containment
                if (box.x >= yx and box.y >= yy and 
                    (box.x+box.width) <= (yx+yw) and 
                    (box.y+box.height) <= (yy+yh)):
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                fs = FusedSubject(
                    subject_id=f"sal_{i}",
                    class_name="显著主体",
                    confidence=saliency_map.max_salient_score,
                    bounding_box=box,
                    is_primary_subject=False,
                    source=SourceType.SALIENCY
                )
                fused.append(fs)
                
        # Determine primary subject by area * confidence
        # For Saliency, area is a huge factor. For YOLO, class confidence is a huge factor.
        best_score = -1
        best_idx = -1
        best_area = -1
        
        for i, s in enumerate(fused):
            area = s.bounding_box.width * s.bounding_box.height
            # YOLO subjects get a bit of a boost, Saliency subjects rely heavily on area
            weight = 1.0 if s.source == SourceType.SALIENCY else 1.5
            
            # Simple heuristic score
            score = (area / img_area) * s.confidence * weight
            
            # Conflict resolution: if scores are very close (< 5% diff), pick the strictly larger bounding box
            if abs(score - best_score) < 0.05 and best_idx != -1:
                if area > best_area:
                    best_score = score
                    best_idx = i
                    best_area = area
            elif score > best_score:
                best_score = score
                best_idx = i
                best_area = area
                
        if best_idx >= 0:
            fused[best_idx].is_primary_subject = True
            
        return fused
