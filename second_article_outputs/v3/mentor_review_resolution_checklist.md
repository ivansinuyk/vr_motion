# Article 2 — mentor review resolution checklist

Covers every finding in `article_package/second_article_master_review.md`
(items M1–M48) and `article_package/article2_master_review_findings.md`
(F01–F24).

**Status vocabulary:** `resolved` · `partially_resolved` · `still_open` ·
`owner_blocked`

**Rebuild context (2026-09-01 evening).** `python audit_rater_independence.py`
exited 0 on the live rater files (integer pixels, no duplicate frames, no
coordinate-reuse envelope). Consensus, agreement, and v3 event/trajectory/
timebase/tables were regenerated against that consensus. The provenance
blocker is **CLEARED**. `article_package/second_article_manuscript.md` and
`article_package/Стаття_Аспірант_Синюк_HAIT_article2_v3.docx` were rebuilt
from those CSVs. The frozen v2 DOCX hash is unchanged.

**Update (2026-09-02).** v4 DOCX adds owner-supplied ethics and expanded AI
disclosure; v3 DOCX kept as fallback. Master sync:
`article_package/research_publication_status.md`.

Number trace: `second_article_outputs/v3/manuscript_number_trace.md`.
PDF preview: `second_article_outputs/v3/article2_v4_preview.pdf` (17 pages).

**Counts (72 findings):** resolved 58 · partially_resolved 8 · still_open 0 ·
owner_blocked 6

---

## Master review — Critical

| Finding ID | Issue | Status | Where fixed | Notes |
|---|---|---|---|---|
| M1 | Top of backswing and downswing transition map to one automatic output | `resolved` | Methods “Time-base and event audit”; Table 4; `event_validation_summary.csv` `auto_source`; `timebase_audit_summary.md` | Both rows are definition comparisons against one shared transition proxy. Human data also separate the two events by a median of only 3 frames. |
| M2 | Study is not a reliability/repeatability design | `resolved` | Title, aim, Methods “Statistical analysis”, Discussion | CV, RC, SEM, MDC and ICC are not calculated or claimed. Between-session corpus variation is never called reliability. |
| M3 | No human-research ethics or consent statement | `owner_blocked` | Methods “Ethics, consent, and data provenance”; declarations block in the DOCX | The text states that the export contains no ethics/consent documents and that submission is conditional. No approval, waiver, or consent is invented. |
| M4 | Accuracy and practical-trust claims exceed the reference standard | `resolved` | Abstract, Results, Discussion, Conclusions | Claims are bounded to sparse 2D agreement versus a mean consensus whose own inter-rater disagreement (4.03% of the diagonal) is larger than the algorithm–consensus discrepancy (2.54%). Coaching/VR adequacy is refused. |

## Master review — High

| Finding ID | Issue | Status | Where fixed | Notes |
|---|---|---|---|---|
| M5 | Stated stratification procedure is inaccurate | `resolved` | Methods “Dataset, sampling, and available metadata”; Table 1 | Strata are viewpoint, capture-speed class, and quality; frame-rate and resolution are summarized after selection. |
| M6 | No annotation reliability or uncertainty | `resolved` | Methods “Manual annotation protocol and rater design”, “Annotation agreement measures”; Table 3; Fig. 3; `annotation_agreement/` | Ivan Syniuk R1 (25 sessions), Daria Plokhotniuk R1 (25), Ivan R2 (10). Inter-rater event median 4 frames; intra-rater 2 frames; planned-point medians 77.1 px / 78.5 px. Reported separately from algorithm agreement. |
| M7 | Control-point selection creates verification bias | `resolved` | Methods protocol; Results failure-tail paragraph | Counts are not read as whole-video tracking success. |
| M8 | Nested trajectory points treated as independent | `resolved` | Methods “Clubhead localization agreement”; Table 5; `trajectory_reference_session_summary.csv` | Session-level medians with session bootstrap. |
| M9 | Centimetre error is not independently calibrated | `resolved` | Methods localization; Table 5 (primary % diagonal); Discussion | Pixels and % diagonal are primary; 13.6 cm is labelled model-dependent. Actual club lengths remain owner-blocked. |
| M10 | Image-diagonal-normalized error omitted from results | `resolved` | Table 5 primary column; Abstract | Session-level median 2.54% (1.98–2.88%). |
| M11 | Catastrophic trajectory failures understated | `resolved` | Results “Clubhead localization agreement and failure tail”; `trajectory_reference_failure_summary.csv` | 22/150 points (14.7%) > 100 px in 13 sessions; 5 > 250 px; 3 > 500 px; follow-through P95 498.3 px, max 2492.9 px. |
| M12 | Sensitivity seeds use Python `hash()` | `resolved` | `run_sensitivity_study.py::stable_session_seed`; Methods perturbation paragraph | Process-independent seed recorded per run. |
| M13 | Stochastic sensitivity uncertainty is unknown | `partially_resolved` | `sensitivity_summary.csv` CIs; Methods | Session-bootstrap intervals are reported; still one dropout/jitter realization per session and dose, disclosed as such. |
| M14 | Robust/usable/exploratory thresholds are arbitrary | `resolved` | Table 6 caption and Methods; Interpretation “Candidate only” | Author-defined operational bands, not coaching tolerances. |
| M15 | Smoothness robustness claim contradicts Table 7 | `resolved` | Table 6; Results; Abstract | Smoothness is 7 low / 5 moderate / 0 high (median 6.2%, worst 15.1%). The “robust in all twelve” claim is gone. |
| M16 | “Most stable under every perturbation family” is false | `resolved` | Results “Perturbation sensitivity” | Path efficiency 5.9% vs smoothness 6.2%; no metric is claimed to dominate every family. |
| M17 | Cross-device comparability of path efficiency overclaimed | `resolved` | Table 6; Discussion | Worst scenario 24.8% under jitter σ=0.008; labelled candidate only. |
| M18 | Ranking method not fully specified | `resolved` | Methods perturbation paragraph | Order is by median of the 12 scenario-level medians; scenario class counts reported; no CV and no composite score. |
| M19 | CV is unsuitable for smoothness | `resolved` | CV removed from article tables and narrative | — |
| M20 | Ablation is not monotonic as claimed | `resolved` | Table 7; Results “Production-stage ablation”; Fig. 7 | RMS jerk 17334 → 14448 → 881 → 181 → 181 → 11835. Non-monotonicity and the RTS departure of 141.4 cm are stated. |
| M21 | Ablation variants are not controlled nested variants | `resolved` | `RTS_FIX_NOTES.md`; Methods ablation; `test_rts_smoother.py` | Production RTS with `Q` is used in both production and ablation. |
| M22 | “Each stage contributes” is unsupported | `resolved` | Table 7; Results | Despiking changed 0 points; Kalman+RTS and Kalman+RTS+despike are identical. |
| M23 | Derivative definitions are nonstandard and underreported | `partially_resolved` | Methods “Production-stage ablation and metric definitions” | Speed, acceleration, jerk, RMS jerk, smoothness, path efficiency, angular velocity and curvature are defined in running text. Editable Word OMML equations are still not present. |
| M24 | Recommended metrics lack construct validity | `resolved` | Discussion; Table 6 “Candidate only” | Stability is separated from construct validity. |
| M25 | Phase-duration sensitivity claimed but not analyzed | `resolved` | Methods perturbation paragraph | Phase durations excluded because event segmentation is invalid. |
| M26 | “All remaining metrics above 25%” is numerically false | `resolved` | Table 6 | Max angular velocity 17.0%; max speed 18.7%; max acceleration 26.0%. Blanket claim removed. |
| M27 | Dataset and participant reporting is inadequate | `owner_blocked` | Methods dataset paragraph lists each missing field | Participant count, demographics, devices and camera geometry are absent from the export. |
| M28 | Frame/time synchronization is not demonstrated | `resolved` | `timebase_audit_summary.md`; Results | ≤19.6 ms annotation-vs-PTS, ≤66.7 ms landmark-vs-PTS; 12/25 variable-interval videos; 1/25 frame-count mismatch. |
| M29 | DOCX Tables 3–7 are largely unreadable | `resolved` | `build_second_article_docx.py` full-width table islands; PDF pages 8–11 | 9 pt tables span the text width. Preview shows intact headers and values (no “signe/d” or “1589/.1”). |

## Master review — Medium

| Finding ID | Issue | Status | Where fixed | Notes |
|---|---|---|---|---|
| M30 | Transition-phase trajectory estimate is too sparse | `resolved` | Table 5 (8/8); Results | Labelled descriptive only, with a wide interval. |
| M31 | “Per-frame reference” is inaccurate terminology | `resolved` | Manuscript throughout (“selected-frame”) | — |
| M32 | Bland–Altman analysis is incomplete | `partially_resolved` | Table 3 LoA; `event_validation_summary.csv` CIs for bias and limits | Bootstrap CIs added; proportional bias / heteroscedasticity still not modelled. |
| M33 | Results lack uncertainty intervals | `resolved` | Tables 3–6; event, trajectory, subgroup and sensitivity CSVs | Session-bootstrap percentile intervals. |
| M34 | The companion workflow is not explicitly cited | `partially_resolved` | In-text [32]; builder adds bibliographic entry | Currently “Unpublished manuscript, 2026”. Venue/DOI remain Phase 12 item 7. |
| M35 | Inherited references do not support several claims | `resolved` | Builder `rewrite_references_and_declarations` | Ref 7 Davis & Challis 2020; ref 24 Kim et al. 2023 golf IMU; ref 30 Ingwersen et al. 2023 monocular golf. |
| M36 | The annotation schematic omits an event | `resolved` | Fig. 2; `make_article2_schematic_figures.py` | Address, top, downswing transition, and impact are marked. |
| M37 | Figures are not publication-ready | `resolved` | Fig. 6 heatmap 0–200% with reader-facing labels; no ICC-named figure in the v3 map | Underscored variable names removed from displayed figures. |
| M38 | Limitations are dismissed despite affecting conclusions | `resolved` | Discussion | The “none of these limitations affects the central conclusions” sentence is gone. |
| M39 | Self-congratulatory reporting language | `resolved` | Results and Discussion | Neutral scientific wording. |
| M40 | The abstract omits decisive limitations | `resolved` | ABSTRACT | Sparse two-rater visual reference, dependent scaling, absent test–retest, and no coaching/VR adequacy are named. |
| M41 | Rank-stability narrative contradicts the output | `resolved` | Results; Table 6 | Median ρ: curvature 0.93, angular velocity 0.81, smoothness 0.73, path efficiency 0.63. Magnitude and rank are reported as distinct. |
| M42 | Sensitivity-family aggregation is not described | `resolved` | Methods perturbation paragraph | Table 6 reports the median of the 12 scenario-level medians, not a pooled median over runs. |
| M43 | Combined degradation is incompletely specified | `resolved` | Methods | 2× thinning + 10% dropout + jitter σ=0.004. |
| M44 | Two ranked metrics are effectively redundant | `resolved` | Methods; Table 6 (8 metrics) | Downswing peak speed excluded as a duplicate of maximum speed. |

## Master review — Low

| Finding ID | Issue | Status | Where fixed | Notes |
|---|---|---|---|---|
| M45 | Address is annotated and counted but not analyzed | `resolved` | Table 2 role “Time-origin diagnostic” | — |
| M46 | Internal labels reduce publication quality | `resolved` | Table 1 reader-facing labels | Raw codes remain only in supplementary subgroup CSVs. |
| M47 | Submission metadata is inconsistently complete | `owner_blocked` | Citation placeholders retained | Volume, issue, pages, DOI and year are editorial. |
| M48 | Reliability-oriented filenames and labels are misleading | `partially_resolved` | Article figure map contains no ICC-named asset | `v3/baseline/repeatability_repeatability.csv` and `fig_repeatability_cv.png` still exist unused. Rename or drop from any submission package. |

---

## Findings file — Critical (F01–F03)

| Finding ID | Issue | Status | Where fixed | Notes |
|---|---|---|---|---|
| F01 | Smoothness “robust in all twelve scenarios” | `resolved` | Table 6 7/5/0; Abstract; Results | Same as M15. Current CSV: 7 low / 5 moderate / 0 high. |
| F02 | Ablation claims monotone jerk reduction | `resolved` | Table 7; Results | Same as M20. Full-pipeline jerk 11835 > Kalman+RTS 181. |
| F03 | Two author photo cells are placeholders | `owner_blocked` | Builder clears placeholder text in place; photos not invented | Ivan and Maksym photos remain (page 17). Oleksii M. Maksymov and Karthik Iyer still have empty photo cells. |

## Findings file — Major (F04–F09)

| Finding ID | Issue | Status | Where fixed | Notes |
|---|---|---|---|---|
| F04 | Article 1 discussed but not cited | `partially_resolved` | [32] in text and bibliography | Needs the real venue/DOI (Phase 12 item 7). |
| F05 | Abstract says error degrades “only in the follow-through” | `resolved` | ABSTRACT; Table 5 | Abstract reports the session-level median, the 22/150 and 3/150 tails, and does not claim a clean backswing/downswing advantage. Downswing median 3.32% is the highest phase median; follow-through P95 is the worst tail. |
| F06 | “All remaining metrics above 25%” is false | `resolved` | Table 6 | Same as M26. |
| F07 | Methods analyze eleven metrics; tables show fewer | `resolved` | Methods; Table 6 (8 metrics) | Phase durations and downswing peak speed excluded with stated reasons. |
| F08 | Single annotator, one round | `resolved` | Table 3; Fig. 3; Methods rater design | Two annotators + Ivan intra-rater + disclosed mean consensus. Agreement is reported honestly (event median 4 frames; point median ~77 px). |
| F09 | No ethics/consent/IRB statement | `owner_blocked` | Methods ethics subsection; declarations | Same as M3. Warning present; approval not invented. |

## Findings file — Moderate (F10–F16)

| Finding ID | Issue | Status | Where fixed | Notes |
|---|---|---|---|---|
| F10 | Stratified subset remains DTL-dominated | `resolved` | Table 1; Results subgroups | 21 DTL / 3 face-on / 1 other stated; face-on flagged as three sessions. |
| F11 | Transition phase has too few control points | `resolved` | Table 5 (8 points, 8 sessions) | Same as M30. |
| F12 | Address annotated but never validated | `resolved` | Table 2 role column | Time-origin diagnostic; 3 of 4 events have automatic counterparts. |
| F13 | “Reliability” in the title overpromises | `resolved` | EN/UA titles and aim | “Reference-Based 2D Agreement and Perturbation Sensitivity… under Heterogeneous Recording Conditions.” |
| F14 | Weak topical fit of references [30] and [7] | `resolved` | Builder replacements | Same as M35. |
| F15 | Fig. 8 asset named `fig_icc_metric_ranking.png` | `resolved` | Builder figure map (Figs 1–7 only) | No ICC-named asset is embedded. See M48 for leftover baseline files. |
| F16 | Kalman+RTS and Kalman+RTS+despike rows identical | `resolved` | Table 7; Results | Despiking reported as non-activating (0 points). |

## Findings file — Minor (F17–F20)

| Finding ID | Issue | Status | Where fixed | Notes |
|---|---|---|---|---|
| F17 | English title omits the Ukrainian clause | `resolved` | TITLE and Ukrainian title | Both now include the workflow / heterogeneous-conditions clause. |
| F18 | All body paragraphs use Normal style | `partially_resolved` | Builder `add_section_heading` / `add_subheading` | Bold/centred runs on Normal, inherited from the format-accepted template. |
| F19 | AI tool name and access date need verification | `owner_blocked` | Acknowledgements AI-use sentence | Currently “GPT-5.6 Sol in Cursor on 28 July 2026”. Author must confirm tool and date. |
| F20 | `manuscript.md` and the DOCX diverge | `resolved` | `build_second_article_docx.py::_parse_manuscript` | Markdown is the single content source for this rebuild. |

## Findings file — Anticipated reviewer questions (F21–F24)

| Finding ID | Issue | Status | Where fixed | Notes |
|---|---|---|---|---|
| F21 | Why trust metre-scale error when scale comes from the system under test? | `resolved` | Methods; Discussion | cm is secondary and model-dependent; circularity is stated. |
| F22 | Is the ~1.7–2 s early bias a bug, a definition mismatch, or performance? | `partially_resolved` | Time-base audit; Table 4; Discussion | Grid mismatch excluded (≤67 ms vs 780–940 ms). Inter-rater event noise is 4 frames vs 38–40 automatic. Source-video trimming still cannot be audited without original files. |
| F23 | Are the 71-session and 25-session scopes clearly separated? | `resolved` | Methods; Results; Fig. 1 | Sensitivity and ablation: all 71. Event, trajectory, and annotation agreement: 25-session annotated subset. |
| F24 | Can metric recommendations stand when event timing fails? | `resolved` | Discussion; Conclusions | Timing-dependent cues are withheld; no application tolerance is claimed; metrics are “candidate only”. |

---

## Owner-blocked items still required before HAIT submission

1. ~~Ethics approval, consent, waiver, or documented exemption (M3, F09).~~ **Addressed in v4** (anonymized public demonstration footage; no IRB required — author statement).
2. Participant and acquisition metadata if recoverable (M27) — still absent; honestly reported in manuscript.
3. Independent club-length calibration if centimetre claims are to be primary (M9) — optional; % diagonal remains primary.
4. Article 1 venue/DOI for reference [32] (M34, F04) — pending Article 1 publication.
5. Photos for Oleksii M. Maksymov and Karthik Iyer (F03).
6. ~~Confirmed AI-tool name and date (F19)~~ **Addressed in v4**; editorial citation metadata (M47) still editorial placeholders.

## Verification notes

- Audit: `python audit_rater_independence.py` exit 0.
- v2 SHA-256 unchanged: `5F5B0CC919E9B8596FA6F9E6B3BDB440DA5ABC9C0F86996514779732D954EA33`.
- v4 DOCX: same layout as v3; ethics + AI disclosure updated; default builder output.
- PDF: 17 pages at `second_article_outputs/v3/article2_v4_preview.pdf`.
