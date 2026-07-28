"""Article 2 - Script 1: select a representative subset for manual annotation.

Reads the first-article ``dataset_summary.csv``, enriches it with stratification
metadata (viewpoint, capture speed, resolution, club, quality grade), and uses
seeded largest-remainder allocation to choose a balanced subset of sessions for
manual event annotation, marking a smaller subset for point-level annotation.

Outputs:
    second_article_outputs/reference_subset.csv
    second_article_outputs/reference_subset_summary.csv

Run:
    python prepare_reference_subset.py
    python prepare_reference_subset.py --target-events 25 --target-points 12
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import second_article_common as common


STRATUM_COLS = ["viewpoint", "motion_class", "quality_grade"]


def _largest_remainder_alloc(group_sizes: dict, total_target: int) -> dict:
    """Allocate ``total_target`` slots across groups proportional to size."""
    n = sum(group_sizes.values())
    if n == 0 or total_target <= 0:
        return {k: 0 for k in group_sizes}
    total_target = min(total_target, n)
    raw = {k: size / n * total_target for k, size in group_sizes.items()}
    base = {k: int(np.floor(v)) for k, v in raw.items()}
    base = {k: min(base[k], group_sizes[k]) for k in base}
    remaining = total_target - sum(base.values())
    # Distribute leftover by largest fractional remainder, respecting caps.
    remainders = sorted(
        group_sizes.keys(),
        key=lambda k: (raw[k] - np.floor(raw[k])),
        reverse=True,
    )
    i = 0
    while remaining > 0 and any(base[k] < group_sizes[k] for k in base):
        k = remainders[i % len(remainders)]
        if base[k] < group_sizes[k]:
            base[k] += 1
            remaining -= 1
        i += 1
    return base


def select_subset(df: pd.DataFrame, target_events: int, target_points: int, seed: int):
    df = df[df["processed"] == True].copy()  # noqa: E712
    df["stratum"] = df[STRATUM_COLS].astype(str).agg(" | ".join, axis=1)

    rng = np.random.default_rng(seed)
    shuffled = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    group_sizes = shuffled.groupby("stratum").size().to_dict()
    alloc = _largest_remainder_alloc(group_sizes, target_events)

    chosen_idx = []
    for stratum, count in alloc.items():
        members = shuffled[shuffled["stratum"] == stratum]
        chosen_idx.extend(members.head(count).index.tolist())

    selected = shuffled.loc[chosen_idx].copy()
    selected["selected_for_events"] = True

    # Point-level subset: prefer easier, viewpoint-diverse sessions so that
    # manual stick-tip clicking is reliable; one per stratum first, then fill.
    quality_rank = {"good": 0, "medium": 1, "difficult": 2}
    selected["_qrank"] = selected["quality_grade"].map(quality_rank).fillna(3)
    point_order = selected.sort_values(["_qrank", "viewpoint"]).copy()

    point_ids = []
    seen_strata = set()
    for _, r in point_order.iterrows():
        if r["stratum"] not in seen_strata:
            point_ids.append(r["session_id"])
            seen_strata.add(r["stratum"])
        if len(point_ids) >= target_points:
            break
    if len(point_ids) < target_points:
        for _, r in point_order.iterrows():
            if r["session_id"] not in point_ids:
                point_ids.append(r["session_id"])
            if len(point_ids) >= target_points:
                break

    selected["selected_for_points"] = selected["session_id"].isin(point_ids)
    selected = selected.drop(columns=["_qrank"])
    return selected.sort_values(["viewpoint", "motion_class", "quality_grade", "session_id"])


def build_summary(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in ["viewpoint", "motion_class", "quality_grade", "club", "fps_bucket", "resolution_bucket"]:
        counts = selected[col].value_counts(dropna=False)
        for value, count in counts.items():
            rows.append(
                {
                    "dimension": col,
                    "value": value,
                    "n_event_sessions": int(count),
                    "n_point_sessions": int(
                        selected[(selected[col] == value) & selected["selected_for_points"]].shape[0]
                    ),
                }
            )
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Select a representative annotation subset.")
    parser.add_argument("--summary-csv", default=str(common.DATASET_SUMMARY_CSV))
    parser.add_argument("--target-events", type=int, default=25)
    parser.add_argument("--target-points", type=int, default=12)
    parser.add_argument("--seed", type=int, default=2024)
    args = parser.parse_args()

    common.ensure_output_dirs()
    meta = common.load_dataset_metadata(args.summary_csv)
    n_processed = int((meta["processed"] == True).sum())  # noqa: E712
    print(f"Loaded {len(meta)} sessions ({n_processed} processed).")

    selected = select_subset(meta, args.target_events, args.target_points, args.seed)
    summary = build_summary(selected)

    subset_path = common.OUTPUT_DIR / "reference_subset.csv"
    summary_path = common.OUTPUT_DIR / "reference_subset_summary.csv"
    selected.to_csv(subset_path, index=False)
    summary.to_csv(summary_path, index=False)

    print(
        f"Selected {len(selected)} sessions for event annotation, "
        f"{int(selected['selected_for_points'].sum())} for point annotation."
    )
    print(f"Wrote {subset_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
