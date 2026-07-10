from __future__ import annotations

import cv2
import numpy as np

from src.core.entities import FusedSubject, SaliencyMap, SourceType

from .features import CompositionFeatures, ContourFeature, FocusFeature, LineFeature
from .geometry import angle_degrees, line_intersection, orientation_histogram
from .thresholds import (
    ANALYSIS_MAX_EDGE,
    MAX_LINE_GAP_RATIO,
    MIN_LINE_LENGTH_RATIO,
    ORIENTATION_BINS,
)


def _readonly(array: np.ndarray) -> np.ndarray:
    array.setflags(write=False)
    return array


class CompositionFeatureExtractor:
    def __init__(self, max_edge: int = ANALYSIS_MAX_EDGE):
        self.max_edge = max_edge

    def extract(
        self,
        frame: np.ndarray,
        subjects: list[FusedSubject],
        saliency: SaliencyMap | None,
    ) -> CompositionFeatures:
        if frame is None or frame.size == 0:
            raise ValueError("empty frame")
        frame_height, frame_width = frame.shape[:2]
        scale = min(1.0, self.max_edge / max(frame_width, frame_height))
        analysis_width = max(1, round(frame_width * scale))
        analysis_height = max(1, round(frame_height * scale))
        small = cv2.resize(frame, (analysis_width, analysis_height), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        gx = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
        magnitude, gradient_angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)

        raw_lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            threshold=max(18, int(max(analysis_width, analysis_height) * 0.08)),
            minLineLength=max(12, int(max(analysis_width, analysis_height) * MIN_LINE_LENGTH_RATIO)),
            maxLineGap=max(3, int(max(analysis_width, analysis_height) * MAX_LINE_GAP_RATIO)),
        )
        line_values = np.empty((0, 4), dtype=np.float32)
        if raw_lines is not None:
            line_values = raw_lines.reshape(-1, 4).astype(np.float32)
        lines = tuple(
            LineFeature(
                x1=float(x1) / analysis_width,
                y1=float(y1) / analysis_height,
                x2=float(x2) / analysis_width,
                y2=float(y2) / analysis_height,
                angle=angle_degrees((x1, y1, x2, y2)),
                length=float(np.hypot(x2 - x1, y2 - y1)) / np.hypot(analysis_width, analysis_height),
            )
            for x1, y1, x2, y2 in line_values
        )

        raw_contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        hierarchy_values = hierarchy[0] if hierarchy is not None else np.empty((0, 4), dtype=int)
        contours: list[ContourFeature] = []
        min_perimeter = max(analysis_width, analysis_height) * 0.1
        for index, contour in enumerate(raw_contours):
            perimeter = float(cv2.arcLength(contour, True))
            if perimeter < min_perimeter:
                continue
            area = float(abs(cv2.contourArea(contour)))
            x, y, width, height = cv2.boundingRect(contour)
            rectangularity = area / max(1.0, float(width * height))
            parent = int(hierarchy_values[index][3]) if len(hierarchy_values) else -1
            depth = 0
            ancestor = parent
            while ancestor >= 0 and depth < 12:
                depth += 1
                ancestor = int(hierarchy_values[ancestor][3])
            normalized = contour.reshape(-1, 2).astype(np.float32)
            normalized[:, 0] /= analysis_width
            normalized[:, 1] /= analysis_height
            contours.append(
                ContourFeature(
                    points=_readonly(normalized),
                    area=area / (analysis_width * analysis_height),
                    perimeter=perimeter / (2 * (analysis_width + analysis_height)),
                    parent=parent,
                    depth=depth,
                    rectangularity=rectangularity,
                )
            )

        corners = cv2.goodFeaturesToTrack(gray, 40, 0.02, max(4, analysis_width // 40))
        if corners is None:
            normalized_corners = np.empty((0, 2), dtype=np.float32)
        else:
            normalized_corners = corners.reshape(-1, 2).astype(np.float32)
            normalized_corners[:, 0] /= analysis_width
            normalized_corners[:, 1] /= analysis_height

        intersections: list[tuple[float, float]] = []
        for first_index, first in enumerate(line_values[:30]):
            for second in line_values[first_index + 1 : 30]:
                if abs(angle_degrees(tuple(first)) - angle_degrees(tuple(second))) < 12:
                    continue
                point = line_intersection(tuple(first), tuple(second), (analysis_width, analysis_height))
                if point:
                    intersections.append((point[0] / analysis_width, point[1] / analysis_height))
        intersection_array = np.asarray(intersections, dtype=np.float32).reshape(-1, 2)

        saliency_map = np.zeros((analysis_height, analysis_width), dtype=np.float32)
        if saliency is not None and isinstance(saliency.heatmap, np.ndarray) and saliency.heatmap.size:
            saliency_map = cv2.resize(
                saliency.heatmap.astype(np.float32), (analysis_width, analysis_height)
            )
            maximum = float(saliency_map.max())
            if maximum > 0:
                saliency_map /= maximum

        visual_mass = saliency_map * 0.45
        primary = next((subject for subject in subjects if subject.is_primary_subject), None)
        primary_focus: FocusFeature | None = None
        subject_area_ratio = 0.0
        subject_clipped = False
        for subject in subjects:
            box = subject.bounding_box
            x1 = int(np.clip(box.x * scale, 0, analysis_width - 1))
            y1 = int(np.clip(box.y * scale, 0, analysis_height - 1))
            x2 = int(np.clip((box.x + box.width) * scale, x1 + 1, analysis_width))
            y2 = int(np.clip((box.y + box.height) * scale, y1 + 1, analysis_height))
            contribution = 0.55 if subject.is_primary_subject else 0.30
            visual_mass[y1:y2, x1:x2] += contribution * subject.confidence
        if primary is not None:
            box = primary.bounding_box
            center_x = (box.x + box.width / 2.0) / frame_width
            center_y = (box.y + box.height / 2.0) / frame_height
            primary_focus = FocusFeature(
                x=float(np.clip(center_x, 0, 1)),
                y=float(np.clip(center_y, 0, 1)),
                weight=float(np.clip(primary.confidence, 0, 1)),
                source=(
                    "saliency"
                    if primary.source is SourceType.SALIENCY
                    else "subject"
                ),
            )
            subject_area_ratio = float(np.clip(box.width * box.height / (frame_width * frame_height), 0, 1))
            subject_clipped = (
                box.x <= 1 or box.y <= 1 or box.x + box.width >= frame_width - 1 or box.y + box.height >= frame_height - 1
            )
        elif saliency_map.max() > 0:
            y, x = np.unravel_index(int(np.argmax(saliency_map)), saliency_map.shape)
            primary_focus = FocusFeature(
                x=float(x / analysis_width),
                y=float(y / analysis_height),
                weight=float(np.clip(saliency.max_salient_score if saliency else 0, 0, 1)),
                source="saliency",
            )

        total_mass = float(visual_mass.sum())
        if total_mass > 0:
            yy, xx = np.indices(visual_mass.shape)
            mass_centroid = (
                float((visual_mass * xx).sum() / total_mass / analysis_width),
                float((visual_mass * yy).sum() / total_mass / analysis_height),
            )
        else:
            mass_centroid = (0.5, 0.5)
        half_h, half_w = analysis_height // 2, analysis_width // 2
        quadrant_values = (
            float(visual_mass[:half_h, :half_w].sum()),
            float(visual_mass[:half_h, half_w:].sum()),
            float(visual_mass[half_h:, :half_w].sum()),
            float(visual_mass[half_h:, half_w:].sum()),
        )
        quadrant_total = sum(quadrant_values)
        quadrant_mass = tuple(value / quadrant_total for value in quadrant_values) if quadrant_total else (0.25,) * 4

        edge_density = float(np.count_nonzero(edges)) / edges.size
        structure_signal = min(1.0, len(lines) / 8.0 + len(contours) / 12.0)
        focus_signal = primary_focus.weight if primary_focus else 0.0
        evidence_quality = float(np.clip(edge_density * 3.0 + structure_signal * 0.45 + focus_signal * 0.35, 0, 1))

        histogram = orientation_histogram(line_values, ORIENTATION_BINS)
        for array in (
            gray,
            edges,
            magnitude,
            gradient_angle,
            normalized_corners,
            intersection_array,
            histogram,
            visual_mass,
        ):
            _readonly(array)

        return CompositionFeatures(
            frame_width=frame_width,
            frame_height=frame_height,
            analysis_width=analysis_width,
            analysis_height=analysis_height,
            gray=gray,
            edges=edges,
            gradient_magnitude=magnitude,
            gradient_angle=gradient_angle,
            lines=lines,
            contours=tuple(contours),
            corners=normalized_corners,
            intersections=intersection_array,
            orientation_histogram=histogram,
            visual_mass=visual_mass,
            mass_centroid=mass_centroid,
            quadrant_mass=quadrant_mass,
            primary_focus=primary_focus,
            subject_area_ratio=subject_area_ratio,
            subject_clipped=subject_clipped,
            evidence_quality=evidence_quality,
        )
