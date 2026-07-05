from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


DEGRADATION_CATEGORIES = ("low_information", "blur", "solid_color", "exposure")
ACTION_GROUPS = ("translation", "rotation", "closer", "back")
REVIEW_STATUSES = ("pending", "accepted", "rejected", "ambiguous")


@dataclass(frozen=True)
class ManifestAudit:
    issues: list[str]
    positive_counts: dict[str, int]
    hard_negative_counts: dict[str, int]
    degraded_counts: dict[str, int]
    recommendation_counts: dict[str, int]
    accepted_cases: int


def _is_algorithm_self_label(value: str) -> bool:
    normalized = value.lower().replace("_", "-")
    return any(token in normalized for token in ("algorithm", "engine-output", "model-output"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_manifest(path: str | Path, *, require_files: bool = True) -> ManifestAudit:
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text())
    labels = set(payload["labels"])
    required = payload["required_counts"]
    issues: list[str] = []
    positive_counts: Counter[str] = Counter()
    negative_counts: Counter[str] = Counter()
    degraded_counts: Counter[str] = Counter()
    recommendation_counts: Counter[str] = Counter()
    source_splits: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    source_cases: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    ids: set[str] = set()
    referenced_paths: set[str] = set()
    accepted_cases = 0

    for case in payload.get("cases", []):
        case_id = case.get("id", "<missing-id>")
        if case.get("path"):
            referenced_paths.add(str(case["path"]))
        if case_id in ids:
            issues.append(f"duplicate case id: {case_id}")
        ids.add(case_id)
        annotation_source = str(case.get("annotation_source", ""))
        review_status = case.get("review_status")
        source = str(case.get("source", ""))
        source_item = str(case.get("source_item_id", ""))
        if source and source_item:
            source_cases[(source, source_item)].append(case_id)
        if _is_algorithm_self_label(annotation_source):
            issues.append(f"algorithm self-label is forbidden: {case_id}")
        if review_status not in REVIEW_STATUSES:
            issues.append(f"invalid review status for {case_id}: {review_status}")
            continue
        if review_status != "accepted":
            continue
        accepted_cases += 1

        if source == "Wikimedia Commons" and not str(case.get("reviewer", "")).strip():
            issues.append(f"missing independent reviewer for accepted Commons case: {case_id}")
        if source == "Wikimedia Commons" and not str(case.get("review_notes", "")).strip():
            issues.append(f"missing review notes for accepted Commons case: {case_id}")
        split = str(case.get("split", ""))
        if not source or not source_item or not split:
            issues.append(f"missing source identity or split: {case_id}")
        else:
            source_splits[(source, source_item)].add(split)
        for field in ("provenance_url", "license", "annotation_source"):
            if not case.get(field):
                issues.append(f"missing {field}: {case_id}")

        case_labels = set(case.get("labels", []))
        negative_for = set(case.get("negative_for", []))
        unknown = (case_labels | negative_for) - labels
        if unknown:
            issues.append(f"unknown labels for {case_id}: {sorted(unknown)}")
        positive_counts.update(case_labels)
        negative_counts.update(negative_for)
        kind = case.get("kind")
        if kind == "positive":
            if not case_labels:
                issues.append(f"positive case has no labels: {case_id}")
        elif kind == "hard_negative":
            if not negative_for:
                issues.append(f"hard negative has no negative_for labels: {case_id}")
        elif kind == "degraded":
            category = case.get("degradation_category")
            if category not in DEGRADATION_CATEGORIES:
                issues.append(f"invalid degradation category: {case_id}")
            else:
                degraded_counts[category] += 1
            if case.get("expected_abstention") is not True:
                issues.append(f"degraded case must expect abstention: {case_id}")
        elif kind == "recommendation":
            group = case.get("recommendation_action_group")
            if group not in ACTION_GROUPS:
                issues.append(f"invalid recommendation action group: {case_id}")
            else:
                recommendation_counts[group] += 1
            if not case.get("recommendation_action"):
                issues.append(f"missing recommendation action: {case_id}")
        else:
            issues.append(f"invalid kind: {case_id}")

        if require_files:
            image_path = manifest_path.parent / str(case.get("path", ""))
            if not image_path.is_file():
                issues.append(f"missing image file: {case_id}")
            elif not case.get("sha256"):
                issues.append(f"missing sha256: {case_id}")
            elif _sha256(image_path) != case["sha256"]:
                issues.append(f"sha256 mismatch: {case_id}")
            if kind == "recommendation":
                after_path = manifest_path.parent / str(case.get("after_path", ""))
                if not after_path.is_file():
                    issues.append(f"missing after image file: {case_id}")
                elif not case.get("after_sha256"):
                    issues.append(f"missing after sha256: {case_id}")
                elif _sha256(after_path) != case["after_sha256"]:
                    issues.append(f"after sha256 mismatch: {case_id}")

    for (source, source_item), splits in source_splits.items():
        if len(splits) > 1:
            issues.append(
                f"split leakage for {source}/{source_item}: {sorted(splits)}"
            )
    for (source, source_item), case_ids in source_cases.items():
        if len(case_ids) > 1:
            issues.append(
                f"duplicate source item {source}/{source_item}: {sorted(case_ids)}"
            )
    if require_files:
        candidate_root = manifest_path.parent / "images/real_candidates"
        if candidate_root.is_dir():
            candidates = {
                path.relative_to(manifest_path.parent).as_posix()
                for path in candidate_root.iterdir()
                if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
            }
            orphans = sorted(candidates - referenced_paths)
            if orphans:
                issues.append(f"orphan real candidate files ({len(orphans)}): {orphans}")

    positive_minimum = int(required["positive_per_label"])
    negative_minimum = int(required["hard_negative_per_label"])
    for label in sorted(labels):
        if positive_counts[label] < positive_minimum:
            issues.append(
                f"positive count below {positive_minimum} for {label}: {positive_counts[label]}"
            )
        if negative_counts[label] < negative_minimum:
            issues.append(
                f"hard-negative count below {negative_minimum} for {label}: {negative_counts[label]}"
            )
    degraded_minimum = int(required["degraded_per_category"])
    for category in DEGRADATION_CATEGORIES:
        if degraded_counts[category] < degraded_minimum:
            issues.append(
                f"degraded count below {degraded_minimum} for {category}: {degraded_counts[category]}"
            )
    recommendation_total = sum(recommendation_counts.values())
    if recommendation_total < int(required["recommendation_total"]):
        issues.append(
            f"recommendation total below {required['recommendation_total']}: {recommendation_total}"
        )
    group_minimum = int(required["recommendation_per_action_group"])
    for group in ACTION_GROUPS:
        if recommendation_counts[group] < group_minimum:
            issues.append(
                f"recommendation count below {group_minimum} for {group}: {recommendation_counts[group]}"
            )

    return ManifestAudit(
        issues=issues,
        positive_counts=dict(positive_counts),
        hard_negative_counts=dict(negative_counts),
        degraded_counts=dict(degraded_counts),
        recommendation_counts=dict(recommendation_counts),
        accepted_cases=accepted_cases,
    )


def assert_acceptance_ready(report: ManifestAudit) -> None:
    if report.issues:
        raise AssertionError("acceptance manifest is not ready:\n- " + "\n- ".join(report.issues))
