"""Audit video, landmark, annotation, and event-detector time bases.

The article-2 event comparison originally assumed that decoded video frames,
landmark-array indices, and annotation times shared frame zero and a constant
frame rate. This script checks those assumptions with decoded presentation
timestamps and writes session- and event-level audit tables.

Outputs:
    second_article_outputs/timebase_audit_sessions.csv
    second_article_outputs/timebase_audit_events.csv
    second_article_outputs/timebase_audit_summary.md
    second_article_outputs/figures/fig_event_frame_identity.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import av
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import second_article_common as common


def _decode_presentation_times(video_path: Path) -> tuple[np.ndarray, float]:
    """Return decoded frame presentation times and nominal average FPS."""
    times: list[float] = []
    with av.open(str(video_path)) as container:
        stream = container.streams.video[0]
        nominal_fps = float(stream.average_rate) if stream.average_rate else np.nan
        for frame in container.decode(stream):
            if frame.time is not None:
                times.append(float(frame.time))
            elif frame.pts is not None and frame.time_base is not None:
                times.append(float(frame.pts * frame.time_base))
            else:
                times.append(np.nan)
    return np.asarray(times, dtype=float), nominal_fps


def _load_landmark_times(session_folder: Path) -> np.ndarray:
    path = session_folder / "mediapipe_data_full.json"
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    values = payload.get("values", payload)
    return np.asarray(
        [pd.to_numeric(frame.get("time"), errors="coerce") for frame in values],
        dtype=float,
    )


def _timing_diagnostics(times: np.ndarray) -> dict[str, float | int | bool]:
    finite = times[np.isfinite(times)]
    diffs = np.diff(finite)
    positive = diffs[diffs > 0]
    median_dt = float(np.median(positive)) if positive.size else np.nan
    max_dt_deviation = (
        float(np.max(np.abs(positive - median_dt))) if positive.size else np.nan
    )
    # A 0.1 ms tolerance is strict enough to identify variable presentation
    # intervals without flagging ordinary rational-rate rounding.
    variable_intervals = bool(
        positive.size and np.any(np.abs(positive - median_dt) > 1e-4)
    )
    return {
        "n": int(len(times)),
        "first_s": float(finite[0]) if finite.size else np.nan,
        "last_s": float(finite[-1]) if finite.size else np.nan,
        "median_dt_s": median_dt,
        "max_dt_deviation_s": max_dt_deviation,
        "nonmonotonic_steps": int(np.sum(diffs <= 0)) if diffs.size else 0,
        "variable_intervals": variable_intervals,
    }


def audit_sessions(subset: pd.DataFrame, annotations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, item in subset.iterrows():
        session_id = str(item["session_id"])
        folder = Path(item["session_folder"])
        video_times, nominal_fps = _decode_presentation_times(
            folder / "video_processed.mp4"
        )
        landmark_times = _load_landmark_times(folder)
        video = _timing_diagnostics(video_times)
        landmarks = _timing_diagnostics(landmark_times)

        ann = annotations[annotations["session_id"].astype(str) == session_id]
        ann_offsets = []
        for _, record in ann.iterrows():
            frame_idx = pd.to_numeric(record.get("reference_frame"), errors="coerce")
            reference_time = pd.to_numeric(
                record.get("reference_time_s"), errors="coerce"
            )
            if (
                pd.notna(frame_idx)
                and pd.notna(reference_time)
                and 0 <= int(frame_idx) < len(video_times)
                and np.isfinite(video_times[int(frame_idx)])
            ):
                pts_from_zero = video_times[int(frame_idx)] - video_times[0]
                ann_offsets.append(float(reference_time - pts_from_zero))

        n_common = min(len(video_times), len(landmark_times))
        grid_diff = np.array([], dtype=float)
        if n_common and np.isfinite(video_times[:n_common]).all():
            video_from_zero = video_times[:n_common] - video_times[0]
            grid_diff = landmark_times[:n_common] - video_from_zero
            grid_diff = grid_diff[np.isfinite(grid_diff)]

        rows.append(
            {
                "session_id": session_id,
                "video_frames_decoded": video["n"],
                "landmark_frames": landmarks["n"],
                "frame_count_difference": int(video["n"]) - int(landmarks["n"]),
                "video_nominal_fps": nominal_fps,
                "video_median_dt_ms": float(video["median_dt_s"]) * 1000.0,
                "video_max_dt_deviation_ms": (
                    float(video["max_dt_deviation_s"]) * 1000.0
                ),
                "video_variable_intervals": video["variable_intervals"],
                "video_nonmonotonic_steps": video["nonmonotonic_steps"],
                "landmark_median_dt_ms": float(landmarks["median_dt_s"]) * 1000.0,
                "landmark_max_dt_deviation_ms": (
                    float(landmarks["max_dt_deviation_s"]) * 1000.0
                ),
                "landmark_nonmonotonic_steps": landmarks["nonmonotonic_steps"],
                "max_landmark_video_grid_difference_ms": (
                    float(np.max(np.abs(grid_diff))) * 1000.0
                    if grid_diff.size
                    else np.nan
                ),
                "max_annotation_pts_difference_ms": (
                    float(np.max(np.abs(ann_offsets))) * 1000.0
                    if ann_offsets
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def audit_events(
    subset: pd.DataFrame,
    annotations: pd.DataFrame,
    dataset_summary: pd.DataFrame,
) -> pd.DataFrame:
    summaries = dataset_summary.set_index(dataset_summary["session_id"].astype(str))
    rows = []
    event_names = ["top_backswing", "downswing_transition", "impact"]
    for _, item in subset.iterrows():
        session_id = str(item["session_id"])
        folder = Path(item["session_folder"])
        video_times, _ = _decode_presentation_times(folder / "video_processed.mp4")
        session_ann = annotations[
            annotations["session_id"].astype(str) == session_id
        ]
        if session_id not in summaries.index:
            continue
        summary = summaries.loc[session_id]
        if isinstance(summary, pd.DataFrame):
            summary = summary.iloc[0]

        for event in event_names:
            reference = session_ann[session_ann["event_name"] == event]
            if reference.empty:
                continue
            reference = reference.iloc[0]
            manual_frame = int(reference["reference_frame"])
            if event == "impact":
                auto_frame = int(summary["impact_idx_auto"])
                auto_source = "impact detector"
            else:
                auto_frame = int(summary["transition_idx_auto"])
                auto_source = "shared transition proxy"

            manual_pts = (
                video_times[manual_frame] - video_times[0]
                if 0 <= manual_frame < len(video_times)
                else np.nan
            )
            auto_pts = (
                video_times[auto_frame] - video_times[0]
                if 0 <= auto_frame < len(video_times)
                else np.nan
            )
            rows.append(
                {
                    "session_id": session_id,
                    "comparison": (
                        "transition proxy vs manual top"
                        if event == "top_backswing"
                        else (
                            "transition proxy vs manual downswing transition"
                            if event == "downswing_transition"
                            else "impact detector vs manual impact"
                        )
                    ),
                    "manual_event": event,
                    "auto_source": auto_source,
                    "manual_frame": manual_frame,
                    "automatic_frame": auto_frame,
                    "signed_error_frames": auto_frame - manual_frame,
                    "absolute_error_frames": abs(auto_frame - manual_frame),
                    "manual_pts_s": manual_pts,
                    "automatic_pts_s": auto_pts,
                    "signed_error_pts_ms": (
                        (auto_pts - manual_pts) * 1000.0
                        if np.isfinite(auto_pts) and np.isfinite(manual_pts)
                        else np.nan
                    ),
                }
            )
    return pd.DataFrame(rows)


def make_identity_figure(events: pd.DataFrame, output: Path) -> None:
    labels = {
        "top_backswing": ("Manual top", "#8064a2", "o"),
        "downswing_transition": ("Manual transition", "#4f81bd", "s"),
        "impact": ("Manual impact", "#c0504d", "^"),
    }
    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    for event, group in events.groupby("manual_event"):
        label, color, marker = labels[event]
        ax.scatter(
            group["manual_frame"],
            group["automatic_frame"],
            label=label,
            color=color,
            marker=marker,
            alpha=0.8,
            s=18,
        )
    upper = float(
        max(events["manual_frame"].max(), events["automatic_frame"].max())
    )
    ax.plot([0, upper], [0, upper], color="black", linestyle="--", label="Identity")
    ax.set_xlabel("Manual frame", fontsize=8)
    ax.set_ylabel("Automatic frame", fontsize=8)
    ax.set_title("Automatic versus manual event frames", fontsize=8.5)
    ax.tick_params(labelsize=7.5)
    ax.legend(frameon=False, fontsize=6.5)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output.with_suffix(".png"), dpi=400)
    fig.savefig(output.with_suffix(".svg"))
    plt.close(fig)


def bootstrap_ci(values: pd.Series, seed: int = 20260728) -> tuple[float, float]:
    array = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if not len(array):
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    estimates = np.asarray(
        [
            np.median(rng.choice(array, size=len(array), replace=True))
            for _ in range(10_000)
        ]
    )
    return tuple(np.quantile(estimates, [0.025, 0.975]))


def write_summary(
    sessions: pd.DataFrame,
    events: pd.DataFrame,
    output_path: Path,
) -> None:
    lines = [
        "# Article 2 time-base audit",
        "",
        f"- Sessions audited: {len(sessions)}.",
        (
            "- Decoded videos with variable presentation intervals: "
            f"{int(sessions['video_variable_intervals'].sum())}/{len(sessions)}."
        ),
        (
            "- Sessions with unequal decoded-video and landmark frame counts: "
            f"{int((sessions['frame_count_difference'] != 0).sum())}/{len(sessions)}."
        ),
        (
            "- Maximum absolute annotation-time versus decoded-PTS discrepancy: "
            f"{sessions['max_annotation_pts_difference_ms'].max():.3f} ms."
        ),
        (
            "- Maximum absolute landmark-time versus decoded-PTS grid discrepancy "
            f"over shared frames: "
            f"{sessions['max_landmark_video_grid_difference_ms'].max():.3f} ms."
        ),
        "",
        "## Event-frame comparisons",
        "",
    ]
    for comparison, group in events.groupby("comparison", sort=False):
        lo, hi = bootstrap_ci(group["absolute_error_frames"])
        lines.append(
            f"- {comparison}: median absolute error "
            f"{group['absolute_error_frames'].median():.1f} frames "
            f"(session bootstrap 95% CI {lo:.1f}-{hi:.1f}); "
            f"median signed error {group['signed_error_frames'].median():.1f} frames."
        )

    ordered = events.sort_values("absolute_error_frames")
    examples = {
        "smallest observed error": ordered.iloc[0],
        "typical error": ordered.iloc[len(ordered) // 2],
        "largest observed error": ordered.iloc[-1],
    }
    lines.extend(["", "## Diagnostic examples", ""])
    for label, row in examples.items():
        lines.append(
            f"- {label}: session `{row['session_id']}`, {row['comparison']}, "
            f"manual frame {int(row['manual_frame'])}, automatic frame "
            f"{int(row['automatic_frame'])}, signed error "
            f"{int(row['signed_error_frames'])} frames."
        )
    lines.extend(
        [
            "",
            "The top-of-backswing and downswing-transition rows are definition "
            "comparisons against one shared automatic transition output; they are "
            "not independent event detectors.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit article-2 event time bases.")
    parser.add_argument(
        "--subset",
        default=str(common.REFERENCE_SUBSET_CSV),
    )
    parser.add_argument(
        "--annotations",
        default=str(common.CONSENSUS_ANNOTATIONS_CSV),
    )
    parser.add_argument(
        "--dataset-summary",
        default=str(common.DATASET_SUMMARY_CSV),
    )
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    if args.out_dir:
        common.configure_article2_outputs(args.out_dir)
    else:
        common.ensure_output_dirs()
    subset = pd.read_csv(args.subset)
    annotations = pd.read_csv(args.annotations)
    # Timebase audit may include multi-rater rows; keep all for provenance checks
    # but prefer consensus file by default.
    dataset_summary = pd.read_csv(args.dataset_summary)

    sessions = audit_sessions(subset, annotations)
    events = audit_events(subset, annotations, dataset_summary)
    sessions.to_csv(common.OUTPUT_DIR / "timebase_audit_sessions.csv", index=False)
    events.to_csv(common.OUTPUT_DIR / "timebase_audit_events.csv", index=False)
    make_identity_figure(
        events,
        common.FIGURE_DIR / "fig_event_frame_identity",
    )
    write_summary(
        sessions,
        events,
        common.OUTPUT_DIR / "timebase_audit_summary.md",
    )
    print(f"Audited {len(sessions)} sessions and {len(events)} event comparisons.")
    print(f"Annotations: {args.annotations}")


if __name__ == "__main__":
    main()
