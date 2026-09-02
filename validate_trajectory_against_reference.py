"""Article 2 - Script 3: validate processed stick-tip trajectory vs manual points.

For each manually annotated stick-tip control point, finds the processed
(smoothed) tip position at the matching time and computes geometric error in
pixels, normalized coordinates, and metres (using the per-frame scale). Errors
are grouped by swing phase, viewpoint, and quality.

This script requires manual point annotations (no synthetic fallback is
possible - the dataset contains no per-frame stick-tip ground truth).

Outputs:
    second_article_outputs/trajectory_reference_errors.csv
    second_article_outputs/trajectory_reference_summary.csv
    second_article_outputs/figures/fig_trajectory_error_distribution.png
    second_article_outputs/figures/fig_trajectory_error_by_phase.png

Run:
    python validate_trajectory_against_reference.py
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
import second_article_common as common
from batch_article_evaluation import (
    _extract_raw_tip_base,
    _scale_series,
    process_session,
)


def load_manual_points(
    annotations_csv=None,
    annotator_id=None,
    annotation_round=None,
):
    path = Path(annotations_csv) if annotations_csv else common.REFERENCE_ANNOTATIONS_CSV
    if not path.exists():
        return pd.DataFrame()
    df = common.load_reference_annotations(
        path,
        annotator_id=annotator_id,
        annotation_round=annotation_round,
        require_single_rater=True,
    )
    pts = df[df["point_name"].astype(str).str.len() > 0].copy()
    for col in ("x_px", "y_px", "reference_time_s", "reference_frame"):
        pts[col] = pd.to_numeric(pts[col], errors="coerce")
    return pts.dropna(subset=["x_px", "y_px"])


def load_manual_events(annotations_csv=None, annotator_id=None, annotation_round=None):
    """Return {session_id: {event_name: reference_time_s}} from the reference."""
    path = Path(annotations_csv) if annotations_csv else common.REFERENCE_ANNOTATIONS_CSV
    if not path.exists():
        return {}
    df = common.load_reference_annotations(
        path,
        annotator_id=annotator_id,
        annotation_round=annotation_round,
        require_single_rater=True,
    )
    ev = df[df["event_name"].astype(str).str.len() > 0].copy()
    ev = ev[ev["point_name"].isna() | (ev["point_name"].astype(str).str.len() == 0)]
    ev["reference_time_s"] = pd.to_numeric(ev["reference_time_s"], errors="coerce")
    out = {}
    for sid, g in ev.groupby("session_id"):
        out[str(sid)] = {
            str(r["event_name"]): float(r["reference_time_s"])
            for _, r in g.iterrows()
            if pd.notna(r["reference_time_s"])
        }
    return out


def classify_phase(idx, ev_idx, impact_win=2):
    """Classify a frame index into a swing phase using MANUAL event indices.

    ``ev_idx`` maps event names to analyzer frame indices derived from the
    manual reference. Using the manual (trusted) events - not the biased
    automatic ones - keeps the phase boundaries correct.
    """
    top = ev_idx.get("top_backswing")
    trans = ev_idx.get("downswing_transition")
    impact = ev_idx.get("impact")
    start_down = trans if trans is not None else top

    if impact is not None and abs(idx - impact) <= impact_win:
        return "impact_region"
    if top is not None and idx <= top:
        return "backswing"
    if impact is not None and start_down is not None and start_down <= idx <= impact:
        return "downswing"
    if impact is not None and idx > impact:
        return "follow_through"
    if top is not None and start_down is not None and top < idx < start_down:
        return "transition"
    return "unknown"


def compute_errors(points_df, dataset_root, annotations_csv=None, annotator_id=None, annotation_round=None):
    manual_events = load_manual_events(annotations_csv, annotator_id, annotation_round)
    metadata = common.load_dataset_metadata().set_index("session_id")
    rows = []
    for sid, g in points_df.groupby("session_id"):
        folder = common.session_folder(dataset_root, str(sid))
        result = process_session(folder, profile="scientific")
        if not result.get("ok"):
            continue
        fps = result.get("fps", 30.0)
        width = result["width"]
        height = result["height"]
        diag = math.hypot(width, height)
        smoothed = result["analyzer"]._get_export_metrics()["smoothed_tip_px"]
        raw, bases = _extract_raw_tip_base(result["data"], width, height)
        scales = _scale_series(raw, bases)
        n = len(smoothed)
        # Phase boundaries from the MANUAL events (trusted), mapped to frame idx.
        ev_times = manual_events.get(str(sid), {})
        ev_idx = {name: int(round(t * fps)) for name, t in ev_times.items()}
        meta = metadata.loc[str(sid)] if str(sid) in metadata.index else {}

        for _, r in g.iterrows():
            t = r["reference_time_s"]
            if pd.isna(t) and pd.notna(r["reference_frame"]):
                t = r["reference_frame"] / fps
            idx = int(round(t * fps)) if pd.notna(t) else None
            if idx is None or idx < 0 or idx >= n or smoothed[idx] is None:
                continue
            sx, sy = smoothed[idx]
            err_px = math.hypot(sx - r["x_px"], sy - r["y_px"])
            scale = scales[idx] if idx < len(scales) else np.nan
            phase = classify_phase(idx, ev_idx)
            rows.append(
                {
                    "session_id": sid,
                    "point_name": r["point_name"],
                    "frame_idx": idx,
                    "phase": phase,
                    "auto_x_px": sx,
                    "auto_y_px": sy,
                    "ref_x_px": r["x_px"],
                    "ref_y_px": r["y_px"],
                    "error_px": err_px,
                    "error_norm": err_px / diag if diag > 0 else np.nan,
                    "error_m": err_px * scale if not np.isnan(scale) else np.nan,
                    "error_visible_club_fraction": (
                        err_px * scale / config.STICK_REAL_LENGTH_M
                        if not np.isnan(scale) and config.STICK_REAL_LENGTH_M > 0
                        else np.nan
                    ),
                    "viewpoint": meta.get("viewpoint", "unknown"),
                    "fps_bucket": meta.get("fps_bucket", "unknown"),
                    "resolution_bucket": meta.get("resolution_bucket", "unknown"),
                    "quality_grade": meta.get("quality_grade", "unknown"),
                    "motion_class": meta.get("motion_class", "unknown"),
                    "club": meta.get("club", "unknown"),
                    "quality_note": r.get("quality_note", ""),
                }
            )
    return pd.DataFrame(rows)


def summarize_point_level(df):
    rows = []
    for phase, g in df.groupby("phase"):
        for unit in (
            "error_px",
            "error_norm",
            "error_m",
            "error_visible_club_fraction",
        ):
            vals = pd.to_numeric(g[unit], errors="coerce").dropna()
            if vals.empty:
                continue
            rows.append(
                {
                    "group": "phase",
                    "value": phase,
                    "unit": unit,
                    "n": int(len(vals)),
                    "mean": float(vals.mean()),
                    "median": float(vals.median()),
                    "p95": float(vals.quantile(0.95)),
                    "max": float(vals.max()),
                }
            )
    overall = pd.to_numeric(df["error_px"], errors="coerce").dropna()
    if not overall.empty:
        rows.append({"group": "overall", "value": "all", "unit": "error_px",
                     "n": int(len(overall)), "mean": float(overall.mean()),
                     "median": float(overall.median()), "p95": float(overall.quantile(0.95)),
                     "max": float(overall.max())})
    return pd.DataFrame(rows)


def _bootstrap_median_ci(values, seed=20260728, n_boot=10_000):
    values = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if not len(values):
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    estimates = np.asarray(
        [
            np.median(rng.choice(values, size=len(values), replace=True))
            for _ in range(n_boot)
        ]
    )
    return tuple(np.quantile(estimates, [0.025, 0.975]))


def summarize_sessions(df):
    """Summarize session-specific medians so points are not pseudoreplicates."""
    rows = []
    groups = [("all", df)] + list(df.groupby("phase"))
    for phase, group in groups:
        session_values = (
            group.groupby("session_id")
            .agg(
                median_error_px=("error_px", "median"),
                median_error_norm=("error_norm", "median"),
                median_error_m=("error_m", "median"),
                median_error_club_fraction=("error_visible_club_fraction", "median"),
                points=("error_px", "size"),
            )
            .reset_index()
        )
        px_ci = _bootstrap_median_ci(session_values["median_error_px"])
        norm_ci = _bootstrap_median_ci(session_values["median_error_norm"])
        rows.append(
            {
                "phase": phase,
                "sessions_n": int(session_values["session_id"].nunique()),
                "points_n": int(len(group)),
                "median_of_session_medians_px": float(
                    session_values["median_error_px"].median()
                ),
                "median_px_ci_lower": px_ci[0],
                "median_px_ci_upper": px_ci[1],
                "median_of_session_medians_norm": float(
                    session_values["median_error_norm"].median()
                ),
                "median_norm_ci_lower": norm_ci[0],
                "median_norm_ci_upper": norm_ci[1],
                "median_of_session_medians_m": float(
                    session_values["median_error_m"].median()
                ),
                "median_of_session_medians_club_fraction": float(
                    session_values["median_error_club_fraction"].median()
                ),
                "point_level_p95_px": float(group["error_px"].quantile(0.95)),
                "point_level_max_px": float(group["error_px"].max()),
                "points_over_100px_n": int((group["error_px"] > 100).sum()),
                "points_over_250px_n": int((group["error_px"] > 250).sum()),
                "points_over_500px_n": int((group["error_px"] > 500).sum()),
            }
        )
    return pd.DataFrame(rows)


def summarize_availability_and_large_errors(df, annotated_points_n):
    comparable = len(df)
    rows = [
        {
            "criterion": "Coordinate available at annotated frame",
            "threshold_px": np.nan,
            "points_n": comparable,
            "percent": comparable / annotated_points_n * 100.0,
            "sessions_with_at_least_one_n": int(df["session_id"].nunique()),
        }
    ]
    for threshold, label in (
        (100, "Large localization error"),
        (250, "Very large localization error"),
        (500, "Catastrophic localization error"),
    ):
        flagged = df[df["error_px"] > threshold]
        rows.append(
            {
                "criterion": label,
                "threshold_px": threshold,
                "points_n": int(len(flagged)),
                "percent": len(flagged) / comparable * 100.0 if comparable else np.nan,
                "sessions_with_at_least_one_n": int(flagged["session_id"].nunique()),
            }
        )
    return pd.DataFrame(rows)


def summarize_subgroups(df):
    rows = []
    for dimension in (
        "viewpoint",
        "fps_bucket",
        "resolution_bucket",
        "quality_grade",
        "motion_class",
        "club",
    ):
        for value, group in df.groupby(dimension):
            session_medians = group.groupby("session_id")["error_norm"].median()
            lo, hi = _bootstrap_median_ci(session_medians)
            rows.append(
                {
                    "dimension": dimension,
                    "value": value,
                    "sessions_n": int(session_medians.shape[0]),
                    "points_n": int(len(group)),
                    "median_session_error_norm": float(session_medians.median()),
                    "ci_lower": lo,
                    "ci_upper": hi,
                }
            )
    return pd.DataFrame(rows)


def make_figures(df):
    if df.empty:
        return
    errs = pd.to_numeric(df["error_px"], errors="coerce").dropna()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(errs, bins=20, color="#4f81bd", edgecolor="white")
    ax.axvline(errs.median(), color="#c0504d", ls="--", label=f"median {errs.median():.1f} px")
    ax.set_xlabel("Trajectory error, px")
    ax.set_ylabel("Control points")
    ax.set_title("Stick-tip trajectory error distribution")
    ax.legend()
    fig.tight_layout()
    fig.savefig(common.FIGURE_DIR / "fig_trajectory_error_distribution.png", dpi=300)
    plt.close(fig)

    phases = [
        p
        for p in [
            "backswing",
            "transition",
            "downswing",
            "impact_region",
            "follow_through",
        ]
        if p in df["phase"].unique()
    ]
    session_phase = (
        df.groupby(["session_id", "phase"], as_index=False)["error_norm"].median()
    )
    data = [
        pd.to_numeric(
            session_phase[session_phase["phase"] == p]["error_norm"],
            errors="coerce",
        ).dropna().values
        * 100.0
        for p in phases
    ]
    if any(len(d) for d in data):
        fig, ax = plt.subplots(figsize=(3.2, 3.4))
        ax.boxplot(data, tick_labels=phases, showfliers=False)
        for i, values in enumerate(data, start=1):
            ax.scatter(
                np.full(len(values), i),
                values,
                color="#4f81bd",
                alpha=0.65,
                s=12,
            )
        ax.set_ylabel("Session median, % image diagonal", fontsize=8)
        ax.set_title("2D clubhead agreement by phase", fontsize=8.5)
        ax.set_xticklabels(
            ["Back", "Transition", "Down", "Impact", "Follow"],
            rotation=25,
            ha="right",
            fontsize=7,
        )
        ax.tick_params(axis="y", labelsize=7.5)
        fig.tight_layout()
        fig.savefig(
            common.FIGURE_DIR / "fig_trajectory_error_by_phase.png", dpi=400
        )
        fig.savefig(common.FIGURE_DIR / "fig_trajectory_error_by_phase.svg")
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Validate processed trajectory vs manual points.")
    parser.add_argument("--dataset-root", default=common.DEFAULT_DATASET_ROOT)
    parser.add_argument(
        "--annotations-csv",
        default=str(common.CONSENSUS_ANNOTATIONS_CSV),
        help="Reference annotations CSV (consensus preferred for algorithm agreement).",
    )
    parser.add_argument("--annotator-id", default=None)
    parser.add_argument("--annotation-round", type=int, default=None)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    if args.out_dir:
        common.configure_article2_outputs(args.out_dir)
    else:
        common.ensure_output_dirs()

    points = load_manual_points(
        args.annotations_csv, args.annotator_id, args.annotation_round
    )
    if points.empty:
        print(f"No manual stick-tip point annotations found in {args.annotations_csv}.")
        print("Run annotate_reference.py and click control points first.")
        return

    df = compute_errors(
        points,
        args.dataset_root,
        args.annotations_csv,
        args.annotator_id,
        args.annotation_round,
    )
    if df.empty:
        print("No comparable points produced (check time/frame alignment).")
        return

    point_summary = summarize_point_level(df)
    session_summary = summarize_sessions(df)
    availability = summarize_availability_and_large_errors(df, len(points))
    subgroups = summarize_subgroups(df)
    df.to_csv(common.OUTPUT_DIR / "trajectory_reference_errors.csv", index=False)
    point_summary.to_csv(
        common.OUTPUT_DIR / "trajectory_reference_summary.csv", index=False
    )
    session_summary.to_csv(
        common.OUTPUT_DIR / "trajectory_reference_session_summary.csv", index=False
    )
    availability.to_csv(
        common.OUTPUT_DIR / "trajectory_reference_failure_summary.csv", index=False
    )
    subgroups.to_csv(
        common.OUTPUT_DIR / "trajectory_reference_subgroup_summary.csv", index=False
    )
    make_figures(df)
    print(
        f"Wrote trajectory-reference outputs ({len(df)} comparable points, "
        f"{df['session_id'].nunique()} sessions)"
    )
    print(f"Reference source: {args.annotations_csv}")


if __name__ == "__main__":
    main()
