"""Generate the two schematic figures for article 2 that are not analysis plots.

fig_study_design.png   - validation workflow / study design diagram (Fig. 1)
fig_annotated_frame.png - schematic annotated frame with reference stick-tip
                          control points and swing-event markers (Fig. 2)

Both are drawn by the authors (no real user frame is used, avoiding consent
issues) and saved into second_article_outputs/figures/.
"""

from __future__ import annotations

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import second_article_common as common

BLUE = "#4f81bd"
GREEN = "#9bbb59"
RED = "#c0504d"
PURPLE = "#8064a2"
GREY = "#595959"


def study_design():
    # Sized for direct insertion in one 8.2 cm manuscript column so labels
    # remain publication-readable after layout.
    fig, ax = plt.subplots(figsize=(3.2, 6.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 16)
    ax.axis("off")

    def box(x, y, w, h, text, color):
        p = FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
            linewidth=1.4, edgecolor=color, facecolor=color + "22",
        )
        ax.add_patch(p)
        ax.text(
            x + w / 2,
            y + h / 2,
            text,
            ha="center",
            va="center",
            fontsize=8.2,
        )

    def arrow(x1, y1, x2, y2):
        ax.add_patch(
            FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
                            linewidth=1.2, color=GREY)
        )

    box(1.0, 14.2, 8.0, 1.2, "71 processed golf-swing sessions", BLUE)
    box(
        1.0,
        12.3,
        8.0,
        1.2,
        "Subset selection by viewpoint,\ncapture speed, and quality",
        BLUE,
    )
    box(1.0, 10.2, 8.0, 1.4, "25 sessions:\n4 events + 260 selected-frame\nclubhead points", GREEN)
    arrow(5.0, 14.2, 5.0, 13.5)
    arrow(5.0, 12.3, 5.0, 11.6)

    box(
        0.4,
        7.9,
        4.35,
        1.5,
        "Event-frame\ncomparison +\ntime-base audit",
        RED,
    )
    box(
        5.25,
        7.9,
        4.35,
        1.5,
        "Sparse 2D\nannotation\nagreement",
        RED,
    )
    box(
        0.4,
        5.7,
        4.35,
        1.5,
        "12-scenario\nperturbation\nsensitivity",
        RED,
    )
    box(
        5.25,
        5.7,
        4.35,
        1.5,
        "Nested\nproduction-stage\nablation",
        RED,
    )
    for x in (2.6, 7.4):
        arrow(5.0, 10.2, x, 9.4)
    arrow(2.6, 7.9, 2.6, 7.2)
    arrow(7.4, 7.9, 7.4, 7.2)

    box(
        1.0,
        3.1,
        8.0,
        1.5,
        "Session-level uncertainty,\nlarge-error rates, and\noperational response tiers",
        GREEN,
    )
    arrow(2.6, 5.7, 4.2, 4.6)
    arrow(7.4, 5.7, 5.8, 4.6)

    box(
        1.0,
        0.8,
        8.0,
        1.3,
        "Evidence limited to one-annotator\n2D agreement and algorithmic\nstress testing",
        PURPLE,
    )
    arrow(5.0, 3.1, 5.0, 2.1)

    ax.set_title("Study design and evidence scope", fontsize=10)
    fig.tight_layout()
    fig.savefig(common.FIGURE_DIR / "fig_study_design.png", dpi=400)
    fig.savefig(common.FIGURE_DIR / "fig_study_design.svg")
    plt.close(fig)


def annotated_frame():
    fig, ax = plt.subplots(figsize=(3.2, 4.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_facecolor("#eef2f7")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(GREY)

    # Simple golfer silhouette (schematic, no real person).
    hip = np.array([4.6, 4.2])
    shoulder = np.array([4.9, 6.2])
    head = np.array([5.05, 6.9])
    ax.plot([hip[0], shoulder[0]], [hip[1], shoulder[1]], color=GREY, lw=3)
    ax.add_patch(plt.Circle(head, 0.35, color=GREY, fill=False, lw=3))
    ax.plot([hip[0], 4.2], [hip[1], 2.2], color=GREY, lw=3)
    ax.plot([hip[0], 5.1], [hip[1], 2.2], color=GREY, lw=3)

    # Swing arc of the stick tip (schematic) and control points along it.
    t = np.linspace(np.deg2rad(200), np.deg2rad(-20), 220)
    cx, cy, r = 4.9, 5.6, 3.1
    arc_x = cx + r * np.cos(t)
    arc_y = cy + r * np.sin(t)
    ax.plot(
        arc_x,
        arc_y,
        color=BLUE,
        lw=1.6,
        ls="--",
        alpha=0.8,
        label="Clubhead swing arc",
    )

    pts_idx = np.linspace(10, len(t) - 10, 10).astype(int)
    ax.scatter(arc_x[pts_idx], arc_y[pts_idx], s=55, color=RED, zorder=5,
               edgecolor="white", label="Manual clubhead points")

    # Event markers.
    def mark(idx, name, color):
        ax.scatter(arc_x[idx], arc_y[idx], s=150, marker="*", color=color, zorder=6,
                   edgecolor="black", linewidths=0.5)
        ax.annotate(name, (arc_x[idx], arc_y[idx]), textcoords="offset points",
                    xytext=(5, 5), fontsize=7.5, fontweight="bold", color=color)

    mark(5, "Address", GREEN)
    mark(len(t) - 12, "Top of\nbackswing", PURPLE)
    mark(len(t) - 35, "Downswing\ntransition", BLUE)
    mark(len(t) // 2, "Impact", RED)

    # Club shaft at impact.
    ax.plot([shoulder[0], arc_x[len(t) // 2]], [shoulder[1], arc_y[len(t) // 2]],
            color="black", lw=1.8, alpha=0.7)

    ax.legend(loc="lower left", fontsize=6.8, framealpha=0.9)
    ax.set_title("Operational event and point annotations", fontsize=9)
    fig.tight_layout()
    fig.savefig(common.FIGURE_DIR / "fig_annotated_frame.png", dpi=400)
    fig.savefig(common.FIGURE_DIR / "fig_annotated_frame.svg")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Make article-2 schematic figures.")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()
    if args.out_dir:
        common.configure_article2_outputs(args.out_dir)
    else:
        common.ensure_output_dirs()
    study_design()
    annotated_frame()
    print("wrote fig_study_design.png and fig_annotated_frame.png")


if __name__ == "__main__":
    main()
