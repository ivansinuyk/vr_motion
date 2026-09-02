"""Article 2 - Script 2: validate automatic swing events vs manual reference.

Compares the automatically detected events (impact, top of backswing proxy,
downswing transition) with the manual reference in
``reference_annotations.csv``. If no manual event rows exist yet, it falls
back to the (unreliable) synthetic mocap keyframes so the pipeline is still
runnable - the ``reference_source`` column records which was used, and the
synthetic fallback must NOT be reported as ground truth.

Outputs:
    second_article_outputs/event_validation_errors.csv
    second_article_outputs/event_validation_summary.csv
    second_article_outputs/figures/fig_event_error_by_event.png
    second_article_outputs/figures/fig_event_error_bland_altman.png

Run:
    python validate_events_against_reference.py
    python validate_events_against_reference.py --allow-synthetic-fallback
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import second_article_common as common
from batch_article_evaluation import extract_reference_keyframes, process_session


def auto_event_times(result):
    """Map analyzer outputs to manual definitions.

    The analyzer exports only one transition boundary. It is compared with
    both manual definitions to diagnose definition mismatch; these are not two
    independent automatic detectors.
    """
    return {
        "impact": result.get("impact_time", np.nan),
        "downswing_transition": result.get("transition_time", np.nan),
        # The analyzer's transition index doubles as a top-of-backswing proxy.
        "top_backswing": result.get("transition_time", np.nan),
    }


def load_manual_events(
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
    events = df[df["event_name"].astype(str).str.len() > 0].copy()
    events = events[events["point_name"].isna() | (events["point_name"].astype(str).str.len() == 0)]
    return events


def build_reference_table(manual_df, dataset_root, allow_synthetic):
    """Return {session_id: {event: (time_s, source)}}."""
    refs = {}
    if not manual_df.empty:
        for sid, g in manual_df.groupby("session_id"):
            refs[str(sid)] = {
                str(r["event_name"]): (float(r["reference_time_s"]), "manual")
                for _, r in g.iterrows()
                if pd.notna(r.get("reference_time_s"))
            }
    if allow_synthetic:
        # Fill any session/event lacking a manual reference with synthetic keyframes.
        subset_path = common.REFERENCE_SUBSET_CSV
        sids = (
            pd.read_csv(subset_path)["session_id"].astype(str).tolist()
            if subset_path.exists()
            else list(refs.keys())
        )
        for sid in sids:
            folder = common.session_folder(dataset_root, sid)
            synth = extract_reference_keyframes(folder)
            refs.setdefault(sid, {})
            for event, t in synth.items():
                if event not in refs[sid]:
                    refs[sid][event] = (float(t), "synthetic")
    return refs


def compute_errors(refs, dataset_root):
    rows = []
    for sid, events in refs.items():
        folder = common.session_folder(dataset_root, sid)
        result = process_session(folder, profile="scientific")
        if not result.get("ok"):
            continue
        fps = result.get("fps", np.nan)
        auto = auto_event_times(result)
        for event, (ref_t, source) in events.items():
            auto_t = auto.get(event, np.nan)
            if np.isnan(auto_t) or np.isnan(ref_t):
                continue
            err = auto_t - ref_t
            rows.append(
                {
                    "session_id": sid,
                    "event": event,
                    "comparison": (
                        "transition proxy vs manual top"
                        if event == "top_backswing"
                        else (
                            "transition proxy vs manual downswing transition"
                            if event == "downswing_transition"
                            else "impact detector vs manual impact"
                        )
                    ),
                    "auto_source": (
                        "shared transition proxy"
                        if event in ("top_backswing", "downswing_transition")
                        else "impact detector"
                    ),
                    "reference_source": source,
                    "auto_time_s": auto_t,
                    "reference_time_s": ref_t,
                    "error_s": err,
                    "abs_error_s": abs(err),
                    "error_ms": err * 1000.0,
                    "abs_error_ms": abs(err) * 1000.0,
                    "error_frames": err * fps if not np.isnan(fps) else np.nan,
                    "abs_error_frames": abs(err) * fps if not np.isnan(fps) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def _bootstrap_event_statistics(group, seed=20260728, n_boot=10_000):
    values = pd.to_numeric(group["error_ms"], errors="coerce").dropna().to_numpy()
    if not len(values):
        return {}
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(n_boot):
        sample = rng.choice(values, size=len(values), replace=True)
        bias = float(np.mean(sample))
        sd = float(np.std(sample, ddof=1)) if len(sample) > 1 else 0.0
        estimates.append(
            (
                float(np.median(sample)),
                float(np.median(np.abs(sample))),
                bias,
                bias - 1.96 * sd,
                bias + 1.96 * sd,
            )
        )
    estimates = np.asarray(estimates)
    intervals = np.quantile(estimates, [0.025, 0.975], axis=0)
    names = (
        "median_signed",
        "median_absolute",
        "mean_bias",
        "loa_lower",
        "loa_upper",
    )
    return {
        f"{name}_ci_lower_ms": float(intervals[0, idx])
        for idx, name in enumerate(names)
    } | {
        f"{name}_ci_upper_ms": float(intervals[1, idx])
        for idx, name in enumerate(names)
    }


def summarize(df):
    rows = []
    for (event, source), g in df.groupby(["event", "reference_source"]):
        abs_ms = g["abs_error_ms"].dropna()
        abs_fr = g["abs_error_frames"].dropna()
        if abs_ms.empty:
            continue
        bias = float(g["error_ms"].mean())
        sd = float(g["error_ms"].std(ddof=1))
        row = {
            "event": event,
            "comparison": g["comparison"].iloc[0],
            "auto_source": g["auto_source"].iloc[0],
            "reference_source": source,
            "n_sessions": int(len(abs_ms)),
            "median_signed_ms": float(g["error_ms"].median()),
            "mean_signed_ms": bias,
            "sd_signed_ms": sd,
            "median_abs_ms": float(abs_ms.median()),
            "p95_abs_ms": float(abs_ms.quantile(0.95)),
            "median_abs_frames": (
                float(abs_fr.median()) if not abs_fr.empty else np.nan
            ),
            "ba_bias_ms": bias,
            "ba_loa_lower_ms": bias - 1.96 * sd,
            "ba_loa_upper_ms": bias + 1.96 * sd,
        }
        row.update(_bootstrap_event_statistics(g))
        rows.append(row)
    return pd.DataFrame(rows)


def make_figures(df):
    if df.empty:
        return
    grouped = df.groupby("event")["abs_error_ms"].median().sort_values()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(grouped.index, grouped.values, color="#4f81bd")
    ax.set_ylabel("Median absolute error, ms")
    ax.set_title("Event timing error by swing event")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(common.FIGURE_DIR / "fig_event_error_by_event.png", dpi=300)
    plt.close(fig)

    events = [e for e in common.EVENT_NAMES if e in df["event"].unique()]
    if events:
        fig, axes = plt.subplots(1, len(events), figsize=(5 * len(events), 4), squeeze=False)
        for ax, event in zip(axes[0], events):
            g = df[df["event"] == event]
            mean = (g["auto_time_s"] + g["reference_time_s"]) / 2.0
            diff = (g["auto_time_s"] - g["reference_time_s"]) * 1000.0
            bias = diff.mean()
            sd = diff.std(ddof=1) if len(diff) > 1 else 0.0
            ax.scatter(mean, diff, alpha=0.7, color="#c0504d")
            ax.axhline(bias, color="black")
            ax.axhline(bias + 1.96 * sd, color="gray", ls="--")
            ax.axhline(bias - 1.96 * sd, color="gray", ls="--")
            ax.set_title(event, fontsize=9)
            ax.set_xlabel("Mean time, s")
            ax.set_ylabel("Auto - ref, ms")
        fig.suptitle("Bland-Altman: event timing")
        fig.tight_layout()
        fig.savefig(common.FIGURE_DIR / "fig_event_error_bland_altman.png", dpi=300)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Validate auto events vs manual reference.")
    parser.add_argument("--dataset-root", default=common.DEFAULT_DATASET_ROOT)
    parser.add_argument(
        "--annotations-csv",
        default=str(common.CONSENSUS_ANNOTATIONS_CSV),
        help="Reference annotations CSV (consensus preferred for algorithm agreement).",
    )
    parser.add_argument("--annotator-id", default=None)
    parser.add_argument("--annotation-round", type=int, default=None)
    parser.add_argument("--out-dir", default=None, help="Write outputs here (default: second_article_outputs).")
    parser.add_argument("--allow-synthetic-fallback", action="store_true",
                        help="Fill missing manual events with unreliable synthetic keyframes.")
    args = parser.parse_args()

    if args.out_dir:
        common.configure_article2_outputs(args.out_dir)
    else:
        common.ensure_output_dirs()

    manual = load_manual_events(
        args.annotations_csv, args.annotator_id, args.annotation_round
    )
    if manual.empty and not args.allow_synthetic_fallback:
        print(f"No manual event annotations found in {args.annotations_csv}.")
        print("Run annotate_reference.py first, or pass --allow-synthetic-fallback "
              "to produce a (clearly-labelled) synthetic baseline.")
        return

    refs = build_reference_table(manual, args.dataset_root, args.allow_synthetic_fallback)
    df = compute_errors(refs, args.dataset_root)
    if df.empty:
        print("No comparable events produced.")
        return

    summary = summarize(df)
    df.to_csv(common.OUTPUT_DIR / "event_validation_errors.csv", index=False)
    summary.to_csv(common.OUTPUT_DIR / "event_validation_summary.csv", index=False)
    make_figures(df)
    print(f"Wrote event_validation_errors.csv ({len(df)} rows) and event_validation_summary.csv")
    print(f"Reference source: {args.annotations_csv}")
    if (df["reference_source"] == "synthetic").any():
        print("NOTE: synthetic-keyframe references were used for some rows; do not report as ground truth.")


if __name__ == "__main__":
    main()
