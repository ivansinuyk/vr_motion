# Research publication status (master sync)

Last updated: **2026-09-02**. This file is the single place to see what each article is, where its artifacts live, and what remains before HAIT submission.

---

## Article line (dissertation arc)

| # | Focus | Journal target | Status |
|---|--------|----------------|--------|
| **1** | Methodological pipeline (Kalman, RTS, metrics, diagnostic batch evaluation) | HAIT | **Format-accepted DOCX** (`Стаття_Аспірант_Синюк_HAIT_aligned_final_v5.docx`). Awaiting publication / DOI for ref [32] in Article 2. |
| **2** | Reference-based 2D agreement, multi-rater protocol, perturbation sensitivity, production ablation | HAIT | **Mentor re-review:** `Стаття_Аспірант_Синюк_HAIT_article2_v4.docx`. Science + 58/72 mentor findings resolved; annotation provenance cleared. |
| **3+** | Not started — see [Future article directions](#future-article-directions) | TBD | Plan after Article 2 acceptance. |

---

## Article 1 — method paper

| Artifact | Path |
|----------|------|
| Current HAIT DOCX | `article_package/Стаття_Аспірант_Синюк_HAIT_aligned_final_v5.docx` |
| HAIT formatter base | `article_package/fix_hait_formatting.py` |
| Batch evaluation (Article 1 figures) | `article_package/evaluation_outputs/` |
| HAIT recipe | `article_package/second_article_plan_and_prompt.md` § HAIT Formatting Requirements |

**Article 2 dependency:** cite as reference **[32]** — currently *Unpublished manuscript, 2026* until Article 1 is published.

---

## Article 2 — validation / agreement paper

### Final title (EN)

*Reference-Based 2D Agreement and Perturbation Sensitivity of a Markerless Video-Based Golf-Club Motion-Analysis Workflow under Heterogeneous Recording Conditions*

### Manuscript and DOCX versions

| Version | Path | Role |
|---------|------|------|
| Text source | `article_package/second_article_manuscript.md` | Canonical editable text |
| **Current** | `article_package/Стаття_Аспірант_Синюк_HAIT_article2_v4.docx` | Ethics + AI disclosure; send to mentor |
| Fallback | `article_package/Стаття_Аспірант_Синюк_HAIT_article2_v3.docx` | Pre-ethics rebuild |
| Frozen | `article_package/Стаття_Аспірант_Синюк_HAIT_article2_v2.docx` | Pre–multi-rater baseline (do not overwrite) |
| PDF preview | `second_article_outputs/v3/article2_v4_preview.pdf` | 17 pages |

Build:

```powershell
python build_second_article_docx.py
python export_docx_preview.py `
  --docx "article_package/Стаття_Аспірант_Синюк_HAIT_article2_v4.docx" `
  --pdf "second_article_outputs/v3/article2_v4_preview.pdf"
```

### What was delivered (scope)

- **71 sessions** corpus; **25-session** stratified annotated subset (viewpoint, speed class, quality).
- **Two annotators** (Ivan Syniuk R1, Daria Plokhotniuk R1) + **Ivan R2** (10 sessions, intra-rater); blinded; `audit_rater_independence.py` exit 0.
- **Consensus** via disclosed mean/midpoint rule (`annotation_adjudication.csv`).
- **Event validation** vs consensus; transition proxy honestly mapped to two manual definitions.
- **Trajectory agreement** at selected frames; primary **% image diagonal**; heavy tail reported.
- **12 perturbation scenarios**; session-bootstrap CIs; path efficiency / smoothness least responsive (candidate only).
- **Production ablation** after **RTS process-noise fix** (`rts_smoother.py`, `test_rts_smoother.py`).
- **7 figures, 7 tables** in full-width table islands; mentor checklist 72 findings (58 resolved, 8 partial, 6 owner — see below).

### Analysis bundle (regenerate)

| Path | Purpose |
|------|---------|
| `second_article_outputs/v3/` | All CSVs, tables, figures for manuscript |
| `second_article_outputs/v3/run_v3_pipeline.ps1` | Steps 1–7 (set `$DATASET_ROOT`) |
| `second_article_outputs/annotation_agreement/` | Human agreement CSVs |
| `second_article_outputs/reference_annotations*.csv` | Raw rater + consensus inputs |
| `second_article_outputs/README.md` | Output tree after cleanup |

QA:

```powershell
python audit_rater_independence.py
python verify_article2_numbers.py
```

### Implemented scripts (Article 2 pipeline)

| Script | Status |
|--------|--------|
| `second_article_common.py` | Shared paths/helpers |
| `prepare_reference_subset.py` | Frozen 25-session subset |
| `prepare_common_annotation_plan.py` | 150-frame blind plan |
| `annotate_reference.py` | Interactive annotation |
| `init_blank_rater_outputs.py` | Blank rater CSV reset |
| `merge_reference_annotations.py` | Multirater merge |
| `prepare_annotation_disagreements.py` | Disagreement list |
| `build_mean_adjudication.py` | Mean consensus rule |
| `build_consensus_reference.py` | Consensus CSV |
| `compute_annotation_agreement.py` | Agreement stats |
| `make_annotation_agreement_figures.py` | Fig. 3 source |
| `audit_rater_independence.py` | Provenance gate |
| `audit_consensus_contamination.py` | Diagnostic only |
| `validate_events_against_reference.py` | Event validation |
| `validate_trajectory_against_reference.py` | Trajectory validation |
| `audit_article2_timebase.py` | Time-base audit |
| `run_sensitivity_study.py` | 12 scenarios, stable seeds |
| `run_ablation_study.py` | Nested production ablation |
| `build_article_tables.py` | Tables 1–7 |
| `make_article2_schematic_figures.py` | Figs 1–2 |
| `build_second_article_docx.py` | HAIT DOCX builder |
| `verify_article2_numbers.py` | Manuscript number trace |
| `export_docx_preview.py` | Word → PDF preview |

**Removed / not used:** `compute_reliability_statistics.py` (no athlete IDs; ICC claims excluded from manuscript).

### Mentor review

| Document | Path |
|----------|------|
| Master review | `article_package/second_article_master_review.md` |
| Findings F01–F24 | `article_package/article2_master_review_findings.md` |
| Resolution checklist | `second_article_outputs/v3/mentor_review_resolution_checklist.md` |
| Execution history | `article_package/article2_post_annotation_publication_runbook.md` |

### Remaining before HAIT OJS upload (not blockers for mentor review)

1. **Author photos** — Oleksii M. Maksymov, Karthik Iyer (empty in Article 1 v5 too).
2. **Article 1 [32]** — update when published (venue + DOI).
3. **Citation line** — vol/issue/pages/DOI filled by editorial after acceptance.
4. **Co-author approval** + HAIT Consent Form + Copyright License.
5. **Optional:** participant/device metadata if recovered from project records.

### Ethics / AI (v4)

- Ethics: anonymized public demonstration footage; no ethics-committee approval required (author-supplied statement in v4).
- AI: GPT-5.6 Sol, Claude Opus 5, Cursor Grok 4.6 in Cursor (2026).

---

## Future article directions

Do **not** repeat Article 1 (pipeline description) or Article 2 (sparse 2D reference agreement + stress tests). Strong candidates for Article 3+:

| Direction | Prerequisite | Scientific question |
|-----------|--------------|---------------------|
| **Pipeline correction + re-validation** | Fix RTS noise model, despiking activation, re-run v3 pipeline on same 25-session reference | Does a revised pipeline improve agreement without new claims beyond the reference precision ceiling? |
| **Athlete test–retest reliability** | Recover participant IDs + repeated trials in export | ICC / SEM / MDC for stable metrics on identifiable athletes |
| **Independent spatial calibration** | Measured club lengths or external scale | Are cm-level claims valid without circular scale from the workflow? |
| **VR / coaching usability** | Task-specific tolerance study with coaches or users | Which metrics support feedback thresholds in a training product? |
| **3D or multi-view extension** | New capture hardware or calibrated multi-camera set | Does adding depth resolve monocular failure modes identified in Article 2? |

When scoping Article 3, start from **Conclusions / limitations** in `second_article_manuscript.md` and the open items in the mentor checklist partials (M13, M23, M32, F22).

---

## Documentation map

| File | Use when |
|------|----------|
| **This file** | Overall sync; onboarding; “what’s done?” |
| `second_article_plan_and_prompt.md` | Original Article 2 design + HAIT recipe (historical + formatter reference) |
| `article2_post_annotation_publication_runbook.md` | Step-by-step execution log (Phases 0–13, completed) |
| `second_article_outputs/README.md` | Regenerating analysis + DOCX |
| `second_article_outputs/annotation_collection_README.md` | Annotation CLI (collection complete) |
| `.cursor/rules/project-overview.mdc` | Cursor agent context |

---

## Dataset default

```
C:\Users\isinu\Downloads\Telegram Desktop\7a0c087a-b6c7-42ea-bc67-63453d4cac7f
```

71 session folders; each with `mediapipe_data_full.json` + `video_processed.mp4`.
