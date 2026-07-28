# Second article master-review findings

Reviewed manuscript: `Стаття_Аспірант_Синюк_HAIT_article2_v1.docx`

The review cross-checked the DOCX, manuscript source, generated tables, CSV outputs, and analysis scripts. No manuscript files were changed during the review.

## Overall verdict

**Major revision bordering on rejection in the current form.**

The event mapping, reliability design, ethics omission, contradictory robustness claims, non-controlled ablation, overclaimed geometric accuracy, and unreadable tables are submission-blocking.

Finding counts:

- Critical: 4
- High: 25
- Medium: 15
- Low: 4

## Priority order

1. Correct the event-validation mapping and verify time origins before interpreting timing bias.
2. Remove or redesign the reliability/repeatability analysis.
3. Resolve ethics, consent, and dataset-provenance reporting.
4. Narrow geometric claims to sparse 2D annotation agreement and report catastrophic failures.
5. Correct the false robustness and monotonic-ablation statements.
6. Redesign the ablation so variants differ by one production stage at a time.
7. Add session-aware uncertainty and annotation reliability.
8. Reformat Tables 3-7 before submission.

## Critical findings

### 1. Two claimed automatic events are the same output

Top of backswing and downswing transition are both mapped to `transition_time`. They are not independent event validations.

### 2. The study is not a reliability or repeatability design

There are no athlete/trial repeated measures. Between-session CV/SD measures heterogeneity; RC, SEM, and MDC derived from unrelated sessions are not valid reliability estimates.

### 3. Human-research ethics and consent are not reported

The manuscript gives no ethics approval, consent/waiver, recruitment source, anonymization, or data-governance statement. Replacing a real frame with a schematic does not resolve research-use consent.

### 4. Accuracy and practical trust claims exceed the reference standard

Sparse 2D clicks from one annotator show agreement with one visual annotation procedure, not biomechanical accuracy, 3D validity, coaching utility, or VR efficacy.

## High-severity findings

### 5. The stated stratification procedure is inaccurate

Code stratifies on viewpoint, motion class, and quality only; frame-rate and resolution buckets are summarized afterward, not used as strata.

### 6. No annotation reliability or uncertainty

One annotator completed one round; there is no inter-rater or intra-rater error for frames or point clicks.

### 7. Control-point selection creates verification bias

Points were selected along the visible arc and conclusions are limited to “where tracked,” likely underrepresenting difficult, blurred, or occluded frames.

### 8. Nested trajectory points are treated as independent

The 260 points are clustered within 25 sessions and sessions contribute unequal point counts; pooled summaries ignore dependence and unequal weighting.

### 9. Centimetre error is not independently calibrated

Pixel error is converted using the workflow's own detected stick-length scale and a fixed 1.0 m club assumption across drivers, irons, and unknown clubs. Physical-unit accuracy therefore depends on the system under validation.

### 10. The most comparable trajectory-error unit is omitted

Methods compute image-diagonal-normalized error, but results report pixels and centimetres despite resolutions ranging from 608/720 to 1920 pixels.

### 11. Catastrophic trajectory failures are understated

Downswing P95 is 1589.1 px and overall P95 is 265.6 px; 9.6% of points exceed 100 px and 3.1% exceed 500 px. The text still calls downswing reliably tracked and emphasizes only medians.

### 12. Sensitivity simulations are not reproducible

Random seeds use Python `hash(session_id)`, which changes across processes unless `PYTHONHASHSEED` is fixed.

### 13. Stochastic sensitivity uncertainty is unknown

Only one dropout/jitter realization is run per session and dose; no repeated Monte Carlo draws or uncertainty intervals are reported.

### 14. Robust/usable/exploratory thresholds are arbitrary

The 10% and 25% cut-offs have no citation, empirical justification, or link to a coaching/VR tolerance.

### 15. Smoothness robustness claim contradicts Table 7

The text says robust in all 12 scenarios; Table 7 reports six robust and six usable.

### 16. “Most stable under every perturbation family” is false

Path efficiency changes less under frame thinning (13.7% vs 14.4%) and scale perturbation (0.0% vs 1.0%).

### 17. Cross-device comparability of path efficiency is overclaimed

Path efficiency changes 29.9% under jitter, has 48.6% worst-case median change, and is exploratory in three scenarios.

### 18. The ranking method is not fully specified or implemented as described

The manuscript says recommendations combine sensitivity and CV, but recommendation logic is based on sensitivity counts/change; no explicit formula shows CV affecting the category.

### 19. CV is unsuitable for the reported smoothness scale

Smoothness is a negative log-transformed quantity with an arbitrary zero; its CV is not readily interpretable or comparable across unlike metrics.

### 20. The ablation is not monotonic as claimed

Median RMS jerk falls to 4637 for Kalman+RTS, then rises to 11871 for the full pipeline. None of the 71 sessions has a non-increasing sequence across all six variants.

### 21. The ablation variants are not controlled nested variants

The isolated RTS variant uses a corrected textbook smoother, while production uses a different RTS implementation plus a downstream clamp.

### 22. “Each stage contributes” is unsupported

Kalman+RTS and Kalman+RTS+despiking have identical median deviation, jerk, smoothness, path efficiency, and speed.

### 23. Derivative definitions are nonstandard and underreported

Acceleration is the derivative of scalar speed and jerk is its scalar derivative; missing samples are skipped while a one-frame interval is retained. No equations appear in the manuscript.

### 24. Recommended metrics lack construct validity

Smoothness and path efficiency were not validated against expertise, swing outcome, established biomechanics, or user benefit; stability alone does not make them swing-quality measures.

### 25. Phase-duration sensitivity is claimed but not analyzed

Backswing and downswing durations are absent from the perturbation metrics and Table 7; cross-session CV alone does not establish perturbation instability.

### 26. “All remaining metrics above 25%” is numerically false

Maximum angular velocity is reported at 24.5% median change.

### 27. Dataset and participant reporting is inadequate

No participant count, demographics, skill, repeated-session structure, devices, camera geometry, inclusion/exclusion criteria, or handling of multiple swings is provided.

### 28. Frame/time synchronization is not demonstrated

The analysis assumes video, JSON, and outputs share frame zero and fps. Very large early event bias could partly reflect an offset or time-origin mismatch.

### 29. DOCX Tables 3-7 are largely unreadable

Fixed 8.2 cm, two-column tables break headers and values into fragments such as “signe/d,” “Poin/ts,” “1589/.1,” and “RM/S jerk.”

## Medium-severity findings

### 30. Transition-phase trajectory estimate is too sparse

Only five pooled points support its median, P75, and P95.

### 31. “Per-frame reference” is inaccurate terminology

Only 8-14 selected control frames per session were annotated, not every frame.

### 32. Bland-Altman analysis is incomplete

No confidence intervals or distribution checks are given, and evident proportional bias/heteroscedasticity is not modeled.

### 33. Results lack uncertainty intervals

No confidence or bootstrap intervals are reported for medians, P95, rank correlations, or limits of agreement.

### 34. The companion workflow is not explicitly cited

The central prior methodological study is mentioned but not clearly identified in the sentence or bibliography.

### 35. Inherited references do not support several claims

Reference 30 does not support rank stability, and reference 24 is a gait accelerometer paper used for golf wearable instrumentation.

### 36. The annotation schematic omits an event

Fig. 2 illustrates address, top, and impact but omits downswing transition despite a four-event protocol.

### 37. Figures are not publication-ready

Raw underscored variable names remain; the heatmap clips values above 100% although changes reach 838%; Fig. 8 visualizes invalid cross-sectional CV as consistency.

### 38. Limitations are dismissed despite affecting conclusions

The statement that none of the limitations affects the central conclusions is incompatible with single-rater error, selective sparse frames, clustering, and scale dependence.

### 39. Self-congratulatory reporting language

Phrases such as “honest negative finding” and “more useful than suppressing it” should be replaced with neutral scientific reporting.

### 40. The abstract omits decisive limitations

It promotes centimetre accuracy and practical recommendations without mentioning sparse single-rater annotation, dependent scaling, or absent test-retest data.

### 41. The rank-stability narrative contradicts the output

Median Spearman rank stability is higher for curvature RMS (about 0.90) and angular velocity (about 0.75) than for smoothness (about 0.63) or path efficiency (about 0.50); derivative rankings did not uniformly collapse.

### 42. Sensitivity-family aggregation is not described

Table 5 reports a second-stage median of scenario-level medians within each perturbation family, not a direct pooled median over observations.

### 43. Combined degradation is incompletely specified

Code uses 2x frame thinning, 10% dropout, and jitter sigma = 0.004, while Methods states only the dropout level.

### 44. Two ranked metrics are effectively redundant

Maximum speed and downswing peak speed have identical baseline values throughout the sensitivity runs and identical CVs, inflating the apparent metric list.

## Low-severity findings

### 45. Address is annotated and counted but not analyzed

Twenty-five address labels contribute to the claimed 100 event annotations without an analytical role.

### 46. Internal labels reduce publication quality

Table 1 uses `dtl`, `face_on`, `super_slow`, and `1080p+` without reader-facing definitions.

### 47. Submission metadata is inconsistently complete

Citation blocks retain placeholders while headers already show a year.

### 48. Reliability-oriented filenames and labels are misleading

The output uses repeatability/SEM/MDC columns and an ICC-labelled figure filename even though no ICC or repeated-measures reliability was calculated.

## Verified consistent items

- Annotation data contain 25 sessions, one annotator, one round, exactly four event annotations per session, and 260 control points.
- Point counts are 8-14 per session, with a median of 10.
- All 75 event comparisons use manual references.
- Event medians, means, P95 values, frame errors, and limits of agreement in Table 3 match the output.
- All 260 trajectory points match their recorded reference frames.
- Table 4 medians and percentiles match the trajectory CSV.
- All 71 x 12 sensitivity runs succeeded.
- All 71 sessions contributed to every ablation variant.
