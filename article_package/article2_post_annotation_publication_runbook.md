# Article 2: post-annotation and publication runbook

Use this file as the execution specification for the agent that continues the
second article after additional human annotation.

## Current frozen baseline

- Manuscript source:
  `article_package/second_article_manuscript.md`
- Mentor-review DOCX:
  `article_package/Стаття_Аспірант_Синюк_HAIT_article2_v2.docx`
- Verified preview:
  `second_article_outputs/article2_v2_preview.pdf`
- Original annotations:
  `second_article_outputs/reference_annotations.csv`
- Frozen 25-session subset:
  `second_article_outputs/reference_subset.csv`
- Dataset default:
  `C:\Users\isinu\Downloads\Telegram Desktop\7a0c087a-b6c7-42ea-bc67-63453d4cac7f`

Never overwrite the v2 manuscript, the original annotation CSV, or the frozen
subset. Build the post-rater revision as v3.

## Non-negotiable role definitions

1. The first annotator is `Ivan Syniuk`, round 1.
2. The second annotator must be a different human. Use that person's stable
   full name as `annotator_id`; do not use `Ivan Syniuk`.
3. The second annotator's first pass is round 1.
4. A later repeat by Ivan is `Ivan Syniuk`, round 2. This measures intra-rater
   agreement and is not a substitute for a second annotator.
5. Annotators must not see automatic event frames, processed clubhead
   coordinates, or each other's coordinates before both raw rounds are locked.
6. Raw rater records must remain immutable. Consensus is a separate dataset.

## Stop conditions

Stop and report a blocker instead of fabricating data if any of these apply:

- video provenance, research-use permission, consent, waiver, or ethics status
  cannot be verified;
- the second annotator is not independent;
- both annotators did not click the same planned trajectory frames;
- raw rater files cannot be recovered separately;
- the production RTS defect has not been resolved or explicitly removed;
- participant or acquisition metadata are unavailable: report them as
  unavailable, never infer them;
- athlete IDs and repeated swings are unavailable: do not calculate or claim
  athlete test-retest reliability, ICC-based repeatability, SEM, or MDC.

## Phase 0: freeze and back up existing work

Run in PowerShell from the repository root:

```powershell
cd "C:\Users\isinu\programming\study\vr_motion"

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item "second_article_outputs\reference_annotations.csv" `
  "second_article_outputs\reference_annotations_before_multirater_$stamp.csv"
Copy-Item "article_package\Стаття_Аспірант_Синюк_HAIT_article2_v2.docx" `
  "article_package\Стаття_Аспірант_Синюк_HAIT_article2_v2_frozen_$stamp.docx"
```

Do not rerun `prepare_reference_subset.py`. The same 25 sessions must be used.

## Phase 1: implement a blinded common-frame annotation mode

This phase must be completed before trajectory annotation by annotator 2.
The required commands below do not exist yet; the future agent must implement
them and add tests.

### 1.1 Create `prepare_common_annotation_plan.py`

Required behavior:

- read Ivan's round-1 point rows only;
- retain the frozen 25 sessions;
- choose six unique control frames per session, giving exactly 150 common
  trajectory frames;
- choose frames deterministically and spread them over the ordered existing
  frames, rather than sampling only easy early frames;
- export session and frame index only, never Ivan's coordinates;
- include phase labels for later stratified reporting, but do not display
  automatic outputs to annotators.

Required command:

```powershell
python prepare_common_annotation_plan.py `
  --annotations "second_article_outputs\reference_annotations.csv" `
  --source-annotator "Ivan Syniuk" `
  --source-round 1 `
  --subset "second_article_outputs\reference_subset.csv" `
  --points-per-session 6 `
  --out "second_article_outputs\second_annotator_frame_plan.csv"
```

Acceptance checks:

- 25 unique sessions;
- exactly 150 unique `(session_id, reference_frame)` pairs;
- six frames in every session;
- no `x_px`, `y_px`, automatic event, or automatic trajectory columns.

### 1.2 Extend `annotate_reference.py`

Add and test these CLI options:

- `--point-plan <csv>`: show and navigate only required control frames;
- `--session-plan <csv>`: optionally limit an intra-rater round;
- `--output <csv>`: write a separate raw rater file;
- `--require-complete`: refuse final completion unless all four events and all
  planned point frames have one clubhead click;
- a key to jump to the next missing planned frame.

The interface may display session ID, current frame, and event definitions. It
must not load or display another annotator's event frames or coordinates.

Keep the current de-duplication key:
`(session_id, annotator_id, annotation_round)`.

## Phase 2: collect annotator-2 data

Use a different human name below:

```powershell
python annotate_reference.py `
  --dataset-root "C:\Users\isinu\Downloads\Telegram Desktop\7a0c087a-b6c7-42ea-bc67-63453d4cac7f" `
  --annotator "SECOND ANNOTATOR FULL NAME" `
  --round 1 `
  --restart `
  --point-plan "second_article_outputs\second_annotator_frame_plan.csv" `
  --output "second_article_outputs\reference_annotations_annotator2_round1.csv" `
  --require-complete
```

For all 25 sessions, annotator 2 independently marks:

- `1`: address — last stable frame before takeaway;
- `2`: top of backswing — maximal backswing extent before reversal;
- `3`: downswing transition — first sustained motion toward impact;
- `4`: impact — closest visible clubhead-ball contact or crossing;
- one clubhead click on each of the six planned frames.

The second annotator therefore completes all 100 event labels and 150 common
trajectory clicks. Annotating all 260 of Ivan's frames is acceptable but not
required by the mentor's stated minimum.

After completion, make the raw CSV read-only or copy it to a frozen filename.

## Phase 3: collect Ivan's intra-rater round

Create `prepare_intrarater_session_plan.py` or equivalent deterministic logic.
Select 10 of the 25 sessions, stratified as far as possible by viewpoint,
frame-rate group, resolution, capture speed, and quality. Store the selection
before annotation.

Required command after implementation:

```powershell
python prepare_intrarater_session_plan.py `
  --subset "second_article_outputs\reference_subset.csv" `
  --sessions 10 `
  --seed 20260728 `
  --out "second_article_outputs\intrarater_session_plan.csv"
```

Ivan performs round 2 without seeing round 1:

```powershell
python annotate_reference.py `
  --dataset-root "C:\Users\isinu\Downloads\Telegram Desktop\7a0c087a-b6c7-42ea-bc67-63453d4cac7f" `
  --annotator "Ivan Syniuk" `
  --round 2 `
  --restart `
  --session-plan "second_article_outputs\intrarater_session_plan.csv" `
  --point-plan "second_article_outputs\second_annotator_frame_plan.csv" `
  --output "second_article_outputs\reference_annotations_ivan_round2.csv" `
  --require-complete
```

Record the interval between Ivan's rounds in the Methods. Do not copy or preload
round-1 labels into round 2.

## Phase 4: merge and validate raw annotation files

Create `merge_reference_annotations.py`.

Inputs:

- Ivan round 1;
- annotator 2 round 1;
- Ivan round 2.

Required command:

```powershell
python merge_reference_annotations.py `
  --input "second_article_outputs\reference_annotations.csv" `
  --input "second_article_outputs\reference_annotations_annotator2_round1.csv" `
  --input "second_article_outputs\reference_annotations_ivan_round2.csv" `
  --out "second_article_outputs\reference_annotations_multirater.csv"
```

Required validation:

- reject duplicate raw rows for the same rater, round, session, event, or
  planned point frame;
- verify all 25 sessions have four events from each round-1 annotator;
- verify 150 common point frames have one click from each round-1 annotator;
- verify all selected intra-rater sessions contain both Ivan rounds;
- preserve annotator names and rounds;
- never overwrite any input file.

## Phase 5: compute annotation agreement

Create `compute_annotation_agreement.py`. It must operate on human annotations
only and remain independent of automatic pipeline outputs.

Required command:

```powershell
python compute_annotation_agreement.py `
  --annotations "second_article_outputs\reference_annotations_multirater.csv" `
  --annotator-a "Ivan Syniuk" `
  --round-a 1 `
  --annotator-b "SECOND ANNOTATOR FULL NAME" `
  --round-b 1 `
  --intrarater-annotator "Ivan Syniuk" `
  --intrarater-round-a 1 `
  --intrarater-round-b 2 `
  --bootstrap-sessions 10000 `
  --out-dir "second_article_outputs\annotation_agreement"
```

Required event outputs:

- paired signed and absolute frame differences by event;
- median, mean, SD, P95, minimum, and maximum;
- exact-frame, within-one-frame, and within-two-frame agreement;
- Bland–Altman bias and limits in frames and milliseconds;
- session-bootstrap 95% confidence intervals;
- clearly specified ICC model if ICC is reported;
- a separate analysis of whether top of backswing and downswing transition are
  distinguishable between annotators.

Required trajectory outputs for the same 150 frames:

- Euclidean click disagreement in pixels;
- disagreement as percent of image diagonal;
- session-specific median disagreement;
- median of session medians with session-bootstrap 95% confidence interval;
- P95, maximum, and counts above predeclared descriptive thresholds;
- optional x- and y-coordinate absolute-agreement ICC, with the exact ICC model
  stated;
- inter-rater and Ivan intra-rater results kept separate.

Required files:

- `annotation_event_pairwise.csv`;
- `annotation_point_pairwise.csv`;
- `annotation_agreement_summary.csv`;
- `annotation_agreement_summary.md`;
- publication-ready agreement figures in PNG and SVG.

Do not call between-session corpus variation "reliability."

## Phase 6: create a blinded consensus reference

Create `build_consensus_reference.py`.

Consensus must be produced without viewing automatic pipeline results.
Preserve all raw rater rows.

Preferred protocol:

1. Show the two human labels/clicks only.
2. Have the annotators or an independent adjudicator select the final event
   frame and clubhead coordinate.
3. Record adjudication status and reason.
4. Write a new row with `annotator_id=consensus` and `annotation_round=1`.

Do not silently let a dictionary overwrite duplicate raters. Do not call a
simple arithmetic mean "consensus" unless that rule was approved before
adjudication and is disclosed.

Required command after implementation:

```powershell
python build_consensus_reference.py `
  --annotations "second_article_outputs\reference_annotations_multirater.csv" `
  --adjudication "second_article_outputs\annotation_adjudication.csv" `
  --out "second_article_outputs\reference_annotations_consensus.csv"
```

Acceptance checks:

- 25 sessions;
- one consensus row for each of the four events per session;
- one consensus point for every planned consensus frame;
- no automatic values in the consensus source;
- complete audit trail back to both raw annotators.

## Phase 7: make validators multi-annotator safe

Update these scripts before rerunning analysis:

- `validate_events_against_reference.py`;
- `validate_trajectory_against_reference.py`;
- `audit_article2_timebase.py`;
- `build_article_tables.py`.

Add explicit `--annotations-csv` and `--out-dir` arguments. Validators must:

- default to no implicit rater selection;
- reject duplicate references for a session/event/frame;
- require either a named rater/round or the consensus file;
- use consensus for algorithm-reference results;
- use raw rater files only for annotation-agreement results.

Add tests proving that duplicate annotator rows raise an error instead of being
silently overwritten or pooled.

## Phase 8: resolve the production RTS defect

The current production RTS predicted covariance omits the process-noise term,
while the earlier favourable isolated ablation used a different corrected
implementation. The production output collapsed away from the observed path.

The future agent must:

1. inspect `rts_smoother.py`, `swing_analyzer.py`, and Kalman covariance
   propagation;
2. make production and ablation use the same mathematically justified RTS
   equations, including process noise where appropriate;
3. add synthetic constant-velocity and missing-sample tests;
4. verify finite covariance, no trajectory collapse, and bounded deviation;
5. retune or remove despiking if it still changes zero points;
6. document every changed parameter;
7. obtain author approval for the algorithm change.

If a defensible RTS correction cannot be established, remove the stage and
redefine the workflow. Do not retain a known defective stage while claiming a
validated production pipeline.

## Phase 9: version all regenerated analysis as v3

Do not overwrite first-article outputs or the reviewed v2 outputs.

Parameterize article-2 scripts with `--out-dir` and change
`second_article_common.py` so the v3 baseline summary is explicit rather than
silently reading `article_package/evaluation_outputs`.

Use:

```powershell
$DATASET_ROOT = "C:\Users\isinu\Downloads\Telegram Desktop\7a0c087a-b6c7-42ea-bc67-63453d4cac7f"
$OUT = "second_article_outputs\v3"

python batch_article_evaluation.py `
  --dataset-root "$DATASET_ROOT" `
  --out-dir "$OUT\baseline"

python validate_events_against_reference.py `
  --dataset-root "$DATASET_ROOT" `
  --annotations-csv "second_article_outputs\reference_annotations_consensus.csv" `
  --out-dir "$OUT"

python validate_trajectory_against_reference.py `
  --dataset-root "$DATASET_ROOT" `
  --annotations-csv "second_article_outputs\reference_annotations_consensus.csv" `
  --out-dir "$OUT"

python run_sensitivity_study.py `
  --dataset-root "$DATASET_ROOT" `
  --out-dir "$OUT"

python run_ablation_study.py `
  --dataset-root "$DATASET_ROOT" `
  --out-dir "$OUT"

python audit_article2_timebase.py `
  --annotations "second_article_outputs\reference_annotations_consensus.csv" `
  --dataset-summary "$OUT\baseline\dataset_summary.csv" `
  --out-dir "$OUT"

python build_article_tables.py `
  --input-dir "$OUT" `
  --out-dir "$OUT\article_tables"

python make_article2_schematic_figures.py `
  --out-dir "$OUT\figures"
```

These `--out-dir` and input-selection options are part of the required future
implementation; confirm each script's `--help` before executing the block.

Do not run `compute_reliability_statistics.py` unless genuine athlete IDs and
repeated trials are supplied.

## Phase 10: update manuscript and build v3

Update `article_package/second_article_manuscript.md` from generated v3 results,
not by manually copying old v2 numbers.

Required manuscript changes:

- report annotator identities or blinded labels and training;
- report shared-frame plan and annotation-round interval;
- define permissible event uncertainty or explicitly report that no
  application tolerance has been established;
- add inter- and intra-rater agreement with confidence intervals;
- explain consensus construction;
- update all event, trajectory, sensitivity, and ablation values;
- retain pixels and image-diagonal-normalized error as primary;
- keep centimetres secondary unless independent calibration is supplied;
- update limitations after the rater and RTS work;
- retain the distinction between numerical stability and construct validity.

Add an `--output` option to `build_second_article_docx.py`, then build a new
version:

```powershell
python build_second_article_docx.py `
  --manuscript "article_package\second_article_manuscript.md" `
  --analysis-dir "second_article_outputs\v3" `
  --output "article_package\Стаття_Аспірант_Синюк_HAIT_article2_v3.docx"
```

Move the mandatory AI-use disclosure to Acknowledgements or immediately before
References, in accordance with the current HAIT AI policy.

Export a separate PDF preview from Word:

```text
second_article_outputs/v3/article2_v3_preview.pdf
```

## Phase 11: final scientific verification

The future agent must verify all of the following:

- every displayed manuscript number is traceable to a generated v3 CSV;
- all reference comparisons use consensus, not silently pooled raters;
- annotation agreement and algorithm agreement are reported separately;
- points are summarized at session level and confidence intervals resample
  sessions;
- all 12 perturbation scenarios are present in supplementary output;
- seeds are process-independent and recorded;
- ablation stages are nested actual production stages;
- despiking activation counts are reported;
- top and transition are not described as independent automatic detectors;
- no cross-session CV is called reliability;
- no claim of coaching, VR, clinical, or impact-biomechanics adequacy is made
  without an application-specific threshold study;
- all figures remain readable in the final Word layout;
- tables do not split critical headers or values;
- all references are cited and verified;
- author photographs and embedded figures remain intact;
- the v2 DOCX remains unchanged.

Run code checks appropriate to the final implementation, including compilation,
unit tests, lints, and a Word-to-PDF visual inspection.

## Phase 12: mandatory owner-supplied publication information

An agent must not invent any item below. The corresponding author must provide:

1. verified source and ownership/licensing of every video;
2. informed consent, ethics approval, formal exemption, or waiver as applicable;
3. permission for scientific analysis and publication;
4. participant count and repeated-session structure, if recoverable;
5. available demographics and acquisition metadata;
6. actual club lengths or independent calibration, if physical-unit accuracy is
   retained;
7. current status and citation details of Article 1;
8. missing author photographs if the HAIT template requires them;
9. final approval from all authors.

Replace the provisional ethics warning in v2 with a factual, institutionally
approved statement before submission. If lawful scientific use cannot be
verified, stop: the article must not be submitted.

## Phase 13: HAIT submission package

Before OJS submission:

- confirm the manuscript is original and not under consideration elsewhere;
- obtain every co-author's approval and authorship consent;
- use the latest HAIT Word template;
- verify English and Ukrainian metadata;
- include all numbered figures, tables, and supplementary files;
- verify every reference and DOI;
- include conflict-of-interest, funding, data-availability, ethics, and AI-use
  disclosures;
- obtain permission for all photos, datasets, and third-party material;
- complete and sign the current HAIT Consent Form;
- complete and sign the current HAIT Copyright License;
- register or log in to HAIT OJS and upload the Word manuscript and required
  supporting files.

The APC is due only after acceptance.

## Copy-paste instruction for the future agent

```text
Follow article_package/article2_post_annotation_publication_runbook.md as the
authoritative execution plan. First inspect the repository and raw annotation
files, then implement every missing CLI/tool listed in the runbook. Preserve
all v2 and raw files, keep human annotation blinded from automatic output,
reject duplicate references, resolve the production RTS defect, regenerate all
analysis into second_article_outputs/v3, build article2_v3.docx, and verify the
Word/PDF layout. Do not fabricate ethics, consent, participant, acquisition, or
club metadata. Stop and report any failed acceptance check or missing mandatory
owner-supplied information.
```
