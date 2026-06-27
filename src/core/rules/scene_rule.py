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
            
        return feedback_list
