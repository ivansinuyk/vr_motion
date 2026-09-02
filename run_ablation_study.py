"""Article 2 - Script 5: controlled ablation of the processing pipeline.

Reconstructs six pipeline variants from the same raw landmarks and computes
ALL derivative metrics from each variant's final trajectory using one shared
derivative function and one time base. This fixes the inconsistency of the
first-article diagnostic ablation, where variants used different metric paths.

Variants:
    raw, median_only, kalman_only, kalman_rts,
    kalman_rts_despike, full_pipeline

Outputs:
    second_article_outputs/ablation_results.csv   (per session x variant)
    second_article_outputs/ablation_summary.csv   (per variant)
    second_article_outputs/figures/fig_ablation_trajectory_deviation.png
    second_article_outputs/figures/fig_ablation_jerk_reduction.png
    second_article_outputs/figures/fig_ablation_metric_stability.png

Run:
    python run_ablation_study.py --limit 8
    python run_ablation_study.py
"""

from __future__ import annotations

import argparse
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import second_article_common as common
from batch_article_evaluation import (
    _extract_raw_tip_base,
    _median_trajectory,
    _scale_series,
    _session_id,
    discover_sessions,
    process_session,
)

VARIANT_ORDER = [
    "raw",
    "median_only",
    "kalman_only",
    "kalman_rts",
    "kalman_rts_despike",
    "full_pipeline",
]

STAT_COLS = [
    "valid_samples",
    "stage_changed_points",
    "mean_dev_m",
    "p95_dev_m",
    "max_dev_m",
    "rms_jerk",
    "smoothness_index",
    "path_efficiency",
    "max_speed",
    "max_accel",
]


def _changed_points(previous, current, tolerance_px=1e-6):
    changed = 0
    for before, after in zip(previous, current):
        if before is None and after is None:
            continue
        if before is None or after is None:
            changed += 1
            continue
        if math.hypot(after[0] - before[0], after[1] - before[1]) > tolerance_px:
            changed += 1
    return changed


def variant_stats(raw, processed, scales, fps, previous_stage):
    """Compute all ablation metrics with one definition and actual elapsed gaps.

    Acceleration is the finite difference of scalar speed and jerk is the finite
    difference of that scalar acceleration. When samples are missing, elapsed
    time spans the full frame gap instead of incorrectly retaining one frame.
    """
    base_dt = 1.0 / fps if fps and fps > 0 else 1.0 / 30.0
    dev = []
    speeds = []
    accels = []
    jerks = []
    path_pts = []  # scaled (m) positions of valid processed points, in order
    prev = None
    prev_idx = None
    prev_speed = None
    prev_acc = None

    for idx, (p_raw, p, scale) in enumerate(zip(raw, processed, scales)):
        if p_raw is not None and p is not None and not np.isnan(scale):
            dev.append(math.hypot((p[0] - p_raw[0]) * scale, (p[1] - p_raw[1]) * scale))
        if p is None or np.isnan(scale):
            continue
        path_pts.append((p[0] * scale, p[1] * scale))
        if prev is None:
            prev = p
            prev_idx = idx
            continue
        dt = max((idx - prev_idx) * base_dt, 1e-9)
        speed = math.hypot(p[0] - prev[0], p[1] - prev[1]) / dt * scale
        accel = (speed - prev_speed) / dt if prev_speed is not None else 0.0
        jerk = (accel - prev_acc) / dt if prev_acc is not None else 0.0
        speeds.append(speed)
        accels.append(accel)
        jerks.append(jerk)
        prev_speed = speed
        prev_acc = accel
        prev = p
        prev_idx = idx

    dev_arr = np.asarray(dev, dtype=float)
    jerk_arr = np.asarray([j for j in jerks if abs(j) > 0], dtype=float)
    mean_sq_jerk = float(np.mean(jerk_arr ** 2)) if jerk_arr.size else 0.0

    # Path efficiency: net displacement / total path length (scaled meters).
    path_eff = np.nan
    if len(path_pts) >= 2:
        total = 0.0
        for a, b in zip(path_pts[:-1], path_pts[1:]):
            total += math.hypot(b[0] - a[0], b[1] - a[1])
        net = math.hypot(path_pts[-1][0] - path_pts[0][0], path_pts[-1][1] - path_pts[0][1])
        path_eff = (net / total) if total > 1e-9 else np.nan

    return {
        "valid_samples": int(len([p for p in processed if p is not None])),
        "stage_changed_points": _changed_points(previous_stage, processed),
        "mean_dev_m": float(np.mean(dev_arr)) if dev_arr.size else np.nan,
        "p95_dev_m": float(np.quantile(dev_arr, 0.95)) if dev_arr.size else np.nan,
        "max_dev_m": float(np.max(dev_arr)) if dev_arr.size else np.nan,
        "rms_jerk": math.sqrt(mean_sq_jerk) if mean_sq_jerk > 0 else 0.0,
        "smoothness_index": -math.log10(mean_sq_jerk + 1e-9),
        "path_efficiency": path_eff,
        "max_speed": float(np.max(speeds)) if speeds else 0.0,
        "max_accel": float(np.max(accels)) if accels else 0.0,
    }


def build_variants(baseline_result):
    data = baseline_result["data"]
    fps = baseline_result["fps"]
    width = baseline_result["width"]
    height = baseline_result["height"]

    raw, bases = _extract_raw_tip_base(data, width, height)
    scales = _scale_series(raw, bases)
    med = _median_trajectory(raw)
    analyzer = baseline_result["analyzer"]
    # Populate the production caches, then expose each actual stage. This keeps
    # the ablation nested and prevents a textbook RTS variant from being
    # compared with a different production RTS implementation.
    full = analyzer._smooth_tip_positions()
    kalman = list(analyzer.tip_positions)
    rts = list(analyzer._rts_tip_px_cache)
    rts_despike = list(analyzer._despiked_tip_px_cache)

    variants = {
        "raw": raw,
        "median_only": med,
        "kalman_only": kalman,
        "kalman_rts": rts,
        "kalman_rts_despike": rts_despike,
        "full_pipeline": full,
    }
    previous = {
        "raw": raw,
        "median_only": raw,
        "kalman_only": med,
        "kalman_rts": kalman,
        "kalman_rts_despike": rts,
        "full_pipeline": rts_despike,
    }
    return raw, scales, variants, previous


def ablation_rows(folder, baseline_result):
    if not baseline_result.get("ok"):
        return []
    fps = baseline_result["fps"]
    raw, scales, variants, previous = build_variants(baseline_result)
    rows = []
    for name, traj in variants.items():
        stats = variant_stats(raw, traj, scales, fps, previous[name])
        rows.append({"session_id": _session_id(folder), "pipeline_variant": name, **stats})
    return rows


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for variant in VARIANT_ORDER:
        g = df[df["pipeline_variant"] == variant]
        if g.empty:
            continue
        rec = {"pipeline_variant": variant, "n_sessions": int(len(g))}
        for col in STAT_COLS:
            vals = pd.to_numeric(g[col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
            rec[f"{col}_median"] = float(vals.median()) if not vals.empty else np.nan
        records.append(rec)
    return pd.DataFrame(records)


def make_figures(df: pd.DataFrame, summary: pd.DataFrame):
    if summary.empty:
        return
    summary = summary.set_index("pipeline_variant").reindex(
        [v for v in VARIANT_ORDER if v in summary["pipeline_variant"].values]
    ) if "pipeline_variant" in summary.columns else summary

    order = [v for v in VARIANT_ORDER if v in df["pipeline_variant"].unique()]
    labels = {
        "raw": "Raw",
        "median_only": "Median",
        "kalman_only": "Kalman",
        "kalman_rts": "Kalman + RTS",
        "kalman_rts_despike": "+ despiking",
        "full_pipeline": "Full pipeline",
    }

    dev = df[df["pipeline_variant"] != "raw"].groupby("pipeline_variant")["mean_dev_m"].median()
    dev = dev.reindex([v for v in order if v != "raw"]).dropna()
    if not dev.empty:
        fig, ax = plt.subplots(figsize=(3.2, 4.2))
        ax.barh([labels[v] for v in dev.index], dev.values * 100.0, color="#4f81bd")
        ax.set_xlabel("Median deviation from raw, cm")
        ax.set_title("Ablation: trajectory deviation from raw landmarks")
        ax.invert_yaxis()
        fig.tight_layout()
        fig.savefig(
            common.FIGURE_DIR / "fig_ablation_trajectory_deviation.png", dpi=400
        )
        fig.savefig(common.FIGURE_DIR / "fig_ablation_trajectory_deviation.svg")
        plt.close(fig)

    jerk = df.groupby("pipeline_variant")["rms_jerk"].median().reindex(order).dropna()
    if not jerk.empty:
        fig, ax = plt.subplots(figsize=(3.2, 4.2))
        ax.barh([labels[v] for v in jerk.index], jerk.values, color="#9bbb59")
        ax.set_xlabel("Median RMS jerk, m/s³")
        ax.set_xscale("log")
        ax.set_title("Production-stage ablation")
        fig.tight_layout()
        fig.savefig(common.FIGURE_DIR / "fig_ablation_jerk_reduction.png", dpi=400)
        fig.savefig(common.FIGURE_DIR / "fig_ablation_jerk_reduction.svg")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for metric, color in [("smoothness_index", "#c0504d"), ("path_efficiency", "#8064a2")]:
        vals = df.groupby("pipeline_variant")[metric].median().reindex(order)
        ax.plot(range(len(vals)), vals.values, marker="o", label=metric, color=color)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([labels[v] for v in order], rotation=25, ha="right")
    ax.set_ylabel("Median value")
    ax.set_title("Ablation: movement-quality metric stability")
    ax.legend()
    fig.tight_layout()
    fig.savefig(common.FIGURE_DIR / "fig_ablation_metric_stability.png", dpi=400)
    fig.savefig(common.FIGURE_DIR / "fig_ablation_metric_stability.svg")
    plt.close(fig)


def resolve_sessions(args):
    sessions = discover_sessions(args.dataset_root)
    if args.use_subset:
        subset_path = common.REFERENCE_SUBSET_CSV
        if subset_path.exists():
            ids = set(pd.read_csv(subset_path)["session_id"].astype(str))
            sessions = [s for s in sessions if s.name in ids]
    if args.limit:
        sessions = sessions[: args.limit]
    return sessions


def main():
    parser = argparse.ArgumentParser(description="Run the article-2 ablation study.")
    parser.add_argument("--dataset-root", default=common.DEFAULT_DATASET_ROOT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--use-subset", action="store_true")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    if args.out_dir:
        common.configure_article2_outputs(args.out_dir)
    else:
        common.ensure_output_dirs()
    sessions = resolve_sessions(args)
    if not sessions:
        raise RuntimeError(f"No sessions found under {args.dataset_root}")

    all_rows = []
    for idx, folder in enumerate(sessions, start=1):
        print(f"[{idx}/{len(sessions)}] {folder.name}")
        baseline = process_session(folder, profile="scientific")
        if not baseline.get("ok"):
            print(f"  baseline failed: {baseline.get('error')}")
            continue
        all_rows.extend(ablation_rows(folder, baseline))

    df = pd.DataFrame(all_rows)
    summary = summarize(df)

    results_path = common.OUTPUT_DIR / "ablation_results.csv"
    summary_path = common.OUTPUT_DIR / "ablation_summary.csv"
    df.to_csv(results_path, index=False)
    summary.to_csv(summary_path, index=False)
    make_figures(df, summary)

    print(f"Wrote {results_path} ({len(df)} rows)")
    print(f"Wrote {summary_path} ({len(summary)} rows)")


if __name__ == "__main__":
    main()
