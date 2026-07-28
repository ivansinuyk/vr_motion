"""Shared helpers for the second-article validation/robustness workflow.

This module centralizes paths, dataset metadata parsing, and small utilities
that the six article-2 scripts reuse. It intentionally builds on top of the
first-article engine in ``batch_article_evaluation.py`` instead of duplicating
the processing pipeline.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

# Default dataset root verified during the pre-analysis pass (71 sessions).
DEFAULT_DATASET_ROOT = (
    r"C:\Users\isinu\Downloads\Telegram Desktop"
    r"\7a0c087a-b6c7-42ea-bc67-63453d4cac7f"
)

# Output locations for the second article.
OUTPUT_DIR = Path("second_article_outputs")
FIGURE_DIR = OUTPUT_DIR / "figures"

# First-article outputs that we reuse as inputs (read-only).
FIRST_ARTICLE_OUTPUTS = Path("article_package/evaluation_outputs")
DATASET_SUMMARY_CSV = FIRST_ARTICLE_OUTPUTS / "dataset_summary.csv"

# Canonical reference-annotation file produced by ``annotate_reference.py``.
REFERENCE_ANNOTATIONS_CSV = OUTPUT_DIR / "reference_annotations.csv"

REFERENCE_ANNOTATION_COLUMNS = [
    "session_id",
    "video_path",
    "fps",
    "frame_width",
    "frame_height",
    "event_name",
    "reference_frame",
    "reference_time_s",
    "point_name",
    "x_px",
    "y_px",
    "annotator_id",
    "annotation_round",
    "quality_note",
]

# Swing events we attempt to validate.
EVENT_NAMES = ["address", "top_backswing", "downswing_transition", "impact"]


def ensure_output_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def _norm(text) -> str:
    return str(text or "").strip().lower()


def parse_viewpoint(tags: str, capture_tags: str) -> str:
    """Return a coarse camera viewpoint label (dtl / face_on / other)."""
    blob = f"{_norm(tags)} {_norm(capture_tags)}"
    if "view=dtl" in blob or " dtl" in f" {blob}" or "down the line" in blob:
        return "dtl"
    if "view=fo" in blob or "face on" in blob or "face-on" in blob or "frontal" in blob:
        return "face_on"
    return "other"


def parse_club(tags: str) -> str:
    blob = _norm(tags)
    for club in ("driver", "iron", "wedge", "hybrid", "putter", "wood"):
        if club in blob:
            return club
    return "unknown"


def parse_motion_class(tags: str, is_slow_motion, fps) -> str:
    """Classify capture speed: super_slow / slow / regular."""
    blob = _norm(tags)
    if "super slow" in blob or "super-slow" in blob:
        return "super_slow"
    if "slow motion" in blob or "slow-motion" in blob or _norm(is_slow_motion) == "true":
        return "slow"
    return "regular"


def fps_bucket(fps) -> str:
    try:
        f = float(fps)
    except (TypeError, ValueError):
        return "unknown"
    if np.isnan(f):
        return "unknown"
    if f <= 30.5:
        return "<=30"
    if f <= 60.5:
        return "31-60"
    if f <= 120.5:
        return "61-120"
    return ">120"


def resolution_bucket(width, height) -> str:
    try:
        w = int(float(width))
        h = int(float(height))
    except (TypeError, ValueError):
        return "unknown"
    long_side = max(w, h)
    if long_side >= 1900:
        return "1080p+"
    if long_side >= 1200:
        return "720-1080p"
    return "<720p"


def parse_quality(tags: str, capture_tags: str) -> dict:
    blob = f"{_norm(tags)} {_norm(capture_tags)}"
    return {
        "keyframes_issue": "keyframes issue" in blob,
        "motion_blur": ("motion_blur=" in blob and "motion_blur=none" not in blob)
        or ("blur" in blob and "no blur" not in blob and "motion_blur=none" not in blob),
        "occlusion": ("occlusion=" in blob and "occlusion=none" not in blob)
        or (" occlusion" in f" {blob}" and "no occlusion" not in blob and "occlusion=none" not in blob),
    }


def quality_grade(quality: dict) -> str:
    """Coarse difficulty grade used for stratified selection."""
    issues = sum(bool(quality.get(k)) for k in ("keyframes_issue", "motion_blur", "occlusion"))
    if issues == 0:
        return "good"
    if issues == 1:
        return "medium"
    return "difficult"


def load_dataset_metadata(summary_csv: Path = DATASET_SUMMARY_CSV) -> pd.DataFrame:
    """Load and enrich the first-article dataset summary with article-2 strata.

    Falls back gracefully if some columns are missing.
    """
    df = pd.read_csv(summary_csv)
    enriched = []
    for _, row in df.iterrows():
        tags = row.get("tags", "")
        capture_tags = row.get("capture_tags", "")
        fps = row.get("video_fps_cv", row.get("video_fps_meta", np.nan))
        quality = parse_quality(tags, capture_tags)
        enriched.append(
            {
                "session_id": row.get("session_id", ""),
                "session_folder": row.get("session_folder", ""),
                "processed": row.get("processed", False),
                "fps": fps,
                "width": row.get("width_cv", row.get("video_width", np.nan)),
                "height": row.get("height_cv", row.get("video_height", np.nan)),
                "frames": row.get("frames_json", np.nan),
                "viewpoint": parse_viewpoint(tags, capture_tags),
                "club": parse_club(tags),
                "motion_class": parse_motion_class(tags, row.get("is_slow_motion", ""), fps),
                "fps_bucket": fps_bucket(fps),
                "resolution_bucket": resolution_bucket(
                    row.get("width_cv", np.nan), row.get("height_cv", np.nan)
                ),
                "keyframes_issue": quality["keyframes_issue"],
                "motion_blur": quality["motion_blur"],
                "occlusion": quality["occlusion"],
                "quality_grade": quality_grade(quality),
                "tags": tags,
            }
        )
    return pd.DataFrame(enriched)


def session_folder(dataset_root: str, session_id: str) -> Path:
    return Path(dataset_root) / session_id
