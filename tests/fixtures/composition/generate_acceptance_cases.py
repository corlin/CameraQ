from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


WIDTH = 320
HEIGHT = 240
GENERATOR_SOURCE = "CameraQ deterministic acceptance generator v1"


def _write_png(root: Path, relative_path: str, frame: np.ndarray) -> str:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(".png", frame)
    if not ok:
        raise RuntimeError(f"could not encode {relative_path}")
    payload = encoded.tobytes()
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _base_case(case_id: str, kind: str, path: str, sha256: str) -> dict:
    return {
        "id": case_id,
        "path": path,
        "sha256": sha256,
        "kind": kind,
        "labels": [],
        "negative_for": [],
        "source": GENERATOR_SOURCE,
        "source_item_id": case_id,
        "provenance_url": f"generator://cameraq/{case_id}",
        "license": "CC0-1.0",
        "annotation_source": "deterministic-human-authored-rule",
        "review_status": "accepted",
        "split": "acceptance",
    }


def _degraded_cases(root: Path) -> list[dict]:
    cases: list[dict] = []
    for index in range(25):
        rng = np.random.default_rng(1400 + index)
        frame = np.full((HEIGHT, WIDTH, 3), 126, dtype=np.uint8)
        noise = rng.integers(-2, 3, frame.shape, dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        case_id = f"generated-degraded-low-information-{index:02d}"
        path = f"images/generated/degraded/{case_id}.png"
        case = _base_case(case_id, "degraded", path, _write_png(root, path, frame))
        case.update(degradation_category="low_information", expected_abstention=True)
        cases.append(case)

    for index in range(25):
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        spacing = 26 + index % 5
        for x in range(0, WIDTH, spacing):
            cv2.line(frame, (x, 0), (x, HEIGHT - 1), (220, 220, 220), 2)
        for y in range(0, HEIGHT, spacing):
            cv2.line(frame, (0, y), (WIDTH - 1, y), (220, 220, 220), 2)
        frame = cv2.GaussianBlur(frame, (31, 31), 9 + index % 4)
        case_id = f"generated-degraded-blur-{index:02d}"
        path = f"images/generated/degraded/{case_id}.png"
        case = _base_case(case_id, "degraded", path, _write_png(root, path, frame))
        case.update(degradation_category="blur", expected_abstention=True)
        cases.append(case)

    for index in range(25):
        color = (
            int((index * 37) % 256),
            int((index * 67) % 256),
            int((index * 97) % 256),
        )
        frame = np.full((HEIGHT, WIDTH, 3), color, dtype=np.uint8)
        case_id = f"generated-degraded-solid-color-{index:02d}"
        path = f"images/generated/degraded/{case_id}.png"
        case = _base_case(case_id, "degraded", path, _write_png(root, path, frame))
        case.update(degradation_category="solid_color", expected_abstention=True)
        cases.append(case)

    for index in range(25):
        value = index if index < 13 else 255 - (index - 13)
        frame = np.full((HEIGHT, WIDTH, 3), value, dtype=np.uint8)
        case_id = f"generated-degraded-exposure-{index:02d}"
        path = f"images/generated/degraded/{case_id}.png"
        case = _base_case(case_id, "degraded", path, _write_png(root, path, frame))
        case.update(degradation_category="exposure", expected_abstention=True)
        cases.append(case)
    return cases


def _recommendation_pair(
    root: Path,
    case_id: str,
    before: np.ndarray,
    after: np.ndarray,
    *,
    action: str,
    group: str,
    target_mode: str,
    subject_box_before: list[float] | None = None,
    subject_box_after: list[float] | None = None,
) -> dict:
    before_path = f"images/generated/recommendation/{case_id}-before.png"
    after_path = f"images/generated/recommendation/{case_id}-after.png"
    case = _base_case(
        case_id,
        "recommendation",
        before_path,
        _write_png(root, before_path, before),
    )
    case.update(
        recommendation_action=action,
        recommendation_action_group=group,
        target_mode=target_mode,
        after_path=after_path,
        after_sha256=_write_png(root, after_path, after),
        subject_box_before=subject_box_before,
        subject_box_after=subject_box_after,
    )
    return case


def _recommendation_cases(root: Path) -> list[dict]:
    cases: list[dict] = []
    target_points = ((1 / 3, 1 / 3), (2 / 3, 1 / 3), (1 / 3, 2 / 3), (2 / 3, 2 / 3))
    translations = (
        ("MOVE_LEFT", (-34, 0)),
        ("MOVE_RIGHT", (34, 0)),
        ("TILT_UP", (0, -28)),
        ("TILT_DOWN", (0, 28)),
    )
    for index in range(15):
        target_x, target_y = target_points[index % len(target_points)]
        action, (dx, dy) = translations[index % len(translations)]
        tx, ty = round(target_x * WIDTH), round(target_y * HEIGHT)
        before = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        after = before.copy()
        cv2.circle(before, (tx + dx, ty + dy), 18, (255, 255, 255), -1)
        cv2.circle(after, (tx, ty), 18, (255, 255, 255), -1)
        subject_width, subject_height = 96, 72
        before_box = [
            (tx + dx - subject_width / 2) / WIDTH,
            (ty + dy - subject_height / 2) / HEIGHT,
            subject_width / WIDTH,
            subject_height / HEIGHT,
        ]
        after_box = [
            (tx - subject_width / 2) / WIDTH,
            (ty - subject_height / 2) / HEIGHT,
            subject_width / WIDTH,
            subject_height / HEIGHT,
        ]
        cases.append(
            _recommendation_pair(
                root,
                f"generated-recommendation-translation-{index:02d}",
                before,
                after,
                action=action,
                group="translation",
                target_mode="RULE_OF_THIRDS",
                subject_box_before=before_box,
                subject_box_after=after_box,
            )
        )

    for index in range(15):
        clockwise = index % 2 == 0
        angle = -18 if clockwise else 18
        center = (WIDTH // 2, HEIGHT // 2)
        length = 110
        radians = np.deg2rad(angle)
        delta = (round(np.cos(radians) * length / 2), round(np.sin(radians) * length / 2))
        before = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        after = before.copy()
        cv2.line(
            before,
            (center[0] - delta[0], center[1] - delta[1]),
            (center[0] + delta[0], center[1] + delta[1]),
            (255, 255, 255),
            5,
        )
        cv2.line(after, (30, center[1]), (WIDTH - 30, center[1]), (255, 255, 255), 5)
        action = "ROTATE_CLOCKWISE" if clockwise else "ROTATE_COUNTERCLOCKWISE"
        cases.append(
            _recommendation_pair(
                root,
                f"generated-recommendation-rotation-{index:02d}",
                before,
                after,
                action=action,
                group="rotation",
                target_mode="HORIZONTAL",
                subject_box_before=[0.10, 0.30, 0.30, 0.30],
                subject_box_after=[0.10, 0.30, 0.30, 0.30],
            )
        )

    for index in range(10):
        before = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        after = before.copy()
        small = 28 + index % 4
        large = 82 + index % 5
        subject_x, subject_y = 80, 108
        cv2.circle(before, (subject_x, subject_y), small // 2, (180, 180, 180), -1)
        cv2.circle(after, (subject_x, subject_y), large // 2, (180, 180, 180), -1)
        cv2.line(before, (100, 120), (220, 120), (255, 255, 255), 4)
        cv2.line(after, (20, 120), (300, 120), (255, 255, 255), 4)
        cases.append(
            _recommendation_pair(
                root,
                f"generated-recommendation-closer-{index:02d}",
                before,
                after,
                action="MOVE_CLOSER",
                group="closer",
                target_mode="HORIZONTAL",
                subject_box_before=[(subject_x - small / 2) / WIDTH, (subject_y - small / 2) / HEIGHT, small / WIDTH, small / HEIGHT],
                subject_box_after=[(subject_x - large / 2) / WIDTH, (subject_y - large / 2) / HEIGHT, large / WIDTH, large / HEIGHT],
            )
        )

    for index in range(10):
        before = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        after = before.copy()
        cv2.line(before, (90, 20), (230, 20), (255, 255, 255), 5)
        cv2.line(after, (20, 20), (300, 20), (255, 255, 255), 5)
        cases.append(
            _recommendation_pair(
                root,
                f"generated-recommendation-back-{index:02d}",
                before,
                after,
                action="MOVE_BACK",
                group="back",
                target_mode="HORIZONTAL",
                subject_box_before=[-0.25, 0.10, 0.75, 0.75],
                subject_box_after=[0.20, 0.15, 0.60, 0.70],
            )
        )
    return cases


def generate_cases(manifest_path: str | Path) -> list[dict]:
    manifest_path = Path(manifest_path)
    payload = json.loads(manifest_path.read_text())
    generated = _degraded_cases(manifest_path.parent) + _recommendation_cases(manifest_path.parent)
    retained = [case for case in payload.get("cases", []) if not str(case.get("id", "")).startswith("generated-")]
    payload["cases"] = retained + generated
    manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return generated


if __name__ == "__main__":
    default_manifest = Path(__file__).with_name("manifest.json")
    cases = generate_cases(default_manifest)
    print(f"generated {len(cases)} deterministic acceptance cases")
