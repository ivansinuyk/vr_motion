"""Measure how much of the v3 reference result is driven by the consensus file.

``audit_rater_independence.py`` establishes *whether* a rater file is genuine.
This script establishes the *consequence*: it compares the stored automatic
clubhead coordinate at each consensus frame against (a) the consensus point that
the v3 analysis actually used and (b) Ivan round 1's genuine click at the same
frame, and reports how strongly the algorithm-vs-consensus error tracks the
displacement of the consensus away from Ivan's click.

Only existing CSVs are read; nothing is recomputed from video. A high Spearman
value plus a large gap between the two error columns means the reference, not
the tracker, is producing the reported error.

Run:
    python audit_consensus_contamination.py
"""

import numpy as np
import pandas as pd

err = pd.read_csv("second_article_outputs/v3/trajectory_reference_errors.csv")
cons = pd.read_csv("second_article_outputs/reference_annotations_consensus.csv")
ivan = pd.read_csv("second_article_outputs/reference_annotations.csv")

cons = cons[cons["point_name"].notna()][
    ["session_id", "reference_frame", "x_px", "y_px", "frame_width", "frame_height"]
]
ivan = ivan[ivan["point_name"].notna()][["session_id", "reference_frame", "x_px", "y_px"]]

df = err.merge(
    cons.rename(columns={"reference_frame": "frame_idx", "x_px": "cx", "y_px": "cy"}),
    on=["session_id", "frame_idx"],
    how="left",
).merge(
    ivan.rename(columns={"reference_frame": "frame_idx", "x_px": "ix", "y_px": "iy"}),
    on=["session_id", "frame_idx"],
    how="left",
)

print("rows=%d  consensus matched=%d  ivan matched=%d" % (len(df), df["cx"].notna().sum(), df["ix"].notna().sum()))

diag = np.hypot(df["frame_width"], df["frame_height"])
df["err_cons_px"] = np.hypot(df["auto_x_px"] - df["cx"], df["auto_y_px"] - df["cy"])
df["err_ivan_px"] = np.hypot(df["auto_x_px"] - df["ix"], df["auto_y_px"] - df["iy"])
df["err_cons_pct"] = 100 * df["err_cons_px"] / diag
df["err_ivan_pct"] = 100 * df["err_ivan_px"] / diag
df["cons_vs_ivan_px"] = np.hypot(df["cx"] - df["ix"], df["cy"] - df["iy"])

print(
    "reproduced stored error_px (max abs difference vs CSV): %.4f"
    % float((df["err_cons_px"] - df["error_px"]).abs().max())
)


def session_median(col):
    per_session = df.groupby("session_id")[col].median()
    return float(per_session.median())


for label, px, pct in [
    ("vs corrupted consensus", "err_cons_px", "err_cons_pct"),
    ("vs Ivan round 1 (genuine)", "err_ivan_px", "err_ivan_pct"),
]:
    print(
        "%-26s median of session medians = %7.1f px | %5.2f %% diag | point median %7.1f px | "
        "points >100 px = %3d/%d"
        % (
            label,
            session_median(px),
            session_median(pct),
            float(df[px].median()),
            int((df[px] > 100).sum()),
            len(df),
        )
    )

print()
print("consensus point displacement from Ivan's click at the same frame:")
print(
    "  median %.1f px | P75 %.1f | P95 %.1f | max %.1f | >100 px: %d/%d"
    % (
        float(df["cons_vs_ivan_px"].median()),
        float(df["cons_vs_ivan_px"].quantile(0.75)),
        float(df["cons_vs_ivan_px"].quantile(0.95)),
        float(df["cons_vs_ivan_px"].max()),
        int((df["cons_vs_ivan_px"] > 100).sum()),
        len(df),
    )
)

corr = df[["err_cons_px", "cons_vs_ivan_px"]].corr(method="spearman").iloc[0, 1]
print("  Spearman(algorithm-vs-consensus error, consensus displacement) = %.3f" % corr)

ce = pd.read_csv("second_article_outputs/reference_annotations_consensus.csv")
ie = pd.read_csv("second_article_outputs/reference_annotations.csv")
ce = ce[ce["event_name"].notna()][["session_id", "event_name", "reference_frame"]]
ie = ie[ie["event_name"].notna()][["session_id", "event_name", "reference_frame"]]
me = ce.merge(ie, on=["session_id", "event_name"], suffixes=("_c", "_i"))
de = me["reference_frame_c"] - me["reference_frame_i"]
print()
print(
    "consensus vs Ivan R1 EVENT frames: n=%d exact=%d median|d|=%.1f P95|d|=%.1f max|d|=%d"
    % (len(me), int((de == 0).sum()), de.abs().median(), de.abs().quantile(0.95), de.abs().max())
)

clean = df[df["cons_vs_ivan_px"] <= 10]
dirty = df[df["cons_vs_ivan_px"] > 100]
print(
    "  where consensus ~= Ivan (<=10 px, n=%d): algorithm error median %.1f px"
    % (len(clean), float(clean["err_cons_px"].median()))
)
print(
    "  where consensus was dragged >100 px (n=%d): algorithm error median %.1f px"
    % (len(dirty), float(dirty["err_cons_px"].median()))
)
