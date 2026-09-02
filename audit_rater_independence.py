"""Sanity-check that raw rater CSVs are genuine independent annotation.

The first generation of this audit only looked for two narrow fabrication
patterns (event offsets capped at +/-2 frames that never match exactly, and
click offsets inside a +/-4 px integer box). A later synthetic rater file passed
both while still being a derivative of Ivan round 1, so the audit now also
checks:

* duplicate ``(session_id, reference_frame)`` point rows inside one rater round,
  which a real annotation session cannot produce and which the previous version
  silently de-duplicated away;
* coordinate quantization -- the OpenCV click tool writes integer pixels, so a
  rater file made of continuous values has been post-processed;
* cross-frame coordinate reuse -- whether every click of a rater file sits a few
  pixels away from *some* Ivan click in the same session, including clicks that
  the frame labels assign to a different frame.

Exit status is non-zero when any check fails, so the script can gate a rebuild.

Run:
    python audit_rater_independence.py
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

BASE = "second_article_outputs/"

# A genuine second rater must not reproduce the reference rater's coordinate
# values; these bounds only trip on files that do.
REUSE_TOLERANCE_PX = 10.0
REUSE_FRACTION_LIMIT = 0.75
ENVELOPE_LIMIT_PX = 60.0
INTEGER_FRACTION_LIMIT = 0.5

FAILURES: list[str] = []


def fail(message: str) -> None:
    FAILURES.append(message)
    print(f"FAIL {message}")


def _filled(s: pd.Series) -> pd.Series:
    return s.notna() & (s.astype(str).str.strip() != "") & (s.astype(str) != "nan")


def _events(df: pd.DataFrame) -> pd.DataFrame:
    ev = df[_filled(df["event_name"]) & ~_filled(df["point_name"])].copy()
    ev["session_id"] = ev["session_id"].astype(str)
    ev["event_name"] = ev["event_name"].astype(str)
    ev["reference_frame"] = pd.to_numeric(ev["reference_frame"], errors="coerce")
    return ev


def _raw_points(df: pd.DataFrame) -> pd.DataFrame:
    """Every point row, duplicates retained."""
    pt = df[_filled(df["point_name"])].copy()
    pt["session_id"] = pt["session_id"].astype(str)
    pt["reference_frame"] = pd.to_numeric(pt["reference_frame"], errors="coerce")
    pt["x_px"] = pd.to_numeric(pt["x_px"], errors="coerce")
    pt["y_px"] = pd.to_numeric(pt["y_px"], errors="coerce")
    pt = pt.dropna(subset=["reference_frame", "x_px", "y_px"])
    pt["reference_frame"] = pt["reference_frame"].astype(int)
    return pt


def _points(df: pd.DataFrame) -> pd.DataFrame:
    return _raw_points(df).drop_duplicates(["session_id", "reference_frame"], keep="last")


def check_frame_label_collisions(name: str, df: pd.DataFrame) -> None:
    pt = _raw_points(df)
    counts = pt.groupby(["session_id", "reference_frame"]).size()
    colliding = counts[counts > 1]
    print(
        f"{name}: point rows={len(pt)} unique (session,frame)={len(counts)} "
        f"colliding frame labels={len(colliding)}"
    )
    if len(colliding):
        sessions = colliding.reset_index()["session_id"].nunique()
        fail(
            f"{name} has {len(colliding)} duplicated (session, frame) point keys across "
            f"{sessions} sessions: one annotation round cannot click the same frame twice, "
            "so the frame labels were rewritten after the fact"
        )


def check_coordinate_quantization(name: str, df: pd.DataFrame, reference_integer_frac: float) -> None:
    pt = _raw_points(df)
    x, y = pt["x_px"].to_numpy(float), pt["y_px"].to_numpy(float)
    integer_frac = float(np.mean((x == np.round(x)) & (y == np.round(y))))
    print(f"{name}: clicks on integer pixel coordinates: {100 * integer_frac:.1f}%")
    if reference_integer_frac > 0.9 and integer_frac < INTEGER_FRACTION_LIMIT:
        fail(
            f"{name} stores {100 * integer_frac:.1f}% integer coordinates while the frozen "
            f"reference rater stores {100 * reference_integer_frac:.1f}%: the click tool emits "
            "integer pixels, so continuous values indicate programmatic jitter"
        )


def check_coordinate_reuse(name: str, a: pd.DataFrame, b: pd.DataFrame) -> None:
    """Does every click in ``b`` sit next to *some* click of ``a`` in that session?"""
    pa, pb = _raw_points(a), _raw_points(b)
    rows = []
    for session, gb in pb.groupby("session_id"):
        ga = pa[pa["session_id"] == session]
        if ga.empty:
            continue
        P = gb[["x_px", "y_px"]].to_numpy(float)
        Q = ga[["x_px", "y_px"]].to_numpy(float)
        dist = np.sqrt(((P[:, None, :] - Q[None, :, :]) ** 2).sum(-1))
        nearest = dist.argmin(1)
        rows.append(
            pd.DataFrame(
                dict(
                    frame=gb["reference_frame"].to_numpy(),
                    nearest_px=dist.min(1),
                    nearest_frame=ga["reference_frame"].to_numpy()[nearest],
                )
            )
        )
    if not rows:
        return
    r = pd.concat(rows, ignore_index=True)
    near = r["nearest_px"] <= REUSE_TOLERANCE_PX
    near_frac = float(near.mean())
    envelope = float(r["nearest_px"].max())
    cross_frame = int((near & (r["frame"] != r["nearest_frame"])).sum())
    print(
        f"{name}: nearest-Ivan-click distance median {float(r['nearest_px'].median()):.2f} px, "
        f"max {envelope:.2f} px; within {REUSE_TOLERANCE_PX:.0f} px of some Ivan click "
        f"{near.sum()}/{len(r)} ({100 * near_frac:.1f}%); of those "
        f"{cross_frame} are matched to a different frame"
    )
    if near_frac >= REUSE_FRACTION_LIMIT and cross_frame > 0:
        fail(
            f"{name} reuses Ivan round-1 coordinate values: {100 * near_frac:.1f}% of its clicks "
            f"lie within {REUSE_TOLERANCE_PX:.0f} px of an Ivan click and {cross_frame} of those "
            "matches belong to a different frame, where the true clubhead is elsewhere"
        )
    if envelope <= ENVELOPE_LIMIT_PX:
        fail(
            f"{name} is fully enveloped by Ivan round 1: no click is further than {envelope:.1f} px "
            "from some Ivan click, which independent annotation of a moving clubhead cannot produce"
        )


def compare(name: str, a: pd.DataFrame, b: pd.DataFrame, plan: pd.DataFrame | None = None) -> None:
    print(f"\n=== ivan_r1 vs {name} ===")
    ea, eb = _events(a), _events(b)
    m = ea.merge(eb, on=["session_id", "event_name"], suffixes=("_a", "_b"))
    d = m["reference_frame_b"] - m["reference_frame_a"]
    print(f"event pairs: {len(m)}")
    print("signed frame diff value counts:")
    print(d.round().astype(int).value_counts().sort_index().to_string())
    print(
        "abs diff: min",
        float(d.abs().min()),
        "max",
        float(d.abs().max()),
        "exact-match frac",
        float((d == 0).mean()),
    )
    fake_events = (d == 0).sum() == 0 and float(d.abs().max()) <= 2
    print("FLAG synthetic-like events (+/-2 never-exact):", fake_events)
    if fake_events:
        fail(f"{name} event frames look like a capped synthetic offset of Ivan round 1")

    pa, pb = _points(a), _points(b)
    if plan is not None:
        plan = plan.copy()
        plan["session_id"] = plan["session_id"].astype(str)
        plan["reference_frame"] = pd.to_numeric(plan["reference_frame"], errors="coerce").astype(int)
        sessions = set(eb["session_id"])
        plan = plan[plan["session_id"].isin(sessions)]
        mp = plan.merge(pa, on=["session_id", "reference_frame"]).merge(
            pb, on=["session_id", "reference_frame"], suffixes=("_a", "_b")
        )
    else:
        mp = pa.merge(pb, on=["session_id", "reference_frame"], suffixes=("_a", "_b"))
    dx = mp["x_px_b"] - mp["x_px_a"]
    dy = mp["y_px_b"] - mp["y_px_a"]
    dist = np.hypot(dx, dy)
    print(f"shared planned/comparable points: {len(mp)}")
    print("dx range", float(dx.min()), float(dx.max()), "| dy range", float(dy.min()), float(dy.max()))
    print(
        "euclid: min %.2f median %.2f max %.2f"
        % (float(dist.min()), float(np.median(dist)), float(dist.max()))
    )
    box = bool(((dx.abs() <= 4) & (dy.abs() <= 4)).all()) and float(
        np.mean(np.isclose(dx, np.round(dx)) & np.isclose(dy, np.round(dy)))
    ) > 0.9
    print("FLAG synthetic-like points (+/-4 integer box):", box)
    if box:
        fail(f"{name} clicks look like a synthetic +/-4 px integer box around Ivan round 1")
    print("frac of clicks within 6 px:", float((dist <= 6).mean()))

    check_coordinate_reuse(name, a, b)


def main() -> int:
    a = pd.read_csv(BASE + "reference_annotations.csv")
    b = pd.read_csv(BASE + "reference_annotations_annotator2_round1.csv")
    c = pd.read_csv(BASE + "reference_annotations_ivan_round2.csv")
    plan = pd.read_csv(BASE + "second_annotator_frame_plan.csv")

    files = [("ivan_r1", a), ("annot2_r1", b), ("ivan_r2", c)]
    for name, df in files:
        ev = _events(df)
        pt = _points(df)
        print(
            f"{name}: rows={len(df)} sessions={df['session_id'].nunique()} "
            f"events={len(ev)} unique_point_frames={len(pt)}"
        )

    print("\n=== per-file integrity ===")
    ref_points = _raw_points(a)
    ref_x = ref_points["x_px"].to_numpy(float)
    ref_y = ref_points["y_px"].to_numpy(float)
    reference_integer_frac = float(np.mean((ref_x == np.round(ref_x)) & (ref_y == np.round(ref_y))))
    for name, df in files:
        check_frame_label_collisions(name, df)
        check_coordinate_quantization(name, df, reference_integer_frac)

    compare("annot2_r1", a, b, plan)
    compare("ivan_r2", a, c, plan)

    print("\n=== verdict ===")
    if FAILURES:
        print(f"SYNTHETIC RATER SIGNATURES DETECTED ({len(FAILURES)} failed checks):")
        for item in FAILURES:
            print(f"  - {item}")
        print(
            "\nDo not build consensus, agreement tables, or a manuscript from these files. "
            "See second_article_outputs/v3/annotation_provenance_blocker.md."
        )
        return 1
    print("no synthetic rater signature detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
