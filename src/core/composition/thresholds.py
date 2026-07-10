from src.core.entities import CompositionMode


ANALYSIS_MAX_EDGE = 320
ORIENTATION_BINS = 18
ENTER_SCORE = 65.0
EXIT_SCORE = 55.0
DISPLAY_ENTER_SCORE = 45.0
DISPLAY_EXIT_SCORE = 35.0
WEIGHT_CONFIG_VERSION = "initial-rule-weights-v1"
MODE_ENTER_SCORES = {mode: ENTER_SCORE for mode in CompositionMode}
MODE_EXIT_SCORES = {mode: EXIT_SCORE for mode in CompositionMode}
MODE_DISPLAY_ENTER_SCORES = {mode: DISPLAY_ENTER_SCORE for mode in CompositionMode}
MODE_DISPLAY_EXIT_SCORES = {mode: DISPLAY_EXIT_SCORE for mode in CompositionMode}
MODE_EVIDENCE_WEIGHTS: dict[CompositionMode, dict[str, float]] = {
    CompositionMode.RULE_OF_THIRDS: {"node": 1.0, "line": 0.82},
    CompositionMode.DYNAMIC_SYMMETRY: {"line": 0.70, "focus": 0.30},
    CompositionMode.BALANCED: {"centroid": 1.0, "mass_symmetry": 1.0},
    CompositionMode.TRIANGLE: {"area": 1.0},
    CompositionMode.DIAGONAL: {"dominance": 0.65, "coverage": 0.35},
    CompositionMode.HORIZONTAL: {"dominance": 0.65, "coverage": 0.35},
    CompositionMode.OBLIQUE: {"dominance": 0.65, "coverage": 0.35},
    CompositionMode.CURVE: {"complexity": 0.55, "shape": 0.45},
    CompositionMode.RADIAL: {"convergence": 1.0},
    CompositionMode.CHECKERBOARD: {"families": 0.65, "intersections": 0.35, "sparse": 0.25},
    CompositionMode.CENTRIPETAL: {"convergence": 0.45, "focus": 0.55},
    CompositionMode.TUNNEL: {"depth": 1.0, "nesting": 1.0},
    CompositionMode.FRAME_WITHIN_FRAME: {"enclosure": 1.0},
    CompositionMode.CROSS: {
        "dominance": 0.65,
        "coverage": 0.35,
        "intersection": 1.0,
        "missing_intersection": 0.45,
    },
    CompositionMode.VERTICAL: {"dominance": 0.65, "coverage": 0.35},
}
MIN_VISIBLE_CONFIDENCE = 0.45
INSUFFICIENT_EVIDENCE_QUALITY = 0.18
MIN_LINE_LENGTH_RATIO = 0.16
MAX_LINE_GAP_RATIO = 0.03


def enter_score(mode: CompositionMode) -> float:
    return MODE_ENTER_SCORES[mode]


def exit_score(mode: CompositionMode) -> float:
    return MODE_EXIT_SCORES[mode]


def display_enter_score(mode: CompositionMode) -> float:
    return MODE_DISPLAY_ENTER_SCORES[mode]


def display_exit_score(mode: CompositionMode) -> float:
    return MODE_DISPLAY_EXIT_SCORES[mode]


def evidence_weight(mode: CompositionMode, component: str) -> float:
    return MODE_EVIDENCE_WEIGHTS[mode][component]
