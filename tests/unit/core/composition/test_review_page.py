import json

from tests.fixtures.composition.generate_review_page import generate_review_page


def test_review_page_preserves_work_and_blocks_silent_empty_export(tmp_path):
    image = tmp_path / "candidate.jpg"
    image.write_bytes(b"fixture")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "candidate-1",
                        "path": "candidate.jpg",
                        "source": "Wikimedia Commons",
                        "labels": ["HORIZONTAL"],
                        "negative_for": [],
                        "provenance_url": "https://example.test/source",
                        "source_title": "Example",
                        "license": "CC BY 4.0",
                        "review_status": "pending",
                    },
                    {
                        "id": "candidate-2",
                        "path": "candidate.jpg",
                        "source": "Wikimedia Commons",
                        "labels": ["VERTICAL"],
                        "negative_for": [],
                        "provenance_url": "https://example.test/source-2",
                        "source_title": "Example 2",
                        "license": "CC BY 4.0",
                        "review_status": "pending",
                    }
                ]
            }
        )
    )
    output = tmp_path / "review.html"

    assert generate_review_page(manifest, output) == 2
    document = output.read_text()

    assert "localStorage" in document
    assert "已决定" in document
    assert "缺少说明" in document
    assert "没有可导出的决定" in document
    assert "card.classList.add('invalid')" in document
    assert "if (decision !== 'pending' && !notes) return;" not in document
    assert all(line == line.rstrip() for line in document.splitlines())
