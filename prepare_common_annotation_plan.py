"""Build a blinded common-frame plan for a second annotator.

Reads Ivan (or another source annotator) round-1 *point* rows only, keeps the
frozen subset sessions, and picks a deterministic spread of control frames per
session. The exported plan contains session/frame identity and phase labels for
reporting — never source coordinates or automatic pipeline values.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import second_article_common as common


def _is_filled(series: pd.Series) -> pd.Series:
    return series.notna() & (series.astype(str).str.strip() != "") & (series.astype(str) != "nan")


def classify_phase(idx: int, ev_idx: dict, impact_win: int = 2) -> str:
    """Match ``validate_trajectory_against_reference.classify_phase``."""
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


def choose_spread_frames(frames: list[int], k: int) -> list[int]:
    """Pick ``k`` unique frames spread across the ordered unique source frames."""
    ordered = sorted({int(f) for f in frames})
    if len(ordered) < k:
        raise ValueError(
            f"Need at least {k} unique source frames, found {len(ordered)}: {ordered}"
        )
    if len(ordered) == k:
        return ordered

    raw_idxs = [int(round(i * (len(ordered) - 1) / (k - 1))) for i in range(k)]
    chosen: list[int] = []
    used: set[int] = set()
    for idx in raw_idxs:
        if idx not in used:
            used.add(idx)
            chosen.append(ordered[idx])
            continue
        # Resolve rare rounding collisions by nearest unused index.
        for delta in range(1, len(ordered)):
            for cand in (idx - delta, idx + delta):
                if 0 <= cand < len(ordered) and cand not in used:
                    used.add(cand)
                    chosen.append(ordered[cand])
                    break
            else:
                continue
            break
    if len(chosen) != k:
        raise RuntimeError(f"Failed to select {k} unique frames from {ordered}")
    return sorted(chosen)


def load_source_points(annotations: Path, annotator: str, round_n: int) -> pd.DataFrame:
    df = pd.read_csv(annotations)
    pts = df[_is_filled(df["point_name"])].copy()
    pts = pts[
        (pts["annotator_id"].astype(str) == str(annotator))
        & (pd.to_numeric(pts["annotation_round"], errors="coerce") == int(round_n))
    ]
    pts["reference_frame"] = pd.to_numeric(pts["reference_frame"], errors="coerce")
    pts = pts.dropna(subset=["reference_frame"])
    pts["reference_frame"] = pts["reference_frame"].astype(int)
    pts["session_id"] = pts["session_id"].astype(str)
    return pts


def load_source_event_frames(
    annotations: Path, annotator: str, round_n: int
) -> dict[str, dict[str, int]]:
    df = pd.read_csv(annotations)
    ev = df[_is_filled(df["event_name"])].copy()
    ev = ev[~_is_filled(ev["point_name"])]
    ev = ev[
        (ev["annotator_id"].astype(str) == str(annotator))
        & (pd.to_numeric(ev["annotation_round"], errors="coerce") == int(round_n))
    ]
    ev["reference_frame"] = pd.to_numeric(ev["reference_frame"], errors="coerce")
    out: dict[str, dict[str, int]] = {}
    for _, r in ev.iterrows():
        if pd.isna(r["reference_frame"]):
            continue
        sid = str(r["session_id"])
        out.setdefault(sid, {})[str(r["event_name"])] = int(r["reference_frame"])
    return out


def build_plan(
    annotations: Path,
    subset: Path,
    annotator: str,
    round_n: int,
    points_per_session: int,
) -> pd.DataFrame:
    subset_df = pd.read_csv(subset)
    session_ids = subset_df["session_id"].astype(str).tolist()
    if len(session_ids) != len(set(session_ids)):
        raise ValueError("Subset contains duplicate session_id values.")

    pts = load_source_points(annotations, annotator, round_n)
    events = load_source_event_frames(annotations, annotator, round_n)

    rows = []
    for sid in session_ids:
        g = pts[pts["session_id"] == sid]
        if g.empty:
            raise ValueError(f"No source point rows for subset session {sid}")
        frames = choose_spread_frames(g["reference_frame"].tolist(), points_per_session)
        ev_idx = events.get(sid, {})
        for i, frame in enumerate(frames, start=1):
            rows.append(
                {
                    "session_id": sid,
                    "reference_frame": frame,
                    "plan_index": i,
                    "phase_label": classify_phase(frame, ev_idx),
                }
            )

    plan = pd.DataFrame(rows)
    forbidden = {"x_px", "y_px", "auto_x", "auto_y", "event_name", "point_name"}
    overlap = forbidden.intersection(plan.columns)
    if overlap:
        raise RuntimeError(f"Plan unexpectedly contains columns: {sorted(overlap)}")
    return plan


def validate_plan(plan: pd.DataFrame, expected_sessions: int, points_per_session: int) -> None:
    n_sessions = plan["session_id"].nunique()
    if n_sessions != expected_sessions:
        raise AssertionError(f"Expected {expected_sessions} sessions, got {n_sessions}")
    pairs = plan[["session_id", "reference_frame"]].drop_duplicates()
    expected_pairs = expected_sessions * points_per_session
    if len(pairs) != expected_pairs:
        raise AssertionError(
            f"Expected {expected_pairs} unique (session, frame) pairs, got {len(pairs)}"
        )
    counts = plan.groupby("session_id").size()
    if not (counts == points_per_session).all():
        bad = counts[counts != points_per_session]
        raise AssertionError(f"Sessions without exactly {points_per_session} frames:\n{bad}")
    if plan.duplicated(subset=["session_id", "reference_frame"]).any():
        raise AssertionError("Duplicate planned frames within a session.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare blinded common-frame plan for a second annotator."
    )
    parser.add_argument("--annotations", default=str(common.REFERENCE_ANNOTATIONS_CSV))
    parser.add_argument("--source-annotator", default="Ivan Syniuk")
    parser.add_argument("--source-round", type=int, default=1)
    parser.add_argument(
        "--subset", default=str(common.OUTPUT_DIR / "reference_subset.csv")
    )
    parser.add_argument("--points-per-session", type=int, default=6)
    parser.add_argument(
        "--out",
        default=str(common.OUTPUT_DIR / "second_annotator_frame_plan.csv"),
    )
    args = parser.parse_args()

    subset_n = pd.read_csv(args.subset)["session_id"].nunique()
    plan = build_plan(
        Path(args.annotations),
        Path(args.subset),
        args.source_annotator,
        args.source_round,
        args.points_per_session,
    )
    validate_plan(plan, subset_n, args.points_per_session)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    plan.to_csv(out, index=False)
    print(f"Wrote {len(plan)} planned frames for {plan['session_id'].nunique()} sessions -> {out}")
    print(plan["phase_label"].value_counts().to_string())


if __name__ == "__main__":
    main()
