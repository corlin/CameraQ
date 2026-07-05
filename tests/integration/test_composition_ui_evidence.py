import json
import subprocess
import sys
from pathlib import Path

import cv2

from scripts.render_composition_ui_evidence import render_ui_evidence


ROOT = Path(__file__).resolve().parents[2]


def test_render_ui_evidence_produces_all_non_camera_validation_states(tmp_path):
    outputs = render_ui_evidence(tmp_path)

    assert set(outputs) == {"minimal", "coach", "pro", "disabled", "sidebar", "report"}
    for state in ("minimal", "coach", "pro", "disabled", "sidebar"):
        image = cv2.imread(str(outputs[state]))
        assert image is not None
        assert image.shape[:2] == (720, 1280)

    report = json.loads(outputs["report"].read_text())
    assert report["uses_camera_frame"] is False
    assert report["minimal"]["composition_lines"] == 1
    assert report["coach"]["composition_lines"] == 3
    assert report["coach"]["has_recommendation"] is True
    assert report["pro"]["evidence_lines"] >= 1
    assert report["disabled"]["composition_lines"] == 0
    assert report["sidebar"]["composition_controls"] == [
        "clear_composition_diagnostics",
        "composition_analysis_interval_s_minus",
        "composition_analysis_interval_s_plus",
        "composition_detection_enabled",
        "composition_diagnostics_enabled",
    ]


def test_ui_evidence_script_runs_directly_from_repository_root(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_composition_ui_evidence.py",
            "--output",
            str(tmp_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "generated 5 UI images" in result.stdout
