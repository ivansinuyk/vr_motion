# Article 2 outputs — layout after cleanup (2026-09-02)

**Master sync (Article 1 + 2 + future):** `article_package/research_publication_status.md`

## Canonical paths

| Path | Purpose |
|------|---------|
| `reference_annotations*.csv`, `annotation_*.csv` | Live human annotation rounds, consensus, adjudication |
| `annotation_agreement/*.csv` | Inter-/intra-rater agreement tables (Fig. 3 / Table 3) |
| `v3/` | **Regenerated analysis bundle** — event/trajectory validation, sensitivity, ablation, tables, figures |
| `v3/run_v3_pipeline.ps1` | Re-run steps 1–7 (set `$DATASET_ROOT` first) |
| `v3/article2_v4_preview.pdf` | Latest DOCX layout check |
| `v3/mentor_review_resolution_checklist.md` | Mentor findings M1–M48 / F01–F24 status |

## Manuscript sources (repo root / `article_package/`)

- `article_package/second_article_manuscript.md` — text source
- `build_second_article_docx.py` — builds `article_package/Стаття_Аспірант_Синюк_HAIT_article2_v4.docx`
- Frozen fallbacks: `article2_v2.docx`, `article2_v3.docx`

## Regenerate DOCX + PDF preview

```powershell
python build_second_article_docx.py
python export_docx_preview.py `
  --docx "article_package/Стаття_Аспірант_Синюк_HAIT_article2_v4.docx" `
  --pdf "second_article_outputs/v3/article2_v4_preview.pdf"
```

Preview page PNGs are ephemeral; only the PDF is kept.

## Removed in cleanup

- Duplicate pre-`v3/` CSVs, tables, and figures at `second_article_outputs/` root
- DOCX preview PNG folders (`_preview_pages*`)
- Superseded PDF previews (`article2_preview.pdf`, `article2_v2_preview.pdf`, `article2_v3_preview.pdf`)
- Diagnostic-only figures not embedded in the article (ICC/repeatability extras, duplicate agreement plots)
- One-off agent prompt, ad-hoc DOCX utilities, deprecated `compute_reliability_statistics.py`
