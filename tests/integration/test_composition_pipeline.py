import json
import os
import time

from src.core.composition.diagnostics import CompositionDiagnostics
from src.core.composition.engine import CompositionEngine
from tests.fixtures.composition.factory import line_image


def analysis():
    return CompositionEngine().analyze(line_image((0,)), [], None, timestamp=1.0)


def test_diagnostics_default_to_memory_only_and_bound_the_buffer(tmp_path):
    diagnostics = CompositionDiagnostics(directory=tmp_path, enabled=False, max_records=3)
    item = analysis()
    for _ in range(5):
        diagnostics.add(item)
    assert len(diagnostics.records) == 3
    assert list(tmp_path.glob("*.ndjson")) == []


def test_opt_in_ndjson_contains_no_raw_frame_and_can_be_cleared(tmp_path):
    diagnostics = CompositionDiagnostics(directory=tmp_path, enabled=True, max_file_bytes=10_000)
    diagnostics.add(analysis())
    files = list(tmp_path.glob("*.ndjson"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text().splitlines()[0])
    serialized = json.dumps(payload).lower()
    assert "raw_frame" not in serialized
    assert "image_bytes" not in serialized
    diagnostics.clear()
    assert diagnostics.records == []
    assert list(tmp_path.glob("*.ndjson")) == []


def test_diagnostics_rotate_files_and_remove_expired_files(tmp_path):
    expired = tmp_path / "expired.ndjson"
    expired.write_text("{}\n")
    old = time.time() - 9 * 24 * 60 * 60
    os.utime(expired, (old, old))
    diagnostics = CompositionDiagnostics(directory=tmp_path, enabled=True, max_file_bytes=300)
    for _ in range(8):
        diagnostics.add(analysis())
    assert not expired.exists()
    assert len(list(tmp_path.glob("*.ndjson"))) >= 2


def test_composition_pipeline_is_offline_and_serializable(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = analysis()
    payload = result.model_dump(mode="json")
    assert len(payload["mode_results"]) == 15
    assert "image" not in json.dumps(payload).lower()
