import json
from urllib.error import HTTPError, URLError

import cv2
import numpy as np
import pytest

from src.core.entities import CompositionMode
from tests.fixtures.composition.curate_commons_cases import (
    CURATION_SPECS,
    _download_and_normalize,
    _request_json,
    case_from_page,
    curate_mode,
    curate_rule_of_thirds,
    deduplicate_manifest,
    license_is_redistributable,
    merge_duplicate_source_cases,
    reproject_existing_categories,
    strip_html,
)


def test_curator_specs_cover_all_composition_modes():
    assert {spec.label for spec in CURATION_SPECS.values()} == {
        mode.value for mode in CompositionMode
    }


def test_commons_license_filter_allows_commercial_redistribution_and_rejects_nc_nd():
    assert license_is_redistributable("CC BY-SA 4.0")
    assert license_is_redistributable("CC0 1.0")
    assert license_is_redistributable("Public domain")
    assert not license_is_redistributable("CC BY-NC 4.0")
    assert not license_is_redistributable("CC BY-ND 4.0")
    assert not license_is_redistributable("")


def test_case_from_page_retains_attribution_and_uses_source_category_not_algorithm_label():
    page = {
        "pageid": 42,
        "title": "File:Example.jpg",
        "imageinfo": [
            {
                "thumburl": "https://upload.wikimedia.org/example.jpg",
                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Example.jpg",
                "extmetadata": {
                    "Artist": {"value": '<a href="/wiki/User:Example">Example Author</a>'},
                    "LicenseShortName": {"value": "CC BY-SA 4.0"},
                    "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"},
                    "Categories": {"value": "Rule of thirds|Landscape photographs"},
                },
            }
        ],
    }

    case = case_from_page(
        page,
        case_id="commons-rule-of-thirds-00",
        relative_path="images/real/commons-rule-of-thirds-00.jpg",
        category="Rule of thirds",
        labels=["RULE_OF_THIRDS"],
        negative_for=[],
    )

    assert case["author"] == "Example Author"
    assert case["license"] == "CC BY-SA 4.0"
    assert case["license_url"].endswith("/by-sa/4.0")
    assert case["annotation_source"] == "Wikimedia Commons human-curated category: Rule of thirds"
    assert case["review_status"] == "pending"
    assert case["modifications"] == "resized to maximum edge 320px; JPEG re-encoded"
    assert strip_html("<b>A &amp; B</b>") == "A & B"


def test_download_retries_rate_limit_and_reuses_completed_file(tmp_path, monkeypatch):
    ok, encoded = cv2.imencode(".jpg", np.zeros((20, 30, 3), dtype=np.uint8))
    assert ok

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return encoded.tobytes()

    calls = []

    def urlopen(*_args, **_kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise HTTPError("https://example.test/image", 429, "rate limited", {}, None)
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    output = tmp_path / "candidate.jpg"

    first_digest = _download_and_normalize("https://example.test/image", output)
    second_digest = _download_and_normalize("https://example.test/image", output)

    assert len(calls) == 2
    assert first_digest == second_digest


def test_download_retries_transient_url_error(tmp_path, monkeypatch):
    ok, encoded = cv2.imencode(".jpg", np.zeros((20, 30, 3), dtype=np.uint8))
    assert ok

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return encoded.tobytes()

    calls = []

    def urlopen(*_args, **_kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise URLError("temporary TLS EOF")
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    digest = _download_and_normalize("https://example.test/image", tmp_path / "candidate.jpg")

    assert len(calls) == 2
    assert len(digest) == 64


def test_metadata_request_retries_rate_limit(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return b'{"query": {"pages": []}}'

    calls = []

    def urlopen(*_args, **_kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise HTTPError("https://example.test/api", 429, "rate limited", {}, None)
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    assert _request_json({"action": "query"}) == {"query": {"pages": []}}
    assert len(calls) == 2


def test_curator_persists_completed_candidates_before_later_download_failure(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": "1.1", "labels": [], "required_counts": {}, "cases": []}))

    def page(page_id, category):
        return {
            "pageid": page_id,
            "title": f"File:{page_id}.jpg",
            "imageinfo": [
                {
                    "mime": "image/jpeg",
                    "thumburl": f"https://example.test/{page_id}.jpg",
                    "descriptionurl": f"https://commons.wikimedia.org/wiki/File:{page_id}.jpg",
                    "extmetadata": {
                        "Artist": {"value": "Example"},
                        "LicenseShortName": {"value": "CC BY 4.0"},
                        "LicenseUrl": {"value": "https://creativecommons.org/licenses/by/4.0"},
                        "Categories": {"value": category},
                    },
                }
            ],
        }

    monkeypatch.setattr(
        "tests.fixtures.composition.curate_commons_cases._category_pages",
        lambda category, limit: [page(1 if category == "Rule of thirds" else 2, category)],
    )
    calls = []

    def download(_url, path):
        calls.append(path)
        if len(calls) == 2:
            raise HTTPError("https://example.test/2.jpg", 429, "rate limited", {}, None)
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), np.zeros((20, 30, 3), dtype=np.uint8))
        return "a" * 64

    monkeypatch.setattr(
        "tests.fixtures.composition.curate_commons_cases._download_and_normalize", download
    )

    with pytest.raises(HTTPError):
        curate_rule_of_thirds(manifest, count=1, download_delay_s=0)

    saved = json.loads(manifest.read_text())["cases"]
    assert [case["id"] for case in saved] == ["commons-rule-of-thirds-positive-00"]


def test_mode_curator_preserves_other_commons_attribution_and_writes_mode_contact_sheets(
    tmp_path, monkeypatch
):
    existing = {
        "id": "commons-rule-of-thirds-positive-00",
        "path": "images/real_candidates/commons-rule-of-thirds-positive-00.jpg",
        "source": "Wikimedia Commons",
        "source_title": "File:Existing.jpg",
        "provenance_url": "https://commons.wikimedia.org/wiki/File:Existing.jpg",
        "author": "Existing Author",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0",
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "labels": ["TUNNEL"],
                "required_counts": {},
                "cases": [existing],
            }
        )
    )

    def page(page_id, category):
        return {
            "pageid": page_id,
            "title": f"File:{page_id}.jpg",
            "imageinfo": [
                {
                    "mime": "image/jpeg",
                    "thumburl": f"https://example.test/{page_id}.jpg",
                    "descriptionurl": f"https://commons.wikimedia.org/wiki/File:{page_id}.jpg",
                    "extmetadata": {
                        "Artist": {"value": "New Author"},
                        "LicenseShortName": {"value": "CC BY 4.0"},
                        "LicenseUrl": {
                            "value": "https://creativecommons.org/licenses/by/4.0"
                        },
                        "Categories": {"value": category},
                    },
                }
            ],
        }

    monkeypatch.setattr(
        "tests.fixtures.composition.curate_commons_cases._category_pages",
        lambda category, limit: [page(10 if "Centered" in category else 11, category)],
    )

    def download(_url, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), np.zeros((20, 30, 3), dtype=np.uint8))
        return "b" * 64

    monkeypatch.setattr(
        "tests.fixtures.composition.curate_commons_cases._download_and_normalize", download
    )

    cases = curate_mode(
        manifest, CURATION_SPECS["tunnel"], count=1, download_delay_s=0
    )

    assert len(cases) == 2
    saved = json.loads(manifest.read_text())["cases"]
    assert saved[0]["id"] == existing["id"]
    assert {case["id"] for case in saved[1:]} == {
        "commons-tunnel-positive-00",
        "commons-tunnel-negative-00",
    }
    attribution = (tmp_path / "ATTRIBUTION.md").read_text()
    assert existing["id"] in attribution
    assert "commons-tunnel-positive-00" in attribution
    assert (tmp_path / "review/commons-tunnel-positive.jpg").is_file()
    assert (tmp_path / "review/commons-tunnel-negative.jpg").is_file()


def test_duplicate_source_cases_merge_multilabel_truth_without_double_counting():
    cases = [
        {
            "id": "first",
            "source": "Wikimedia Commons",
            "source_item_id": "42",
            "kind": "hard_negative",
            "labels": [],
            "negative_for": ["RULE_OF_THIRDS"],
        },
        {
            "id": "duplicate",
            "source": "Wikimedia Commons",
            "source_item_id": "42",
            "kind": "hard_negative",
            "labels": [],
            "negative_for": ["DIAGONAL"],
        },
    ]

    merged = merge_duplicate_source_cases(cases)

    assert len(merged) == 1
    assert merged[0]["id"] == "first"
    assert merged[0]["negative_for"] == ["DIAGONAL", "RULE_OF_THIRDS"]


def test_manifest_deduplication_rebuilds_mode_contact_sheet_from_merged_truth(tmp_path):
    image_dir = tmp_path / "images/real_candidates"
    image_dir.mkdir(parents=True)
    image_path = image_dir / "first.jpg"
    cv2.imwrite(str(image_path), np.zeros((20, 30, 3), dtype=np.uint8))
    common = {
        "source": "Wikimedia Commons",
        "source_item_id": "42",
        "kind": "hard_negative",
        "labels": [],
        "source_title": "File:Example.jpg",
        "provenance_url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
        "author": "Example",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0",
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        **common,
                        "id": "first",
                        "path": "images/real_candidates/first.jpg",
                        "negative_for": ["RULE_OF_THIRDS"],
                    },
                    {
                        **common,
                        "id": "duplicate",
                        "path": "images/real_candidates/duplicate.jpg",
                        "negative_for": ["DIAGONAL"],
                    },
                ]
            }
        )
    )

    assert deduplicate_manifest(manifest) == 1
    assert (tmp_path / "review/commons-diagonal-negative.jpg").is_file()
    assert (tmp_path / "review/commons-rule-of-thirds-negative.jpg").is_file()


def test_curator_reuses_existing_source_as_multilabel_case_without_redownloading(
    tmp_path, monkeypatch
):
    existing_path = tmp_path / "images/real_candidates/existing.jpg"
    existing_path.parent.mkdir(parents=True)
    cv2.imwrite(str(existing_path), np.zeros((20, 30, 3), dtype=np.uint8))
    existing = {
        "id": "existing",
        "path": "images/real_candidates/existing.jpg",
        "source": "Wikimedia Commons",
        "source_item_id": "10",
        "source_title": "File:10.jpg",
        "provenance_url": "https://commons.wikimedia.org/wiki/File:10.jpg",
        "author": "Example",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0",
        "kind": "positive",
        "labels": ["RULE_OF_THIRDS"],
        "negative_for": [],
        "annotation_source": "Wikimedia Commons human-curated category: Rule of thirds",
        "source_categories": ["Rule of thirds"],
        "review_status": "pending",
        "split": "acceptance",
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"cases": [existing]}))

    def page(page_id, category):
        return {
            "pageid": page_id,
            "title": f"File:{page_id}.jpg",
            "imageinfo": [
                {
                    "mime": "image/jpeg",
                    "thumburl": f"https://example.test/{page_id}.jpg",
                    "descriptionurl": f"https://commons.wikimedia.org/wiki/File:{page_id}.jpg",
                    "extmetadata": {
                        "Artist": {"value": "Example"},
                        "LicenseShortName": {"value": "CC BY 4.0"},
                        "LicenseUrl": {
                            "value": "https://creativecommons.org/licenses/by/4.0"
                        },
                        "Categories": {"value": category},
                    },
                }
            ],
        }

    monkeypatch.setattr(
        "tests.fixtures.composition.curate_commons_cases._category_pages",
        lambda category, limit: [page(10 if "Centered tunnel" in category else 11, category)],
    )
    downloads = []

    def download(_url, path):
        downloads.append(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), np.zeros((20, 30, 3), dtype=np.uint8))
        return "c" * 64

    monkeypatch.setattr(
        "tests.fixtures.composition.curate_commons_cases._download_and_normalize", download
    )

    curate_mode(manifest, CURATION_SPECS["tunnel"], count=1, download_delay_s=0)

    saved = json.loads(manifest.read_text())["cases"]
    reused = next(case for case in saved if case["id"] == "existing")
    assert reused["labels"] == ["RULE_OF_THIRDS", "TUNNEL"]
    assert "Centered tunnel perspective" in reused["annotation_source"]
    assert len(downloads) == 1


def test_curator_bounds_new_downloads_for_polite_resumable_batches(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"cases": []}))

    def page(page_id, category):
        return {
            "pageid": page_id,
            "title": f"File:{page_id}.jpg",
            "imageinfo": [
                {
                    "mime": "image/jpeg",
                    "thumburl": f"https://example.test/{page_id}.jpg",
                    "descriptionurl": f"https://commons.wikimedia.org/wiki/File:{page_id}.jpg",
                    "extmetadata": {
                        "Artist": {"value": "Example"},
                        "LicenseShortName": {"value": "CC BY 4.0"},
                        "LicenseUrl": {
                            "value": "https://creativecommons.org/licenses/by/4.0"
                        },
                        "Categories": {"value": category},
                    },
                }
            ],
        }

    monkeypatch.setattr(
        "tests.fixtures.composition.curate_commons_cases._category_pages",
        lambda category, limit: [page(1, category), page(2, category)],
    )
    downloads = []

    def download(_url, path):
        downloads.append(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), np.zeros((20, 30, 3), dtype=np.uint8))
        return "d" * 64

    monkeypatch.setattr(
        "tests.fixtures.composition.curate_commons_cases._download_and_normalize", download
    )

    curate_mode(
        manifest,
        CURATION_SPECS["horizontal"],
        count=2,
        max_new_downloads=1,
        download_delay_s=0,
    )

    assert len(downloads) == 1
    assert len(json.loads(manifest.read_text())["cases"]) == 1


def test_reproject_existing_categories_adds_cross_mode_truth_without_network(tmp_path):
    image_dir = tmp_path / "images/real_candidates"
    image_dir.mkdir(parents=True)
    image_path = image_dir / "horizontal.jpg"
    cv2.imwrite(str(image_path), np.zeros((20, 30, 3), dtype=np.uint8))
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "horizontal",
                        "path": "images/real_candidates/horizontal.jpg",
                        "source": "Wikimedia Commons",
                        "source_item_id": "42",
                        "source_title": "File:Horizontal.jpg",
                        "provenance_url": "https://commons.wikimedia.org/wiki/File:Horizontal.jpg",
                        "author": "Example",
                        "license": "CC BY 4.0",
                        "license_url": "https://creativecommons.org/licenses/by/4.0",
                        "kind": "positive",
                        "labels": ["HORIZONTAL"],
                        "negative_for": [],
                        "source_categories": ["Horizontal lines"],
                        "annotation_source": "Wikimedia Commons human-curated category: Horizontal lines",
                        "review_status": "accepted",
                        "reviewer": "Reviewer",
                        "review_notes": "Previously reviewed",
                    }
                ]
            }
        )
    )

    changed = reproject_existing_categories(manifest)

    assert changed == 1
    saved = json.loads(manifest.read_text())["cases"][0]
    assert saved["labels"] == ["HORIZONTAL"]
    assert saved["negative_for"] == ["OBLIQUE", "VERTICAL"]
    assert saved["review_status"] == "pending"
    assert "reviewer" not in saved
    assert (tmp_path / "review/commons-oblique-negative.jpg").is_file()
    assert (tmp_path / "review/commons-vertical-negative.jpg").is_file()


def test_resuming_same_mode_preserves_cross_mode_truth_without_redownloading(
    tmp_path, monkeypatch
):
    image_dir = tmp_path / "images/real_candidates"
    image_dir.mkdir(parents=True)

    def existing(case_id, page_id, category, labels, negative_for):
        path = image_dir / f"{case_id}.jpg"
        cv2.imwrite(str(path), np.zeros((20, 30, 3), dtype=np.uint8))
        return {
            "id": case_id,
            "path": f"images/real_candidates/{case_id}.jpg",
            "source": "Wikimedia Commons",
            "source_item_id": str(page_id),
            "source_title": f"File:{page_id}.jpg",
            "provenance_url": f"https://commons.wikimedia.org/wiki/File:{page_id}.jpg",
            "author": "Example",
            "license": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0",
            "kind": "positive" if labels else "hard_negative",
            "labels": labels,
            "negative_for": negative_for,
            "source_categories": [category],
            "annotation_source": f"Wikimedia Commons human-curated category: {category}",
            "review_status": "pending",
            "split": "acceptance",
        }

    positive = existing(
        "commons-horizontal-positive-00",
        1,
        "Horizontal lines",
        ["HORIZONTAL"],
        ["OBLIQUE", "VERTICAL"],
    )
    negative = existing(
        "commons-horizontal-negative-00",
        2,
        "Vertical lines",
        ["VERTICAL"],
        ["HORIZONTAL"],
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"cases": [positive, negative]}))

    def page(case, category):
        return {
            "pageid": int(case["source_item_id"]),
            "title": case["source_title"],
            "imageinfo": [
                {
                    "mime": "image/jpeg",
                    "thumburl": f"https://example.test/{case['source_item_id']}.jpg",
                    "descriptionurl": case["provenance_url"],
                    "extmetadata": {
                        "Artist": {"value": "Example"},
                        "LicenseShortName": {"value": "CC BY 4.0"},
                        "LicenseUrl": {"value": case["license_url"]},
                        "Categories": {"value": category},
                    },
                }
            ],
        }

    monkeypatch.setattr(
        "tests.fixtures.composition.curate_commons_cases._category_pages",
        lambda category, limit: [
            page(positive if category == "Horizontal lines" else negative, category)
        ],
    )
    monkeypatch.setattr(
        "tests.fixtures.composition.curate_commons_cases._download_and_normalize",
        lambda *_args, **_kwargs: pytest.fail("cached same-mode candidates must not redownload"),
    )

    curate_mode(
        manifest,
        CURATION_SPECS["horizontal"],
        count=1,
        max_new_downloads=0,
        download_delay_s=0,
    )

    saved = json.loads(manifest.read_text())["cases"]
    assert len(saved) == 2
    resumed_positive = next(case for case in saved if case["source_item_id"] == "1")
    assert resumed_positive["labels"] == ["HORIZONTAL"]
    assert resumed_positive["negative_for"] == ["OBLIQUE", "VERTICAL"]
