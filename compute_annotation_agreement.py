"""Compute inter-rater and intra-rater annotation agreement (human labels only)."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import second_article_common as common


def _filled(s: pd.Series) -> pd.Series:
    return s.notna() & (s.astype(str).str.strip() != "") & (s.astype(str) != "nan")


def _events(df: pd.DataFrame, annotator: str, round_n: int) -> pd.DataFrame:
    sub = df[
        (df["annotator_id"].astype(str) == annotator)
        & (pd.to_numeric(df["annotation_round"], errors="coerce") == round_n)
    ]
    ev = sub[_filled(sub["event_name"]) & ~_filled(sub["point_name"])].copy()
    ev["session_id"] = ev["session_id"].astype(str)
    ev["event_name"] = ev["event_name"].astype(str)
    ev["reference_frame"] = pd.to_numeric(ev["reference_frame"], errors="coerce")
    ev["reference_time_s"] = pd.to_numeric(ev["reference_time_s"], errors="coerce")
    ev["fps"] = pd.to_numeric(ev["fps"], errors="coerce")
    return ev


def _points(df: pd.DataFrame, annotator: str, round_n: int) -> pd.DataFrame:
    sub = df[
        (df["annotator_id"].astype(str) == annotator)
        & (pd.to_numeric(df["annotation_round"], errors="coerce") == round_n)
    ]
    pts = sub[_filled(sub["point_name"])].copy()
    pts["session_id"] = pts["session_id"].astype(str)
    pts["reference_frame"] = pd.to_numeric(pts["reference_frame"], errors="coerce")
    pts["x_px"] = pd.to_numeric(pts["x_px"], errors="coerce")
    pts["y_px"] = pd.to_numeric(pts["y_px"], errors="coerce")
    pts["frame_width"] = pd.to_numeric(pts["frame_width"], errors="coerce")
    pts["frame_height"] = pd.to_numeric(pts["frame_height"], errors="coerce")
    pts = pts.dropna(subset=["reference_frame", "x_px", "y_px"])
    pts["reference_frame"] = pts["reference_frame"].astype(int)
    return pts.drop_duplicates(["session_id", "reference_frame"], keep="first")


def _bootstrap_ci(session_values: pd.Series, n_boot: int, seed: int = 20260901):
    vals = session_values.dropna().to_numpy(dtype=float)
    if len(vals) == 0:
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        sample = rng.choice(vals, size=len(vals), replace=True)
        boots.append(np.median(sample))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(np.median(vals)), float(lo), float(hi)


def event_pairwise(a: pd.DataFrame, b: pd.DataFrame, label: str) -> pd.DataFrame:
    m = a.merge(b, on=["session_id", "event_name"], suffixes=("_a", "_b"))
    m["signed_frame_diff"] = m["reference_frame_a"] - m["reference_frame_b"]
    m["abs_frame_diff"] = m["signed_frame_diff"].abs()
    fps = m["fps_a"].fillna(m["fps_b"])
    m["signed_ms_diff"] = m["signed_frame_diff"] * (1000.0 / fps.replace(0, np.nan))
    m["abs_ms_diff"] = m["signed_ms_diff"].abs()
    m["exact_frame"] = (m["abs_frame_diff"] == 0).astype(int)
    m["within_1_frame"] = (m["abs_frame_diff"] <= 1).astype(int)
    m["within_2_frame"] = (m["abs_frame_diff"] <= 2).astype(int)
    m["comparison"] = label
    return m


def point_pairwise(a: pd.DataFrame, b: pd.DataFrame, plan: pd.DataFrame, label: str) -> pd.DataFrame:
    plan = plan.copy()
    plan["session_id"] = plan["session_id"].astype(str)
    plan["reference_frame"] = pd.to_numeric(plan["reference_frame"], errors="coerce").astype(int)
    rows = []
    for _, pr in plan.iterrows():
        sid, frame = str(pr["session_id"]), int(pr["reference_frame"])
        ra = a[(a["session_id"] == sid) & (a["reference_frame"] == frame)]
        rb = b[(b["session_id"] == sid) & (b["reference_frame"] == frame)]
        if ra.empty or rb.empty:
            continue
        xa, ya = float(ra.iloc[0]["x_px"]), float(ra.iloc[0]["y_px"])
        xb, yb = float(rb.iloc[0]["x_px"]), float(rb.iloc[0]["y_px"])
        w = float(ra.iloc[0]["frame_width"] or rb.iloc[0]["frame_width"] or 0)
        h = float(ra.iloc[0]["frame_height"] or rb.iloc[0]["frame_height"] or 0)
        diag = math.hypot(w, h) if w and h else math.nan
        dist = math.hypot(xa - xb, ya - yb)
        rows.append(
            {
                "comparison": label,
                "session_id": sid,
                "reference_frame": frame,
                "phase_label": pr.get("phase_label", ""),
                "x_a": xa,
                "y_a": ya,
                "x_b": xb,
                "y_b": yb,
                "pixel_distance": dist,
                "pct_image_diagonal": 100.0 * dist / diag if diag else math.nan,
                "over_10px": int(dist > 10),
                "over_25px": int(dist > 25),
                "over_50px": int(dist > 50),
            }
        )
    return pd.DataFrame(rows)


def summarize_events(pair: pd.DataFrame, n_boot: int) -> list[dict]:
    rows = []
    for event, g in list(pair.groupby("event_name")) + [("ALL", pair)]:
        sess = g.groupby("session_id")["abs_frame_diff"].median()
        med, lo, hi = _bootstrap_ci(sess, n_boot)
        signed = g["signed_frame_diff"]
        bias = float(signed.mean())
        sd = float(signed.std(ddof=1)) if len(signed) > 1 else math.nan
        rows.append(
            {
                "comparison": g["comparison"].iloc[0],
                "domain": "event",
                "group": event,
                "n_pairs": len(g),
                "n_sessions": g["session_id"].nunique(),
                "median_abs_frame": float(g["abs_frame_diff"].median()),
                "mean_abs_frame": float(g["abs_frame_diff"].mean()),
                "sd_abs_frame": float(g["abs_frame_diff"].std(ddof=1)) if len(g) > 1 else math.nan,
                "p95_abs_frame": float(g["abs_frame_diff"].quantile(0.95)),
                "min_abs_frame": float(g["abs_frame_diff"].min()),
                "max_abs_frame": float(g["abs_frame_diff"].max()),
                "median_abs_ms": float(g["abs_ms_diff"].median()),
                "exact_frame_frac": float(g["exact_frame"].mean()),
                "within_1_frame_frac": float(g["within_1_frame"].mean()),
                "within_2_frame_frac": float(g["within_2_frame"].mean()),
                "bias_frame": bias,
                "loa_low_frame": bias - 1.96 * sd if pd.notna(sd) else math.nan,
                "loa_high_frame": bias + 1.96 * sd if pd.notna(sd) else math.nan,
                "session_median_abs_frame": med,
                "session_median_abs_frame_ci_low": lo,
                "session_median_abs_frame_ci_high": hi,
                "note": (
                    "top_backswing vs downswing_transition distinguishability "
                    "reported separately"
                    if event == "ALL"
                    else ""
                ),
            }
        )
    # Distinguishability of top vs transition between annotators
    wide = pair.pivot_table(
        index="session_id", columns="event_name", values="reference_frame_a", aggfunc="first"
    )
    # Use annotator A frames for separation; also compare B
    for who, frame_col in (("a", "reference_frame_a"), ("b", "reference_frame_b")):
        tops = pair[pair["event_name"] == "top_backswing"][["session_id", frame_col]].rename(
            columns={frame_col: "top"}
        )
        trans = pair[pair["event_name"] == "downswing_transition"][
            ["session_id", frame_col]
        ].rename(columns={frame_col: "trans"})
        sep = tops.merge(trans, on="session_id")
        sep["gap"] = (sep["trans"] - sep["top"]).abs()
        rows.append(
            {
                "comparison": pair["comparison"].iloc[0],
                "domain": "event_definition",
                "group": f"top_vs_transition_gap_annotator_{who}",
                "n_pairs": len(sep),
                "n_sessions": len(sep),
                "median_abs_frame": float(sep["gap"].median()),
                "mean_abs_frame": float(sep["gap"].mean()),
                "sd_abs_frame": float(sep["gap"].std(ddof=1)) if len(sep) > 1 else math.nan,
                "p95_abs_frame": float(sep["gap"].quantile(0.95)),
                "min_abs_frame": float(sep["gap"].min()),
                "max_abs_frame": float(sep["gap"].max()),
                "median_abs_ms": math.nan,
                "exact_frame_frac": float((sep["gap"] == 0).mean()),
                "within_1_frame_frac": float((sep["gap"] <= 1).mean()),
                "within_2_frame_frac": float((sep["gap"] <= 2).mean()),
                "bias_frame": math.nan,
                "loa_low_frame": math.nan,
                "loa_high_frame": math.nan,
                "session_median_abs_frame": float(sep["gap"].median()),
                "session_median_abs_frame_ci_low": math.nan,
                "session_median_abs_frame_ci_high": math.nan,
                "note": "Same-session |top-transition| gap for one annotator; not ICC",
            }
        )
    return rows


def summarize_points(pair: pd.DataFrame, n_boot: int) -> list[dict]:
    rows = []
    sess = pair.groupby("session_id")["pixel_distance"].median()
    med, lo, hi = _bootstrap_ci(sess, n_boot)
    rows.append(
        {
            "comparison": pair["comparison"].iloc[0],
            "domain": "point",
            "group": "ALL_planned",
            "n_pairs": len(pair),
            "n_sessions": pair["session_id"].nunique(),
            "median_pixel": float(pair["pixel_distance"].median()),
            "mean_pixel": float(pair["pixel_distance"].mean()),
            "sd_pixel": float(pair["pixel_distance"].std(ddof=1)) if len(pair) > 1 else math.nan,
            "p95_pixel": float(pair["pixel_distance"].quantile(0.95)),
            "max_pixel": float(pair["pixel_distance"].max()),
            "median_pct_diag": float(pair["pct_image_diagonal"].median()),
            "session_median_pixel": med,
            "session_median_pixel_ci_low": lo,
            "session_median_pixel_ci_high": hi,
            "n_over_10px": int(pair["over_10px"].sum()),
            "n_over_25px": int(pair["over_25px"].sum()),
            "n_over_50px": int(pair["over_50px"].sum()),
            "note": "Inter/intra-rater human clicks only; not algorithm agreement",
        }
    )
    return rows


def make_figures(event_pair: pd.DataFrame, point_pair: pd.DataFrame, out_dir: Path) -> None:
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    if not event_pair.empty:
        fig, ax = plt.subplots(figsize=(7, 4))
        events = sorted(event_pair["event_name"].unique())
        data = [event_pair.loc[event_pair["event_name"] == e, "abs_frame_diff"] for e in events]
        ax.boxplot(data, tick_labels=events, showfliers=False)
        ax.set_ylabel("|frame difference|")
        ax.set_title(event_pair["comparison"].iloc[0] + " event agreement")
        fig.tight_layout()
        fig.savefig(fig_dir / "fig_annotation_event_agreement.png", dpi=300)
        fig.savefig(fig_dir / "fig_annotation_event_agreement.svg")
        plt.close(fig)
    if not point_pair.empty:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.hist(point_pair["pixel_distance"], bins=20, color="#4f81bd", edgecolor="white")
        ax.set_xlabel("Euclidean click disagreement, px")
        ax.set_ylabel("Count")
        ax.set_title(point_pair["comparison"].iloc[0] + " point agreement")
        fig.tight_layout()
        fig.savefig(fig_dir / "fig_annotation_point_agreement.png", dpi=300)
        fig.savefig(fig_dir / "fig_annotation_point_agreement.svg")
        plt.close(fig)


def write_markdown(summary: pd.DataFrame, out_path: Path) -> None:
    lines = [
        "# Annotation agreement summary",
        "",
        "Human–human agreement only. Algorithm-vs-reference results are separate.",
        "",
        "Between-session corpus variation is **not** called reliability here.",
        "",
    ]
    for comparison, g in summary.groupby("comparison"):
        lines.append(f"## {comparison}")
        lines.append("")
        lines.append("```")
        lines.append(g.to_string(index=False))
        lines.append("```")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute annotation agreement tables.")
    parser.add_argument(
        "--annotations",
        default=str(common.ARTICLE2_ROOT / "reference_annotations_multirater.csv"),
    )
    parser.add_argument("--annotator-a", default="Ivan Syniuk")
    parser.add_argument("--round-a", type=int, default=1)
    parser.add_argument("--annotator-b", default="Daria Plokhotniuk")
    parser.add_argument("--round-b", type=int, default=1)
    parser.add_argument("--intrarater-annotator", default="Ivan Syniuk")
    parser.add_argument("--intrarater-round-a", type=int, default=1)
    parser.add_argument("--intrarater-round-b", type=int, default=2)
    parser.add_argument(
        "--point-plan",
        default=str(common.ARTICLE2_ROOT / "second_annotator_frame_plan.csv"),
    )
    parser.add_argument("--bootstrap-sessions", type=int, default=10000)
    parser.add_argument(
        "--out-dir",
        default=str(common.ARTICLE2_ROOT / "annotation_agreement"),
    )
    args = parser.parse_args()

    df = pd.read_csv(args.annotations)
    plan = pd.read_csv(args.point_plan)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    inter_e = event_pairwise(
        _events(df, args.annotator_a, args.round_a),
        _events(df, args.annotator_b, args.round_b),
        "inter_rater",
    )
    inter_p = point_pairwise(
        _points(df, args.annotator_a, args.round_a),
        _points(df, args.annotator_b, args.round_b),
        plan,
        "inter_rater",
    )

    # Intra-rater: restrict plan/events to sessions present in round 2
    r2_sessions = set(
        _events(df, args.intrarater_annotator, args.intrarater_round_b)["session_id"]
    )
    plan_intra = plan[plan["session_id"].astype(str).isin(r2_sessions)]
    intra_e = event_pairwise(
        _events(df, args.intrarater_annotator, args.intrarater_round_a),
        _events(df, args.intrarater_annotator, args.intrarater_round_b),
        "intra_rater_ivan",
    )
    intra_e = intra_e[intra_e["session_id"].isin(r2_sessions)]
    intra_p = point_pairwise(
        _points(df, args.intrarater_annotator, args.intrarater_round_a),
        _points(df, args.intrarater_annotator, args.intrarater_round_b),
        plan_intra,
        "intra_rater_ivan",
    )

    event_all = pd.concat([inter_e, intra_e], ignore_index=True)
    point_all = pd.concat([inter_p, intra_p], ignore_index=True)
    event_all.to_csv(out_dir / "annotation_event_pairwise.csv", index=False)
    point_all.to_csv(out_dir / "annotation_point_pairwise.csv", index=False)

    summary_rows = []
    for pair in (inter_e, intra_e):
        if not pair.empty:
            summary_rows.extend(summarize_events(pair, args.bootstrap_sessions))
    for pair in (inter_p, intra_p):
        if not pair.empty:
            summary_rows.extend(summarize_points(pair, args.bootstrap_sessions))
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(out_dir / "annotation_agreement_summary.csv", index=False)
    write_markdown(summary, out_dir / "annotation_agreement_summary.md")

    make_figures(inter_e, inter_p, out_dir)
    make_figures(intra_e, intra_p, out_dir / "intra")
    print(f"Wrote annotation agreement outputs -> {out_dir}")
    print(summary[["comparison", "domain", "group", "n_pairs"]].to_string(index=False))


if __name__ == "__main__":
    main()
