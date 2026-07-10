"""Record independent human review decisions for composition candidates."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path


REVIEW_STATUSES = ("pending", "accepted", "rejected", "ambiguous")
REVIEW_QUEUE_FIELDS = (
    "id",
    "path",
    "kind",
    "proposed_labels",
    "proposed_negative_for",
    "source_title",
    "provenance_url",
    "license",
    "current_status",
    "decision",
    "reviewer",
    "review_notes",
)


def _validate_decision(status: str, reviewer: str, notes: str) -> None:
    if status not in REVIEW_STATUSES:
        raise ValueError(f"unsupported review status: {status}")
    if status != "pending" and not reviewer.strip():
        raise ValueError("reviewer is required for a review decision")
    if status != "pending" and not notes.strip():
        raise ValueError("review notes are required for a review decision")


def _apply_decision(case: dict, status: str, reviewer: str, notes: str) -> None:
    case["review_status"] = status
    if status == "pending":
        case.pop("reviewer", None)
        case.pop("review_notes", None)
        case.pop("reviewed_at", None)
    else:
        case["reviewer"] = reviewer.strip()
        case["review_notes"] = notes.strip()
        case["reviewed_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")


def review_candidate(
    manifest_path: str | Path,
    case_id: str,
    *,
    status: str,
    reviewer: str,
    notes: str,
) -> dict:
    _validate_decision(status, reviewer, notes)

    path = Path(manifest_path)
    payload = json.loads(path.read_text())
    for case in payload.get("cases", []):
        if case.get("id") != case_id:
            continue
        _apply_decision(case, status, reviewer, notes)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        return case
    raise KeyError(f"unknown candidate id: {case_id}")


def add_negative_annotations(
    manifest_path: str | Path, annotations: dict[str, list[str]]
) -> int:
    """Add independently reviewed cross-mode negatives and reset stale decisions."""
    path = Path(manifest_path)
    payload = json.loads(path.read_text())
    known_labels = set(payload.get("labels", []))
    cases_by_id = {str(case.get("id")): case for case in payload.get("cases", [])}
    unknown_ids = sorted(set(annotations) - set(cases_by_id))
    if unknown_ids:
        raise KeyError(f"unknown candidate ids: {unknown_ids}")
    unknown_labels = sorted(
        {
            label
            for labels in annotations.values()
            for label in labels
            if label not in known_labels
        }
    )
    if unknown_labels:
        raise ValueError(f"unknown composition labels: {unknown_labels}")

    changed = 0
    for case_id, additions in annotations.items():
        case = cases_by_id[case_id]
        before = set(case.get("negative_for", []))
        after = before | set(additions)
        if after == before:
            continue
        case["negative_for"] = sorted(after)
        _apply_decision(case, "pending", "", "")
        changed += 1
    if changed:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return changed


def add_positive_annotations(
    manifest_path: str | Path, annotations: dict[str, list[str]]
) -> int:
    """Add independently reviewed cross-mode positives and reset stale decisions."""
    path = Path(manifest_path)
    payload = json.loads(path.read_text())
    known_labels = set(payload.get("labels", []))
    cases_by_id = {str(case.get("id")): case for case in payload.get("cases", [])}
    unknown_ids = sorted(set(annotations) - set(cases_by_id))
    if unknown_ids:
        raise KeyError(f"unknown candidate ids: {unknown_ids}")
    unknown_labels = sorted(
        {
            label
            for labels in annotations.values()
            for label in labels
            if label not in known_labels
        }
    )
    if unknown_labels:
        raise ValueError(f"unknown composition labels: {unknown_labels}")

    changed = 0
    for case_id, additions in annotations.items():
        case = cases_by_id[case_id]
        before = set(case.get("labels", []))
        after = before | set(additions)
        if after == before:
            continue
        case["labels"] = sorted(after)
        case["negative_for"] = sorted(
            set(case.get("negative_for", [])) - set(additions)
        )
        case["kind"] = "positive"
        _apply_decision(case, "pending", "", "")
        changed += 1
    if changed:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return changed


def export_review_queue(manifest_path: str | Path, output_path: str | Path) -> int:
    payload = json.loads(Path(manifest_path).read_text())
    cases = [
        case
        for case in payload.get("cases", [])
        if case.get("source") == "Wikimedia Commons"
    ]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=REVIEW_QUEUE_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    "id": case.get("id", ""),
                    "path": case.get("path", ""),
                    "kind": case.get("kind", ""),
                    "proposed_labels": "|".join(case.get("labels", [])),
                    "proposed_negative_for": "|".join(case.get("negative_for", [])),
                    "source_title": case.get("source_title", ""),
                    "provenance_url": case.get("provenance_url", ""),
                    "license": case.get("license", ""),
                    "current_status": case.get("review_status", ""),
                    "decision": "",
                    "reviewer": "",
                    "review_notes": "",
                }
            )
    return len(cases)


def import_review_decisions(manifest_path: str | Path, queue_path: str | Path) -> int:
    manifest = Path(manifest_path)
    payload = json.loads(manifest.read_text())
    cases_by_id = {str(case.get("id")): case for case in payload.get("cases", [])}
    with Path(queue_path).open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    decisions: list[tuple[dict, str, str, str]] = []
    for row in rows:
        decision = str(row.get("decision", "")).strip()
        if not decision:
            continue
        case_id = str(row.get("id", "")).strip()
        if case_id not in cases_by_id:
            raise KeyError(f"unknown candidate id: {case_id}")
        reviewer = str(row.get("reviewer", ""))
        notes = str(row.get("review_notes", ""))
        _validate_decision(decision, reviewer, notes)
        decisions.append((cases_by_id[case_id], decision, reviewer, notes))

    for case, decision, reviewer, notes in decisions:
        _apply_decision(case, decision, reviewer, notes)
    manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return len(decisions)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.set_defaults(manifest=Path(__file__).with_name("manifest.json"))
    commands = parser.add_subparsers(dest="command", required=True)
    set_parser = commands.add_parser("set", help="record one review decision")
    set_parser.add_argument("case_id")
    set_parser.add_argument("status", choices=REVIEW_STATUSES)
    set_parser.add_argument("--reviewer", required=True)
    set_parser.add_argument("--notes", required=True)
    set_parser.add_argument("--manifest", type=Path, default=parser.get_default("manifest"))
    export_parser = commands.add_parser("export", help="export a CSV review queue")
    export_parser.add_argument("output", type=Path)
    export_parser.add_argument("--manifest", type=Path, default=parser.get_default("manifest"))
    import_parser = commands.add_parser("import", help="import CSV decision fields")
    import_parser.add_argument("queue", type=Path)
    import_parser.add_argument("--manifest", type=Path, default=parser.get_default("manifest"))
    args = parser.parse_args()
    if args.command == "set":
        reviewed = review_candidate(
            args.manifest,
            args.case_id,
            status=args.status,
            reviewer=args.reviewer,
            notes=args.notes,
        )
        print(f"{reviewed['id']}: {reviewed['review_status']}")
    elif args.command == "export":
        print(f"exported {export_review_queue(args.manifest, args.output)} candidates")
    else:
        print(f"imported {import_review_decisions(args.manifest, args.queue)} decisions")


if __name__ == "__main__":
    main()
