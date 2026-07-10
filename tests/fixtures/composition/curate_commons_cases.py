from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from pathlib import Path

import cv2
import numpy as np


API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "CameraQ/0.1 composition acceptance curation (local test fixtures)"
MAX_EDGE = 320


@dataclass(frozen=True)
class CurationSpec:
    slug: str
    label: str
    positive_category: str
    negative_category: str


CURATION_SPECS = {
    "rule-of-thirds": CurationSpec(
        slug="rule-of-thirds",
        label="RULE_OF_THIRDS",
        positive_category="Rule of thirds",
        negative_category="Centered objects",
    ),
    "diagonal": CurationSpec(
        slug="diagonal",
        label="DIAGONAL",
        positive_category="Diagonal images (left)",
        negative_category="Centered objects",
    ),
    "dynamic-symmetry": CurationSpec(
        slug="dynamic-symmetry",
        label="DYNAMIC_SYMMETRY",
        positive_category="Rabatment of the rectangle",
        negative_category="Symmetric images",
    ),
    "balanced": CurationSpec(
        slug="balanced",
        label="BALANCED",
        positive_category="Symmetric images",
        negative_category="Asymmetry",
    ),
    "triangle": CurationSpec(
        slug="triangle",
        label="TRIANGLE",
        positive_category="Triangles in art",
        negative_category="Cross-shaped objects",
    ),
    "horizontal": CurationSpec(
        slug="horizontal",
        label="HORIZONTAL",
        positive_category="Horizontal lines",
        negative_category="Vertical lines",
    ),
    "oblique": CurationSpec(
        slug="oblique",
        label="OBLIQUE",
        positive_category="Intentional camera tilt",
        negative_category="Horizontal lines",
    ),
    "curve": CurationSpec(
        slug="curve",
        label="CURVE",
        positive_category="Wavy lines",
        negative_category="Parallel lines",
    ),
    "radial": CurationSpec(
        slug="radial",
        label="RADIAL",
        positive_category="Rotational symmetry",
        negative_category="Concentric circles",
    ),
    "checkerboard": CurationSpec(
        slug="checkerboard",
        label="CHECKERBOARD",
        positive_category="Grids",
        negative_category="Parallel lines",
    ),
    "centripetal": CurationSpec(
        slug="centripetal",
        label="CENTRIPETAL",
        positive_category="Leading lines",
        negative_category="Centered objects",
    ),
    "cross": CurationSpec(
        slug="cross",
        label="CROSS",
        positive_category="Cross-shaped objects",
        negative_category="Y-shaped objects",
    ),
    "vertical": CurationSpec(
        slug="vertical",
        label="VERTICAL",
        positive_category="Vertical lines",
        negative_category="Horizontal lines",
    ),
    "frame-within-frame": CurationSpec(
        slug="frame-within-frame",
        label="FRAME_WITHIN_FRAME",
        positive_category="Views from frames",
        negative_category="Empty picture frames",
    ),
    "tunnel": CurationSpec(
        slug="tunnel",
        label="TUNNEL",
        positive_category="Centered tunnel perspective",
        negative_category="Tunnel portals",
    ),
}


def merge_duplicate_source_cases(cases: list[dict]) -> list[dict]:
    merged: list[dict] = []
    by_source: dict[tuple[str, str], dict] = {}
    for original in cases:
        case = dict(original)
        source_key = (str(case.get("source", "")), str(case.get("source_item_id", "")))
        if not all(source_key):
            merged.append(case)
            continue
        existing = by_source.get(source_key)
        if existing is None:
            by_source[source_key] = case
            merged.append(case)
            continue
        existing["labels"] = sorted(set(existing.get("labels", [])) | set(case.get("labels", [])))
        existing["negative_for"] = sorted(
            set(existing.get("negative_for", [])) | set(case.get("negative_for", []))
        )
        if existing["labels"]:
            existing["kind"] = "positive"
    return merged


def strip_html(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def license_is_redistributable(name: str) -> bool:
    normalized = name.upper().replace("-", " ")
    if not normalized or "NC" in normalized or "NONCOMMERCIAL" in normalized or "ND" in normalized:
        return False
    return any(token in normalized for token in ("CC BY", "CC0", "PUBLIC DOMAIN", "PDM"))


def _metadata(info: dict, key: str) -> str:
    return str(info.get("extmetadata", {}).get(key, {}).get("value", ""))


def case_from_page(
    page: dict,
    *,
    case_id: str,
    relative_path: str,
    category: str,
    labels: list[str],
    negative_for: list[str],
) -> dict:
    info = page["imageinfo"][0]
    return {
        "id": case_id,
        "path": relative_path,
        "kind": "positive" if labels else "hard_negative",
        "labels": labels,
        "negative_for": negative_for,
        "source": "Wikimedia Commons",
        "source_item_id": str(page["pageid"]),
        "source_title": page["title"],
        "provenance_url": info["descriptionurl"],
        "download_url": info["thumburl"],
        "author": strip_html(_metadata(info, "Artist")) or "Wikimedia Commons contributor",
        "license": _metadata(info, "LicenseShortName"),
        "license_url": _metadata(info, "LicenseUrl"),
        "annotation_source": f"Wikimedia Commons human-curated category: {category}",
        "source_categories": _metadata(info, "Categories").split("|"),
        "review_status": "pending",
        "split": "acceptance",
        "modifications": "resized to maximum edge 320px; JPEG re-encoded",
    }


def _request_json(parameters: dict) -> dict:
    url = API_URL + "?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt, fallback_delay in enumerate((10, 30, 60, 120)):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            retry_after = error.headers.get("Retry-After") if error.headers else None
            time.sleep(float(retry_after) if retry_after else fallback_delay)
        except URLError:
            if attempt == 3:
                raise
            time.sleep(fallback_delay)
    raise RuntimeError(f"metadata request failed without response: {url}")


def _category_pages(category: str, limit: int = 80) -> list[dict]:
    pages: list[dict] = []
    continuation: str | None = None
    while len(pages) < limit:
        parameters = {
            "action": "query",
            "generator": "categorymembers",
            "gcmtitle": f"Category:{category}",
            "gcmtype": "file",
            "gcmlimit": "50",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime",
            "iiurlwidth": "320",
            "format": "json",
            "formatversion": "2",
        }
        if continuation:
            parameters["gcmcontinue"] = continuation
        payload = _request_json(parameters)
        pages.extend(payload.get("query", {}).get("pages", []))
        continuation = payload.get("continue", {}).get("gcmcontinue")
        if not continuation:
            break
    return pages[:limit]


def _safe_candidate(page: dict, *, excluded_category: str | None = None) -> bool:
    if not page.get("imageinfo"):
        return False
    info = page["imageinfo"][0]
    mime = str(info.get("mime", ""))
    license_name = _metadata(info, "LicenseShortName")
    categories = set(_metadata(info, "Categories").split("|"))
    if mime not in {"image/jpeg", "image/png"} or not license_is_redistributable(license_name):
        return False
    if excluded_category and excluded_category in categories:
        return False
    privacy_tokens = ("Portraits", "People", "Men", "Women", "Children")
    return not any(any(token in category for token in privacy_tokens) for category in categories)


def _download_and_normalize(url: str, path: Path) -> str:
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    payload = None
    for attempt, fallback_delay in enumerate((10, 30, 60, 120)):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
            break
        except HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            retry_after = error.headers.get("Retry-After") if error.headers else None
            time.sleep(float(retry_after) if retry_after else fallback_delay)
        except URLError:
            if attempt == 3:
                raise
            time.sleep(fallback_delay)
    if payload is None:
        raise RuntimeError(f"download failed without payload: {url}")
    frame = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError(f"could not decode {url}")
    height, width = frame.shape[:2]
    scale = min(1.0, MAX_EDGE / max(width, height))
    if scale < 1.0:
        frame = cv2.resize(
            frame,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise ValueError(f"could not encode {path}")
    output = encoded.tobytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(output)
    return hashlib.sha256(output).hexdigest()


def _encode_jpeg(frame: np.ndarray, path: Path) -> str:
    ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise ValueError(f"could not encode {path}")
    output = encoded.tobytes()
    path.write_bytes(output)
    return hashlib.sha256(output).hexdigest()


def edge_crop_for_unbalanced_composition(
    frame: np.ndarray, *, retain_left: bool
) -> np.ndarray:
    """Tightly crop one side so a centered subject falls near the opposite edge."""
    if frame.ndim != 3 or frame.shape[1] < 4:
        raise ValueError("expected a color image at least four pixels wide")
    width = frame.shape[1]
    crop_width = max(2, round(width * 0.62))
    start = 0 if retain_left else width - crop_width
    return frame[:, start : start + crop_width].copy()


def apply_unbalanced_edge_crops(
    manifest_path: str | Path, case_ids: list[str]
) -> int:
    """Create reproducible real-image hard negatives without losing provenance."""
    path = Path(manifest_path)
    payload = json.loads(path.read_text())
    cases_by_id = {str(case.get("id")): case for case in payload.get("cases", [])}
    unknown = sorted(set(case_ids) - set(cases_by_id))
    if unknown:
        raise KeyError(f"unknown candidate ids: {unknown}")

    marker = "directional 62% edge crop for controlled unbalanced composition"
    changed = 0
    for index, case_id in enumerate(case_ids):
        case = cases_by_id[case_id]
        modifications = str(case.get("modifications", ""))
        if marker in modifications:
            continue
        image_path = path.parent / str(case["path"])
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise ValueError(f"could not decode {image_path}")
        cropped = edge_crop_for_unbalanced_composition(
            frame, retain_left=index % 2 == 0
        )
        case["sha256"] = _encode_jpeg(cropped, image_path)
        case["modifications"] = f"{modifications}; {marker}".strip("; ")
        case["review_status"] = "pending"
        case.pop("reviewer", None)
        case.pop("review_notes", None)
        case.pop("reviewed_at", None)
        changed += 1

    if changed:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return changed


def _contact_sheet(root: Path, cases: list[dict], relative_path: str) -> None:
    tile_width, tile_height = 240, 190
    columns = 5
    rows = (len(cases) + columns - 1) // columns
    sheet = np.full((rows * tile_height, columns * tile_width, 3), 245, dtype=np.uint8)
    for index, case in enumerate(cases):
        frame = cv2.imread(str(root / case["path"]))
        if frame is None:
            continue
        available_height = tile_height - 28
        scale = min((tile_width - 8) / frame.shape[1], available_height / frame.shape[0])
        resized = cv2.resize(
            frame,
            (max(1, round(frame.shape[1] * scale)), max(1, round(frame.shape[0] * scale))),
            interpolation=cv2.INTER_AREA,
        )
        row, column = divmod(index, columns)
        x = column * tile_width + (tile_width - resized.shape[1]) // 2
        y = row * tile_height + 24 + (available_height - resized.shape[0]) // 2
        sheet[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
        cv2.putText(
            sheet,
            f"{index:02d} {case['id']}",
            (column * tile_width + 5, row * tile_height + 17),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (20, 20, 20),
            1,
            cv2.LINE_AA,
        )
    output = root / relative_path
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), sheet)


def _attribution_markdown(cases: list[dict]) -> str:
    lines = [
        "# Wikimedia Commons candidate attribution",
        "",
        "These resized candidate files are pending composition review and do not count toward acceptance metrics.",
        "Each row retains the original author, source and license; the local copy was resized and JPEG re-encoded.",
        "",
        "| Local ID | Original | Author | License |",
        "|---|---|---|---|",
    ]
    for case in cases:
        author = case["author"].replace("|", "\\|")
        title = case["source_title"].replace("|", "\\|")
        lines.append(
            f"| `{case['id']}` | [{title}]({case['provenance_url']}) | {author} | "
            f"[{case['license']}]({case['license_url']}) |"
        )
    return "\n".join(lines) + "\n"


def _persist_candidates(
    manifest_path: Path,
    payload: dict,
    retained: list[dict],
    curated: list[dict],
    spec: CurationSpec,
) -> None:
    payload["cases"] = merge_duplicate_source_cases(retained + curated)
    manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    root = manifest_path.parent
    positives = [case for case in curated if case["labels"]]
    negatives = [case for case in curated if case["negative_for"]]
    if positives:
        _contact_sheet(root, positives, f"review/commons-{spec.slug}-positive.jpg")
    if negatives:
        _contact_sheet(root, negatives, f"review/commons-{spec.slug}-negative.jpg")
    all_commons = [
        case for case in payload["cases"] if case.get("source") == "Wikimedia Commons"
    ]
    (root / "ATTRIBUTION.md").write_text(_attribution_markdown(all_commons))


def rebuild_contact_sheets(manifest_path: str | Path) -> None:
    path = Path(manifest_path)
    payload = json.loads(path.read_text())
    commons = [
        case for case in payload.get("cases", []) if case.get("source") == "Wikimedia Commons"
    ]
    for spec in CURATION_SPECS.values():
        positives = [case for case in commons if spec.label in case.get("labels", [])]
        negatives = [case for case in commons if spec.label in case.get("negative_for", [])]
        if positives:
            _contact_sheet(path.parent, positives, f"review/commons-{spec.slug}-positive.jpg")
        if negatives:
            _contact_sheet(path.parent, negatives, f"review/commons-{spec.slug}-negative.jpg")


def deduplicate_manifest(manifest_path: str | Path) -> int:
    path = Path(manifest_path)
    payload = json.loads(path.read_text())
    before = len(payload.get("cases", []))
    payload["cases"] = merge_duplicate_source_cases(payload.get("cases", []))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    commons = [
        case for case in payload["cases"] if case.get("source") == "Wikimedia Commons"
    ]
    (path.parent / "ATTRIBUTION.md").write_text(_attribution_markdown(commons))
    rebuild_contact_sheets(path)
    return before - len(payload["cases"])


def reproject_existing_categories(manifest_path: str | Path) -> int:
    """Reuse downloaded Commons category evidence for every matching mode proposal."""
    path = Path(manifest_path)
    payload = json.loads(path.read_text())
    category_truth: dict[str, tuple[set[str], set[str]]] = {}
    for spec in CURATION_SPECS.values():
        positive_labels, positive_negatives = category_truth.setdefault(
            spec.positive_category, (set(), set())
        )
        positive_labels.add(spec.label)
        negative_labels, negative_for = category_truth.setdefault(
            spec.negative_category, (set(), set())
        )
        negative_for.add(spec.label)

    changed = 0
    for case in payload.get("cases", []):
        if case.get("source") != "Wikimedia Commons":
            continue
        labels = set(case.get("labels", []))
        negative_for = set(case.get("negative_for", []))
        before = (set(labels), set(negative_for))
        for category in case.get("source_categories", []):
            additions = category_truth.get(category)
            if additions is None:
                continue
            labels.update(additions[0])
            negative_for.update(additions[1])
        if (labels, negative_for) == before:
            continue
        case["labels"] = sorted(labels)
        case["negative_for"] = sorted(negative_for)
        case["kind"] = "positive" if labels else "hard_negative"
        case["review_status"] = "pending"
        case.pop("reviewer", None)
        case.pop("review_notes", None)
        case.pop("reviewed_at", None)
        changed += 1

    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    commons = [
        case for case in payload.get("cases", []) if case.get("source") == "Wikimedia Commons"
    ]
    (path.parent / "ATTRIBUTION.md").write_text(_attribution_markdown(commons))
    rebuild_contact_sheets(path)
    return changed


def curate_mode(
    manifest_path: str | Path,
    spec: CurationSpec,
    count: int = 20,
    *,
    max_new_downloads: int | None = None,
    download_delay_s: float = 2.0,
) -> list[dict]:
    manifest_path = Path(manifest_path)
    root = manifest_path.parent
    payload = json.loads(manifest_path.read_text())
    retained = list(payload.get("cases", []))
    existing_by_page_id = {
        str(case.get("source_item_id")): case
        for case in retained
        if case.get("source") == "Wikimedia Commons" and case.get("source_item_id")
    }
    specifications = (
        (spec.positive_category, [spec.label], [], None, "positive"),
        (
            spec.negative_category,
            [],
            [spec.label],
            spec.positive_category,
            "negative",
        ),
    )
    curated: list[dict] = []
    new_downloads = 0
    used_page_ids: set[str] = set()
    for category, labels, negatives, excluded, role in specifications:
        candidates = [
            page
            for page in _category_pages(category, limit=max(80, count * 4))
            if _safe_candidate(page, excluded_category=excluded)
        ]
        selected = []
        for page in candidates:
            page_id = str(page["pageid"])
            if page_id in used_page_ids:
                continue
            used_page_ids.add(page_id)
            selected.append(page)
            if len(selected) == count:
                break
        if len(selected) < count:
            raise RuntimeError(f"only {len(selected)} safe candidates found for {category}")
        for index, page in enumerate(selected):
            page_id = str(page["pageid"])
            existing = existing_by_page_id.get(page_id)
            if existing is not None:
                before = (tuple(existing.get("labels", [])), tuple(existing.get("negative_for", [])))
                existing["labels"] = sorted(set(existing.get("labels", [])) | set(labels))
                existing["negative_for"] = sorted(
                    set(existing.get("negative_for", [])) | set(negatives)
                )
                if existing["labels"]:
                    existing["kind"] = "positive"
                annotations = set(existing.get("annotation_sources", []))
                if existing.get("annotation_source"):
                    annotations.add(str(existing["annotation_source"]))
                annotations.add(f"Wikimedia Commons human-curated category: {category}")
                existing["annotation_sources"] = sorted(annotations)
                existing["annotation_source"] = "; ".join(sorted(annotations))
                existing["source_categories"] = sorted(
                    set(existing.get("source_categories", [])) | {category}
                )
                after = (tuple(existing["labels"]), tuple(existing["negative_for"]))
                if after != before:
                    existing["review_status"] = "pending"
                    existing.pop("reviewer", None)
                    existing.pop("review_notes", None)
                    existing.pop("reviewed_at", None)
                _persist_candidates(manifest_path, payload, retained, curated, spec)
                continue
            case_id = f"commons-{spec.slug}-{role}-{index:02d}"
            relative_path = f"images/real_candidates/{case_id}.jpg"
            case = case_from_page(
                page,
                case_id=case_id,
                relative_path=relative_path,
                category=category,
                labels=labels,
                negative_for=negatives,
            )
            output_path = root / relative_path
            was_cached = output_path.is_file()
            if (
                not was_cached
                and max_new_downloads is not None
                and new_downloads >= max_new_downloads
            ):
                _persist_candidates(manifest_path, payload, retained, curated, spec)
                rebuild_contact_sheets(manifest_path)
                return curated
            try:
                case["sha256"] = _download_and_normalize(
                    page["imageinfo"][0]["thumburl"], output_path
                )
            except Exception:
                _persist_candidates(manifest_path, payload, retained, curated, spec)
                raise
            curated.append(case)
            existing_by_page_id[page_id] = case
            _persist_candidates(manifest_path, payload, retained, curated, spec)
            if not was_cached:
                new_downloads += 1
                if download_delay_s > 0:
                    time.sleep(download_delay_s)
    rebuild_contact_sheets(manifest_path)
    return curated


def curate_rule_of_thirds(
    manifest_path: str | Path,
    count: int = 20,
    *,
    max_new_downloads: int | None = None,
    download_delay_s: float = 2.0,
) -> list[dict]:
    return curate_mode(
        manifest_path,
        CURATION_SPECS["rule-of-thirds"],
        count=count,
        max_new_downloads=max_new_downloads,
        download_delay_s=download_delay_s,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Curate licensed Wikimedia candidates")
    parser.add_argument("--mode", choices=sorted(CURATION_SPECS), default="rule-of-thirds")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--deduplicate-only", action="store_true")
    parser.add_argument("--reproject-existing", action="store_true")
    parser.add_argument("--probe-category", action="append", default=[])
    parser.add_argument("--max-new", type=int)
    parser.add_argument("--download-delay", type=float, default=2.0)
    args = parser.parse_args()
    default_manifest = Path(__file__).with_name("manifest.json")
    if args.probe_category:
        for category in args.probe_category:
            try:
                pages = _category_pages(category, limit=max(80, args.count * 4))
                safe = [page for page in pages if _safe_candidate(page)]
                print(f"{category}: total={len(pages)} safe={len(safe)}")
            except HTTPError as error:
                print(f"{category}: HTTP {error.code}")
            time.sleep(2.0)
        raise SystemExit(0)
    if args.deduplicate_only:
        print(f"merged {deduplicate_manifest(default_manifest)} duplicate source cases")
        raise SystemExit(0)
    if args.reproject_existing:
        print(
            f"updated {reproject_existing_categories(default_manifest)} existing Commons cases"
        )
        raise SystemExit(0)
    cases = curate_mode(
        default_manifest,
        CURATION_SPECS[args.mode],
        count=args.count,
        max_new_downloads=args.max_new,
        download_delay_s=args.download_delay,
    )
    print(f"downloaded {len(cases)} pending Wikimedia Commons candidates for {args.mode}")
