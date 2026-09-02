"""Trace every quantitative claim in the article-2 manuscript back to a v3 CSV.

The script reads only generated analysis outputs (``second_article_outputs/v3``
and ``second_article_outputs/annotation_agreement``) and prints a digest that is
used while editing ``article_package/second_article_manuscript.md``. Nothing is
recomputed from video: the digest is a projection of the accepted CSVs so that a
reviewer can match each manuscript sentence to a file and column.

Run:
    python verify_article2_numbers.py
    python verify_article2_numbers.py --out second_article_outputs/v3/manuscript_number_trace.md
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import pandas as pd

V3 = Path("second_article_outputs/v3")
AGREE = Path("second_article_outputs/annotation_agreement")
ANNOT = Path("second_article_outputs")

REQUIRED = [
    V3 / "event_validation_summary.csv",
    V3 / "event_validation_errors.csv",
    V3 / "trajectory_reference_summary.csv",
    V3 / "trajectory_reference_session_summary.csv",
    V3 / "trajectory_reference_failure_summary.csv",
    V3 / "trajectory_reference_subgroup_summary.csv",
    V3 / "trajectory_reference_errors.csv",
    V3 / "sensitivity_summary.csv",
    V3 / "ablation_summary.csv",
    V3 / "timebase_audit_sessions.csv",
    V3 / "baseline" / "dataset_summary.csv",
    AGREE / "annotation_agreement_summary.csv",
    AGREE / "annotation_event_pairwise.csv",
    AGREE / "annotation_point_pairwise.csv",
    ANNOT / "reference_annotations_consensus.csv",
    ANNOT / "annotation_adjudication.csv",
    ANNOT / "reference_annotations_multirater.csv",
]

EVENT_ORDER = ["top_backswing", "downswing_transition", "impact"]
METRIC_ORDER = [
    "smoothness_index",
    "path_efficiency",
    "max_speed",
    "max_accel",
    "max_ang_vel",
    "curvature_rms",
    "swing_tempo",
    "backswing_peak_speed",
]


def check_inputs() -> None:
    missing = [str(path) for path in REQUIRED if not path.exists()]
    if missing:
        raise SystemExit("missing required inputs:\n  " + "\n  ".join(missing))


def section(out: io.StringIO, title: str) -> None:
    out.write(f"\n## {title}\n\n")


def line(out: io.StringIO, text: str) -> None:
    out.write(f"- {text}\n")


def annotation_provenance(out: io.StringIO) -> None:
    section(out, "Annotation provenance (raw raters, consensus, adjudication)")
    multi = pd.read_csv(ANNOT / "reference_annotations_multirater.csv")
    for (annotator, rnd), grp in multi.groupby(["annotator_id", "annotation_round"]):
        events = grp[grp["event_name"].notna()]
        points = grp[grp["point_name"].notna()]
        line(
            out,
            f"raw rater `{annotator}` round {rnd}: {grp['session_id'].nunique()} sessions, "
            f"{len(events)} event labels, {len(points)} clubhead points "
            "[reference_annotations_multirater.csv]",
        )

    cons = pd.read_csv(ANNOT / "reference_annotations_consensus.csv")
    cons_events = cons[cons["event_name"].notna()]
    cons_points = cons[cons["point_name"].notna()]
    line(
        out,
        f"consensus reference: {cons['session_id'].nunique()} sessions, {len(cons_events)} event rows "
        f"({cons_events['event_name'].nunique()} event types), {len(cons_points)} clubhead points "
        "[reference_annotations_consensus.csv]",
    )

    adj = pd.read_csv(ANNOT / "annotation_adjudication.csv")
    line(
        out,
        f"adjudication rows: {len(adj)} total; by kind "
        f"{adj['kind'].value_counts().to_dict()}; by decision {adj['decision'].value_counts().to_dict()}; "
        f"status {adj['adjudication_status'].value_counts().to_dict()} [annotation_adjudication.csv]",
    )
    line(out, f"adjudication reasons: {sorted(adj['reason'].unique())} [annotation_adjudication.csv]")


def annotation_agreement(out: io.StringIO) -> None:
    section(out, "Annotation agreement (human-human only)")
    summ = pd.read_csv(AGREE / "annotation_agreement_summary.csv")
    for comparison in ["inter_rater", "intra_rater_ivan"]:
        block = summ[summ["comparison"] == comparison]
        events = block[(block["domain"] == "event")]
        for _, row in events.iterrows():
            line(
                out,
                f"{comparison} / {row['group']}: n={int(row['n_pairs'])} pairs in "
                f"{int(row['n_sessions'])} sessions; median |Δframe|={row['median_abs_frame']:.3g}; "
                f"P95={row['p95_abs_frame']:.3g}; max={row['max_abs_frame']:.3g}; "
                f"median |Δt|={row['median_abs_ms']:.4g} ms; exact={row['exact_frame_frac']:.3g}; "
                f"within1={row['within_1_frame_frac']:.3g}; within2={row['within_2_frame_frac']:.3g}; "
                f"bias={row['bias_frame']:.3g}; LoA=[{row['loa_low_frame']:.3g}, {row['loa_high_frame']:.3g}]; "
                f"session median={row['session_median_abs_frame']:.3g} "
                f"(CI {row['session_median_abs_frame_ci_low']:.3g}-{row['session_median_abs_frame_ci_high']:.3g})",
            )
        defs = block[block["domain"] == "event_definition"]
        for _, row in defs.iterrows():
            line(
                out,
                f"{comparison} / {row['group']}: median |top-transition| gap="
                f"{row['median_abs_frame']:.3g} frames; mean={row['mean_abs_frame']:.3g}; "
                f"max={row['max_abs_frame']:.3g}; frac gap<=2 frames={row['within_2_frame_frac']:.3g}",
            )
        pts = block[block["domain"] == "point"]
        for _, row in pts.iterrows():
            line(
                out,
                f"{comparison} / planned points: n={int(row['n_pairs'])} in {int(row['n_sessions'])} sessions; "
                f"median={row['median_pixel']:.4g} px ({row['median_pct_diag']:.3g}% diag); "
                f"P95={row['p95_pixel']:.4g} px; max={row['max_pixel']:.4g} px; "
                f"session median={row['session_median_pixel']:.4g} px "
                f"(CI {row['session_median_pixel_ci_low']:.4g}-{row['session_median_pixel_ci_high']:.4g}); "
                f">10px={int(row['n_over_10px'])}; >25px={int(row['n_over_25px'])}; "
                f">50px={int(row['n_over_50px'])}",
            )

    pair = pd.read_csv(AGREE / "annotation_point_pairwise.csv")
    for comparison, grp in pair.groupby("comparison"):
        line(
            out,
            f"{comparison} point pairs available by phase: "
            f"{grp['phase_label'].value_counts().to_dict()} [annotation_point_pairwise.csv]",
        )


def event_results(out: io.StringIO) -> None:
    section(out, "Algorithm vs consensus - event timing")
    summ = pd.read_csv(V3 / "event_validation_summary.csv").set_index("event")
    for event in EVENT_ORDER:
        row = summ.loc[event]
        line(
            out,
            f"{event} ({row['comparison']}): n={int(row['n_sessions'])}; "
            f"median |Δt|={row['median_abs_ms']:.4g} ms "
            f"(CI {row['median_absolute_ci_lower_ms']:.4g}-{row['median_absolute_ci_upper_ms']:.4g}); "
            f"median |Δframe|={row['median_abs_frames']:.3g}; "
            f"median signed={row['median_signed_ms']:.4g} ms; mean bias={row['ba_bias_ms']:.5g} ms "
            f"(CI {row['mean_bias_ci_lower_ms']:.5g}-{row['mean_bias_ci_upper_ms']:.5g}); "
            f"SD={row['sd_signed_ms']:.5g} ms; P95 |Δt|={row['p95_abs_ms']:.5g} ms; "
            f"LoA=[{row['ba_loa_lower_ms']:.5g}, {row['ba_loa_upper_ms']:.5g}] ms",
        )
    errors = pd.read_csv(V3 / "event_validation_errors.csv")
    line(out, f"event comparisons total: {len(errors)} rows across {errors['session_id'].nunique()} sessions")
    line(
        out,
        f"|Δframe| overall: min={errors['abs_error_frames'].min():.3g}; "
        f"median={errors['abs_error_frames'].median():.3g}; max={errors['abs_error_frames'].max():.3g}",
    )
    line(
        out,
        f"signed frame error sign counts: negative={(errors['error_frames'] < 0).sum()}; "
        f"zero={(errors['error_frames'] == 0).sum()}; positive={(errors['error_frames'] > 0).sum()}",
    )
    line(out, f"distinct auto_source values: {sorted(errors['auto_source'].unique())}")

    tb = pd.read_csv(V3 / "timebase_audit_sessions.csv")
    line(out, f"timebase audit columns: {list(tb.columns)}")
    for col in tb.columns:
        if tb[col].dtype.kind in "fi" and tb[col].notna().any():
            line(out, f"timebase `{col}`: max={tb[col].max():.6g}; min={tb[col].min():.6g}")


def trajectory_results(out: io.StringIO) -> None:
    section(out, "Algorithm vs consensus - clubhead localization")
    sess = pd.read_csv(V3 / "trajectory_reference_session_summary.csv")
    for _, row in sess.iterrows():
        line(
            out,
            f"{row['phase']}: n_s={int(row['sessions_n'])}, n_p={int(row['points_n'])}; "
            f"median of session medians={row['median_of_session_medians_px']:.4g} px "
            f"(CI {row['median_px_ci_lower']:.4g}-{row['median_px_ci_upper']:.4g}); "
            f"{100 * row['median_of_session_medians_norm']:.4g}% diag "
            f"(CI {100 * row['median_norm_ci_lower']:.4g}-{100 * row['median_norm_ci_upper']:.4g}); "
            f"model-dependent {100 * row['median_of_session_medians_m']:.4g} cm; "
            f"point P95={row['point_level_p95_px']:.5g} px; point max={row['point_level_max_px']:.5g} px; "
            f">100px={int(row['points_over_100px_n'])}; >250px={int(row['points_over_250px_n'])}; "
            f">500px={int(row['points_over_500px_n'])}",
        )
    fail = pd.read_csv(V3 / "trajectory_reference_failure_summary.csv")
    for _, row in fail.iterrows():
        line(
            out,
            f"failure tail `{row['criterion']}`: n={int(row['points_n'])} "
            f"({row['percent']:.4g}%) in {int(row['sessions_with_at_least_one_n'])} sessions",
        )
    pts = pd.read_csv(V3 / "trajectory_reference_errors.csv")
    line(out, f"point counts by phase: {pts['phase'].value_counts().to_dict()}")
    line(
        out,
        f"point-level error_px: median={pts['error_px'].median():.5g}; "
        f"P95={pts['error_px'].quantile(0.95):.5g}; max={pts['error_px'].max():.5g}",
    )
    sub = pd.read_csv(V3 / "trajectory_reference_subgroup_summary.csv")
    for _, row in sub.iterrows():
        line(
            out,
            f"subgroup {row['dimension']}={row['value']}: {int(row['sessions_n'])} sessions, "
            f"{int(row['points_n'])} points; median={100 * row['median_session_error_norm']:.4g}% diag "
            f"(CI {100 * row['ci_lower']:.4g}-{100 * row['ci_upper']:.4g})",
        )


def sensitivity_results(out: io.StringIO) -> None:
    section(out, "Perturbation sensitivity")
    sens = pd.read_csv(V3 / "sensitivity_summary.csv")
    line(out, f"scenarios={sens['scenario'].nunique()}; metrics={sens['metric'].nunique()}; rows={len(sens)}")
    line(out, f"scenario list: {sorted(sens['scenario'].unique())}")
    for metric in METRIC_ORDER:
        grp = sens[sens["metric"] == metric]
        classes = grp["response_class"].value_counts().to_dict()
        worst_row = grp.loc[grp["median_abs_symmetric_pct_change"].idxmax()]
        best_row = grp.loc[grp["median_abs_symmetric_pct_change"].idxmin()]
        line(
            out,
            f"{metric}: median of scenario medians={grp['median_abs_symmetric_pct_change'].median():.4g}%; "
            f"worst={worst_row['median_abs_symmetric_pct_change']:.4g}% ({worst_row['scenario']}); "
            f"best={best_row['median_abs_symmetric_pct_change']:.4g}% ({best_row['scenario']}); "
            f"median rho={grp['rank_stability_spearman'].median():.3g}; "
            f"rho range={grp['rank_stability_spearman'].min():.3g}-{grp['rank_stability_spearman'].max():.3g}; "
            f"classes={classes}",
        )
    line(
        out,
        "runs completed per scenario/metric (n column): "
        f"min={sens['n'].min()}, max={sens['n'].max()}",
    )


def ablation_results(out: io.StringIO) -> None:
    section(out, "Production-stage ablation")
    abl = pd.read_csv(V3 / "ablation_summary.csv")
    for _, row in abl.iterrows():
        line(
            out,
            f"{row['pipeline_variant']}: n={int(row['n_sessions'])}; "
            f"changed points median={row['stage_changed_points_median']:.4g}; "
            f"mean dev={100 * row['mean_dev_m_median']:.4g} cm; "
            f"P95 dev={100 * row['p95_dev_m_median']:.4g} cm; "
            f"max dev={100 * row['max_dev_m_median']:.4g} cm; "
            f"RMS jerk={row['rms_jerk_median']:.6g}; smoothness={row['smoothness_index_median']:.4g}; "
            f"path eff={row['path_efficiency_median']:.4g}; max speed={row['max_speed_median']:.4g}; "
            f"valid samples median={row['valid_samples_median']:.4g}",
        )


def dataset_facts(out: io.StringIO) -> None:
    section(out, "Dataset")
    ds = pd.read_csv(V3 / "baseline" / "dataset_summary.csv")
    line(out, f"sessions processed: {len(ds)}; processed flag counts {ds['processed'].value_counts().to_dict()}")
    line(out, f"fps range (video_fps_cv): {ds['video_fps_cv'].min():.5g}-{ds['video_fps_cv'].max():.5g}")
    line(
        out,
        f"width range {ds['width_cv'].min():.0f}-{ds['width_cv'].max():.0f}; "
        f"height range {ds['height_cv'].min():.0f}-{ds['height_cv'].max():.0f}",
    )
    resolutions = sorted({f"{int(w)}x{int(h)}" for w, h in zip(ds["width_cv"], ds["height_cv"])})
    line(out, f"distinct resolutions: {resolutions}")
    line(out, f"frames_json range: {ds['frames_json'].min():.0f}-{ds['frames_json'].max():.0f}")
    for column in ("session_id",):
        line(out, f"unique {column}: {ds[column].nunique()}")


def check_manuscript(path: Path) -> int:
    """Assert that the manuscript quotes the values the CSVs actually contain."""
    text = Path(path).read_text(encoding="utf-8")

    agree = pd.read_csv(AGREE / "annotation_agreement_summary.csv")
    inter_ev = agree[
        (agree["comparison"] == "inter_rater") & (agree["domain"] == "event") & (agree["group"] == "ALL")
    ].iloc[0]
    intra_ev = agree[
        (agree["comparison"] == "intra_rater_ivan") & (agree["domain"] == "event") & (agree["group"] == "ALL")
    ].iloc[0]
    inter_pt = agree[(agree["comparison"] == "inter_rater") & (agree["domain"] == "point")].iloc[0]
    intra_pt = agree[(agree["comparison"] == "intra_rater_ivan") & (agree["domain"] == "point")].iloc[0]

    events = pd.read_csv(V3 / "event_validation_summary.csv").set_index("event")
    traj = pd.read_csv(V3 / "trajectory_reference_session_summary.csv").set_index("phase")
    fail = pd.read_csv(V3 / "trajectory_reference_failure_summary.csv").set_index("criterion")
    abl = pd.read_csv(V3 / "ablation_summary.csv").set_index("pipeline_variant")
    sens = pd.read_csv(V3 / "sensitivity_summary.csv")

    def sens_median(metric):
        return sens.loc[sens["metric"] == metric, "median_abs_symmetric_pct_change"].median()

    checks = [
        ("inter-rater event median frames", f"{inter_ev['median_abs_frame']:.0f} frames"),
        ("inter-rater event median ms", f"{inter_ev['median_abs_ms']:.0f} ms"),
        ("inter-rater exact frame %", f"{100 * inter_ev['exact_frame_frac']:.0f}%"),
        ("intra-rater event median frames", f"{intra_ev['median_abs_frame']:.0f} frames"),
        ("inter-rater point median px", f"{inter_pt['median_pixel']:.1f} pixels"),
        # median_pct_diag is already stored as a percentage, unlike the
        # trajectory summary's *_norm columns, which are fractions.
        ("inter-rater point median % diag", f"{inter_pt['median_pct_diag']:.2f}% of the image diagonal"),
        ("intra-rater point median px", f"{intra_pt['median_pixel']:.1f} pixels"),
        ("event top median ms", f"{events.loc['top_backswing', 'median_abs_ms']:.0f} ms"),
        ("event transition median ms", f"{events.loc['downswing_transition', 'median_abs_ms']:.0f} ms"),
        ("event impact median ms", f"{events.loc['impact', 'median_abs_ms']:.0f} ms"),
        ("trajectory overall px", f"{traj.loc['all', 'median_of_session_medians_px']:.1f} pixels"),
        (
            "trajectory overall % diag",
            f"{100 * traj.loc['all', 'median_of_session_medians_norm']:.2f}% of the image diagonal",
        ),
        ("points over 100 px", f"{fail.loc['Large localization error', 'points_n']:.0f} of 150"),
        ("ablation raw jerk", f"{abl.loc['raw', 'rms_jerk_median']:,.0f}".replace(",", " ")),
        ("ablation full jerk", f"{abl.loc['full_pipeline', 'rms_jerk_median']:,.0f}".replace(",", " ")),
        ("ablation rts deviation", f"{100 * abl.loc['kalman_rts', 'mean_dev_m_median']:.1f} cm"),
        ("sensitivity path efficiency", f"{sens_median('path_efficiency'):.1f}%"),
        ("sensitivity smoothness", f"{sens_median('smoothness_index'):.1f}%"),
    ]

    failures = 0
    print(f"\n## Manuscript cross-check ({path})\n")
    for label, needle in checks:
        ok = needle in text
        print(f"- [{'ok' if ok else 'MISSING'}] {label}: {needle!r}")
        failures += 0 if ok else 1
    if failures:
        print(f"\n{failures} expected value(s) not found verbatim in the manuscript.")
    else:
        print("\nall checked values appear verbatim in the manuscript.")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None, help="optional Markdown digest path")
    parser.add_argument(
        "--check-manuscript",
        default=None,
        help="assert the manuscript quotes the CSV values (exit 1 on mismatch)",
    )
    args = parser.parse_args()

    # Windows consoles default to cp1251 here and cannot render the Greek/maths glyphs.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    check_inputs()
    out = io.StringIO()
    out.write("# Article 2 manuscript number trace\n\n")
    out.write(
        "Generated by `verify_article2_numbers.py` from `second_article_outputs/v3/` and "
        "`second_article_outputs/annotation_agreement/`. Every manuscript figure of merit must "
        "appear below; anything absent here must not be stated in the article.\n"
    )
    annotation_provenance(out)
    annotation_agreement(out)
    event_results(out)
    trajectory_results(out)
    sensitivity_results(out)
    ablation_results(out)
    dataset_facts(out)

    text = out.getvalue()
    print(text)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path}")

    if args.check_manuscript:
        raise SystemExit(1 if check_manuscript(Path(args.check_manuscript)) else 0)


if __name__ == "__main__":
    main()
