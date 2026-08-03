from src.core.entities import CompositionMode


ANALYSIS_MAX_EDGE = 320
ORIENTATION_BINS = 18
ENTER_SCORE = 65.0
EXIT_SCORE = 55.0
DISPLAY_ENTER_SCORE = 35.0
DISPLAY_EXIT_SCORE = 25.0
WEIGHT_CONFIG_VERSION = "reviewed-calibration-v3"
MODE_ENTER_SCORES = {
    CompositionMode.RULE_OF_THIRDS: 59.46,
    CompositionMode.DYNAMIC_SYMMETRY: 50.86,
    CompositionMode.BALANCED: 78.85,
    CompositionMode.TRIANGLE: 65.93,
    CompositionMode.DIAGONAL: 21.22,
    CompositionMode.HORIZONTAL: 75.0,
    CompositionMode.OBLIQUE: 44.72,
    CompositionMode.CURVE: 35.46,
    CompositionMode.RADIAL: 49.49,
    CompositionMode.CHECKERBOARD: 38.0,
    CompositionMode.CENTRIPETAL: 17.65,
    CompositionMode.TUNNEL: 36.34,
    CompositionMode.FRAME_WITHIN_FRAME: 95.85,
    CompositionMode.CROSS: 46.13,
    CompositionMode.VERTICAL: 23.38,
}
MODE_EXIT_SCORES = {
    CompositionMode.RULE_OF_THIRDS: 49.46,
    CompositionMode.DYNAMIC_SYMMETRY: 40.86,
    CompositionMode.BALANCED: 68.85,
    CompositionMode.TRIANGLE: 55.93,
    CompositionMode.DIAGONAL: 11.22,
    CompositionMode.HORIZONTAL: 65.0,
    CompositionMode.OBLIQUE: 34.72,
    CompositionMode.CURVE: 25.46,
    CompositionMode.RADIAL: 39.49,
    CompositionMode.CHECKERBOARD: 28.0,
    CompositionMode.CENTRIPETAL: 7.65,
    CompositionMode.TUNNEL: 26.34,
    CompositionMode.FRAME_WITHIN_FRAME: 85.85,
    CompositionMode.CROSS: 36.13,
    CompositionMode.VERTICAL: 13.38,
}
MODE_DISPLAY_ENTER_SCORES = {mode: DISPLAY_ENTER_SCORE for mode in CompositionMode}
MODE_DISPLAY_ENTER_SCORES[CompositionMode.TRIANGLE] = 28.0
MODE_DISPLAY_EXIT_SCORES = {
    mode: max(10.0, score - 10.0)
    for mode, score in MODE_DISPLAY_ENTER_SCORES.items()
}
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
        "missing_intersection": 0.55,
    },
    CompositionMode.VERTICAL: {"dominance": 0.65, "coverage": 0.35},
}
MIN_VISIBLE_CONFIDENCE = 0.45
INSUFFICIENT_EVIDENCE_QUALITY = 0.18
MIN_LINE_LENGTH_RATIO = 0.16
MAX_LINE_GAP_RATIO = 0.03
SCENE_CHANGE_THRESHOLD = 5.0
TOP_MODE_RANKING_BONUS: dict[CompositionMode, float] = {
    CompositionMode.CENTRIPETAL: 25.0,
    CompositionMode.RADIAL: 25.0,
    CompositionMode.CROSS: 25.0,
    CompositionMode.DIAGONAL: 25.0,
    CompositionMode.CURVE: 25.0,
    CompositionMode.VERTICAL: 25.0,
}


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
