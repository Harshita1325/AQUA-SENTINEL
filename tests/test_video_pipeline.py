"""
Unit tests for the advanced underwater video processing pipeline.

These smoke-style tests validate critical behaviors without requiring
the heavyweight UIEB/EUVP or YOLO models by injecting lightweight stubs.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from webapp.video_processor import (  # noqa: E402
    TemporalTracker,
    ThreatRuleEngine,
    VideoProcessingConfig,
    VideoProcessor,
)


def _make_test_video(tmp_path: Path, frame_count: int = 10, fps: int = 10) -> Path:
    """Create a synthetic grayscale video for deterministic tests."""
    video_path = tmp_path / "test_video.mp4"
    writer = cv2.VideoWriter(
        str(video_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (64, 64),
    )
    for i in range(frame_count):
        frame = np.full((64, 64, 3), i * 15, dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return video_path


def test_frame_generator_preserves_order_and_timestamps(tmp_path):
    video = _make_test_video(tmp_path, frame_count=5, fps=5)
    processor = VideoProcessor(autoload_models=False)
    cap = cv2.VideoCapture(str(video))
    frames = list(processor._frame_generator(cap, mode="batch"))
    cap.release()

    indices = [idx for idx, _, _ in frames]
    timestamps = [ts for _, ts, _ in frames]

    assert indices == list(range(5)), "Frame indices must remain sequential"
    assert timestamps == sorted(timestamps), "Frame timestamps must be monotonic"


def test_temporal_smoothing_prevents_large_flicker():
    processor = VideoProcessor(autoload_models=False)
    bright = np.full((32, 32, 3), 250, dtype=np.uint8)
    dark = np.full((32, 32, 3), 30, dtype=np.uint8)

    processor._apply_temporal_smoothing(bright)
    smoothed = processor._apply_temporal_smoothing(dark)

    # Smoothing should pull the dark frame closer to the previous bright frame
    assert np.mean(smoothed) > np.mean(dark), "Temporal smoothing should reduce flicker"


def test_tracker_id_stability_over_sequence():
    config = VideoProcessingConfig()
    tracker = TemporalTracker(config)

    detections = [
        {"bbox": [10 + i, 10, 40 + i, 40], "class_name": "submarine", "confidence": 0.9}
        for i in range(30)
    ]

    track_ids = set()
    timestamp = 0.0
    for det in detections:
        timestamp += 0.1
        tracks = tracker.update([det], timestamp)
        assert len(tracks) == 1
        track_ids.add(tracks[0].track_id)

    assert len(track_ids) == 1, "Single moving object should retain a stable track ID"


class DummyProcessor(VideoProcessor):
    """Stub processor that skips heavy model/detector loading."""

    def __init__(self):
        super().__init__(autoload_models=False)
        self.rule_engine = ThreatRuleEngine(self.config)
        self.detector = SimpleNamespace()  # placeholder
        self._detection_toggle = False

    def _enhance_frame(self, frame, model_key):
        return frame  # no-op for testing

    def _run_detection(self, frame):
        # Alternate between detection/no detection to exercise log formatting
        if self._detection_toggle:
            self._detection_toggle = False
            return [
                {
                    "bbox": [5, 5, 25, 25],
                    "confidence": 0.8,
                    "class_name": "submarine",
                    "center": (15, 15),
                }
            ]
        self._detection_toggle = True
        return []

    def _estimate_distance(self, detection, image_shape):
        return {"distance_m": 12.0, "distance_display": "~12.0m", "confidence": "high", "error_margin": "±15%"}


def test_process_video_produces_logs_and_summary(tmp_path):
    video = _make_test_video(tmp_path, frame_count=6, fps=6)
    processor = DummyProcessor()

    output_video = tmp_path / "annotated.mp4"
    log_path = tmp_path / "detections.jsonl"
    summary_path = tmp_path / "summary.json"

    stats = processor.process_video(
        str(video),
        str(output_video),
        log_path=str(log_path),
        summary_path=str(summary_path),
    )

    assert output_video.exists(), "Annotated video file must be created"
    assert log_path.exists(), "Per-frame JSONL log must exist"
    assert summary_path.exists(), "Summary JSON must exist"

    # Validate JSONL structure
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == stats["total_frames"]
    first_entry = json.loads(lines[0])
    assert {"frame_index", "timestamp", "detections", "tracks"} <= first_entry.keys()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "tracks" in summary and isinstance(summary["tracks"], list)


if __name__ == "__main__":
    pytest.main([__file__])

