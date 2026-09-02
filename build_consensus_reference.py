"""Build consensus reference annotations from an adjudication sheet.

Uses only human adjudication decisions (no automatic pipeline values).
Raw rater rows are not modified.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import second_article_common as common


def _filled(series: pd.Series) -> pd.Series:
    return series.notna() & (series.astype(str).str.strip() != "") & (series.astype(str) != "nan")


def _session_meta(multirater: pd.DataFrame) -> dict[str, dict]:
    meta = {}
    for sid, g in multirater.groupby(multirater["session_id"].astype(str)):
        row = g.iloc[0]
        meta[str(sid)] = {
            "video_path": row.get("video_path", ""),
            "fps": float(pd.to_numeric(row.get("fps"), errors="coerce") or 0.0),
            "frame_width": int(pd.to_numeric(row.get("frame_width"), errors="coerce") or 0),
            "frame_height": int(pd.to_numeric(row.get("frame_height"), errors="coerce") or 0),
        }
    return meta


def build_consensus(
    adjudication_path: Path,
    multirater_path: Path | None,
    annotations_fallback: list[Path],
) -> pd.DataFrame:
    adj = pd.read_csv(adjudication_path)
    required = {
        "disagreement_id",
        "kind",
        "session_id",
        "decision",
        "consensus_reference_frame",
        "adjudication_status",
    }
    missing = required - set(adj.columns)
    if missing:
        raise ValueError(f"Adjudication missing columns: {sorted(missing)}")

    unresolved = adj[adj["adjudication_status"].astype(str).str.lower() != "resolved"]
    if not unresolved.empty:
        raise ValueError(
            f"{len(unresolved)} adjudication rows are not resolved "
            f"(statuses={unresolved['adjudication_status'].unique().tolist()})"
        )

    if multirater_path and multirater_path.exists():
        multi = pd.read_csv(multirater_path)
    else:
        frames = [pd.read_csv(p) for p in annotations_fallback]
        multi = pd.concat(frames, ignore_index=True)
    meta = _session_meta(multi)

    rows = []
    for _, r in adj.iterrows():
        sid = str(r["session_id"])
        if sid not in meta:
            raise KeyError(f"No session metadata for {sid}")
        m = meta[sid]
        fps = m["fps"] or 30.0
        kind = str(r["kind"]).strip().lower()
        frame = int(pd.to_numeric(r["consensus_reference_frame"], errors="coerce"))
        t = frame / fps if fps else 0.0
        base = {
            "session_id": sid,
            "video_path": m["video_path"],
            "fps": m["fps"],
            "frame_width": m["frame_width"],
            "frame_height": m["frame_height"],
            "event_name": "",
            "reference_frame": frame,
            "reference_time_s": round(t, 5),
            "point_name": "",
            "x_px": "",
            "y_px": "",
            "annotator_id": "consensus",
            "annotation_round": 1,
            "quality_note": (
                f"adjudication:{r['disagreement_id']};"
                f"decision:{r.get('decision', '')};"
                f"reason:{r.get('reason', '')}"
            ),
        }
        if kind == "event":
            event_name = str(r.get("event_name", "")).strip()
            if not event_name:
                raise ValueError(f"{r['disagreement_id']}: event row missing event_name")
            base["event_name"] = event_name
            rows.append(base)
        elif kind == "point":
            x = pd.to_numeric(r.get("consensus_x_px"), errors="coerce")
            y = pd.to_numeric(r.get("consensus_y_px"), errors="coerce")
            if pd.isna(x) or pd.isna(y):
                raise ValueError(f"{r['disagreement_id']}: point row missing consensus x/y")
            base["point_name"] = "stick_tip_1"
            base["x_px"] = float(x)
            base["y_px"] = float(y)
            rows.append(base)
        else:
            raise ValueError(f"{r['disagreement_id']}: unknown kind {kind!r}")

    out = pd.DataFrame(rows, columns=common.REFERENCE_ANNOTATION_COLUMNS)
    return out


def validate_consensus(df: pd.DataFrame, expected_sessions: int = 25, points_per_session: int = 6) -> None:
    if df["annotator_id"].nunique() != 1 or df["annotator_id"].iloc[0] != "consensus":
        raise AssertionError("Consensus file must use annotator_id=consensus only")
    sessions = df["session_id"].nunique()
    if sessions != expected_sessions:
        raise AssertionError(f"Expected {expected_sessions} sessions, got {sessions}")

    ev = df[_filled(df["event_name"]) & ~_filled(df["point_name"])]
    pt = df[_filled(df["point_name"])]
    if len(ev) != expected_sessions * 4:
        raise AssertionError(f"Expected {expected_sessions * 4} event rows, got {len(ev)}")
    counts = ev.groupby("session_id")["event_name"].nunique()
    if not (counts == 4).all():
        raise AssertionError("Each session must have four consensus events")
    if len(pt) != expected_sessions * points_per_session:
        raise AssertionError(
            f"Expected {expected_sessions * points_per_session} consensus points, got {len(pt)}"
        )
    # No automatic-looking columns beyond schema.
    forbidden = {"auto_x_px", "auto_y_px", "algorithm_frame"}
    if forbidden.intersection(df.columns):
        raise AssertionError("Consensus must not include automatic pipeline columns")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build consensus reference from adjudication.")
    parser.add_argument(
        "--annotations",
        default=str(common.OUTPUT_DIR / "reference_annotations_multirater.csv"),
        help="Merged multi-rater CSV (preferred for session metadata).",
    )
    parser.add_argument(
        "--adjudication",
        default=str(common.OUTPUT_DIR / "annotation_adjudication.csv"),
    )
    parser.add_argument(
        "--fallback-annotations",
        action="append",
        default=None,
        help="Fallback raw CSVs if merged file is missing (repeatable).",
    )
    parser.add_argument(
        "--out",
        default=str(common.OUTPUT_DIR / "reference_annotations_consensus.csv"),
    )
    args = parser.parse_args()

    fallback = args.fallback_annotations or [
        str(common.REFERENCE_ANNOTATIONS_CSV),
        str(common.OUTPUT_DIR / "reference_annotations_annotator2_round1.csv"),
        str(common.OUTPUT_DIR / "reference_annotations_ivan_round2.csv"),
    ]

    consensus = build_consensus(
        Path(args.adjudication),
        Path(args.annotations),
        [Path(p) for p in fallback],
    )
    validate_consensus(consensus)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    consensus.to_csv(out, index=False)
    print(
        f"Wrote consensus: {len(consensus)} rows "
        f"({consensus['session_id'].nunique()} sessions) -> {out}"
    )


if __name__ == "__main__":
    main()
