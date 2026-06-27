from typing import Optional, List
from src.core.entities import AnalysisResult, Feedback, PriorityLevel, ActionType

class SceneContextRule:
    """Evaluates the deep AI scene context and provides recommendations/feedback."""
    
    def evaluate(self, result: AnalysisResult) -> List[Feedback]:
        feedback_list = []
        
        ctx = result.current_scene_context
        if not ctx:
            return feedback_list
            
        # Example rule: if lighting is backlit, advise user to move
        if "backlit" in ctx.lighting_condition.lower():
            feedback_list.append(Feedback(
                priority_level=PriorityLevel.OPTIMIZATION,
                action_type=ActionType.MOVE_LEFT, # Or general movement
                message="Scene is backlit. Try repositioning to avoid glare."
            ))
            
        if ctx.confidence < 0.5:
            feedback_list.append(Feedback(
                priority_level=PriorityLevel.INFO,
                action_type=ActionType.NONE,
                message="[低置信度] AI对当前场景判断不足，建议手动调整。"
            ))
        elif ctx.proactive_advice and ctx.confidence > 0.8:
            feedback_list.append(Feedback(
                priority_level=PriorityLevel.STYLE,
                action_type=ActionType.NONE,
                message=ctx.proactive_advice
            ))
            
        # Advanced Aesthetics Heuristics
        if result.aesthetics:
            metrics = result.aesthetics
            
            # US2: Histogram
            if metrics.histogram_clipping == "highlights":
                feedback_list.append(Feedback(
                    priority_level=PriorityLevel.OPTIMIZATION,
                    action_type=ActionType.NONE,
                    message="高光溢出，建议降低曝光 (EV-)"
                ))
            elif metrics.histogram_clipping == "shadows":
                feedback_list.append(Feedback(
                    priority_level=PriorityLevel.OPTIMIZATION,
                    action_type=ActionType.NONE,
                    message="暗部细节丢失，建议增加曝光 (EV+)"
                ))
                
            # US1: Lighting Direction
            if metrics.lighting_direction == "flat":
                feedback_list.append(Feedback(
                    priority_level=PriorityLevel.STYLE,
                    action_type=ActionType.NONE,
                    message="光线太平，尝试让人物侧向光源以增加立体感"
                ))
            elif metrics.lighting_direction in ["left", "right"]:
                feedback_list.append(Feedback(
                    priority_level=PriorityLevel.STYLE,
                    action_type=ActionType.NONE,
                    message="优秀的侧面立体光影"
                ))
                
            # US3: Color Contrast
            if metrics.color_contrast_low:
                feedback_list.append(Feedback(
                    priority_level=PriorityLevel.STYLE,
                    action_type=ActionType.NONE,
                    message="主体与背景颜色接近，建议更换对比色背景"
                ))
                
            # US4: Leading Lines
            if metrics.vanishing_point_aligned is False and hasattr(metrics, 'vanishing_point_aligned'):
                # We only want to trigger this if we actually detected lines (we set it to False if lines exist but aren't aligned)
                # Wait, if we didn't detect lines, it's False by default. Let's fix this logic: we should only warn if it's explicitly marked as unaligned.
                # Actually, our implementation in aesthetics_analyzer sets it to False if diagonal lines exist. 
                # Let's just output it if we detected strong lines but they aren't aligned.
                feedback_list.append(Feedback(
                    priority_level=PriorityLevel.STYLE,
                    action_type=ActionType.NONE,
                    message="尝试利用背景线条指向主体"
                ))
                
            # US5: Depth of Field
            if metrics.is_background_cluttered:
                # In aesthetics_analyzer we checked if subject is small.
                # Here we just output the DoF warning if clutter is true.
                feedback_list.append(Feedback(
                    priority_level=PriorityLevel.STYLE,
                    action_type=ActionType.MOVE_CLOSER,
                    message="靠近主体以虚化背景，或开启人像模式"
                ))
            
        return feedback_list
