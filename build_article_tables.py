"""Article 2 - consolidate analysis outputs into article-ready tables.

Reads the six second-article CSV outputs plus the first-article dataset
summary and emits one CSV per manuscript table under
``second_article_outputs/article_tables/`` together with a human-readable
``article_tables.md`` digest used while drafting the manuscript.

Tables produced (numbering follows the planned manuscript):
    table1_dataset_subset.csv        dataset vs annotated-subset characteristics
    table2_annotation_protocol.csv   manual annotation protocol summary
    table3_event_timing.csv          event timing validation vs manual reference
    table4_trajectory_error.csv      trajectory error by swing phase
    table5_sensitivity.csv           sensitivity: median |% change| by metric group
    table6_ablation.csv              ablation comparison of pipeline variants
    table7_robustness_ranking.csv    metric robustness ranking + recommended use

Run:
    python build_article_tables.py
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import second_article_common as common
from pathlib import Path

# Perturbation scenarios grouped for the compact sensitivity table.
SCENARIO_GROUPS = {
    "Frame thinning (2x / 3x)": ["frame_thinning_2x", "frame_thinning_3x"],
    "Landmark dropout (5-20 %)": [
        "landmark_dropout_5pct",
        "landmark_dropout_10pct",
        "landmark_dropout_20pct",
    ],
    "Coordinate jitter (sigma 0.004 / 0.008)": [
        "jitter_sigma_0p004",
        "jitter_sigma_0p008",
    ],
    "Scale perturbation (+/-5 %, +/-10 %)": [
        "scale_minus_5pct",
        "scale_plus_5pct",
        "scale_minus_10pct",
        "scale_plus_10pct",
    ],
    "Combined degradation": ["combined_degradation"],
}

METRIC_LABELS = {
    "smoothness_index": "Smoothness index",
    "path_efficiency": "Path efficiency",
    "max_speed": "Maximum speed",
    "max_accel": "Maximum acceleration",
    "max_ang_vel": "Maximum angular velocity",
    "curvature_rms": "Curvature RMS",
    "swing_tempo": "Swing tempo",
    "backswing_peak_speed": "Backswing peak speed",
}

VARIANT_LABELS = {
    "raw": "Raw landmarks",
    "median_only": "Median only",
    "kalman_only": "Kalman only",
    "kalman_rts": "Kalman + RTS",
    "kalman_rts_despike": "Kalman + RTS + despiking",
    "full_pipeline": "Full pipeline",
}

PHASE_LABELS = {
    "backswing": "Backswing",
    "transition": "Transition",
    "downswing": "Downswing",
    "impact_region": "Impact region",
    "follow_through": "Follow-through",
}


def table1_dataset_subset() -> pd.DataFrame:
    meta = common.load_dataset_metadata()
    subset = pd.read_csv(common.REFERENCE_SUBSET_CSV)
    ann_path = common.CONSENSUS_ANNOTATIONS_CSV
    if not ann_path.exists():
        ann_path = common.REFERENCE_ANNOTATIONS_CSV
    ann = pd.read_csv(ann_path)
    pts = ann[ann["point_name"].astype(str).str.len() > 0]
    annotated_ids = set(subset["session_id"].astype(str))
    sub_meta = meta[meta["session_id"].astype(str).isin(annotated_ids)]

    reader_labels = {
        "dtl": "down-the-line",
        "face_on": "face-on",
        "super_slow": "super slow motion",
        "<=30": "≤30",
        "31-60": "31–60",
        "720-1080p": "720–1080 p",
        "1080p+": "≥1080 p",
        "<720p": "<720 p",
    }

    def dist(df, col):
        counts = df[col].value_counts()
        return "; ".join(
            f"{reader_labels.get(k, k)}: {v}" for k, v in counts.items()
        )

    rows = [
        {"Characteristic": "Sessions, n", "Full dataset": len(meta), "Annotated subset": len(sub_meta)},
        {"Characteristic": "Camera viewpoint", "Full dataset": dist(meta, "viewpoint"), "Annotated subset": dist(sub_meta, "viewpoint")},
        {"Characteristic": "Capture speed class", "Full dataset": dist(meta, "motion_class"), "Annotated subset": dist(sub_meta, "motion_class")},
        {"Characteristic": "Frame-rate bucket, fps", "Full dataset": dist(meta, "fps_bucket"), "Annotated subset": dist(sub_meta, "fps_bucket")},
        {"Characteristic": "Resolution bucket", "Full dataset": dist(meta, "resolution_bucket"), "Annotated subset": dist(sub_meta, "resolution_bucket")},
        {"Characteristic": "Quality grade", "Full dataset": dist(meta, "quality_grade"), "Annotated subset": dist(sub_meta, "quality_grade")},
        {"Characteristic": "Club type", "Full dataset": dist(meta, "club"), "Annotated subset": dist(sub_meta, "club")},
        {
            "Characteristic": "Clubhead control points, n",
            "Full dataset": "-",
            "Annotated subset": f"{len(pts)} (in {pts['session_id'].nunique()} sessions)",
        },
    ]
    return pd.DataFrame(rows)


def table2_annotation_protocol() -> pd.DataFrame:
    rows = [
        {
            "Event": "Address",
            "Visual criterion": "Last stable frame before takeaway",
            "Role": "Time-origin diagnostic",
        },
        {
            "Event": "Top of backswing",
            "Visual criterion": "Maximal backswing extent before reversal",
            "Role": "Compared with transition proxy",
        },
        {
            "Event": "Downswing transition",
            "Visual criterion": "First sustained motion toward impact",
            "Role": "Compared with transition proxy",
        },
        {
            "Event": "Impact",
            "Visual criterion": "Closest visible clubhead-ball contact",
            "Role": "Compared with impact detector",
        },
    ]
    return pd.DataFrame(rows)


def table3_event_timing() -> pd.DataFrame:
    summ = pd.read_csv(common.OUTPUT_DIR / "event_validation_summary.csv")
    order = ["top_backswing", "downswing_transition", "impact"]
    rows = []
    for ev in order:
        r = summ[summ["event"] == ev]
        if r.empty:
            continue
        r = r.iloc[0]
        rows.append(
            {
                "Auto / manual": (
                    "Transition / top"
                    if ev == "top_backswing"
                    else (
                        "Transition / transition"
                        if ev == "downswing_transition"
                        else "Impact / impact"
                    )
                ),
                "n": int(r["n_sessions"]),
                "Median |error|, frames": round(float(r["median_abs_frames"])),
                "Median |error|, ms (95% CI)": (
                    f"{float(r['median_abs_ms']):.0f} "
                    f"({float(r['median_absolute_ci_lower_ms']):.0f}–"
                    f"{float(r['median_absolute_ci_upper_ms']):.0f})"
                ),
            }
        )
    return pd.DataFrame(rows)


def table4_trajectory_error() -> pd.DataFrame:
    summary = pd.read_csv(
        common.OUTPUT_DIR / "trajectory_reference_session_summary.csv"
    )
    rows = []
    order = [
        "backswing",
        "transition",
        "downswing",
        "impact_region",
        "follow_through",
        "all",
    ]
    for phase in order:
        match = summary[summary["phase"] == phase]
        if match.empty:
            continue
        r = match.iloc[0]
        rows.append(
            {
                "Phase": PHASE_LABELS.get(phase, "All phases"),
                "n_s / n_p": (
                    f"{int(r['sessions_n'])}/{int(r['points_n'])}"
                ),
                "Median, % diag. (95% CI)": (
                    f"{float(r['median_of_session_medians_norm']) * 100:.2f} "
                    f"({float(r['median_norm_ci_lower']) * 100:.2f}–"
                    f"{float(r['median_norm_ci_upper']) * 100:.2f})"
                ),
                "P95 / max, px": (
                    f"{float(r['point_level_p95_px']):.1f} / "
                    f"{float(r['point_level_max_px']):.1f}"
                ),
            }
        )
    return pd.DataFrame(rows)


def table5_sensitivity() -> pd.DataFrame:
    summ = pd.read_csv(common.OUTPUT_DIR / "sensitivity_summary.csv")
    metric_order = [
        "smoothness_index",
        "path_efficiency",
        "max_speed",
        "max_accel",
        "max_ang_vel",
        "curvature_rms",
        "swing_tempo",
        "backswing_peak_speed",
    ]
    rows = []
    for metric in metric_order:
        selected = summ[summ["metric"] == metric]
        rows.append(
            {
                "Metric": METRIC_LABELS[metric],
                "Median Δsym, %": round(
                    float(selected["median_abs_symmetric_pct_change"].median()), 1
                ),
                "Worst, %": round(
                    float(selected["median_abs_symmetric_pct_change"].max()), 1
                ),
                "Median ρ": round(
                    float(selected["rank_stability_spearman"].median()), 2
                ),
            }
        )
    return pd.DataFrame(rows)


def table6_ablation() -> pd.DataFrame:
    summ = pd.read_csv(common.OUTPUT_DIR / "ablation_summary.csv")
    rows = []
    for variant in VARIANT_LABELS:
        r = summ[summ["pipeline_variant"] == variant]
        if r.empty:
            continue
        r = r.iloc[0]
        rows.append(
            {
                "Stage": VARIANT_LABELS[variant],
                "Δpoints, n": round(
                    float(r["stage_changed_points_median"])
                ),
                "Δraw, cm": round(
                    float(r["mean_dev_m_median"]) * 100.0, 1
                ),
                "RMS jerk, m/s^3": (
                    f"{float(r['rms_jerk_median']):.2f}"
                    if float(r["rms_jerk_median"]) < 100
                    else f"{float(r['rms_jerk_median']):.0f}"
                ),
            }
        )
    return pd.DataFrame(rows)


def table7_robustness_ranking() -> pd.DataFrame:
    summ = pd.read_csv(common.OUTPUT_DIR / "sensitivity_summary.csv")

    rows = []
    for metric, g in summ.groupby("metric"):
        med_all = float(g["median_abs_symmetric_pct_change"].median())
        cls = g["response_class"].value_counts()
        n_low = int(cls.get("low", 0))
        n_moderate = int(cls.get("moderate", 0))
        n_high = int(cls.get("high", 0))
        rows.append(
            {
                "Metric": METRIC_LABELS.get(metric, metric),
                "Median symmetric |change|, %": round(med_all, 1),
                "Scenarios low/moderate/high": (
                    f"{n_low}/{n_moderate}/{n_high}"
                ),
                "Interpretation": (
                    "Candidate only"
                    if n_high == 0
                    else (
                        "Condition-dependent"
                        if n_high <= 3
                        else "High perturbation sensitivity"
                    )
                ),
            }
        )
    df = pd.DataFrame(rows).sort_values("Median symmetric |change|, %")
    return df.reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Build article-2 consolidated tables.")
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Directory containing analysis CSVs (default: second_article_outputs).",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory for article_tables/ (default: <input-dir>/article_tables).",
    )
    args = parser.parse_args()

    if args.input_dir:
        common.configure_article2_outputs(args.input_dir)
    else:
        common.ensure_output_dirs()

    tables_dir = Path(args.out_dir) if args.out_dir else (common.OUTPUT_DIR / "article_tables")
    tables_dir.mkdir(parents=True, exist_ok=True)

    builders = {
        "table1_dataset_subset": table1_dataset_subset,
        "table2_annotation_protocol": table2_annotation_protocol,
        "table3_event_timing": table3_event_timing,
        "table4_trajectory_error": table4_trajectory_error,
        "table5_sensitivity": table5_sensitivity,
        "table6_ablation": table6_ablation,
        "table7_robustness_ranking": table7_robustness_ranking,
    }
    md_parts = ["# Article 2 - consolidated tables\n"]
    for name, fn in builders.items():
        df = fn()
        df.to_csv(tables_dir / f"{name}.csv", index=False)
        md_parts.append(f"## {name}\n\n{df.to_string(index=False)}\n")
        print(f"wrote {name}.csv ({len(df)} rows)")
    (tables_dir / "article_tables.md").write_text("\n".join(md_parts), encoding="utf-8")
    print(f"wrote {tables_dir / 'article_tables.md'}")


if __name__ == "__main__":
    main()
