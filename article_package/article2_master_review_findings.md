# Article 2 — Master Reviewer Findings

**Manuscript:** `article_package/Стаття_Аспірант_Синюк_HAIT_article2_v1.docx`  
**Cross-checked against:** `second_article_outputs/` CSVs  
**Status:** findings only — no edits applied  
**Canvas source (same workspace):** `.cursor` project canvases / `article2-master-review.canvas.tsx`

## Overall verdict

Scientifically honest core (negative event-timing finding + cautious metric ranking) is strong, but three submission blockers stand out: one false “robust in all 12” claim, a non-monotone jerk narrative vs Table 6, and missing author photos for two co-authors.

**Counts:** Critical 3 · Major 6 · Moderate 7 · Minor 4 · Question 4

**Severity key**
- **Critical** — likely reject / major-revision trigger or factual error
- **Major** — strong reviewer objection
- **Moderate** — expected questions / weaknesses
- **Minor** — editorial polish
- **Question** — anticipated peer-review probes

---

## Critical

### F01 — Factual / Results
**Issue:** Smoothness index is claimed to be “robust in all twelve perturbation scenarios,” but the sensitivity CSV classifies it as robust in only 6/12 and usable in 6/12 (frame thinning, dropout 10–20%, jitter 0.008, combined).  
**Evidence:** Table 7 source already encodes 6/6/0; body text contradicts both the CSV and the paper’s own &lt;10% / &lt;25% thresholds.

### F02 — Factual / Ablation
**Issue:** Ablation text claims an “expected monotone reduction of jerk along the filtering chain,” but the full pipeline RMS jerk (~11871) is higher than Kalman+RTS / Kalman+RTS+despike (~4637).  
**Evidence:** Table 6 numbers are correct; the narrative overclaims monotonicity. A reviewer will spot this immediately.

### F03 — Formatting / Authors
**Issue:** About the Authors: Oleksii M. Maksymov and Karthik Iyer photo cells are literal placeholders “[3×4 cm color photo]” with no embedded images (Ivan and Maksym photos are present).  
**Evidence:** DOCX last table rows 2–3: 0 drawings / 0 blips.

---

## Major

### F04 — Scientific framing
**Issue:** Companion methodological study (Article 1) is discussed as prior work but is not listed/cited as a bibliographic reference. Reviewers will ask how to locate the workflow being validated.  
**Evidence:** Introduction / Methods refer only to “companion methodological study.”

### F05 — Overclaim / Abstract
**Issue:** Abstract says trajectory error degrades “only in the follow-through,” but impact-region median (~19 px / 4.5 cm) is also worse than backswing/downswing, and downswing P95 is extreme (~1589 px).  
**Evidence:** Table 4; `trajectory_reference_summary.csv`.

### F06 — Factual / Ranking text
**Issue:** Results claim all remaining metrics have median changes “above 25%,” but maximum angular velocity’s overall median |change| is 24.5% (borderline usable by the stated rule, yet labeled exploratory).  
**Evidence:** `table7_robustness_ranking.csv` vs Results paragraph on Table 7.

### F07 — Methods–Results consistency
**Issue:** Methods analyze eleven exported metrics (including phase durations), and Results mention phase-duration metrics as exploratory, but Table 5/7 and Fig. 8 omit phase-duration metrics.  
**Evidence:** `reliability_statistics.csv` has backswing/downswing_duration; tables do not.

### F08 — Reference validity
**Issue:** Single annotator, one round: no inter-annotator reliability. For a validation paper this is a core weakness reviewers will treat as limiting the strength of “accuracy” claims.  
**Evidence:** Acknowledged in Limitations, but still a primary review risk.

### F09 — Ethics / Data
**Issue:** No ethics/consent/IRB (or explicit exemption) statement for videos of people, despite privacy being cited as reason for a schematic Fig. 2.  
**Evidence:** Declarations cover conflict, funding, AI use — not human-subjects ethics.

---

## Moderate

### F10 — Sampling balance
**Issue:** “Stratified” subset remains heavily DTL-dominated (21 DTL vs 3 face-on vs 1 other). Face-on generalizability is weakly supported.  
**Evidence:** Table 1 annotated subset.

### F11 — Sample size / Phases
**Issue:** Transition phase has only n=5 control points; phase-specific medians there are statistically fragile.  
**Evidence:** Table 4.

### F12 — Ground-truth definition
**Issue:** Manual clicks are treated as reference, but address is annotated and never validated; automatic vs manual comparison covers only 3/4 events. Reviewers may ask why address was collected.  
**Evidence:** Table 2 vs Table 3.

### F13 — Reliability wording
**Issue:** “Reliability” in title/aim is mostly cross-session CV/RC on a heterogeneous corpus, explicitly not test–retest. Title may overpromise reliability in the biomechanics sense.  
**Evidence:** Methods reliability paragraph + Limitations.

### F14 — Citation quality
**Issue:** [30] (Sweeting et al., sprint activity profiles) is used to support rank-stability of golf metrics — weak topical fit. [7] (Challis rigid-body transform) is a stretch for differentiation-noise claims.  
**Evidence:** Sensitivity paragraph cites [30]; Intro cites [7] with [6].

### F15 — Figure metadata
**Issue:** Fig. 8 asset is named `fig_icc_metric_ranking.png` while caption/text say CV ranking and ICC was not computed (no athlete grouping).  
**Evidence:** `build_second_article_docx.py` figure map; `compute_reliability_statistics.py`.

### F16 — Ablation interpretation
**Issue:** Kalman+RTS and Kalman+RTS+despike rows are numerically identical for reported columns (except max accel in CSV). Reviewers will ask whether despiking ever fired or whether the table is redundant.  
**Evidence:** Table 6 / `ablation_summary.csv`.

---

## Minor

### F17 — Title consistency
**Issue:** English title omits “workflow” / heterogeneous-conditions clause present in the Ukrainian title and in the manuscript.md working title.  
**Evidence:** DOCX EN title vs UA title; `second_article_manuscript.md`.

### F18 — HAIT formatting
**Issue:** All body paragraphs use Normal style (no Heading styles). May be template-driven, but editors sometimes flag section-heading structure.  
**Evidence:** python-docx style census: Normal only.

### F19 — AI disclosure
**Issue:** AI tool named “GPT-5.5” with access date 3 May 2026 — verify exact tool name/date for honesty of disclosure.  
**Evidence:** Declarations block.

### F20 — Source sync
**Issue:** Master markdown still has a longer Methods RC formula and a citation title with “workflow”; DOCX diverges slightly from `manuscript.md`.  
**Evidence:** `second_article_manuscript.md` vs DOCX extract.

---

## Questions reviewers are likely to ask

### F21
Why is metre-scale error trusted when scale itself comes from the same markerless stick-length estimate being evaluated?  
**Evidence:** Methods scale calibration + Limitations stick-length assumption.

### F22
Is ~1.7–2 s early bias a detector bug (units/offset), a definition mismatch, or true performance? Magnitude ≫ swing duration invites “implementation error?” scrutiny.  
**Evidence:** Table 3; Discussion already flags recalibration need.

### F23
Were sensitivity/ablation run on all 71 sessions while accuracy used 25 annotated ones — is mixing scopes clearly enough separated in every claim?  
**Evidence:** Methods sensitivity vs event/trajectory sections.

### F24
Can smoothness/path-efficiency recommendations for VR coaching stand when event timing (needed for phase cues) fails this badly?  
**Evidence:** Discussion VR guidance vs event negative finding.

---

## Suggested fix priority (if revising later)

1. Correct smoothness “all twelve” wording to match 6 robust / 6 usable.
2. Soften ablation “monotone jerk” claim; explain full-pipeline jerk rebound.
3. Restore Oleksii / Karthik author photos (or remove placeholder text).
4. Then: cite Article 1 formally, tighten abstract trajectory wording, align Tables 5/7 with the “eleven metrics” story, add ethics/consent note.
