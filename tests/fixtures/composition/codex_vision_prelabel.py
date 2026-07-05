"""Materialize the temporary Codex contact-sheet review as auditable CSV files.

This is a one-session visual prelabel, not an API-backed or human ground-truth
review.  The explicit index sets below preserve exactly what was accepted from
the 30 generated contact sheets; anything not accepted or held for a closer
look is rejected as a candidate proposal.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).parent
QUEUE = ROOT / "review" / "review-queue.csv"
PRELABELS = ROOT / "review" / "codex-vision-prelabels.csv"
DECISIONS = ROOT / "review" / "codex-vision-decisions.csv"
REVIEWER = "codex-vision-temporary-2026-07-05"


@dataclass(frozen=True)
class SheetAssessment:
    accepted: frozenset[int]
    pending: frozenset[int] = frozenset()
    reviewed_count: int = 20


def _indices(values: str) -> frozenset[int]:
    return frozenset(int(value) for value in values.split() if value)


ASSESSMENTS = {
    "rule-of-thirds-positive": SheetAssessment(
        _indices("0 1 4 5 6 7 8 9 12 13 15 16"), _indices("11 14 19")
    ),
    "rule-of-thirds-negative": SheetAssessment(
        _indices("0 1 3 5 9 10 11 13 15 16 18 19")
    ),
    "diagonal-positive": SheetAssessment(
        _indices("0 1 2 3 4 5 6 7 8 9 11 12 13 14 16 17 18 19")
    ),
    "dynamic-symmetry-positive": SheetAssessment(
        _indices("10 13 15 18"), _indices("19")
    ),
    "dynamic-symmetry-negative": SheetAssessment(
        _indices("1 2 3 5 6 7 9 10 12 13 16 18 19"), _indices("0 17")
    ),
    "balanced-negative": SheetAssessment(frozenset()),
    "triangle-positive": SheetAssessment(
        _indices("0 1 2 3 5 7 8 10 11 12 13 14 15 16"), _indices("17")
    ),
    "triangle-negative": SheetAssessment(
        _indices("1 3 4 6 7 8 10 11 14 18 19")
    ),
    "horizontal-positive": SheetAssessment(frozenset()),
    "horizontal-photo-positive": SheetAssessment(
        _indices("0 1 2 3 4 5 6 7 9 10 11 12 13 14 15 16 17 18 19 21"),
        reviewed_count=22,
    ),
    "horizontal-negative": SheetAssessment(
        _indices("10 12 13 14 16 17 19"), _indices("11")
    ),
    "vertical-photo-positive": SheetAssessment(
        _indices("0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17"),
        reviewed_count=18,
    ),
    "oblique-positive": SheetAssessment(
        _indices("7 12 13 14 17 18 19"), _indices("2 4 5 9 16")
    ),
    "curve-positive": SheetAssessment(
        _indices("0 4 5 6 7 8 9 10 11 12 17 19"), _indices("16")
    ),
    "curve-negative": SheetAssessment(frozenset(), reviewed_count=19),
    "radial-positive": SheetAssessment(
        _indices("0 1 2 3 4 5 6 7 8 10 11 13 14 15 17 18 19"),
        _indices("12 16"),
    ),
    "radial-negative": SheetAssessment(
        _indices("0 1 2 4 5 8 10 12 13 14 15 16 17 19")
    ),
    "checkerboard-positive": SheetAssessment(
        _indices("13 16 17 18"), _indices("5")
    ),
    "centripetal-positive": SheetAssessment(
        _indices("0 1 2 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19"),
        _indices("3"),
    ),
    "frame-within-frame-positive": SheetAssessment(_indices("0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19")),
    "frame-within-frame-negative": SheetAssessment(_indices("0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 16 17 18")),
    "tunnel-positive": SheetAssessment(_indices("0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19")),
    "tunnel-negative": SheetAssessment(_indices("0 1 3 4 5 6 7 8 9 10 11 12 13 14 15 18 19")),
    "cross-negative": SheetAssessment(_indices("1 2 3 6 7 8 9 10 14 15 16 17 18")),
}


def _group_and_index(case_id: str) -> tuple[str, int]:
    if not case_id.startswith("commons-"):
        raise ValueError(f"not a Commons candidate: {case_id}")
    stem, raw_index = case_id.rsplit("-", 1)
    group = stem.removeprefix("commons-")
    if group not in ASSESSMENTS:
        raise KeyError(f"missing contact-sheet assessment for {group}")
    return group, int(raw_index)


def _rationale(row: dict[str, str], decision: str) -> str:
    labels = row["proposed_labels"] or "none"
    negatives = row["proposed_negative_for"] or "none"
    if decision == "accepted":
        return (
            "Codex临时视觉预标注：联系表中可见的主体、长线、轮廓或空间关系清晰支持"
            f"建议正例[{labels}]及困难反例[{negatives}]，未发现与规格定义直接冲突。"
        )
    if decision == "pending":
        return (
            "Codex临时视觉预标注：联系表缩略图不足以稳定确认局部结构、主体位置或多标签边界，"
            "保留pending并建议查看原图。"
        )
    return (
        "Codex临时视觉预标注：画面结构与建议模式不符，或样本只是几何示意、孤立素材/来源类别误提名，"
        f"不能可靠支持正例[{labels}]及困难反例[{negatives}]。"
    )


def classify_index(group: str, index: int) -> tuple[str, str]:
    assessment = ASSESSMENTS[group]
    if index >= assessment.reviewed_count:
        return "pending", "0.00"
    if index in assessment.pending:
        return "pending", "0.55"
    if index in assessment.accepted:
        return "accepted", "0.90"
    return "rejected", "0.90"


def generate() -> tuple[int, int]:
    with QUEUE.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    prelabels: list[dict[str, str]] = []
    decisions: list[dict[str, str]] = []
    for row in rows:
        group, index = _group_and_index(row["id"])
        decision, confidence = classify_index(group, index)
        notes = _rationale(row, decision)
        prelabels.append(
            {
                "id": row["id"],
                "path": row["path"],
                "proposed_labels": row["proposed_labels"],
                "proposed_negative_for": row["proposed_negative_for"],
                "suggested_decision": decision,
                "confidence": confidence,
                "reviewer": REVIEWER,
                "review_notes": notes,
            }
        )
        if decision != "pending":
            decisions.append(
                {
                    "id": row["id"],
                    "decision": decision,
                    "reviewer": REVIEWER,
                    "review_notes": notes,
                }
            )

    with PRELABELS.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=prelabels[0].keys())
        writer.writeheader()
        writer.writerows(prelabels)
    with DECISIONS.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("id", "decision", "reviewer", "review_notes"))
        writer.writeheader()
        writer.writerows(decisions)
    return len(prelabels), len(decisions)


if __name__ == "__main__":
    total, decided = generate()
    print(f"wrote {total} prelabels and {decided} high-confidence decisions")
