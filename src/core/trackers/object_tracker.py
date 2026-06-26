from typing import List, Dict, Optional
import math
from src.core.entities import DetectedSubject, TrackedSubject, BoundingBox

class ObjectTracker:
    """
    A lightweight Centroid tracking algorithm.
    """
    def __init__(self, max_disappeared=5, max_distance=100.0, intersection_x_thresholds=None):
        self.next_track_id = 0
        self.tracks: Dict[int, TrackedSubject] = {}
        self.disappeared: Dict[int, int] = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        # Composition nodes to check against (e.g., rule of thirds vertical lines)
        self.intersection_x_thresholds = intersection_x_thresholds or []

    def _get_centroid(self, box: BoundingBox) -> tuple[float, float]:
        return (box.x + box.width / 2.0, box.y + box.height / 2.0)

    def _calculate_distance(self, c1: tuple[float, float], c2: tuple[float, float]) -> float:
        return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

    def register(self, subject: DetectedSubject) -> TrackedSubject:
        ts = TrackedSubject(
            track_id=self.next_track_id,
            subject_id=subject.subject_id,
            class_name=subject.class_name,
            confidence=subject.confidence,
            bounding_box=subject.bounding_box,
            keypoints=subject.keypoints,
            is_primary_subject=subject.is_primary_subject,
            history=[subject.bounding_box]
        )
        self.tracks[self.next_track_id] = ts
        self.disappeared[self.next_track_id] = 0
        self.next_track_id += 1
        return ts

    def deregister(self, track_id: int):
        del self.tracks[track_id]
        del self.disappeared[track_id]

    def update(self, detections: List[DetectedSubject], image_width: Optional[float] = None) -> List[TrackedSubject]:
        if image_width is not None and getattr(self, '_last_width', None) != image_width:
            self._last_width = image_width
            self.intersection_x_thresholds = [image_width / 3.0, 2.0 * image_width / 3.0]
            
        if len(detections) == 0:
            for track_id in list(self.disappeared.keys()):
                self.disappeared[track_id] += 1
                if self.disappeared[track_id] > self.max_disappeared:
                    self.deregister(track_id)
            return list(self.tracks.values())

        input_centroids = [self._get_centroid(d.bounding_box) for d in detections]

        if len(self.tracks) == 0:
            for d in detections:
                self.register(d)
        else:
            track_ids = list(self.tracks.keys())
            track_centroids = [self._get_centroid(t.bounding_box) for t in self.tracks.values()]

            # Compute distance matrix
            distances = [
                [self._calculate_distance(t_cent, d_cent) for d_cent in input_centroids]
                for t_cent in track_centroids
            ]

            # Find matches (greedy)
            used_t = set()
            used_d = set()

            for t_idx in range(len(track_ids)):
                if t_idx in used_t: continue
                
                min_dist = float('inf')
                min_d_idx = -1
                for d_idx in range(len(input_centroids)):
                    if d_idx in used_d: continue
                    d = distances[t_idx][d_idx]
                    if d < min_dist:
                        min_dist = d
                        min_d_idx = d_idx

                if min_d_idx != -1 and min_dist < self.max_distance:
                    track_id = track_ids[t_idx]
                    t_subj = self.tracks[track_id]
                    d_subj = detections[min_d_idx]

                    # Update history and calculate velocity
                    old_c = self._get_centroid(t_subj.bounding_box)
                    new_c = self._get_centroid(d_subj.bounding_box)
                    t_subj.velocity_x = new_c[0] - old_c[0]
                    t_subj.velocity_y = new_c[1] - old_c[1]

                    t_subj.bounding_box = d_subj.bounding_box
                    t_subj.confidence = d_subj.confidence
                    t_subj.history.append(d_subj.bounding_box)
                    # keep history small
                    if len(t_subj.history) > 10:
                        t_subj.history.pop(0)

                    self._check_composition_intersection(t_subj, new_c)

                    self.disappeared[track_id] = 0
                    used_t.add(t_idx)
                    used_d.add(min_d_idx)

            # Handle unmatched tracks
            for t_idx in range(len(track_ids)):
                if t_idx not in used_t:
                    track_id = track_ids[t_idx]
                    self.disappeared[track_id] += 1
                    if self.disappeared[track_id] > self.max_disappeared:
                        self.deregister(track_id)

            # Register unmatched detections
            for d_idx in range(len(input_centroids)):
                if d_idx not in used_d:
                    self.register(detections[d_idx])

        return list(self.tracks.values())

    def _check_composition_intersection(self, subject: TrackedSubject, current_c: tuple[float, float]):
        subject.will_intersect_composition_node = False
        subject.time_to_intersection = 0.0

        if not self.intersection_x_thresholds or subject.velocity_x == 0:
            return

        for threshold in self.intersection_x_thresholds:
            # If moving towards the threshold
            if (subject.velocity_x > 0 and current_c[0] < threshold) or \
               (subject.velocity_x < 0 and current_c[0] > threshold):
                
                distance = abs(threshold - current_c[0])
                # We expect them to cross within ~10 frames (approx 0.3-0.5s if 20-30fps)
                frames_to_intersect = distance / abs(subject.velocity_x)
                if frames_to_intersect < 15:
                    subject.will_intersect_composition_node = True
                    subject.time_to_intersection = frames_to_intersect / 30.0 # roughly assuming 30fps baseline
                    break
