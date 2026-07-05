import json
from pathlib import Path

from src.core.entities import CompositionMode


def test_json_contract_matches_public_mode_enum_and_excludes_images():
    contract_path = Path("specs/014-composition-pattern-recognition/contracts/composition-analysis.schema.json")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert set(contract["$defs"]["mode"]["enum"]) == {mode.value for mode in CompositionMode}
    serialized = json.dumps(contract).lower()
    assert "image_bytes" not in serialized
    assert "raw_frame" not in serialized


def test_contract_requires_analysis_fields():
    contract = json.loads(
        Path("specs/014-composition-pattern-recognition/contracts/composition-analysis.schema.json").read_text()
    )
    assert set(contract["required"]) == {
        "analysis_version",
        "timestamp",
        "frame_width",
        "frame_height",
        "evidence_quality",
        "mode_results",
        "top_modes",
        "recommendation",
        "insufficient_evidence",
        "processing_time_ms",
    }
