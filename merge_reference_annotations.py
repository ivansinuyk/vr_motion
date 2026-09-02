"""Merge raw multi-rater annotation CSVs without overwriting duplicates."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import second_article_common as common


def _filled(series: pd.Series) -> pd.Series:
    return series.notna() & (series.astype(str).str.strip() != "") & (series.astype(str) != "nan")


def _norm(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in common.REFERENCE_ANNOTATION_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out[common.REFERENCE_ANNOTATION_COLUMNS]
    out["session_id"] = out["session_id"].astype(str)
    out["annotator_id"] = out["annotator_id"].astype(str)
    out["annotation_round"] = pd.to_numeric(out["annotation_round"], errors="coerce")
    return out


def _row_key(df: pd.DataFrame) -> pd.Series:
    """Identity for rejecting duplicate raw rows."""
    event = df["event_name"].where(_filled(df["event_name"]), "")
    point = df["point_name"].where(_filled(df["point_name"]), "")
    frame = pd.to_numeric(df["reference_frame"], errors="coerce").fillna(-1).astype(int).astype(str)
    return (
        df["session_id"].astype(str)
        + "|"
        + df["annotator_id"].astype(str)
        + "|"
        + df["annotation_round"].astype(str)
        + "|"
        + event.astype(str)
        + "|"
        + point.astype(str)
        + "|"
        + frame
    )


def merge_annotation_files(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        frames.append(_norm(pd.read_csv(path)))
    merged = pd.concat(frames, ignore_index=True)

    # Multiple tip clicks on the same frame are allowed in the UI; keep the
    # last click per (session, annotator, round, frame) for point rows.
    is_point = _filled(merged["point_name"])
    points = merged[is_point].copy()
    events = merged[~is_point].copy()
    if not points.empty:
        points["_frame"] = pd.to_numeric(points["reference_frame"], errors="coerce")
        before = len(points)
        points = points.sort_index().drop_duplicates(
            subset=["session_id", "annotator_id", "annotation_round", "_frame"],
            keep="last",
        )
        dropped = before - len(points)
        if dropped:
            print(f"Note: dropped {dropped} duplicate point-click rows (kept last per frame).")
        points = points.drop(columns="_frame")
    merged = pd.concat([events, points], ignore_index=True)

    keys = _row_key(merged)
    dup_mask = keys.duplicated(keep=False)
    if dup_mask.any():
        sample = merged.loc[dup_mask].head(10)
        raise ValueError(
            "Duplicate raw rows for the same rater/round/session/event-or-point/frame:\n"
            + sample.to_string(index=False)
        )
    return merged


def validate_merged(
    merged: pd.DataFrame,
    annotator_a: str,
    annotator_b: str,
    intrarater_annotator: str,
    planned_pairs: int | None = None,
) -> None:
    def subset(annotator: str, round_n: int) -> pd.DataFrame:
        return merged[
            (merged["annotator_id"] == annotator)
            & (merged["annotation_round"] == round_n)
        ]

    for annotator, round_n, n_sessions in (
        (annotator_a, 1, 25),
        (annotator_b, 1, 25),
    ):
        sub = subset(annotator, round_n)
        ev = sub[_filled(sub["event_name"]) & ~_filled(sub["point_name"])]
        if ev["session_id"].nunique() != n_sessions:
            raise AssertionError(
                f"{annotator} round {round_n}: expected {n_sessions} event sessions, "
                f"got {ev['session_id'].nunique()}"
            )
        counts = ev.groupby("session_id")["event_name"].nunique()
        if not (counts == 4).all():
            raise AssertionError(f"{annotator} round {round_n}: not all sessions have 4 events")

    # Intra-rater: at least some sessions for round 2
    r2 = subset(intrarater_annotator, 2)
    if r2.empty:
        raise AssertionError(f"Missing {intrarater_annotator} round 2 rows")
    print(
        f"Merged OK: {len(merged)} rows; "
        f"annotators={sorted(merged['annotator_id'].unique())}; "
        f"Ivan R2 sessions={r2['session_id'].nunique()}"
    )
    if planned_pairs is not None:
        print(f"(planned common frames expected elsewhere: {planned_pairs})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge raw multi-rater annotation files.")
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Raw annotation CSV (repeatable).",
    )
    parser.add_argument(
        "--out",
        default=str(common.OUTPUT_DIR / "reference_annotations_multirater.csv"),
    )
    parser.add_argument("--annotator-a", default="Ivan Syniuk")
    parser.add_argument("--annotator-b", default="Daria Plokhotniuk")
    parser.add_argument("--intrarater-annotator", default="Ivan Syniuk")
    args = parser.parse_args()

    paths = [Path(p) for p in args.input]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(p)

    merged = merge_annotation_files(paths)
    validate_merged(merged, args.annotator_a, args.annotator_b, args.intrarater_annotator)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
