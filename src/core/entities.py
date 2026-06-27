from enum import Enum
from typing import List, Optional, Any, Tuple
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    MOVE_LEFT = "MoveLeft"
    MOVE_RIGHT = "MoveRight"
    MOVE_CLOSER = "MoveCloser"
    MOVE_BACK = "MoveBack"
    TILT_UP = "TiltUp"
    TILT_DOWN = "TiltDown"
    ROTATE = "Rotate"
    NONE = "None"

class CoachingLevel(str, Enum):
    OFF = "OFF"
    MINIMAL = "MINIMAL"
    COACH = "COACH"
    PRO = "PRO"


class PriorityLevel(int, Enum):
    HARD_ERROR = 1
    SUBJECT = 2
    INTERFERENCE = 3
    OPTIMIZATION = 4
    STYLE = 5

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class Keypoint(BaseModel):
    x: float
    y: float
    confidence: float

class Point(BaseModel):
    x: float
    y: float

class Line(BaseModel):
    p1: Point
    p2: Point

class DetectedSubject(BaseModel):
    subject_id: str
    class_name: str
    confidence: float
    bounding_box: BoundingBox
    keypoints: Optional[List[Keypoint]] = None
    is_primary_subject: bool = False

class SourceType(str, Enum):
    YOLO = "YOLO"
    SALIENCY = "SALIENCY"
    FUSED = "FUSED"

class FusedSubject(DetectedSubject):
    source: SourceType = SourceType.FUSED

class SaliencyMap(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    heatmap: Any  # numpy array
    bounding_boxes: List[BoundingBox] = Field(default_factory=list)
    max_salient_score: float = 0.0



class CompositionScore(BaseModel):
    total_score: int
    subject_score: int
    structure_score: int
    balance_score: int
    interference_score: int
    style_score: int

class Feedback(BaseModel):
    priority_level: PriorityLevel
    action_type: ActionType
    message: str
    target_point: Optional[Point] = None

class CropStyle(str, Enum):
    RULE_OF_THIRDS = "RuleOfThirds"
    CENTERED = "Centered"
    SOCIAL_VERTICAL = "SocialVertical"

class CropRecommendation(BaseModel):
    crop_style: CropStyle
    bounding_box: BoundingBox
    reasoning: str



class AestheticsMetrics(BaseModel):
    brightness_level: float = 0.0
    is_overexposed: bool = False
    is_underexposed: bool = False
    is_severe_backlight: bool = False
    color_harmony_score: float = 1.0
    background_clutter_score: float = 0.0
    is_background_cluttered: bool = False
    lighting_feedback: str = ""

class TrackedSubject(DetectedSubject):
    track_id: int
    history: List[BoundingBox] = Field(default_factory=list)
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    will_intersect_composition_node: bool = False
    time_to_intersection: float = 0.0

class AICoachingResult(BaseModel):
    advice_text: str = ""
    timestamp: float = 0.0
    duration: float = 10.0
    is_error: bool = False
    interaction_type: str = "PROACTIVE_POPUP"
    target_box: Optional[Tuple[int, int, int, int]] = None
    directional_arrows: List[str] = Field(default_factory=list)
    active_template: str = "Default"
    perfect_alignment: bool = False

    def is_active(self, current_time: float) -> bool:
        return (current_time - self.timestamp) <= self.duration

class InteractionType(str, Enum):
    PROACTIVE_VOICE = "PROACTIVE_VOICE"
    PROACTIVE_POPUP = "PROACTIVE_POPUP"
    REACTIVE_CHAT = "REACTIVE_CHAT"

class AIInteraction(BaseModel):
    timestamp: float
    message: str
    type: InteractionType
    acknowledged: bool = False

class SceneContext(BaseModel):
    scene_type: str = ""
    lighting_condition: str = ""
    recommended_iso: int = 0
    recommended_shutter: str = ""
    proactive_advice: str = ""
    confidence: float = 0.0
    timestamp: float = 0.0

class AnalysisResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    image_with_overlays: Any = None # Can be numpy array or path
    feedback_message: str
    score: 'CompositionScore'
    recommended_crops: List[CropRecommendation] = Field(default_factory=list)
    subjects: List[DetectedSubject] = Field(default_factory=list)
    aesthetics: Optional[AestheticsMetrics] = None
    tracked_subjects: List[TrackedSubject] = Field(default_factory=list)
    shutter_opportunity: bool = False
    ai_coaching: Optional[AICoachingResult] = None
    current_scene_context: Optional[SceneContext] = None
    active_interactions: List[AIInteraction] = Field(default_factory=list)
    debug_data: dict = Field(default_factory=dict)
