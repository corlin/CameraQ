from enum import Enum
from typing import List, Optional, Any, Tuple
from pydantic import BaseModel, Field, model_validator

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
    histogram_clipping: Optional[str] = None
    lighting_direction: Optional[str] = None
    color_contrast_low: bool = False
    vanishing_point_aligned: bool = False

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


class CompositionMode(str, Enum):
    RULE_OF_THIRDS = "RULE_OF_THIRDS"
    DYNAMIC_SYMMETRY = "DYNAMIC_SYMMETRY"
    BALANCED = "BALANCED"
    TRIANGLE = "TRIANGLE"
    DIAGONAL = "DIAGONAL"
    HORIZONTAL = "HORIZONTAL"
    OBLIQUE = "OBLIQUE"
    CURVE = "CURVE"
    RADIAL = "RADIAL"
    CHECKERBOARD = "CHECKERBOARD"
    CENTRIPETAL = "CENTRIPETAL"
    TUNNEL = "TUNNEL"
    FRAME_WITHIN_FRAME = "FRAME_WITHIN_FRAME"
    CROSS = "CROSS"
    VERTICAL = "VERTICAL"


class CompositionConfidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CompositionEvidenceType(str, Enum):
    SUBJECT_POSITION = "SUBJECT_POSITION"
    SALIENCY_FOCUS = "SALIENCY_FOCUS"
    LINE = "LINE"
    LINE_INTERSECTION = "LINE_INTERSECTION"
    CONTOUR = "CONTOUR"
    NESTED_CONTOUR = "NESTED_CONTOUR"
    VANISHING_POINT = "VANISHING_POINT"
    VISUAL_MASS = "VISUAL_MASS"
    REPETITION = "REPETITION"
    SYMMETRY = "SYMMETRY"
    CURVATURE = "CURVATURE"


class CompositionAction(str, Enum):
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    TILT_UP = "TILT_UP"
    TILT_DOWN = "TILT_DOWN"
    ROTATE_CLOCKWISE = "ROTATE_CLOCKWISE"
    ROTATE_COUNTERCLOCKWISE = "ROTATE_COUNTERCLOCKWISE"
    MOVE_CLOSER = "MOVE_CLOSER"
    MOVE_BACK = "MOVE_BACK"
    KEEP = "KEEP"


class NormalizedPoint(BaseModel):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)


class NormalizedLine(BaseModel):
    p1: NormalizedPoint
    p2: NormalizedPoint

    @model_validator(mode="after")
    def distinct_points(self):
        if self.p1 == self.p2:
            raise ValueError("line endpoints must differ")
        return self


class CompositionEvidence(BaseModel):
    evidence_type: CompositionEvidenceType
    strength: float = Field(ge=0.0, le=1.0)
    description: str = Field(min_length=1)
    points: List[NormalizedPoint] = Field(default_factory=list)
    lines: List[NormalizedLine] = Field(default_factory=list)
    contour: List[NormalizedPoint] = Field(default_factory=list)


class CompositionModeResult(BaseModel):
    mode: CompositionMode
    match_score: float = Field(ge=0.0, le=100.0)
    confidence: CompositionConfidence
    evidence: List[CompositionEvidence] = Field(default_factory=list)
    is_visible: bool = False
    stable_for_ms: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def visible_results_have_evidence(self):
        if self.is_visible and not self.evidence:
            raise ValueError("visible composition results require evidence")
        return self


class TargetCompositionRecommendation(BaseModel):
    target_mode: CompositionMode
    action: CompositionAction
    reason: str = Field(min_length=1)
    current_score: float = Field(ge=0.0, le=100.0)
    projected_score: float = Field(ge=0.0, le=100.0)
    adjustment_cost: float = Field(ge=0.0, le=1.0)
    priority: float = Field(ge=0.0, le=1.0)
    target_points: List[NormalizedPoint] = Field(default_factory=list)
    aligned: bool = False

    @model_validator(mode="after")
    def recommendation_is_coherent(self):
        if self.projected_score < self.current_score:
            raise ValueError("projected score cannot be lower than current score")
        if self.aligned and self.action is not CompositionAction.KEEP:
            raise ValueError("aligned recommendation must use KEEP")
        if self.action is not CompositionAction.KEEP and self.projected_score <= self.current_score:
            raise ValueError("directional recommendation must improve the score")
        return self


class CompositionAnalysis(BaseModel):
    analysis_version: str = "1.0"
    timestamp: float = Field(ge=0.0)
    frame_width: int = Field(gt=0)
    frame_height: int = Field(gt=0)
    evidence_quality: float = Field(ge=0.0, le=1.0)
    mode_results: List[CompositionModeResult]
    top_modes: List[CompositionMode] = Field(default_factory=list, max_length=3)
    recommendation: Optional[TargetCompositionRecommendation] = None
    insufficient_evidence: bool = False
    processing_time_ms: float = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_result_set(self):
        modes = [result.mode for result in self.mode_results]
        if len(modes) != len(CompositionMode) or set(modes) != set(CompositionMode):
            raise ValueError("mode_results must contain every composition mode exactly once")
        if len(set(self.top_modes)) != len(self.top_modes):
            raise ValueError("top_modes cannot contain duplicates")
        visible = {result.mode for result in self.mode_results if result.is_visible}
        if not set(self.top_modes).issubset(visible):
            raise ValueError("top_modes must reference visible results")
        if self.insufficient_evidence and self.recommendation:
            if self.recommendation.action is not CompositionAction.KEEP:
                raise ValueError("insufficient evidence forbids directional recommendations")
        return self

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
    composition_analysis: Optional[CompositionAnalysis] = None
    active_interactions: List[AIInteraction] = Field(default_factory=list)
    debug_data: dict = Field(default_factory=dict)
