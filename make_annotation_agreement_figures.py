"""Render publication-ready annotation-agreement figures for article 2.

``compute_annotation_agreement.py`` writes diagnostic plots whose titles and tick
labels are raw column values (``inter_rater``, ``top_backswing``). Master-review
item M37 asks for reader-facing labels in the submitted figures, so this script
re-renders the same pairwise data with journal labelling and writes into the v3
figure directory. The agreement CSVs themselves are read only, never rewritten,
so every plotted value still traces to
``second_article_outputs/annotation_agreement/``.

Run:
    python make_annotation_agreement_figures.py
    python make_annotation_agreement_figures.py --out-dir second_article_outputs/v3/figures
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AGREE_DIR = Path("second_article_outputs/annotation_agreement")

EVENT_LABELS = {
    "address": "Address",
    "top_backswing": "Top of\nbackswing",
    "downswing_transition": "Downswing\ntransition",
    "impact": "Impact",
}
EVENT_ORDER = ["address", "top_backswing", "downswing_transition", "impact"]

COMPARISON_LABELS = {
    "inter_rater": "Between annotators",
    "intra_rater_ivan": "Within annotator (repeat round)",
}
COMPARISON_COLOURS = {"inter_rater": "#3b6ea5", "intra_rater_ivan": "#d1893c"}


def event_panel(ax: plt.Axes, events: pd.DataFrame) -> None:
    positions, data, colours = [], [], []
    for slot, event in enumerate(EVENT_ORDER):
        for offset, comparison in enumerate(COMPARISON_LABELS):
            values = events.loc[
                (events["event_name"] == event) & (events["comparison"] == comparison),
                "abs_frame_diff",
            ].dropna()
            if values.empty:
                continue
            positions.append(slot + (offset - 0.5) * 0.34)
            data.append(values.to_numpy(float))
            colours.append(COMPARISON_COLOURS[comparison])

    boxes = ax.boxplot(
        data,
        positions=positions,
        widths=0.3,
        patch_artist=True,
        medianprops=dict(color="black", linewidth=1.1),
        flierprops=dict(marker="o", markersize=2.2, markerfacecolor="none", markeredgewidth=0.5),
    )
    for patch, colour in zip(boxes["boxes"], colours):
        patch.set_facecolor(colour)
        patch.set_alpha(0.55)
        patch.set_linewidth(0.7)

    ax.set_xticks(range(len(EVENT_ORDER)))
    ax.set_xticklabels([EVENT_LABELS[e] for e in EVENT_ORDER], fontsize=7)
    ax.set_ylabel("Absolute frame difference", fontsize=8)
    ax.set_title("a  Event-frame agreement", fontsize=9, loc="left")
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=COMPARISON_COLOURS[c], alpha=0.55, edgecolor="black", linewidth=0.7)
        for c in COMPARISON_LABELS
    ]
    ax.legend(handles, list(COMPARISON_LABELS.values()), fontsize=6.5, loc="upper left", framealpha=0.9)


def point_panel(ax: plt.Axes, points: pd.DataFrame) -> None:
    for comparison, label in COMPARISON_LABELS.items():
        values = points.loc[points["comparison"] == comparison, "pixel_distance"].dropna().to_numpy(float)
        if values.size == 0:
            continue
        ordered = np.sort(values)
        share = np.arange(1, ordered.size + 1) / ordered.size
        ax.step(
            ordered,
            100 * share,
            where="post",
            color=COMPARISON_COLOURS[comparison],
            linewidth=1.4,
            label=f"{label} (n={ordered.size}, median {np.median(ordered):.0f} px)",
        )
        ax.axvline(float(np.median(ordered)), color=COMPARISON_COLOURS[comparison], linestyle=":", linewidth=0.8)

    ax.set_xlabel("Euclidean clubhead click disagreement, px", fontsize=8)
    ax.set_ylabel("Cumulative share of pairs, %", fontsize=8)
    ax.set_title("b  Clubhead click agreement", fontsize=9, loc="left")
    ax.tick_params(labelsize=7)
    ax.grid(alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=6.5, loc="lower right", framealpha=0.9)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agreement-dir", default=str(AGREE_DIR))
    parser.add_argument("--out-dir", default="second_article_outputs/v3/figures")
    args = parser.parse_args()

    agree_dir = Path(args.agreement_dir)
    events = pd.read_csv(agree_dir / "annotation_event_pairwise.csv")
    points = pd.read_csv(agree_dir / "annotation_point_pairwise.csv")

    fig, axes = plt.subplots(2, 1, figsize=(3.5, 5.0))
    event_panel(axes[0], events)
    point_panel(axes[1], points)
    fig.tight_layout(h_pad=1.6)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / "fig_annotation_agreement.png"
    fig.savefig(png, dpi=400)
    fig.savefig(out_dir / "fig_annotation_agreement.svg")
    plt.close(fig)
    print(f"wrote {png} and .svg")


if __name__ == "__main__":
    main()
