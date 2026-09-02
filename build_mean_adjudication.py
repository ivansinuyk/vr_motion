"""Build annotation_adjudication.csv from disagreements using a disclosed rule.

Default rule (author-approved previously): decision=mean
- events: round midpoint of frame_a and frame_b
- points: arithmetic mean of (x_a,y_a) and (x_b,y_b); frame = planned frame
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def build_mean_adjudication(disagreements: pd.DataFrame, adjudicator: str) -> pd.DataFrame:
    rows = []
    for _, r in disagreements.iterrows():
        kind = str(r["kind"])
        if kind == "event":
            fa = pd.to_numeric(r.get("frame_a"), errors="coerce")
            fb = pd.to_numeric(r.get("frame_b"), errors="coerce")
            if pd.isna(fa) or pd.isna(fb):
                raise ValueError(f"{r['disagreement_id']}: missing event frames")
            cons_frame = int(np.round((float(fa) + float(fb)) / 2.0))
            rows.append(
                {
                    "disagreement_id": r["disagreement_id"],
                    "kind": kind,
                    "session_id": r["session_id"],
                    "event_name": r["event_name"],
                    "reference_frame": "",
                    "decision": "mean",
                    "consensus_reference_frame": cons_frame,
                    "consensus_x_px": "",
                    "consensus_y_px": "",
                    "adjudication_status": "resolved",
                    "reason": "midpoint of Ivan and Daria frames (disclosed mean rule)",
                    "adjudicator_id": adjudicator,
                }
            )
        elif kind == "point":
            xa = pd.to_numeric(r.get("x_a"), errors="coerce")
            ya = pd.to_numeric(r.get("y_a"), errors="coerce")
            xb = pd.to_numeric(r.get("x_b"), errors="coerce")
            yb = pd.to_numeric(r.get("y_b"), errors="coerce")
            frame = pd.to_numeric(r.get("reference_frame"), errors="coerce")
            if pd.isna(xa) or pd.isna(ya) or pd.isna(xb) or pd.isna(yb) or pd.isna(frame):
                raise ValueError(f"{r['disagreement_id']}: missing point coords/frame")
            rows.append(
                {
                    "disagreement_id": r["disagreement_id"],
                    "kind": kind,
                    "session_id": r["session_id"],
                    "event_name": "",
                    "reference_frame": int(frame),
                    "decision": "mean",
                    "consensus_reference_frame": int(frame),
                    "consensus_x_px": (float(xa) + float(xb)) / 2.0,
                    "consensus_y_px": (float(ya) + float(yb)) / 2.0,
                    "adjudication_status": "resolved",
                    "reason": "pixel mean of Ivan and Daria clicks (disclosed mean rule)",
                    "adjudicator_id": adjudicator,
                }
            )
        else:
            raise ValueError(f"Unknown kind {kind}")
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--disagreements",
        default="second_article_outputs/annotation_disagreements.csv",
    )
    parser.add_argument(
        "--out",
        default="second_article_outputs/annotation_adjudication.csv",
    )
    parser.add_argument("--adjudicator", default="Ivan Syniuk")
    args = parser.parse_args()

    d = pd.read_csv(args.disagreements)
    out = build_mean_adjudication(d, args.adjudicator)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {len(out)} adjudication rows -> {args.out}")


if __name__ == "__main__":
    main()
