"""Create blank header-only rater CSVs for a fresh annotation pass.

Quarantines any existing file to the archive folder before writing the blank
output. Use this before starting Phase 2 (second annotator) or Phase 3 (Ivan
round 2) in article_package/article2_post_annotation_publication_runbook.md.

Run:
    python init_blank_rater_outputs.py --which annotator2
    python init_blank_rater_outputs.py --which ivan-round2
    python init_blank_rater_outputs.py --which both
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

import second_article_common as common

OUTPUTS = {
    "annotator2": common.OUTPUT_DIR / "reference_annotations_annotator2_round1.csv",
    "ivan-round2": common.OUTPUT_DIR / "reference_annotations_ivan_round2.csv",
}
ARCHIVE_DIR = common.OUTPUT_DIR / "_quarantine"


def init_blank(path: Path, *, quarantine: bool) -> None:
    header = ",".join(common.REFERENCE_ANNOTATION_COLUMNS) + "\n"
    if path.exists() and quarantine:
        data_lines = sum(1 for _ in path.open(encoding="utf-8")) - 1
        if data_lines > 0:
            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            dst = ARCHIVE_DIR / f"{path.stem}_quarantined_{stamp}{path.suffix}"
            shutil.move(path, dst)
            print(f"Archived {path} -> {dst} ({data_lines} data rows)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header, encoding="utf-8")
    print(f"Wrote blank {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--which",
        choices=["annotator2", "ivan-round2", "both"],
        required=True,
        help="Which blank rater output to (re)create.",
    )
    parser.add_argument(
        "--no-quarantine",
        action="store_true",
        help="Overwrite in place without archiving a non-empty file.",
    )
    args = parser.parse_args()
    keys = list(OUTPUTS) if args.which == "both" else [args.which]
    for key in keys:
        init_blank(OUTPUTS[key], quarantine=not args.no_quarantine)


if __name__ == "__main__":
    main()
