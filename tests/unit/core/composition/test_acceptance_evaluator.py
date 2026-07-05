import json

from tests.fixtures.composition.evaluate_acceptance import evaluate_manifest
from tests.fixtures.composition.generate_acceptance_cases import generate_cases


def test_evaluator_measures_generated_degradation_and_recommendation_sets(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "labels": [],
                "required_counts": {},
                "cases": [],
            }
        )
    )
    generate_cases(manifest_path)

    report = evaluate_manifest(manifest_path)

    assert report.degraded_total == 100
    assert report.degraded_abstentions == 100
    assert report.degraded_abstention_rate == 1.0
    assert report.recommendation_total == 50
    assert report.recommendation_improvements == 50
    assert report.recommendation_improvement_rate == 1.0
    assert report.recommendation_action_matches == 50
    assert report.recommendation_action_match_rate == 1.0
