"""Build Ivan vs Daria disagreement list for consensus adjudication.

Compares round-1 event labels and the 150 planned common-frame clubhead clicks.
Does not use automatic pipeline outputs.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

import second_article_common as common

ANNOTATOR_A_DEFAULT = "Ivan Syniuk"
ANNOTATOR_B_DEFAULT = "Daria Plokhotniuk"


def _filled(series: pd.Series) -> pd.Series:
    return series.notna() & (series.astype(str).str.strip() != "") & (series.astype(str) != "nan")


def _load_rater(path: Path, annotator: str, round_n: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[
        (df["annotator_id"].astype(str) == str(annotator))
        & (pd.to_numeric(df["annotation_round"], errors="coerce") == int(round_n))
    ].copy()
    if df.empty:
        raise ValueError(f"No rows for {annotator!r} round {round_n} in {path}")
    return df


def _events(df: pd.DataFrame) -> pd.DataFrame:
    ev = df[_filled(df["event_name"]) & ~_filled(df["point_name"])].copy()
    ev["session_id"] = ev["session_id"].astype(str)
    ev["event_name"] = ev["event_name"].astype(str)
    ev["reference_frame"] = pd.to_numeric(ev["reference_frame"], errors="coerce")
    ev["reference_time_s"] = pd.to_numeric(ev["reference_time_s"], errors="coerce")
    return ev


def _points(df: pd.DataFrame) -> pd.DataFrame:
    pts = df[_filled(df["point_name"])].copy()
    pts["session_id"] = pts["session_id"].astype(str)
    pts["reference_frame"] = pd.to_numeric(pts["reference_frame"], errors="coerce")
    pts["x_px"] = pd.to_numeric(pts["x_px"], errors="coerce")
    pts["y_px"] = pd.to_numeric(pts["y_px"], errors="coerce")
    pts = pts.dropna(subset=["reference_frame", "x_px", "y_px"])
    pts["reference_frame"] = pts["reference_frame"].astype(int)
    # One click per frame: keep first if duplicates.
    pts = pts.sort_values(["session_id", "reference_frame"]).drop_duplicates(
        ["session_id", "reference_frame"], keep="first"
    )
    return pts


def build_disagreements(
    path_a: Path,
    path_b: Path,
    plan_path: Path,
    annotator_a: str,
    annotator_b: str,
    round_a: int,
    round_b: int,
) -> pd.DataFrame:
    a = _load_rater(path_a, annotator_a, round_a)
    b = _load_rater(path_b, annotator_b, round_b)
    plan = pd.read_csv(plan_path)
    plan["session_id"] = plan["session_id"].astype(str)
    plan["reference_frame"] = pd.to_numeric(plan["reference_frame"], errors="coerce").astype(int)

    rows: list[dict] = []

    ea, eb = _events(a), _events(b)
    ev = ea.merge(
        eb,
        on=["session_id", "event_name"],
        suffixes=("_a", "_b"),
        how="outer",
        indicator=True,
    )
    for _, r in ev.iterrows():
        fa = r.get("reference_frame_a")
        fb = r.get("reference_frame_b")
        frame_diff = (
            abs(float(fa) - float(fb)) if pd.notna(fa) and pd.notna(fb) else math.nan
        )
        rows.append(
            {
                "kind": "event",
                "session_id": r["session_id"],
                "event_name": r["event_name"],
                "reference_frame": "",  # N/A for events (two candidates)
                "plan_index": "",
                "phase_label": "",
                "annotator_a": annotator_a,
                "annotator_b": annotator_b,
                "round_a": round_a,
                "round_b": round_b,
                "frame_a": fa if pd.notna(fa) else "",
                "time_s_a": r.get("reference_time_s_a", ""),
                "frame_b": fb if pd.notna(fb) else "",
                "time_s_b": r.get("reference_time_s_b", ""),
                "x_a": "",
                "y_a": "",
                "x_b": "",
                "y_b": "",
                "frame_abs_diff": frame_diff if pd.notna(frame_diff) else "",
                "pixel_distance": "",
                "match_status": r["_merge"],
                "needs_adjudication": "yes" if (pd.isna(frame_diff) or frame_diff > 0) else "optional",
            }
        )

    pa, pb = _points(a), _points(b)
    for _, pr in plan.iterrows():
        sid = str(pr["session_id"])
        frame = int(pr["reference_frame"])
        ra = pa[(pa["session_id"] == sid) & (pa["reference_frame"] == frame)]
        rb = pb[(pb["session_id"] == sid) & (pb["reference_frame"] == frame)]
        xa = ya = xb = yb = math.nan
        status = "both"
        if ra.empty and rb.empty:
            status = "missing_both"
        elif ra.empty:
            status = "missing_a"
        elif rb.empty:
            status = "missing_b"
        else:
            xa, ya = float(ra.iloc[0]["x_px"]), float(ra.iloc[0]["y_px"])
            xb, yb = float(rb.iloc[0]["x_px"]), float(rb.iloc[0]["y_px"])
        dist = (
            math.hypot(xa - xb, ya - yb)
            if status == "both"
            else math.nan
        )
        rows.append(
            {
                "kind": "point",
                "session_id": sid,
                "event_name": "",
                "reference_frame": frame,
                "plan_index": pr.get("plan_index", ""),
                "phase_label": pr.get("phase_label", ""),
                "annotator_a": annotator_a,
                "annotator_b": annotator_b,
                "round_a": round_a,
                "round_b": round_b,
                "frame_a": frame if status != "missing_a" and status != "missing_both" else "",
                "time_s_a": "",
                "frame_b": frame if status != "missing_b" and status != "missing_both" else "",
                "time_s_b": "",
                "x_a": xa if pd.notna(xa) else "",
                "y_a": ya if pd.notna(ya) else "",
                "x_b": xb if pd.notna(xb) else "",
                "y_b": yb if pd.notna(yb) else "",
                "frame_abs_diff": 0 if status == "both" else "",
                "pixel_distance": dist if pd.notna(dist) else "",
                "match_status": status,
                "needs_adjudication": "yes"
                if status != "both" or (pd.notna(dist) and dist > 0)
                else "optional",
            }
        )

    out = pd.DataFrame(rows)
    # Stable order: events then points, by session.
    kind_order = {"event": 0, "point": 1}
    out["_k"] = out["kind"].map(kind_order)
    out = out.sort_values(["_k", "session_id", "event_name", "reference_frame"]).drop(
        columns="_k"
    )
    out.insert(0, "disagreement_id", [f"D{i:04d}" for i in range(1, len(out) + 1)])
    return out.reset_index(drop=True)


def adjudication_template(disagreements: pd.DataFrame) -> pd.DataFrame:
    """Empty adjudication sheet: one row per disagreement_id."""
    rows = []
    for _, r in disagreements.iterrows():
        rows.append(
            {
                "disagreement_id": r["disagreement_id"],
                "kind": r["kind"],
                "session_id": r["session_id"],
                "event_name": r["event_name"],
                "reference_frame": r["reference_frame"],
                # Required decision fields:
                "decision": "",  # choose_a | choose_b | mean | custom
                "consensus_reference_frame": "",  # events: required; points: copy planned frame
                "consensus_x_px": "",  # points only
                "consensus_y_px": "",  # points only
                "adjudication_status": "pending",  # pending | resolved | deferred
                "reason": "",
                "adjudicator_id": "",  # your name
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate annotation disagreement list.")
    parser.add_argument(
        "--annotations-a",
        default=str(common.REFERENCE_ANNOTATIONS_CSV),
        help="Ivan (or annotator A) CSV",
    )
    parser.add_argument(
        "--annotations-b",
        default=str(common.OUTPUT_DIR / "reference_annotations_annotator2_round1.csv"),
    )
    parser.add_argument(
        "--point-plan",
        default=str(common.OUTPUT_DIR / "second_annotator_frame_plan.csv"),
    )
    parser.add_argument("--annotator-a", default=ANNOTATOR_A_DEFAULT)
    parser.add_argument("--annotator-b", default=ANNOTATOR_B_DEFAULT)
    parser.add_argument("--round-a", type=int, default=1)
    parser.add_argument("--round-b", type=int, default=1)
    parser.add_argument(
        "--out",
        default=str(common.OUTPUT_DIR / "annotation_disagreements.csv"),
    )
    parser.add_argument(
        "--adjudication-template",
        default=str(common.OUTPUT_DIR / "annotation_adjudication_template.csv"),
    )
    args = parser.parse_args()

    disagreements = build_disagreements(
        Path(args.annotations_a),
        Path(args.annotations_b),
        Path(args.point_plan),
        args.annotator_a,
        args.annotator_b,
        args.round_a,
        args.round_b,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    disagreements.to_csv(out, index=False)

    template = adjudication_template(disagreements)
    template_path = Path(args.adjudication_template)
    template.to_csv(template_path, index=False)

    n_ev = (disagreements["kind"] == "event").sum()
    n_pt = (disagreements["kind"] == "point").sum()
    n_need = (disagreements["needs_adjudication"] == "yes").sum()
    print(f"Wrote {len(disagreements)} rows -> {out}")
    print(f"  events: {n_ev}, planned points: {n_pt}, needs_adjudication=yes: {n_need}")
    print(f"Wrote adjudication template -> {template_path}")
    if n_ev:
        ev = disagreements[disagreements["kind"] == "event"]
        diffs = pd.to_numeric(ev["frame_abs_diff"], errors="coerce")
        print(
            "  event |frame_a-frame_b|: "
            f"median={diffs.median():.1f}, max={diffs.max():.1f}, exact={int((diffs == 0).sum())}"
        )
    if n_pt:
        pt = disagreements[disagreements["kind"] == "point"]
        dist = pd.to_numeric(pt["pixel_distance"], errors="coerce")
        print(
            "  point pixel_distance: "
            f"median={dist.median():.2f}, max={dist.max():.2f}, exact={int((dist == 0).sum())}"
        )


if __name__ == "__main__":
    main()
