"""Article 2 - Script 6: reliability statistics for exported metrics.

Computes cross-session dispersion statistics (CV, repeatability coefficient,
SEM, MDC) from the dataset metrics, an inter-variant agreement analysis
(Bland-Altman of full pipeline vs Kalman+RTS+despike), and an optional ICC
when an explicit grouping of repeated measures is provided.

SCIENTIFIC CAUTION: without known athlete/trial grouping, the cross-session
dispersion here reflects between-session heterogeneity of the whole dataset,
NOT within-athlete test-retest repeatability. The outputs are labelled
accordingly and must not be reported as athlete repeatability.

Outputs:
    second_article_outputs/reliability_statistics.csv
    second_article_outputs/figures/fig_bland_altman_selected_metrics.png
    second_article_outputs/figures/fig_icc_metric_ranking.png

Run:
    python compute_reliability_statistics.py
    python compute_reliability_statistics.py --group-col athlete_id --group-csv repeated.csv
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

DISPERSION_METRICS = [
    "max_speed",
    "max_ang_vel",
    "max_accel",
    "swing_tempo",
    "smoothness_index",
    "path_efficiency",
    "curvature_rms",
    "backswing_duration",
    "downswing_duration",
    "backswing_peak_speed",
    "downswing_peak_speed",
]

BLAND_ALTMAN_METRICS = ["smoothness_index", "path_efficiency", "max_speed", "max_accel"]


def dispersion_rows(df: pd.DataFrame) -> list:
    rows = []
    for metric in DISPERSION_METRICS:
        if metric not in df.columns:
            continue
        vals = pd.to_numeric(df[metric], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if len(vals) < 2:
            continue
        mean = float(vals.mean())
        sd = float(vals.std(ddof=1))
        cv = abs(sd / mean * 100.0) if abs(mean) > 1e-12 else np.nan
        rc = 1.96 * math.sqrt(2.0) * sd
        rows.append(
            {
                "metric": metric,
                "scope": "cross_session_dispersion",
                "n": int(len(vals)),
                "mean": mean,
                "sd": sd,
                "cv_percent": cv,
                "repeatability_coeff": rc,
                "sem": sd,
                "mdc_95": 1.96 * math.sqrt(2.0) * sd,
            }
        )
    return rows


def compute_icc_oneway(values: np.ndarray, groups: np.ndarray):
    """One-way random-effects ICC(1) for repeated measures within groups."""
    dfm = pd.DataFrame({"v": values, "g": groups}).dropna()
    if dfm["g"].nunique() < 2:
        return np.nan
    grand = dfm["v"].mean()
    n_total = len(dfm)
    k = dfm.groupby("g").size()
    # Balanced approximation using mean group size.
    k0 = k.mean()
    group_means = dfm.groupby("g")["v"].mean()
    ss_between = float(((group_means - grand) ** 2 * k).sum())
    ss_within = float(((dfm["v"] - dfm["g"].map(group_means)) ** 2).sum())
    df_between = dfm["g"].nunique() - 1
    df_within = n_total - dfm["g"].nunique()
    if df_between <= 0 or df_within <= 0:
        return np.nan
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within
    denom = ms_between + (k0 - 1) * ms_within
    if abs(denom) < 1e-12:
        return np.nan
    return float((ms_between - ms_within) / denom)


def icc_rows(group_df: pd.DataFrame, group_col: str) -> list:
    rows = []
    for metric in DISPERSION_METRICS:
        if metric not in group_df.columns:
            continue
        sub = group_df[[group_col, metric]].copy()
        sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
        sub = sub.dropna()
        if sub.empty:
            continue
        icc = compute_icc_oneway(sub[metric].values, sub[group_col].values)
        sd = float(sub[metric].std(ddof=1)) if len(sub) > 1 else np.nan
        sem = sd * math.sqrt(max(0.0, 1.0 - icc)) if not np.isnan(icc) else np.nan
        rows.append(
            {
                "metric": metric,
                "scope": f"icc_by_{group_col}",
                "n": int(len(sub)),
                "mean": float(sub[metric].mean()),
                "sd": sd,
                "cv_percent": np.nan,
                "repeatability_coeff": np.nan,
                "icc1": icc,
                "sem": sem,
                "mdc_95": 1.96 * math.sqrt(2.0) * sem if not np.isnan(sem) else np.nan,
            }
        )
    return rows


def bland_altman(ablation_csv, fig_path):
    if not ablation_csv.exists():
        print(f"  (skip Bland-Altman: {ablation_csv} not found)")
        return []
    df = pd.read_csv(ablation_csv)
    m1 = df[df["pipeline_variant"] == "full_pipeline"].set_index("session_id")
    m2 = df[df["pipeline_variant"] == "kalman_rts_despike"].set_index("session_id")
    common_ids = m1.index.intersection(m2.index)
    if len(common_ids) < 3:
        print("  (skip Bland-Altman: not enough paired sessions)")
        return []

    metrics = [m for m in BLAND_ALTMAN_METRICS if m in df.columns]
    rows = []
    ncols = 2
    nrows = int(math.ceil(len(metrics) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 4 * nrows))
    axes = np.atleast_1d(axes).ravel()
    for ax, metric in zip(axes, metrics):
        a = pd.to_numeric(m1.loc[common_ids, metric], errors="coerce")
        b = pd.to_numeric(m2.loc[common_ids, metric], errors="coerce")
        paired = pd.DataFrame({"a": a, "b": b}).replace([np.inf, -np.inf], np.nan).dropna()
        if len(paired) < 3:
            ax.set_visible(False)
            continue
        mean = (paired["a"] + paired["b"]) / 2.0
        diff = paired["a"] - paired["b"]
        bias = float(diff.mean())
        sd = float(diff.std(ddof=1))
        loa_lo, loa_hi = bias - 1.96 * sd, bias + 1.96 * sd
        ax.scatter(mean, diff, alpha=0.7, color="#4f81bd")
        ax.axhline(bias, color="black", lw=1.2)
        ax.axhline(loa_hi, color="#c0504d", ls="--", lw=1)
        ax.axhline(loa_lo, color="#c0504d", ls="--", lw=1)
        ax.set_title(f"{metric} (full vs Kalman+RTS+despike)", fontsize=9)
        ax.set_xlabel("Mean of two variants")
        ax.set_ylabel("Difference")
        rows.append(
            {
                "metric": metric,
                "scope": "bland_altman_full_vs_kalman_rts_despike",
                "n": int(len(paired)),
                "mean": float(mean.mean()),
                "bias": bias,
                "loa_lower": loa_lo,
                "loa_upper": loa_hi,
                "sd": sd,
            }
        )
    for ax in axes[len(metrics):]:
        ax.set_visible(False)
    fig.suptitle("Bland-Altman agreement between processing variants")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
    return rows


def ranking_figure(dispersion_df: pd.DataFrame, fig_path):
    if dispersion_df.empty:
        return
    ranked = dispersion_df.dropna(subset=["cv_percent"]).sort_values("cv_percent")
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#4f81bd" if c < 25 else ("#f0ad4e" if c < 50 else "#c0504d") for c in ranked["cv_percent"]]
    ax.barh(ranked["metric"], ranked["cv_percent"], color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Cross-session CV, % (lower = more consistent)")
    ax.set_title("Metric consistency ranking (cross-session dispersion, not athlete repeatability)")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Compute article-2 reliability statistics.")
    parser.add_argument("--summary-csv", default=str(common.DATASET_SUMMARY_CSV))
    parser.add_argument("--ablation-csv", default=str(common.OUTPUT_DIR / "ablation_results.csv"))
    parser.add_argument("--group-csv", default=None, help="Optional CSV with repeated measures.")
    parser.add_argument("--group-col", default=None, help="Grouping column for ICC (e.g. athlete_id).")
    args = parser.parse_args()

    common.ensure_output_dirs()
    df = pd.read_csv(args.summary_csv)
    df = df[df.get("processed", True) == True] if "processed" in df.columns else df  # noqa: E712

    all_rows = dispersion_rows(df)

    if args.group_csv and args.group_col:
        from pathlib import Path

        gpath = Path(args.group_csv)
        if gpath.exists():
            gdf = pd.read_csv(gpath)
            if args.group_col in gdf.columns:
                all_rows.extend(icc_rows(gdf, args.group_col))
            else:
                print(f"  (group column '{args.group_col}' not in {gpath})")
        else:
            print(f"  (group CSV {gpath} not found; skipping ICC)")

    ba_rows = bland_altman(
        common.OUTPUT_DIR / "ablation_results.csv"
        if args.ablation_csv is None
        else __import__("pathlib").Path(args.ablation_csv),
        common.FIGURE_DIR / "fig_bland_altman_selected_metrics.png",
    )

    stats_df = pd.DataFrame(all_rows)
    ranking_figure(stats_df[stats_df["scope"] == "cross_session_dispersion"],
                   common.FIGURE_DIR / "fig_icc_metric_ranking.png")

    combined = pd.concat([stats_df, pd.DataFrame(ba_rows)], ignore_index=True, sort=False)
    out_path = common.OUTPUT_DIR / "reliability_statistics.csv"
    combined.to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(combined)} rows)")


if __name__ == "__main__":
    main()
