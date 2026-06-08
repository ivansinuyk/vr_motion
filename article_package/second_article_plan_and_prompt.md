# Second Article Plan and Agent Prompt

## Working Title

Robustness and Validation of a Markerless Video-Based Golf Swing Motion-Analysis Workflow Under Heterogeneous Recording Conditions

Alternative titles:

- Validation and Sensitivity Analysis of Markerless Golf-Stick Motion Tracking for Sport-Biomechanics Applications
- Robustness of Kalman- and RTS-Smoothed Markerless Golf Swing Metrics Under Frame-Rate, Landmark, and Scale Perturbations
- Accuracy, Repeatability, and Robustness of Video-Based Golf-Stick Kinematic Indicators for VR Training Analytics

## Purpose of This Document

This Markdown file is a future-use planning brief and prompt for writing a second research article related to the existing VR/golf motion-analysis project.

It does not implement code and does not generate the article now. It records:

- what was already done in the first article;
- what the second article should focus on;
- what data, scripts, CSV files, graphs, and validation outputs should be implemented later;
- what HAIT-style formatting requirements should be remembered;
- a ready-to-send prompt for another AI agent when the author is ready to work on the second article.

## Step 0 Pre-Analysis Findings (verified against the live dataset)

This section was added after inspecting the actual project state, not just the assumptions in this brief. It is the authoritative status as of the pre-analysis pass.

### What already exists and is reusable

- 71 valid sessions are present and all 71 process successfully (`dataset_summary.csv`, `processed = True` for every row). The dataset root is `C:\Users\isinu\Downloads\Telegram Desktop\7a0c087a-b6c7-42ea-bc67-63453d4cac7f\`.
- Each session folder is far richer than this brief assumed. Per session it contains: `mediapipe_data_full.json`, `video_processed.mp4`, `mocap_data.json`, `resource_data.json`, `template.json`, `P1.jpg`-`P10.jpg` (extracted swing-position frames), `dtw_results.json`, and `predictions_mocap/`, `debug_keyframes/`, `dtw_debug/` subfolders.
- `mocap_data.json` already holds a P-system keyframe list with times: Address (P1), Takeaway (P2), Backswing Halfway (P3), Top of Backswing (P4), Downswing/Transition (P5), P6, Impact (P7), plus chart/angle definitions.
- The first-article evaluation engine is fully reusable. `batch_article_evaluation.py` already implements session processing, the synthetic-keyframe reference comparison, sensitivity scenarios (frame thinning 2x, 10 % landmark dropout, +5 % scale), the four-variant ablation (median / Kalman / Kalman+RTS / full pipeline), repeatability CV, and trajectory deviation. The second-article scripts should extend these functions, not rewrite them.
- Existing CSVs/figures in `article_package/evaluation_outputs/` are present (dataset_summary, validation_keyframe_errors, sensitivity_results, ablation_results, repeatability, trajectory_deviation_summary, plus figures).

### The critical gap (this is the scientific opening for article 2)

- The existing `mocap_data.json` keyframes are NOT trustworthy ground truth. `metaData.autoMetaTags` flags most positions as `synthetic-p2 ... synthetic-p7` (auto-generated/interpolated), and the large majority of sessions carry a `Keyframes Issue` tag in `resource_data.json`.
- Reference event times are sparse: of 71 sessions only 20 have any usable reference event time, and only 8 have a usable top-of-backswing reference (213 validation rows total, 48 with a reference time). So even the weak auto-reference covers <30 % of the dataset.
- `dtw_results.json` is frequently empty (`cost: null`, empty `path`), so DTW alignment to the template is not a usable reference signal as-is.
- There is NO trajectory-level (pixel point) reference anywhere. Nothing in the dataset gives a per-frame stick-tip ground-truth coordinate. Objective 3 (geometric trajectory error) cannot be done without new manual point annotation.

### Practical consequence

- Manual annotation remains the single most important missing piece, exactly as this brief states - but the framing should change. The P1-P10 JPGs and synthetic keyframes are excellent annotation *aids* (frames are pre-extracted at the key positions), and the unreliability of the synthetic keyframes is itself a publishable motivation: "the system's automatic keyframes are unreliable, so we built a manual reference and quantified the error".
- `second_article_outputs/` does not exist yet, and none of the six planned article-2 scripts exist yet. Author photos are not loose files in `article_package/`; they live embedded inside the v4 DOCX and must be reused from there.

## Background: What the First Article Covered

The first article was prepared as a HAIT-aligned manuscript and accepted format-wise by the editors:

- Final HAIT-formatted DOCX: `article_package/Стаття_Аспірант_Синюк_HAIT_aligned_final_v4.docx` (13 pages, 9 embedded figures preserved, 30 IEEE-style references, English + Ukrainian metadata, "About the Authors" table with photo cells).
- Earlier figures-only baseline (kept for archival reference): `article_package/Стаття_Аспірант_Синюк_HAIT_aligned_final_with_figures_wordsafe_v3.docx`.
- Reusable HAIT formatter script: `article_package/fix_hait_formatting.py` (rebuilds metadata, references, Ukrainian block, author-info table, headers/footers; preserves embedded images in table cells).

The first article focused mainly on the method and workflow:

- markerless video-based golf-stick motion analysis;
- body and golf-stick landmark extraction;
- conversion of normalized landmarks into pixel coordinates;
- median pre-filtering;
- confidence-aware Kalman filtering;
- Rauch-Tung-Striebel backward smoothing;
- trajectory despiking;
- bounded polynomial smoothing;
- dynamic scale calibration;
- extraction of kinematic and biomechanical metrics;
- raw, filtered, and smoothed trajectory comparison;
- session-level repeatability;
- diagnostic validation, sensitivity, and ablation results.

The first article intentionally framed some results cautiously because the validation and ablation outputs were diagnostic, not yet a controlled accuracy study. This creates a strong opportunity for a second article focused specifically on validation, robustness, and metric reliability.

## Recommended Focus for the Second Article

The strongest and least repetitive second article would be:

**Validation and robustness analysis of the markerless golf-stick motion-analysis workflow.**

The first article answers:

> How is the markerless motion-analysis workflow designed and what metrics does it produce?

The second article should answer:

> How accurate, robust, and reliable are the generated swing events, trajectories, and metrics under reference annotation and controlled perturbations?

This makes the second article complementary, not redundant. It also supports a future dissertation structure:

- Article 1: system and methodological pipeline.
- Article 2: validation, robustness, and reliability evidence.
- Dissertation: integrated method development, experimental validation, and sport/VR application.

## Possible Research Aim

The aim of the second study is to evaluate the accuracy, robustness, and reliability of a markerless video-based golf-stick motion-analysis workflow under heterogeneous recording conditions and controlled input perturbations.

## Possible Research Objectives

1. To construct a manually annotated reference subset for key swing events and selected stick-tip trajectory control points.
2. To quantify event-detection accuracy for impact, top of backswing, and downswing transition.
3. To estimate geometric trajectory error between automatically processed stick-tip positions and manually annotated reference points.
4. To evaluate the sensitivity of exported metrics to frame thinning, simulated landmark dropout, scale perturbation, and combined degradation.
5. To compare processing variants through an ablation study: raw landmarks, median-only filtering, Kalman filtering, Kalman plus RTS smoothing, and the full pipeline.
6. To identify which kinematic and movement-quality metrics are robust enough for cross-session comparison.
7. To formulate practical recommendations for using markerless golf-swing metrics in VR training and sport-biomechanics applications.

## Possible Hypotheses

H1. Global movement-quality metrics such as smoothness index and path efficiency are more robust under heterogeneous capture conditions than peak derivative metrics such as maximum acceleration and maximum angular velocity.

H2. Confidence-aware Kalman filtering followed by RTS smoothing reduces trajectory jitter while preserving the main swing path better than median-only filtering or Kalman filtering without backward smoothing.

H3. Event timing accuracy is more sensitive to phase-boundary definition and frame rate than global trajectory-shape metrics.

H4. Scale perturbation has a predictable effect on metric magnitude, while landmark dropout and frame thinning produce larger changes in derivative-based metrics.

## Data Already Available in the Project

Known project context from the first article work:

- There are 71 processed golf-stick swing sessions.
- Existing metadata include frame count, frame rate, resolution, viewpoint, stroke type, and video-quality tags.
- Existing generated outputs are stored under:
  - `article_package/evaluation_outputs/`
  - `article_package/evaluation_outputs/figures/`
- Existing or previously generated files include:
  - `dataset_summary.csv`
  - `validation_keyframe_errors.csv`
  - `sensitivity_results.csv`
  - `ablation_results.csv`
  - `repeatability_repeatability.csv`
  - `trajectory_deviation_summary.csv`
  - `batch_evaluation_summary.md`
  - `fig_repeatability_cv.png`
  - `fig_example_kinematics_trajectory.png`
  - `fig_validation_keyframe_errors.png`
  - `fig_sensitivity_results.png`
  - `fig_ablation_results.png`
- Existing analysis scripts include:
  - `batch_article_evaluation.py`
  - `evaluate_filters.py`
  - `parameter_sweep.py`
  - `swing_analyzer.py`
  - `analysis.py`
  - `kalman.py`
  - `rts_smoother.py`
  - `utils_filter.py`
  - `drawing.py`

The second article should not simply reuse these outputs unchanged. It should improve them into a controlled validation and robustness study.

## New Data or Annotation Needed

The most important missing piece is a stronger reference subset. Note (confirmed in Step 0): a weak auto-reference already exists in `mocap_data.json` (synthetic P1-P7 keyframe times, only ~20/71 sessions usable) and there is no trajectory-point reference at all. The manual annotation below replaces/augments the synthetic keyframes and is the genuine new data the article depends on.

Recommended manual annotations:

- impact frame/time;
- top of backswing frame/time;
- downswing transition frame/time;
- optional address/start frame;
- 5-10 stick-tip control points per selected swing;
- optional stick-base or stick-midpoint reference points;
- optional ball position at impact;
- optional quality tags: occlusion, blur, camera viewpoint, slow-motion, super-slow-motion.

Recommended annotation format:

`reference_annotations.csv`

Suggested columns:

- `session_id`
- `video_path` or `source_id`
- `fps`
- `frame_width`
- `frame_height`
- `event_name`
- `reference_frame`
- `reference_time_s`
- `point_name`
- `x_px`
- `y_px`
- `annotator_id`
- `annotation_round`
- `quality_note`

If two annotators are available, add inter-annotator reliability:

- mean absolute disagreement in frames/ms;
- mean point distance in pixels;
- ICC or agreement statistics where applicable.

## Scripts to Implement Later

Do not implement now. These are recommended future scripts.

### 1. `prepare_reference_subset.py`

Purpose:

- select representative sessions for manual annotation;
- balance by viewpoint, frame rate, resolution, stroke type, and quality tags;
- export a list of videos/sessions for annotation.

Outputs:

- `second_article_outputs/reference_subset.csv`
- `second_article_outputs/reference_subset_summary.csv`

Recommended selection:

- 20-30 sessions minimum for event validation;
- 10-15 sessions with point-level annotations;
- include good, medium, and difficult recordings.

### 2. `validate_events_against_reference.py`

Purpose:

- compare automatic event detections with manual reference events;
- compute signed and absolute timing errors.

Outputs:

- `second_article_outputs/event_validation_errors.csv`
- `second_article_outputs/event_validation_summary.csv`
- `second_article_outputs/figures/fig_event_error_by_event.png`
- `second_article_outputs/figures/fig_event_error_bland_altman.png`

Metrics:

- signed error in frames;
- absolute error in frames;
- signed error in milliseconds;
- absolute error in milliseconds;
- median absolute error;
- 95th percentile absolute error;
- detection failure rate;
- Bland-Altman mean bias and limits of agreement.

### 3. `validate_trajectory_against_reference.py`

Purpose:

- compare processed stick-tip trajectories with manually annotated reference points;
- evaluate geometric error.

Outputs:

- `second_article_outputs/trajectory_reference_errors.csv`
- `second_article_outputs/trajectory_reference_summary.csv`
- `second_article_outputs/figures/fig_trajectory_error_distribution.png`
- `second_article_outputs/figures/fig_trajectory_error_by_phase.png`

Metrics:

- Euclidean error in pixels;
- Euclidean error in normalized coordinates;
- Euclidean error in metres if scale is reliable;
- phase-specific error: backswing, downswing, impact region;
- error by viewpoint and quality tag.

### 4. `run_sensitivity_study.py`

Purpose:

- run controlled perturbations on the same sessions;
- measure metric stability.

Perturbations:

- frame thinning: every 2nd frame, every 3rd frame;
- simulated landmark dropout: 5%, 10%, 20%;
- coordinate jitter: small Gaussian noise added to landmarks;
- scale perturbation: +/- 5%, +/- 10%;
- combined degradation: frame thinning + dropout + jitter;
- optional viewpoint subgroup analysis.

Outputs:

- `second_article_outputs/sensitivity_results.csv`
- `second_article_outputs/sensitivity_summary.csv`
- `second_article_outputs/figures/fig_sensitivity_metric_heatmap.png`
- `second_article_outputs/figures/fig_sensitivity_by_perturbation.png`

Metrics:

- absolute change;
- percentage change;
- median absolute percentage change;
- rank stability;
- classification stability for robust vs exploratory metrics.

### 5. `run_ablation_study.py`

Purpose:

- compare processing variants on the same sessions and same metric definitions;
- avoid the inconsistency seen in the first diagnostic ablation table.

Variants:

- raw landmarks;
- median-only;
- Kalman only;
- Kalman + RTS;
- Kalman + RTS + despiking;
- full pipeline with polynomial smoothing and scale bounding.

Important requirement:

- compute all derivative metrics from the final trajectory of each variant using the same derivative function and the same time base.

Outputs:

- `second_article_outputs/ablation_results.csv`
- `second_article_outputs/ablation_summary.csv`
- `second_article_outputs/figures/fig_ablation_trajectory_deviation.png`
- `second_article_outputs/figures/fig_ablation_jerk_reduction.png`
- `second_article_outputs/figures/fig_ablation_metric_stability.png`

Metrics:

- trajectory deviation from reference or from selected baseline;
- RMS jerk;
- smoothness index;
- path efficiency;
- event timing stability;
- processing success rate;
- missing-data bridging performance.

### 6. `compute_reliability_statistics.py`

Purpose:

- compute stronger reliability statistics if repeated trials or repeated annotations are available.

Outputs:

- `second_article_outputs/reliability_statistics.csv`
- `second_article_outputs/figures/fig_bland_altman_selected_metrics.png`
- `second_article_outputs/figures/fig_icc_metric_ranking.png`

Metrics:

- coefficient of variation;
- repeatability coefficient;
- intraclass correlation coefficient if grouping exists;
- Bland-Altman limits of agreement;
- standard error of measurement;
- minimal detectable change.

## Main Figures for the Second Article

Suggested figures:

1. Study design and validation workflow.
2. Example manually annotated frame with reference stick-tip points.
3. Event timing error by swing event.
4. Trajectory point error distribution.
5. Sensitivity heatmap by metric and perturbation.
6. Ablation comparison of processing variants.
7. Bland-Altman or agreement plot for selected robust metrics.

Fig. 2 should use a permitted/anonymized video frame, not a real user frame without consent.

## Main Tables for the Second Article

Suggested tables:

1. Dataset and reference subset characteristics.
2. Manual annotation protocol.
3. Event timing validation results.
4. Trajectory reference error results.
5. Sensitivity analysis summary.
6. Ablation comparison.
7. Robustness ranking of metrics.
8. Limitations and recommended metric-use categories.

## Recommended Metric Categories

The second article should classify metrics into practical categories.

Potential robust metrics:

- smoothness index;
- path efficiency;
- normalized trajectory deviation;
- possibly tempo if phase detection is improved.

Potential exploratory metrics:

- maximum acceleration;
- maximum angular velocity;
- curvature RMS;
- backswing peak speed;
- phase durations if event detection remains unstable.

Potential reporting categories:

- robust under heterogeneous capture;
- usable with controlled acquisition;
- exploratory only;
- not recommended without external validation.

## Scientific Cautions

The second article must avoid overclaiming.

Do not claim:

- laboratory-grade accuracy unless compared with a trusted reference;
- dense 3D biomechanical validity from monocular 2D video;
- robust event detection if timing errors remain in seconds;
- repeatability across athletes if athlete/trial grouping is not known.

It is acceptable and scientifically strong to report negative findings:

- event detection requires recalibration;
- derivative metrics are unstable under heterogeneous video;
- some metrics are robust while others should remain exploratory.

## HAIT Formatting Requirements (verified against first article)

Official HAIT requirements page:

`https://hait.od.ua/index.php/journal/requirements`

The list below is the recipe that was applied, reviewed, and accepted format-wise for the first article. Reuse the same recipe (and the same `fix_hait_formatting.py` script as a starting point) for the second article.

### Page setup

- File format: Microsoft Word DOCX, English only.
- Page size: A4 (210 x 297 mm), portrait.
- Margins: top, left, right = 2 cm; bottom = 2.5 cm.
- Font: Times New Roman, 11 pt (default `Normal` style).
- Line spacing: single.
- Body alignment: justified.
- Paragraph indent: 0.75 cm (first-line).
- Automatic hyphenation enabled.
- Page numbering: NOT added by the author.
- Different odd/even headers and footers enabled.
- Length: 12 to 14 full pages; the last page must be at least 75 % filled.

### Column layout

- Single-column: DOI, UDC, title, author list, affiliations, abstract, keywords, citation text, "REFERENCES" and reference entries, post-references statements, Ukrainian metadata, "ABOUT THE AUTHORS" table.
- Double-column: the main article body from INTRODUCTION through CONCLUSIONS / ACKNOWLEDGMENTS (column width 8.25 cm, gap 0.5 cm). Use a section break on the current page when switching column count.

### Headers and footers (editorial-style, but pre-filled by the author)

- Header line 1 (10 pt, left aligned): authors' surnames + initials, then journal title ("Herald of Advanced Information Technology").
- Header line 2: year and issue number, underlined with a 1.5 pt solid line; ~15 pt spacing below.
- Footer: 1-row, 3-column borderless table (only the top border visible, 1 pt), first cell contains `ISSN 2617-4316 (Print)` and `ISSN 2663-7723 (Online)` in 10 pt, left aligned, 3 pt before each line.
- Configure separate odd/even headers and footers (HAIT requires distinct ones for odd/even pages even if the content is identical).

### Article structure

The manuscript must contain (titles may be adapted but the function must remain clear):

1. INTRODUCTION
2. LITERATURE REVIEW AND PROBLEM STATEMENT
3. RESEARCH AIM AND OBJECTIVES
4. MATERIALS AND METHODS (may be renamed to reflect both experimental and methodological components)
5. RESEARCH RESULTS (may be renamed to match the topic)
6. DISCUSSION OF RESULTS
7. CONCLUSIONS
8. ACKNOWLEDGMENTS (if applicable)
9. REFERENCES
10. Ukrainian-language duplicate of core metadata
11. ABOUT THE AUTHORS

### Title block, authors, affiliations

- DOI line: 11 pt, bold, left aligned, no indent, first line of the first page (assigned by editorial office).
- UDC line: 11 pt, bold, left aligned, no indent, second line.
- Title: 16 pt, bold, title case, centered, with one blank line above and below.
- Author list (English): each author on two lines:
  - Line 1: First name + middle initial + last name (11 pt, bold) with superscript affiliation number, e.g. `Anatoly A. Ivanov^1`.
  - Line 2: ORCID URL; email; `Scopus Author ID:` (if applicable). 9 pt, regular.
- Affiliations: each on its own line below the authors, right aligned, with superscript matching the authors; format `Institution, address, city, country`.

### Abstract

- Heading `ABSTRACT` in 12 pt, bold, centered, followed by one blank line.
- Body: 9 pt, regular, justified, first-line indent 0.75 cm.
- 300-350 words, minimum 2000 characters with spaces.
- No numbers, abbreviations, formulas, tables, or references inside the abstract.
- Structure: relevance -> aim/objectives -> methods -> results -> conclusions (novelty + practical value).
- Do not repeat the title or copy text from the body.

### Keywords

- Same line block immediately after the abstract.
- Begin with `Keywords:` (9 pt, bold, first-line indent 0.75 cm, justified).
- Then up to 6 terms in nominative case, max two words per term, separated by `;`, no period at the end, no abbreviations, no generic single-word terms.

### Citation text

- Appears one blank line after the keywords.
- Font 8 pt, bold, justified, no first-line indent.
- Begin with italic `For citation:` followed by the full citation string. The final wording is supplied by the editorial board after acceptance, but include a plausible placeholder.

### Copyright footer on first page

- Anchored at the bottom of the left (single) column of page 1.
- One-line horizontal border (1 pt, paragraph border style) above the text.
- Below the line: `©` (10 pt, bold), then authors' surnames + initials, then publication year, comma separated (10 pt, regular).

### Body text

- Section headings (`INTRODUCTION`, etc.): 11 pt, bold, ALL CAPS, centered, 6 pt before, 6 pt after.
- Subsection headings: 11 pt, bold italic; the first article used justified subsection headings with the 0.75 cm body indent so they look like the sample paragraph leaders.
- Body paragraphs: 11 pt, justified, first-line indent 0.75 cm, single spacing, two columns.

### Punctuation and number conventions

- No period after the article title, section headings, table titles, or units of measurement.
- Use the `-th` notation for ordinal indices in variables (e.g. `i-th`).
- For abbreviations of multi-word phrases, separate components with spaces, not hyphens.
- All units must comply with SI.
- Numbers below 11 spelled out, unless used with a unit, inside a math expression, or combined with larger numerals in the same sentence.
- Decimals use a period as the separator and always have a leading zero (e.g. `0.35`, not `.35`).
- Avoid starting sentences with a numeral.
- Use ellipsis (`...`) inside math expressions to indicate continuation.

### Lists

- Each list must have at least two elements.
- Numbered lists use either `1.` or `(1)`; unnumbered lists use a hyphen `-`.

### Formulas

- Use MathType or another full equation editor; formulas must be editable (no images).
- Centered within the column, no paragraph indent. Numbered only when referenced, with the number right-aligned in parentheses (e.g. `(1)`).
- Recommended sizes: main symbols 11 pt; superscripts 8 pt; subscripts 6 pt; large symbols 14 pt; small symbols 10 pt.
- Latin variable names: italic. Greek symbols: not italic. Operators / standard functions (`min`, `max`, `sin`, `cos`, `tg`, `ctg`, ...): not italic. Cyrillic characters are not allowed in formulas.
- Formulas are part of the sentence and end with the appropriate punctuation.
- Simple inline math may use plain Word characters if it still renders cleanly.

### Figures

- Centered in the column, no paragraph indent. Inline if the figure fits a column; otherwise top/bottom of the page as a full-width single-column block.
- Caption: 11 pt, centered, no indent. Format: `Fig.` (italic regular) + number + period + title starting with a capital letter (bold). Example: `Fig. 2. Results of system modeling`.
- Source line on the next line: 8 pt, italic, bold, centered. Format: `Source:` + URL, or `compiled by the authors`, or a bracketed citation.
- Every figure must be cited; in-text use a space after `Fig.` (`Fig. 3`) but no space for compound references (`Fig. 3c`).
- Image format JPG (or equivalent high-resolution raster), no pixelation when enlarged; color is allowed.
- Maximum width: 17 cm (full page) or 8 cm (column width).
- Labels inside images: Times New Roman 11 pt, no bold or italic. Part labels (a, b, c, ...) must be editable text in the caption, not baked into the image.

### Tables

- Centered, no indent. Inline if it fits the column width; otherwise top/bottom of the page as full-width single-column block.
- Title above the table: 11 pt, centered, no indent. Format: `Table` (italic) + number + period + capitalized title (bold). Example: `Table 3. Summary of experimental results`.
- Source line below the table: 8 pt, italic, bold, centered.
- Built with MS Word table tools.
- Cell text 11 pt Times New Roman, consistent across all tables.
- Units in column headers (do not repeat in rows). No empty header cells. Vertical orientation only. If a table spans multiple pages, do not repeat the caption.
- Single-level sequential numbering shared with figures and formulas.

### In-text citations

- IEEE numbered style, square brackets, e.g. `[1]`, `[2]`.
- Sources numbered by order of first mention. Each cited source listed individually inside the same brackets: `[2], [4], [7]`. No ranges. Citations precede punctuation. Every reference in the list must appear in the text.

### Conclusions

- Aligned with the aim/objectives, concise, persuasive, highlight scientific novelty and practical relevance. Optionally include prospects for future research. Do not repeat earlier content verbatim.

### Reference list

- Heading: `REFERENCES`, 11 pt, bold, centered, no indent.
- Single column. Each entry: 11 pt, justified, 0.75 cm first-line indent, numbered (no brackets in the list itself).
- All entries in English. If the original is in another language, translate the title and append the language note (e.g. `(in Ukrainian)`).
- IEEE style: `Surname, A. B.` for authors, multiple authors comma separated and `&` before the last; journal / book / conference names italic; article titles in quotation marks (not italic); date / volume / pages as `2022; Vol. 10: 123-130` (no `pp.` / `p.`).
- For online resources add an access date: `(Accessed: Apr. 29, 2025)`.
- DOIs included when available, written as full URLs (`https://doi.org/...`).
- Scopus EID URL must be included when the source is indexed in Scopus, e.g. `https://www.scopus.com/pages/publications/<EID>`.
- Minimum 25 references, ideally 30+. At least 5-7 references with DOIs and indexed in Scopus. Prefer sources from the last 5 years. Self-citations <= 30 % of the list. Do not use GOST / DSTU / other local standards.

### Post-references statements

- `Conflicts of Interest:` statement (mandatory). If none, use the journal-recommended phrase.
- `Funding:` statement (mandatory; may be `no external funding`).
- Submission history dates: `Received`, `Received after revision`, `Accepted` (filled by the editorial office; include placeholders).

### Ukrainian metadata block (mandatory after REFERENCES)

- УДК, then 16 pt bold centered Ukrainian title.
- Authors with full patronymics (e.g. `Іванов Анатолій Андрійович`), not just initials.
- Right-aligned Ukrainian affiliations, shared superscripts per institution.
- `АНОТАЦІЯ` heading (12 pt bold centered), 9 pt justified body with 0.75 cm indent, same structured content as the English abstract.
- `Ключові слова:` block (9 pt bold prefix, 9 pt body, `;` separated).
- `Для цитування:` block, 8 pt italic/bold prefix, otherwise mirrors English citation line.

### About the Authors

- Heading `ABOUT THE AUTHORS` (11 pt bold centered) followed by a borderless two-column table.
- First column: color photo, 3 x 4 cm.
- Second column (8 pt):
  - first name + middle initial + last name (bold) + academic degree, title, position, affiliation, affiliation address;
  - ORCID URL + email (semicolon-separated) + `Scopus Author ID:` if applicable;
  - `Research field:` (bold italic) followed by regular text;
  - Ukrainian full name + degree + title + position + affiliation + address.

### Practical implementation notes (learned in v4)

- `fix_hait_formatting.py` already encodes all of the above. For the second article, copy the script and adjust the constants for title, authors, affiliations, abstract, keywords, citation line, copyright, Ukrainian metadata, author bios, and the references list.
- When the script touches the "About the Authors" table, modify it in place. Deleting and recreating the table loses photos because drawings live inside the table cells.
- When rebuilding references, exclude `In:`, edition markers (`2nd ed.`), and publisher locations from the italicized source name. Use a curated regex (the script already contains `NON_SOURCE_RE`).
- Keep a copy of the previous final DOCX as a backup before re-running the formatter, and verify by exporting to PDF and inspecting each page image.

## Suggested Article Structure

1. UDC, authors, affiliations, title, abstract, keywords, citation line.
2. INTRODUCTION
   - problem of validating markerless sport-motion systems;
   - limitations of monocular video;
   - need for robustness and uncertainty evaluation.
3. LITERATURE REVIEW AND PROBLEM STATEMENT
   - markerless pose estimation in sport;
   - golf swing analysis;
   - validation of motion-analysis systems;
   - filtering and derivative-noise problems.
4. RESEARCH AIM AND OBJECTIVES
5. MATERIALS AND METHODS
   - dataset and reference subset;
   - manual annotation protocol;
   - automatic processing workflow;
   - event validation;
   - trajectory validation;
   - sensitivity perturbations;
   - ablation variants;
   - statistical analysis.
6. RESEARCH RESULTS
   - dataset/reference subset;
   - event timing error;
   - trajectory error;
   - sensitivity analysis;
   - ablation analysis;
   - metric robustness ranking.
7. DISCUSSION OF RESULTS
   - which metrics are usable;
   - why derivatives are unstable;
   - implications for VR feedback;
   - limitations.
8. CONCLUSIONS
9. ACKNOWLEDGMENTS
10. REFERENCES
11. Ukrainian metadata.
12. Author information.

## Ready-to-Send Prompt for a Future Agent

```text
You are an expert academic researcher, scientific editor, and Python data-analysis assistant specializing in computer vision, sport biomechanics, markerless motion analysis, and Scopus-level manuscript preparation.

I need help preparing a second research article related to my existing project:

Project topic:
Markerless video-based golf-stick motion analysis for VR/sport-biomechanics applications.

First article already completed:
It focused on the full methodological pipeline: landmark extraction, median pre-filtering, confidence-aware Kalman filtering, RTS smoothing, trajectory despiking, polynomial smoothing, dynamic scale calibration, kinematic metric extraction, raw-vs-smoothed comparison, session-level repeatability, and diagnostic validation/sensitivity/ablation outputs.

The second article must not repeat the first one. It should focus on:
Validation, robustness, sensitivity analysis, ablation, and metric reliability of the markerless golf-stick motion-analysis workflow.

Target journal formatting style:
Herald of Advanced Information Technology (HAIT)
Official requirements:
https://hait.od.ua/index.php/journal/requirements

Important HAIT requirements (already proven for the first article - reuse the same recipe):
- DOCX manuscript, English only, 12-14 pages, last page at least 75 % filled.
- A4 portrait. Margins: top/left/right 2 cm; bottom 2.5 cm. Hyphenation on. No page numbers.
- Times New Roman 11 pt, single line spacing, justified body, 0.75 cm first-line indent.
- Single column for DOI/UDC/title/authors/affiliations/ABSTRACT/keywords/citation, REFERENCES, post-references, Ukrainian metadata, and ABOUT THE AUTHORS.
- Two columns for the main body (column width 8.25 cm, gap 0.5 cm) from INTRODUCTION through CONCLUSIONS / ACKNOWLEDGMENTS.
- Header line 1 (10 pt left): authors + journal title; header line 2: year and issue with 1.5 pt underline. Footer: 1-row 3-column borderless table with `ISSN 2617-4316 (Print)` and `ISSN 2663-7723 (Online)` 10 pt left. Distinct odd/even headers/footers.
- DOI 11 pt bold left, UDC 11 pt bold left, title 16 pt bold centered, author lines 11 pt bold + ORCID/email/Scopus 9 pt, right-aligned affiliations.
- `ABSTRACT` heading 12 pt bold centered, body 9 pt justified with 0.75 cm indent, 300-350 words, no numbers/abbreviations/refs.
- `Keywords:` 9 pt bold prefix, up to 6 nominative-case terms separated by `;`.
- `For citation:` line 8 pt bold, italic prefix.
- Copyright footer on page 1: 1 pt horizontal border + `(c)` 10 pt bold + authors + year.
- Section headings 11 pt bold ALL CAPS centered (6 pt before/after); subsection headings 11 pt bold italic.
- Figures: caption `Fig. N.` (italic regular) + title (bold), centered 11 pt; source line 8 pt bold italic centered.
- Tables: title `Table N.` (italic) + title (bold), centered 11 pt; cells 11 pt; source line 8 pt bold italic centered; no empty header cells.
- Formulas: editable Word/MathType equations only, centered, numbered only when referenced (right-aligned `(N)`), Latin italic, Greek/operators not italic, no Cyrillic.
- In-text citations: IEEE numbered, square brackets, individual numbers, before punctuation, no ranges.
- REFERENCES: heading 11 pt bold centered; entries 11 pt justified with 0.75 cm indent, numbered (no brackets in the list itself); IEEE format with italic journal/conference names, quoted article titles, `Vol. ... No. ...:` pagination, no `pp.`; DOIs as full URLs; Scopus URLs where available; access date for online sources; >=25 references (ideally 30+), >=5-7 with DOIs and Scopus-indexed, <=30 % self-citations, prefer last 5 years.
- Post-references: `Conflicts of Interest:` and `Funding:` statements, then `Received`/`Received after revision`/`Accepted` placeholders.
- Ukrainian metadata block after REFERENCES: УДК, 16 pt bold Ukrainian title, full patronymics, right-aligned Ukrainian affiliations, `АНОТАЦІЯ` 12 pt bold centered, 9 pt body, `Ключові слова:` block, `Для цитування:` block.
- ABOUT THE AUTHORS: borderless 2-column table with 3 x 4 cm color photo on the left; right column 8 pt with name (bold), degree/title/position/affiliation, ORCID/email/Scopus, `Research field:` (bold italic), and Ukrainian full-patronymic block.
- Reuse `article_package/fix_hait_formatting.py` as the formatter: clone it, swap the constants (title, authors, abstract, keywords, citation, copyright, Ukrainian metadata, author bios, references), and run it on the new manuscript. Modify the author-info table in place; never delete and recreate it, or the embedded photos are lost.

Existing project files likely relevant:
- batch_article_evaluation.py
- evaluate_filters.py
- parameter_sweep.py
- swing_analyzer.py
- analysis.py
- kalman.py
- rts_smoother.py
- utils_filter.py
- drawing.py
- article_package/evaluation_outputs/dataset_summary.csv
- article_package/evaluation_outputs/validation_keyframe_errors.csv
- article_package/evaluation_outputs/sensitivity_results.csv
- article_package/evaluation_outputs/ablation_results.csv
- article_package/evaluation_outputs/repeatability_repeatability.csv
- article_package/evaluation_outputs/trajectory_deviation_summary.csv
- article_package/evaluation_outputs/figures/

Important note:
The first article treated validation/sensitivity/ablation results as diagnostic because some values were not strong enough for final accuracy claims. The second article should improve these outputs and make them the main scientific contribution.

Please help me plan and then implement the second article workflow.

Do not immediately write the final article. First:
1. Inspect the existing project structure and available outputs.
2. Identify what additional reference annotations are needed.
3. Propose the exact experimental design for the second article.
4. Define scripts to implement, CSV outputs to generate, figures to produce, and tables to include.
5. Identify which results can be reused from the first article and which must be recalculated.
6. Highlight scientific risks, especially overclaiming accuracy without reference data.

Recommended new outputs to implement:
- second_article_outputs/reference_subset.csv
- second_article_outputs/reference_subset_summary.csv
- second_article_outputs/reference_annotations.csv, if manual labels are available
- second_article_outputs/event_validation_errors.csv
- second_article_outputs/event_validation_summary.csv
- second_article_outputs/trajectory_reference_errors.csv
- second_article_outputs/trajectory_reference_summary.csv
- second_article_outputs/sensitivity_results.csv
- second_article_outputs/sensitivity_summary.csv
- second_article_outputs/ablation_results.csv
- second_article_outputs/ablation_summary.csv
- second_article_outputs/reliability_statistics.csv
- second_article_outputs/figures/fig_event_error_by_event.png
- second_article_outputs/figures/fig_trajectory_error_distribution.png
- second_article_outputs/figures/fig_sensitivity_metric_heatmap.png
- second_article_outputs/figures/fig_ablation_trajectory_deviation.png
- second_article_outputs/figures/fig_bland_altman_selected_metrics.png

Recommended research aim:
To evaluate the accuracy, robustness, and reliability of a markerless video-based golf-stick motion-analysis workflow under heterogeneous recording conditions and controlled input perturbations.

Recommended objectives:
1. Construct a manually annotated reference subset for key swing events and selected stick-tip trajectory control points.
2. Quantify event-detection accuracy for impact, top of backswing, and downswing transition.
3. Estimate geometric trajectory error between automatically processed stick-tip positions and manually annotated reference points.
4. Evaluate sensitivity of exported metrics to frame thinning, landmark dropout, coordinate jitter, scale perturbation, and combined degradation.
5. Compare processing variants through an ablation study.
6. Identify which metrics are robust enough for cross-session comparison.
7. Formulate recommendations for VR training and sport-biomechanics use.

Expected article structure:
- INTRODUCTION
- LITERATURE REVIEW AND PROBLEM STATEMENT
- RESEARCH AIM AND OBJECTIVES
- MATERIALS AND METHODS
- RESEARCH RESULTS
- DISCUSSION OF RESULTS
- CONCLUSIONS
- ACKNOWLEDGMENTS
- REFERENCES
- Ukrainian metadata
- Author information

Please begin by analyzing the current project and producing a detailed implementation plan, not by writing the final paper immediately.
```

## Final Note

The second article becomes strongest if manual reference annotations are added. Without them, the article can still be a robustness/sensitivity study, but it should not claim full external accuracy validation.
