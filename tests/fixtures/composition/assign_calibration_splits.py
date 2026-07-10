"""Deterministically stratify reviewed real cases without source leakage."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


ModeBucket = tuple[str, bool]
Bucket = tuple[str, bool, str]
SPLIT_SEED = "cameraq-composition-v1"


def _case_mode_buckets(case: dict) -> set[ModeBucket]:
    buckets = {(str(label), True) for label in case.get("labels", [])}
    buckets.update((str(label), False) for label in case.get("negative_for", []))
    return buckets


def _source_families(case: dict) -> tuple[str, ...]:
    raw = case.get("annotation_sources") or case.get("annotation_source") or "unknown"
    values = raw if isinstance(raw, list) else str(raw).split(";")
    return tuple(sorted({str(value).strip() for value in values if str(value).strip()}))


def _stable_rank(case_id: str) -> int:
    payload = f"{SPLIT_SEED}\0{case_id}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def assign_calibration_splits(
    manifest_path: str | Path, *, calibration_fraction: float = 0.4
) -> dict[str, int]:
    if not 0 < calibration_fraction < 1:
        raise ValueError("calibration_fraction must be between zero and one")
    path = Path(manifest_path)
    payload = json.loads(path.read_text())
    cases = [
        case
        for case in payload.get("cases", [])
        if case.get("review_status") == "accepted"
        and case.get("kind") in {"positive", "hard_negative"}
    ]
    mode_buckets_by_id = {
        str(case["id"]): _case_mode_buckets(case) for case in cases
    }
    family_candidates_by_id = {
        str(case["id"]): {
            (label, truth, family)
            for label, truth in mode_buckets_by_id[str(case["id"])]
            for family in _source_families(case)
        }
        for case in cases
    }
    family_totals = Counter(
        bucket for buckets in family_candidates_by_id.values() for bucket in buckets
    )
    buckets_by_id = {
        case_id: {
            (label, truth, "*") for label, truth in mode_buckets
        }
        | {
            bucket
            for bucket in family_candidates_by_id[case_id]
            if family_totals[bucket] >= 2
        }
        for case_id, mode_buckets in mode_buckets_by_id.items()
    }
    totals = Counter(bucket for buckets in buckets_by_id.values() for bucket in buckets)
    too_small = sorted(bucket for bucket, total in totals.items() if total < 2)
    if too_small:
        raise ValueError(f"need at least two reviewed cases per bucket: {too_small}")
    targets = {
        bucket: max(1, min(total - 1, round(total * calibration_fraction)))
        for bucket, total in totals.items()
    }

    selected: set[str] = set()
    selected_counts: Counter[Bucket] = Counter()
    while any(selected_counts[bucket] < target for bucket, target in targets.items()):
        ranked: list[tuple[int, int, int, str]] = []
        for case_id, buckets in buckets_by_id.items():
            if case_id in selected:
                continue
            if any(selected_counts[bucket] >= totals[bucket] - 1 for bucket in buckets):
                continue
            gain = sum(
                max(0, targets[bucket] - selected_counts[bucket]) for bucket in buckets
            )
            if gain:
                overshoot = sum(
                    selected_counts[bucket] >= targets[bucket] for bucket in buckets
                )
                ranked.append((gain, -overshoot, -_stable_rank(case_id), case_id))
        if not ranked:
            missing = {
                bucket: targets[bucket] - selected_counts[bucket]
                for bucket in targets
                if selected_counts[bucket] < targets[bucket]
            }
            raise ValueError(f"could not satisfy calibration strata: {missing}")
        _, _, _, chosen = max(
            ranked, key=lambda item: (item[0], item[1], item[2])
        )
        selected.add(chosen)
        selected_counts.update(buckets_by_id[chosen])

    for case in cases:
        case["split"] = "calibration" if str(case["id"]) in selected else "acceptance"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return {
        "calibration_cases": len(selected),
        "acceptance_cases": len(cases) - len(selected),
        "strata": len(targets),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=Path(__file__).with_name("manifest.json")
    )
    parser.add_argument("--fraction", type=float, default=0.4)
    args = parser.parse_args()
    print(assign_calibration_splits(args.manifest, calibration_fraction=args.fraction))


if __name__ == "__main__":
    main()
