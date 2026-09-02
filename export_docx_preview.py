"""Export a DOCX to PDF with Word and render page images for layout review.

Used to produce the article-2 preview required by the publication runbook:
``second_article_outputs/v3/article2_v3_preview.pdf``. Word is driven through
COM, so the instance is always quit in a ``finally`` block - a leftover headless
WINWORD process keeps the DOCX locked and breaks the next build.

Run:
    python export_docx_preview.py \
        --docx "article_package/Стаття_Аспірант_Синюк_HAIT_article2_v3.docx" \
        --pdf second_article_outputs/v3/article2_v3_preview.pdf \
        --pages-dir second_article_outputs/v3/_preview_pages
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

WD_FORMAT_PDF = 17
STAT_PAGES = 2


def export_pdf(docx: Path, pdf: Path) -> dict:
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    try:
        doc = word.Documents.Open(str(docx), ReadOnly=True, AddToRecentFiles=False)
        doc.Repaginate()
        stats = {
            "pages": int(doc.ComputeStatistics(STAT_PAGES)),
            "inline_shapes": int(doc.InlineShapes.Count),
            "tables": int(doc.Tables.Count),
        }
        pdf.parent.mkdir(parents=True, exist_ok=True)
        doc.ExportAsFixedFormat(str(pdf), WD_FORMAT_PDF)
        return stats
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()
        pythoncom.CoUninitialize()


def render_pages(pdf: Path, pages_dir: Path, dpi: int) -> int:
    import fitz

    pages_dir.mkdir(parents=True, exist_ok=True)
    for stale in pages_dir.glob("page*.png"):
        stale.unlink()
    with fitz.open(pdf) as document:
        for index, page in enumerate(document, start=1):
            page.get_pixmap(dpi=dpi).save(pages_dir / f"page{index:02d}.png")
        return document.page_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docx", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--pages-dir", default=None, help="optional PNG output directory")
    parser.add_argument("--dpi", type=int, default=105)
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    docx = Path(args.docx).resolve()
    if not docx.exists():
        raise SystemExit(f"missing DOCX: {docx}")
    pdf = Path(args.pdf).resolve()

    stats = export_pdf(docx, pdf)
    print(f"exported {pdf}")
    print(f"  pages={stats['pages']} inline_shapes={stats['inline_shapes']} tables={stats['tables']}")

    if args.pages_dir:
        count = render_pages(pdf, Path(args.pages_dir), args.dpi)
        print(f"  rendered {count} page images at {args.dpi} dpi into {args.pages_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
