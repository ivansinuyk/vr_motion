# Second article - manuscript master text

Working title: **Reference-Based 2D Agreement and Perturbation Sensitivity of Markerless Video-Based Golf-Club Motion Analysis**

This file is the canonical editable source for the revised article. `build_second_article_docx.py` reads this text and injects it into a copy of the HAIT-formatted template while preserving the journal page structure, headers, footers, references, and author-information table.

---

## TITLE

Reference-Based 2D Agreement and Perturbation Sensitivity of Markerless Video-Based Golf-Club Motion Analysis

## KEYWORDS

markerless motion analysis; golf swing; clubhead tracking; manual annotation; perturbation analysis; measurement agreement

## ABSTRACT

Markerless video analysis could broaden access to golf-swing measurement, but visual plausibility does not establish measurement validity. This study assessed the agreement and perturbation sensitivity of a monocular golf-club motion-analysis workflow without treating sparse manual clicks as biomechanical ground truth. A subset of 25 sessions was selected from 71 heterogeneous processed recordings using viewpoint, capture-speed class, and video-quality strata. One annotator marked address, top of backswing, downswing transition, impact, and 260 clubhead control points at selected frames. Event comparisons were audited against decoded presentation timestamps. Clubhead localization was summarized first within each session and then across sessions, with session-level bootstrap confidence intervals. Twelve frame-thinning, landmark-dropout, coordinate-jitter, scale, and combined stress tests were applied to all 71 sessions, and six actual production stages were compared in a nested ablation. The automatic transition output was the same proxy for both manually defined transition events and therefore did not constitute two detectors. Median absolute disagreement was 42–46 frames, or 817–1000 ms, and the mean signed bias ranged from −1987 to −1730 ms. Timestamp discrepancies were at most 67 ms over the common frame grid and could not explain the event disagreement. Across sessions, the median of session-specific clubhead errors was 0.82% of the image diagonal (95% confidence interval 0.69–0.90%), or 14.4 pixels (12.7–18.2 pixels). The distribution was heavy-tailed: 25 of 260 points exceeded 100 pixels and 8 exceeded 500 pixels. Smoothness index showed the lowest perturbation response, with a median absolute symmetric change of 10.0% and no high-response scenarios under study-specific operational thresholds; path efficiency was next but had three high-response scenarios. Production-stage ablation showed that the Rauch–Tung–Striebel output collapsed away from the observed path, despiking changed no points, and final bounded reconstruction restored geometry while reintroducing derivative variation. The evidence supports only sparse 2D annotation agreement and algorithmic stress-test conclusions. It does not establish external biomechanical validity, test–retest reliability, cross-athlete comparability, or adequacy for coaching and virtual-reality feedback.

## Ukrainian title

Еталонне оцінювання двовимірної узгодженості та чутливості до збурень безмаркерного відеоаналізу руху ключки для гольфу

## Ukrainian keywords

безмаркерний аналіз руху; гольф-свінг; відстеження головки ключки; ручне анотування; аналіз збурень; узгодженість вимірювань

## Ukrainian abstract

Безмаркерний відеоаналіз може розширити доступ до вимірювання гольф-свінгу, однак візуальна правдоподібність не доводить валідності вимірювань. У дослідженні оцінено узгодженість і чутливість до збурень монокулярного пайплайну аналізу руху ключки для гольфу без трактування розріджених ручних позначок як біомеханічної істини. Із 71 неоднорідного опрацьованого запису за стратами ракурсу, класу швидкості зйомки та якості відео відібрано 25 сесій. Один анотатор позначив вихідне положення, вершину замаху, перехід до даунсвінгу, удар і 260 контрольних положень головки ключки у вибраних кадрах. Порівняння подій перевірено за декодованими часовими мітками кадрів. Похибку локалізації спочатку узагальнювали в межах кожної сесії, а потім між сесіями із сесійним бутстрепом довірчих інтервалів. До всіх 71 сесій застосовано 12 стрес-тестів із проріджуванням кадрів, випаданням орієнтирів, координатним шумом, зміною масштабу та комбінованою деградацією; шість фактичних виробничих етапів порівняно у вкладеній абляції. Один автоматичний вихід переходу використовувався як проксі для двох ручних подій і не був двома незалежними детекторами. Медіанна абсолютна розбіжність становила 42–46 кадрів, або 817–1000 мс, а середнє знакове зміщення — від −1730 до −1987 мс. Розбіжності часової сітки не перевищували 67 мс і не пояснювали результат. Медіана сесійних медіан похибки головки ключки становила 0,82% діагоналі кадру (95% довірчий інтервал 0,69–0,90%), або 14,4 пікселя (12,7–18,2 пікселя). Розподіл мав важкий хвіст: похибка 25 із 260 точок перевищувала 100 пікселів, а 8 точок — 500 пікселів. Індекс плавності мав найменшу реакцію на збурення: медіанна абсолютна симетрична зміна дорівнювала 10,0%, без сценаріїв високої реакції за операційними порогами цього дослідження; ефективність траєкторії посіла друге місце, але мала три сценарії високої реакції. Абляція показала колапс результату згладжувача Рауха–Тунга–Штрібеля, відсутність активації видалення викидів і повторне внесення варіативності похідних під час фінальної обмеженої реконструкції. Отримані дані доводять лише узгодженість із розрідженою двовимірною анотацією та реакцію алгоритму на стрес-тести. Вони не доводять зовнішньої біомеханічної валідності, надійності test–retest, порівнюваності між спортсменами чи достатності для тренерського зворотного зв’язку та віртуальної реальності.

## For citation (English)

For citation: Syniuk I. M., Maksymov M. V., Maksymov O. M., Iyer K. "Reference-based 2D agreement and perturbation sensitivity of markerless video-based golf-club motion analysis". Herald of Advanced Information Technology. - [Year]. - Vol. [..]. - No. [..]. - Pp. [..-..]. DOI: [assigned by editorial team]

## For citation (Ukrainian)

Для цитування: Синюк І. М., Максимов М. В., Максимов О. М., Айєр К. «Еталонне оцінювання двовимірної узгодженості та чутливості до збурень безмаркерного відеоаналізу руху ключки для гольфу». Herald of Advanced Information Technology. - [Рік]. - Т. [..]. - № [..]. - С. [..-..]. DOI: [призначається редакцією]

---

# BODY

## INTRODUCTION

Quantitative golf-swing assessment supports technique research, coaching, and the development of interactive training systems. Laboratory optical motion capture can resolve segment and club kinematics with controlled calibration, but it requires synchronized cameras, markers, and specialist operation [1], [2]. Golf biomechanics has therefore been studied through laboratory kinematics, clubhead-speed and power analysis, and segment sequencing [8], [9], [10], [11], [23]. These methods establish what can be measured under controlled conditions but do not by themselves solve the problem of low-cost field acquisition.

Portable inertial measurement units and ordinary video lower the acquisition burden. Golf-specific inertial systems have been compared with three-dimensional motion capture, while single-camera studies have combined pose estimation and object detection to examine golfer posture and clubhead trajectories [24], [31]. General pose-estimation frameworks such as OpenPose, BlazePose, and MediaPipe make markerless processing accessible [3], [4], [5]. Nevertheless, accessibility is not equivalent to accuracy, and a visually smooth trajectory can remain temporally misaligned, geometrically biased, or unstable under small changes in the input.

Validation literature distinguishes agreement with an explicit reference from reliability across repeated measurements. Markerless estimates are affected by viewpoint, occlusion, motion blur, training-domain mismatch, and monocular projection [12], [13], [25], [26], [27], [28]. Golf-specific evidence is especially cautionary: monocular three-dimensional pose models that look convincing after reprojection can still be unsuitable for kinematic analysis when compared with synchronized marker-based data [30]. Derivatives amplify coordinate noise, and impact-like, non-stationary motion creates additional filtering problems [6], [7], [19].

The workflow evaluated here was introduced in a companion methodological manuscript and combines median pre-filtering, confidence-aware Kalman tracking, Rauch–Tung–Striebel smoothing, trajectory despiking, bounded polynomial reconstruction, and dynamic scaling [32]. The present work asks a narrower question: what agreement and numerical sensitivity can be demonstrated with the available data? The evidence is deliberately limited to manual two-dimensional annotations, decoded video timing, synthetic perturbations, and production-stage ablation. Figure 1 summarizes the study design and its evidence boundary.

## LITERATURE REVIEW AND PROBLEM STATEMENT

Markerless sports analysis spans general human-pose estimation, sport-specific movement recognition, and task-specific object tracking [3], [4], [5], [29]. In golf, Yamamoto et al. used a single sagittal camera, human-pose estimation, and DeepLabCut clubhead tracking to study proficiency and individual swing characteristics [31]. Ingwersen et al. compared monocular pose models with synchronized marker-based golf data and found substantial quantitative error despite plausible visual reconstructions [30]. Together these studies show that golf-specific validation must report the reference standard, camera geometry, event definitions, and failure tails rather than relying on representative images.

Signal conditioning changes both geometry and derived metrics. Median filters suppress isolated outliers [14]; Kalman filtering combines a dynamic model with noisy measurements [15], [16]; Rauch–Tung–Striebel smoothing uses later observations to refine earlier states [17]; and local polynomial methods can reduce noise while preserving trajectory shape [18]. For rapidly changing motion, however, the filter that best suppresses coordinate noise may attenuate true motion or create endpoint and derivative artefacts [7]. Smoothness measures based on jerk are consequently sensitive to the derivative definition and to the time interval used across missing samples [19].

Measurement terminology is also consequential. Test–retest reliability, intraclass correlation, standard error of measurement, and minimal detectable change require repeated observations with an identifiable grouping structure [20], [21]. Between-session dispersion in a heterogeneous corpus does not meet that definition. Bland–Altman bias and limits of agreement describe paired differences but do not transform a single-annotator reference into ground truth [22]. Robust summaries such as medians are useful for skewed error distributions [14], but they must be accompanied by uncertainty and failure-tail reporting.

Three gaps motivate this study. First, the available workflow had not been compared with manually selected clubhead positions and visually defined events. Second, the alignment of video frames, landmark indices, and annotation times had not been audited before interpreting large timing errors. Third, previous sensitivity and ablation summaries used unstable random seeds, percentage changes unsuitable near zero, a non-production smoothing variant, and cross-session coefficients of variation mislabeled as reliability. The problem addressed here is to correct those design and reporting weaknesses without claiming evidence that the dataset cannot provide.

## RESEARCH AIM AND OBJECTIVES

The aim is to assess two-dimensional manual-annotation agreement and perturbation sensitivity of a markerless video-based golf-club motion-analysis workflow under heterogeneous recording conditions.

The research objectives are:

1. To define a selected-frame manual annotation protocol and state its evidential limits.
2. To audit video presentation timestamps, landmark times, frame counts, and event-definition mapping before interpreting event disagreement.
3. To estimate session-level clubhead localization agreement in pixels and image-diagonal-normalized units and to quantify large-error tails.
4. To characterize metric response to 12 controlled perturbation scenarios using deterministic simulation and symmetric relative change.
5. To compare the actual nested production stages and identify stages that are inactive or introduce undesirable behaviour.
6. To distinguish demonstrated findings from untested biomechanical validity, reliability, and application-level usefulness.

## MATERIALS AND METHODS

### Dataset, sampling, and available metadata

The corpus contained 71 processed golf-swing sessions. Frame rates ranged from 23.98 to 60.00 frames/s, and resolutions ranged from 576 × 1024 to 1920 × 1080 pixels. Viewpoint was predominantly down-the-line (59 sessions), with 10 face-on and 2 other views; 16 sessions had unknown club type. The selection algorithm formed strata from viewpoint, capture-speed class, and quality grade, then sampled 25 sessions with a fixed seed. Frame-rate and resolution distributions were summarized after selection but were not sampling strata. The selected set contained 21 down-the-line, 3 face-on, and 1 other view (Table 1). The export did not encode participant identity, number of sessions per participant, age, skill, device, camera distance or height, shutter speed, lighting, codec settings, or whether slow-motion interpolation had been applied. These omissions prevent participant-level generalization and test–retest analysis.

### Ethics, consent, and data provenance

Session folders were locally stored and identified by universally unique identifiers, but the available project export did not contain recruitment records, source licensing, informed-consent documentation, an ethics-committee decision, or a waiver. This revision therefore does not infer that research-use permission exists merely because identifiers are absent. No participant image is reproduced in the article. Submission must remain conditional on the authors and institution verifying the source of the videos, consent or waiver, de-identification procedure, ethics status, and permission for scientific use. The schematic in Fig. 2 is retained because replacing it with a real frame would not resolve the underlying provenance requirement.

### Manual annotation protocol

One annotator completed one round for all 25 sessions. The annotation interface displayed decoded video frames without automatic event markers or processed clubhead coordinates. Four events and 8–14 selected-frame clubhead points per session were recorded in original pixel coordinates, yielding 100 event labels and 260 control points. Address was recorded to inspect time origin but had no automatic counterpart. Operational definitions are given in Table 2 and illustrated schematically in Fig. 2. Control points were deliberately placed along visible portions of the swing arc; consequently, the sample favours frames where a visual click was possible and cannot estimate whole-video tracking availability. The reference is therefore a sparsely sampled, single-annotator, two-dimensional visual reference, not a continuous or external biomechanical ground truth.

### Automatic workflow

Normalized landmark coordinates were converted to pixels. A running median preceded a confidence-aware constant-velocity Kalman filter with physical gating and adaptive measurement noise. Stored forward states were passed to the production Rauch–Tung–Striebel smoother, then to trajectory despiking and bounded polynomial/Laplacian reconstruction with blending and a maximum deviation from raw coordinates. A running median of detected shaft length supplied the pixel-to-metre factor using an assumed physical club length of 1.0 m. The evaluated output was generated with the scientific profile described in the companion workflow [32].

### Time-base and event audit

Every selected processed video was decoded with presentation timestamps. For each session, decoded frame count, timestamp intervals, the landmark-array `time` field, and manual `reference_frame/reference_time_s` pairs were compared. An event scatter plot used manual and automatic frame indices with an identity line. The workflow exports one impact index and one transition index. The transition index was compared separately with manual top of backswing and manual downswing transition only as a definition diagnostic; the two rows share the same automatic output and are not independent detectors.

### Event agreement measures

For session i and manual definition e, signed frame error was `E_frame(i,e) = frame_auto(i,e) - frame_manual(i,e)`. Negative values indicate an early automatic output. Presentation-time error was `E_time(i,e) = time_auto(i,e) - time_manual(i,e)` and was reported in milliseconds. Absolute error was the magnitude of the signed error. For each comparison, the median signed error, median absolute error, mean bias, standard deviation of paired differences, 95th percentile absolute error, and Bland–Altman limits `bias ± 1.96 × SD` were calculated [22]. Session bootstrap intervals resampled the 25 paired sessions 10 000 times.

### Clubhead localization agreement

At every annotated frame, the Euclidean pixel discrepancy was `D_px = sqrt[(x_auto - x_manual)^2 + (y_auto - y_manual)^2]`. The primary resolution-normalized measure was `D_diag = D_px / sqrt(width^2 + height^2)`. A secondary physical estimate used `D_m = D_px × L_assumed / length_px`, where `L_assumed = 1.0 m` and `length_px` was the workflow's running detected club length. Because this scale is generated by the evaluated workflow and actual club length is unavailable for 16 sessions, centimetre values are model-dependent and are not treated as independently calibrated accuracy. Error relative to visible detected club length is algebraically `D_m / L_assumed` and has the same dependence. Points were assigned to phases from manual events. To respect clustering, the median was first calculated within each session and phase; medians and 95% bootstrap intervals were then calculated across sessions. Point-level 95th percentiles, maxima, and counts above 100, 250, and 500 pixels describe the heavy tail.

### Perturbation sensitivity

All 71 sessions were reprocessed under 12 scenarios: frame thinning by factors of 2 and 3; club-landmark dropout of 5%, 10%, and 20%; independent coordinate jitter with normalized standard deviations 0.004 and 0.008; scale changes of −10%, −5%, +5%, and +10%; and a combined case comprising twofold thinning, 10% dropout, and 0.004 jitter. Depending on frame size, the jitter doses correspond approximately to 2–8 and 5–15 pixels per coordinate. These are study-specific stress-test doses, not empirically estimated prevalence levels. Dropout and jitter used a process-independent seed derived from the session identifier; one realization per session and dose was evaluated.

For baseline value m0 and perturbed value mp, absolute symmetric change was `Delta_sym = 200 × |mp - m0| / (|mp| + |m0|)`. This bounded measure avoids the unbounded denominator problem of ordinary percentage change, although interpretation remains difficult near zero and for an index with an arbitrary origin. Spearman rank correlation quantified preservation of session ordering. Session bootstrap intervals used 2000 resamples for median change and 1000 for rank correlation. For descriptive summaries only, median changes below 10%, from 10% to below 25%, and at least 25% were labelled low, moderate, and high response. These author-defined operational bands are not coaching tolerances or measurement-validity thresholds. Phase-duration metrics were excluded because the event segmentation was not valid, and downswing peak speed was excluded because it duplicated maximum speed in these runs.

### Production-stage ablation and metric definitions

The nested ablation exposed the actual arrays produced after raw landmark extraction, median filtering, forward Kalman filtering, production Rauch–Tung–Striebel smoothing, despiking, and final bounded reconstruction. Unlike the previous diagnostic, no corrected textbook smoother was substituted for the production implementation. For every stage, the number of points changed relative to the preceding stage was counted before rounding. A common derivative calculation used the actual elapsed interval across missing samples. Scalar speed was displacement magnitude divided by elapsed time; scalar acceleration was the first difference of speed; scalar jerk was the first difference of acceleration; and `RMS_jerk = sqrt[mean(jerk^2)]`. The smoothness index was `S = -log10[mean(jerk^2) + 10^-9]`, so larger values indicate lower RMS jerk only within this definition. Path efficiency was endpoint displacement divided by cumulative path length. Maximum angular velocity was the maximum absolute first difference of shaft angle per unit time, and curvature RMS was the root mean square of three-point planar curvature. Stability of these computed quantities does not establish that they measure swing quality.

### Statistical analysis

Sessions, rather than individual control points, were the resampling unit. Bootstrap confidence intervals used the percentile method with a fixed seed. Point-level distributions are additionally shown to expose rare failures, but no p-values are reported for the small and imbalanced viewpoint, frame-rate, resolution, quality, capture-speed, or club subgroups. Between-session coefficients of variation, repeatability coefficients, standard errors of measurement, minimal detectable changes, and intraclass correlations were removed because athlete/trial repeated-measure grouping was unavailable [20], [21]. Results are reported only for methods explicitly shown in the tables, figures, or supplementary comma-separated files.

## RESEARCH RESULTS

### Reference subset and protocol

The 25-session subset retained multiple frame-rate, resolution, capture-speed, club, and quality categories but remained dominated by down-the-line recordings (Table 1). All selected sessions contained four manual event labels and selected-frame clubhead points. The 260 points were not uniformly distributed by phase: 105 were in backswing, 5 in transition, 44 in downswing, 59 near impact, and 47 in follow-through. The transition estimate is therefore descriptive only.

### Time-base audit and event disagreement

Decoded video and landmark frame counts matched in 24 of 25 sessions; the remaining session differed by one frame. Twelve videos had non-uniform presentation intervals. Manual annotation times differed from decoded presentation times by at most 19.6 ms, and the landmark-time grid differed from the decoded grid by at most 66.7 ms over common frames. These discrepancies are too small to explain median event disagreement of 817–1000 ms, although frame-based reporting remains primary and source-to-processed-video alignment could not be audited without the original source files.

The transition proxy fired a median 43 frames early relative to manual top and 46 frames early relative to manual downswing transition; the impact output fired a median 42 frames early (Table 3; Fig. 3). Median absolute errors were 920 ms (95% CI 760–1835 ms), 1000 ms (820–1902 ms), and 817 ms (660–960 ms), respectively. Mean biases were −1914, −1987, and −1730 ms, with 95th percentile absolute errors between 4707 and 4893 ms. The smallest observed absolute error was 14 frames, a typical error was 43 frames, and the largest was 534 frames. Figure 3 shows that most outputs lie far below the identity line. The result is an end-to-end disagreement of the current processed output with one annotator's definitions, not proof that all error originates in a single detector component.

### Clubhead localization agreement and failure tail

Across 25 session-specific medians, clubhead discrepancy was 14.4 pixels (95% CI 12.7–18.2 pixels) or 0.82% of image diagonal (0.69–0.90%). The corresponding model-dependent physical estimate was 3.9 cm. Session-median normalized discrepancy was 0.67% in backswing, 0.67% in downswing, 0.88% near impact, and 0.92% in follow-through (Table 4; Fig. 4). Only five sessions contributed a transition point, yielding a very wide interval.

The point-level distribution was strongly right-skewed. Its 95th percentile was 265.6 pixels and its maximum was 2473.0 pixels. Twenty-five of 260 points (9.6%) exceeded 100 pixels across 11 sessions; 14 points (5.4%) exceeded 250 pixels across 5 sessions; and 8 points (3.1%) exceeded 500 pixels across 2 sessions. Downswing and follow-through point-level 95th percentiles were 1589.1 and 706.5 pixels. The workflow returned a coordinate at all 260 selected frames, but coordinate availability did not guarantee correct localization. Because frames were selected where the clubhead was visually annotatable, these counts cannot be interpreted as whole-video tracking-success rates.

Exploratory subgroup summaries suggested larger session-median normalized errors at no more than 30 frames/s than at 31–60 frames/s (1.20% versus 0.75%) and below 720 p than at 1080 p or higher (1.20% versus 0.75%). The difficult-quality group had a median of 2.15%, but its four-session confidence interval was extremely wide. Face-on results were based on only three sessions. These patterns are hypothesis-generating and do not support adjusted or causal comparisons.

### Perturbation sensitivity

All 852 perturbed runs completed. Smoothness index had the lowest overall response: its median absolute symmetric change across the 12 scenarios was 10.0%, its worst scenario was 20.9%, and its operational counts were 6 low, 6 moderate, and 0 high responses (Table 5; Fig. 5). Path efficiency had a median change of 14.2% but reached 46.5% and had three high-response scenarios. Maximum speed had a median of 24.2% and six high-response scenarios. Maximum acceleration, swing tempo, curvature RMS, and backswing peak speed had median changes from 39.8% to 75.4%.

Magnitude response and rank preservation were not interchangeable. Curvature RMS and maximum angular velocity retained median Spearman correlations of 0.89 and 0.79 despite large magnitude changes, whereas smoothness index and path efficiency had median correlations of 0.63 and 0.61. Scale perturbations produced the smallest responses for scale-free quantities, while thinning, jitter, and combined degradation dominated most derivative metrics. The complete 12-scenario table, including confidence intervals, is retained as supplementary comma-separated output.

### Production-stage ablation

The corrected ablation did not show monotonic improvement (Table 6; Fig. 6). Median RMS jerk decreased from 17 334 m/s³ for raw landmarks to 14 448 after the median stage and 881 after the production Kalman stage. The production Rauch–Tung–Striebel stage reduced RMS jerk to 0.43 m/s³ but moved a median 170.2 cm from the raw path and reduced median maximum speed to 0.18 m/s, indicating trajectory collapse rather than useful smoothing. The production smoother computes predicted covariance without the process-noise term used by the earlier isolated textbook reconstruction; the two variants were therefore not equivalent.

Despiking changed zero points in every one of the 71 sessions, so no positive contribution can be attributed to that stage under the current thresholds. Final bounded reconstruction changed a median 162 points and returned mean deviation to 2.3 cm, but RMS jerk increased to 11 871 m/s³. The final stage therefore restored proximity to the observed path while reintroducing derivative variation. These findings identify implementation and parameter issues; they do not validate the causal benefit of each pipeline stage.

## DISCUSSION OF RESULTS

The central result is narrower than the original manuscript claimed. Typical selected-frame clubhead positions agreed reasonably closely with one annotator in two-dimensional image space, but the distribution contained severe failures and the reference was neither continuous nor external. A session-level median of 0.82% of image diagonal describes the typical annotated frame; it does not erase the 9.6% of points above 100 pixels or establish clubhead accuracy during unselected, blurred, or occluded frames. The centimetre estimate is secondary because the evaluated workflow supplied its own scale and actual club lengths were not available.

The timing audit materially changes interpretation of the event result. Presentation-time and landmark-grid discrepancies were tens of milliseconds, whereas event disagreement was hundreds to thousands of milliseconds. The large early bias therefore persists after a processed-video time-base check. However, the transition comparison also exposed a definition error: one automatic transition output had been presented as if it independently detected top of backswing and downswing transition. The revised analysis treats these as two comparisons of one proxy. Source-video trimming and preprocessing history remain unverified, and a second blinded annotator is needed before algorithm and annotation disagreement can be separated.

The perturbation study supports a relative statement, not a validity claim. Smoothness index responded less than the other tested outputs, and path efficiency was often less responsive than derivative peaks. Yet path efficiency had three high-response scenarios, and neither metric has been validated against expertise, shot outcome, coach judgement, or user benefit. Rank preservation for curvature and angular velocity despite large magnitude changes further shows why a single "robust" label is inadequate. Numerical stability is one property of an implementation; construct validity and application tolerance are separate questions.

The production-stage ablation is a negative but actionable diagnostic. It explains the previously contradictory narrative: a substituted textbook smoother produced favourable intermediate numbers, whereas the actual production smoother collapsed the trajectory, despiking never activated, and bounded reconstruction blended the path back toward raw observations. The appropriate response is not to claim that every stage contributes, but to correct the production smoother, retune or remove the inactive stage, and repeat all reference and perturbation analyses on the revised pipeline.

The study has substantial limitations. One annotator and one round provide no intra- or inter-annotator uncertainty. Selected visible frames create verification bias. Points are clustered within sessions, participant identities and repeated trials are unavailable, and viewpoint groups are imbalanced. The perturbations are author-defined stress tests with one stochastic realization per session and are not calibrated to empirical dropout or jitter distributions. Monocular two-dimensional coordinates cannot resolve depth, perspective, or foreshortening. Data provenance, consent, and ethics status are not documented in the export. These limitations affect the strength of the conclusions and are not dismissed as inconsequential.

For application, the observed error may be compatible with coarse trajectory visualization in some settings, but application-specific acceptability thresholds have not been established. The data do not justify biomechanical impact analysis, athlete-to-athlete comparison, real-time reliability claims, or unqualified coaching and virtual-reality feedback. Such uses require an independently calibrated reference, verified provenance, repeated athlete trials, blinded repeat annotation, and a user- or task-specific tolerance study.

## CONCLUSIONS

The study demonstrates that the current workflow disagrees substantially with one annotator's event frames, even after a processed-video timestamp audit, and that one automatic transition output had been compared with two manual definitions. For selected clubhead frames, the median of session-specific errors was 0.82% of image diagonal, but severe localization failures remained: 9.6% of points exceeded 100 pixels and 3.1% exceeded 500 pixels.

Smoothness index showed the lowest response to the 12 study-specific perturbations, while path efficiency was condition-dependent and derivative metrics generally showed larger magnitude responses. These results describe numerical sensitivity only. They do not establish that any metric validly measures swing quality or is suitable for cross-athlete comparison.

The production-stage ablation identified trajectory collapse in the actual Rauch–Tung–Striebel stage, no activation of despiking, and renewed derivative variation after final reconstruction. Before submission as a validation study, the pipeline should be corrected and re-evaluated; a second blinded annotator, repeat athlete trials, independent spatial calibration, verified ethics and consent, and complete acquisition metadata are required. The present contribution is therefore a reproducible protocol and a bounded 2D agreement and stress-test result, not full external validation or reliability evidence.

## ACKNOWLEDGMENTS

The authors thank the research supervisor and collaborators who reviewed the manuscript and the motion-analysis workflow. Responsibility for the data, analysis, interpretation, and final text remains with the authors.
