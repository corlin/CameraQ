import json
from collections import Counter

from tests.fixtures.composition.generate_acceptance_cases import generate_cases


def test_generated_acceptance_cases_have_required_counts_pairs_and_stable_files(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "labels": [],
                "required_counts": {},
                "cases": [{"id": "real-case-placeholder", "kind": "positive"}],
            }
        )
    )

    generated = generate_cases(manifest_path)

    assert len(generated) == 150
    kinds = Counter(case["kind"] for case in generated)
    assert kinds == {"degraded": 100, "recommendation": 50}
    degraded = Counter(case["degradation_category"] for case in generated if case["kind"] == "degraded")
    assert degraded == {"low_information": 25, "blur": 25, "solid_color": 25, "exposure": 25}
    action_groups = Counter(
        case["recommendation_action_group"]
        for case in generated
        if case["kind"] == "recommendation"
    )
    assert action_groups == {"translation": 15, "rotation": 15, "closer": 10, "back": 10}
    for case in generated:
        assert len(case["sha256"]) == 64
        assert (tmp_path / case["path"]).is_file()
        if case["kind"] == "recommendation":
            assert len(case["after_sha256"]) == 64
            assert (tmp_path / case["after_path"]).is_file()
            if case["recommendation_action_group"] in {"translation", "rotation"}:
                assert case["subject_box_before"] is not None
                assert case["subject_box_before"][2] * case["subject_box_before"][3] >= 0.08

    payload = json.loads(manifest_path.read_text())
    assert payload["cases"][0]["id"] == "real-case-placeholder"
    assert len(payload["cases"]) == 151

    rerun = generate_cases(manifest_path)
    assert rerun == generated
    assert len(json.loads(manifest_path.read_text())["cases"]) == 151
