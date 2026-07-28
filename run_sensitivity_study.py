"""Article 2 - Script 4: controlled sensitivity / robustness study.

Runs a richer perturbation battery than the first-article diagnostic pass:
frame thinning (2x, 3x), landmark dropout (5/10/20 %), Gaussian coordinate
jitter, scale perturbation (+/-5 %, +/-10 %), and a combined-degradation case.
Each perturbed run is compared against the per-session unperturbed baseline.

Outputs:
    second_article_outputs/sensitivity_results.csv   (per session x scenario x metric)
    second_article_outputs/sensitivity_summary.csv   (per scenario x metric)
    second_article_outputs/figures/fig_sensitivity_metric_heatmap.png
    second_article_outputs/figures/fig_sensitivity_by_perturbation.png

Run:
    python run_sensitivity_study.py --limit 8        # quick check
    python run_sensitivity_study.py                  # full dataset
    python run_sensitivity_study.py --use-subset     # only annotation subset
"""

from __future__ import annotations

import argparse
import copy
import hashlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
import second_article_common as common
from batch_article_evaluation import (
    _safe_float,
    _session_id,
    clone_frame_thinned,
    clone_with_landmark_dropout,
    discover_sessions,
    process_session,
)

SENS_METRICS = [
    "max_speed",
    "max_ang_vel",
    "max_accel",
    "swing_tempo",
    "smoothness_index",
    "path_efficiency",
    "curvature_rms",
    "backswing_peak_speed",
]

STICK_LANDMARKS = (17, 18, 19)

SCENARIO_FAMILIES = {
    "Frame thinning": ["frame_thinning_2x", "frame_thinning_3x"],
    "Landmark dropout": [
        "landmark_dropout_5pct",
        "landmark_dropout_10pct",
        "landmark_dropout_20pct",
    ],
    "Coordinate jitter": ["jitter_sigma_0p004", "jitter_sigma_0p008"],
    "Scale perturbation": [
        "scale_minus_10pct",
        "scale_minus_5pct",
        "scale_plus_5pct",
        "scale_plus_10pct",
    ],
    "Combined": ["combined_degradation"],
}

METRIC_LABELS = {
    "smoothness_index": "Smoothness",
    "path_efficiency": "Path efficiency",
    "max_speed": "Max speed",
    "max_ang_vel": "Max angular velocity",
    "max_accel": "Max acceleration",
    "curvature_rms": "Curvature RMS",
    "swing_tempo": "Tempo",
    "backswing_peak_speed": "Backswing peak",
}


def clone_with_jitter(data, sigma_norm=0.004, seed=42, indices=STICK_LANDMARKS):
    """Add zero-mean Gaussian noise (normalized coords) to stick landmarks."""
    rng = np.random.default_rng(seed)
    out = copy.deepcopy(data)
    for frame in out:
        landmarks = frame.get("landmarks", [])
        if not landmarks:
            continue
        pts = landmarks[0]
        for idx in indices:
            if idx < len(pts) and pts[idx].get("x") is not None and pts[idx].get("y") is not None:
                pts[idx]["x"] = float(pts[idx]["x"]) + float(rng.normal(0.0, sigma_norm))
                pts[idx]["y"] = float(pts[idx]["y"]) + float(rng.normal(0.0, sigma_norm))
    return out


def build_scenarios(baseline_result, session_seed):
    fps = baseline_result["fps"]
    data = baseline_result["data"]
    base_len = config.STICK_REAL_LENGTH_M

    combined = clone_frame_thinned(data, 2)
    combined = clone_with_landmark_dropout(combined, 0.10, seed=session_seed + 1)
    combined = clone_with_jitter(combined, sigma_norm=0.004, seed=session_seed + 2)

    return [
        ("frame_thinning_2x", {"data_override": clone_frame_thinned(data, 2), "fps_override": fps / 2.0}),
        ("frame_thinning_3x", {"data_override": clone_frame_thinned(data, 3), "fps_override": fps / 3.0}),
        ("landmark_dropout_5pct", {"data_override": clone_with_landmark_dropout(data, 0.05, seed=session_seed)}),
        ("landmark_dropout_10pct", {"data_override": clone_with_landmark_dropout(data, 0.10, seed=session_seed)}),
        ("landmark_dropout_20pct", {"data_override": clone_with_landmark_dropout(data, 0.20, seed=session_seed)}),
        ("jitter_sigma_0p004", {"data_override": clone_with_jitter(data, 0.004, seed=session_seed)}),
        ("jitter_sigma_0p008", {"data_override": clone_with_jitter(data, 0.008, seed=session_seed)}),
        ("scale_minus_10pct", {"stick_length_m": base_len * 0.90}),
        ("scale_minus_5pct", {"stick_length_m": base_len * 0.95}),
        ("scale_plus_5pct", {"stick_length_m": base_len * 1.05}),
        ("scale_plus_10pct", {"stick_length_m": base_len * 1.10}),
        (
            "combined_degradation",
            {"data_override": combined, "fps_override": fps / 2.0},
        ),
    ]


def stable_session_seed(session_id: str) -> int:
    """Return a process-independent seed derived from the session identifier."""
    digest = hashlib.sha256(str(session_id).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], byteorder="little", signed=False)


def sensitivity_rows(folder, baseline_result):
    if not baseline_result.get("ok"):
        return []
    base = baseline_result["summary"]
    session_seed = stable_session_seed(_session_id(folder))
    rows = []
    for scenario, kwargs in build_scenarios(baseline_result, session_seed):
        res = process_session(folder, profile="scientific", **kwargs)
        row = {
            "session_id": _session_id(folder),
            "scenario": scenario,
            "session_seed": session_seed,
            "processed": bool(res.get("ok")),
        }
        if res.get("ok"):
            for metric in SENS_METRICS:
                b = _safe_float(base.get(metric))
                v = _safe_float(res["summary"].get(metric))
                row[f"{metric}_baseline"] = b
                row[f"{metric}_scenario"] = v
                delta = v - b if not (np.isnan(v) or np.isnan(b)) else np.nan
                pct = (delta / b * 100.0) if not (np.isnan(delta) or abs(b) < 1e-12) else np.nan
                sym_denom = abs(v) + abs(b)
                symmetric_pct = (
                    200.0 * delta / sym_denom
                    if not (np.isnan(delta) or sym_denom < 1e-12)
                    else np.nan
                )
                row[f"{metric}_delta"] = delta
                row[f"{metric}_pct_change"] = pct
                row[f"{metric}_symmetric_pct_change"] = symmetric_pct
        else:
            row["error"] = res.get("error", "")
        rows.append(row)
    return rows


def _average_ranks(values: np.ndarray) -> np.ndarray:
    """Return one-based average ranks with deterministic tie handling."""
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        stop = start + 1
        while stop < len(values) and sorted_values[stop] == sorted_values[start]:
            stop += 1
        ranks[order[start:stop]] = 0.5 * (start + stop - 1) + 1.0
        start = stop
    return ranks


def _spearman_arrays(first: np.ndarray, second: np.ndarray) -> float:
    first_ranks = _average_ranks(first)
    second_ranks = _average_ranks(second)
    if np.std(first_ranks) < 1e-12 or np.std(second_ranks) < 1e-12:
        return np.nan
    return float(np.corrcoef(first_ranks, second_ranks)[0, 1])


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(20260728)
    records = []
    for scenario, g in df.groupby("scenario"):
        for metric in SENS_METRICS:
            col = f"{metric}_symmetric_pct_change"
            if col not in g:
                continue
            pct = pd.to_numeric(g[col], errors="coerce")
            abs_pct = pct.abs().replace([np.inf, -np.inf], np.nan).dropna()
            if abs_pct.empty:
                continue
            base_vals = pd.to_numeric(g.get(f"{metric}_baseline"), errors="coerce")
            scen_vals = pd.to_numeric(g.get(f"{metric}_scenario"), errors="coerce")
            paired = pd.DataFrame({"b": base_vals, "s": scen_vals}).replace([np.inf, -np.inf], np.nan).dropna()
            # Spearman = Pearson of ranks (avoids a scipy dependency).
            rank_corr = (
                _spearman_arrays(
                    paired["b"].to_numpy(dtype=float),
                    paired["s"].to_numpy(dtype=float),
                )
                if len(paired) >= 3
                else np.nan
            )
            median_abs = float(abs_pct.median())
            median_boot = []
            rank_boot = []
            if len(abs_pct) >= 3:
                abs_array = abs_pct.to_numpy(dtype=float)
                for _ in range(2_000):
                    sample = rng.choice(
                        abs_array, size=len(abs_array), replace=True
                    )
                    median_boot.append(float(np.median(sample)))
            if len(paired) >= 4:
                pair_array = paired.to_numpy(dtype=float)
                for _ in range(1_000):
                    idx = rng.integers(0, len(pair_array), size=len(pair_array))
                    rank_boot.append(
                        _spearman_arrays(pair_array[idx, 0], pair_array[idx, 1])
                    )
            records.append(
                {
                    "scenario": scenario,
                    "metric": metric,
                    "n": int(abs_pct.shape[0]),
                    "median_abs_symmetric_pct_change": median_abs,
                    "median_abs_change_ci_lower": (
                        float(np.quantile(median_boot, 0.025))
                        if median_boot
                        else np.nan
                    ),
                    "median_abs_change_ci_upper": (
                        float(np.quantile(median_boot, 0.975))
                        if median_boot
                        else np.nan
                    ),
                    "mean_abs_symmetric_pct_change": float(abs_pct.mean()),
                    "p95_abs_symmetric_pct_change": float(abs_pct.quantile(0.95)),
                    "rank_stability_spearman": rank_corr,
                    "rank_stability_ci_lower": (
                        float(np.nanquantile(rank_boot, 0.025))
                        if rank_boot
                        else np.nan
                    ),
                    "rank_stability_ci_upper": (
                        float(np.nanquantile(rank_boot, 0.975))
                        if rank_boot
                        else np.nan
                    ),
                    "response_class": classify(median_abs),
                }
            )
    return pd.DataFrame(records)


def classify(median_abs_pct: float) -> str:
    if np.isnan(median_abs_pct):
        return "unknown"
    if median_abs_pct < 10.0:
        return "low"
    if median_abs_pct < 25.0:
        return "moderate"
    return "high"


def make_figures(summary: pd.DataFrame):
    if summary.empty:
        return
    family_rows = []
    for family, scenarios in SCENARIO_FAMILIES.items():
        subset = summary[summary["scenario"].isin(scenarios)]
        for metric, group in subset.groupby("metric"):
            family_rows.append(
                {
                    "family": family,
                    "metric": metric,
                    "value": group["median_abs_symmetric_pct_change"].median(),
                }
            )
    family_df = pd.DataFrame(family_rows)
    metric_order = [metric for metric in SENS_METRICS if metric in family_df["metric"].unique()]
    pivot = (
        family_df.pivot(index="metric", columns="family", values="value")
        .reindex(metric_order)
        .reindex(columns=list(SCENARIO_FAMILIES))
    )

    fig, ax = plt.subplots(figsize=(3.2, 4.8))
    data = pivot.values.astype(float)
    im = ax.imshow(data, aspect="auto", cmap="YlOrRd", vmin=0, vmax=200)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=6.5)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([METRIC_LABELS[m] for m in pivot.index], fontsize=7)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=6,
                        color="black" if val < 50 else "white")
    ax.set_title("Symmetric change by perturbation family", fontsize=8.5)
    colorbar = fig.colorbar(im, ax=ax)
    colorbar.set_label("Median absolute change, %", fontsize=7)
    colorbar.ax.tick_params(labelsize=6.5)
    fig.tight_layout()
    fig.savefig(common.FIGURE_DIR / "fig_sensitivity_metric_heatmap.png", dpi=400)
    fig.savefig(common.FIGURE_DIR / "fig_sensitivity_metric_heatmap.svg")
    plt.close(fig)

    by_scn = (
        summary.groupby("scenario")["median_abs_symmetric_pct_change"]
        .median()
        .sort_values()
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(by_scn.index, by_scn.values, color="#c0504d")
    ax.set_xlabel("Median absolute symmetric metric change, %")
    ax.set_title("Overall metric sensitivity by perturbation")
    fig.tight_layout()
    fig.savefig(common.FIGURE_DIR / "fig_sensitivity_by_perturbation.png", dpi=300)
    plt.close(fig)


def resolve_sessions(args):
    sessions = discover_sessions(args.dataset_root)
    if args.use_subset:
        subset_path = common.OUTPUT_DIR / "reference_subset.csv"
        if subset_path.exists():
            ids = set(pd.read_csv(subset_path)["session_id"].astype(str))
            sessions = [s for s in sessions if s.name in ids]
    if args.limit:
        sessions = sessions[: args.limit]
    return sessions


def main():
    parser = argparse.ArgumentParser(description="Run the article-2 sensitivity study.")
    parser.add_argument("--dataset-root", default=common.DEFAULT_DATASET_ROOT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--use-subset", action="store_true", help="Restrict to reference_subset.csv sessions.")
    args = parser.parse_args()

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
        all_rows.extend(sensitivity_rows(folder, baseline))

    df = pd.DataFrame(all_rows)
    summary = summarize(df)

    results_path = common.OUTPUT_DIR / "sensitivity_results.csv"
    summary_path = common.OUTPUT_DIR / "sensitivity_summary.csv"
    df.to_csv(results_path, index=False)
    summary.to_csv(summary_path, index=False)
    make_figures(summary)

    print(f"Wrote {results_path} ({len(df)} rows)")
    print(f"Wrote {summary_path} ({len(summary)} rows)")
    if not summary.empty:
        low_response = summary[summary["response_class"] == "low"]["metric"].unique()
        print(f"Metrics with low response in at least one scenario: {sorted(low_response)}")


if __name__ == "__main__":
    main()
