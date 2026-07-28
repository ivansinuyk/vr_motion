"""Build the HAIT-formatted second-article DOCX from the accepted v5 template.

Rather than re-implementing the HAIT formatter (whose recipe is documented in
``second_article_plan_and_prompt.md``), this script clones the already
format-accepted first-article DOCX and edits it *in place*:

* the first-page single-column block (title, abstract, keywords, citation) is
  rewritten for article 2 while keeping authors, affiliations, DOI/UDC and the
  copyright line unchanged;
* the two-column body between INTRODUCTION and the section break before
  REFERENCES is fully replaced with the article-2 text, tables, and figures;
* the Ukrainian metadata block (title, abstract, keywords, citation) is
  rewritten;
* the REFERENCES list and, critically, the ABOUT THE AUTHORS photo table are
  left untouched so the embedded author photos, headers/footers, odd/even
  header-footer settings, margins, and column/section structure are preserved.

Run:
    python build_second_article_docx.py
"""

from __future__ import annotations

import glob
import re
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

TEMPLATE = glob.glob("article_package/*final_v5.docx")[0]
OUTPUT = "article_package/Стаття_Аспірант_Синюк_HAIT_article2_v2.docx"
MANUSCRIPT_PATH = Path("article_package/second_article_manuscript.md")
FIG_DIR = Path("second_article_outputs/figures")
TABLES_DIR = Path("second_article_outputs/article_tables")

FONT = "Times New Roman"
COL_WIDTH_CM = 8.2
INDENT_CM = 0.75


# --------------------------------------------------------------------------- #
# low-level run / paragraph helpers
# --------------------------------------------------------------------------- #
def _set_run_font(run, size, bold=False, italic=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), FONT)


def rebuild_runs(par, specs):
    """Clear a paragraph's runs and add (text, bold, italic, size) specs."""
    for r in list(par.runs):
        r._element.getparent().remove(r._element)
    for text, bold, italic, size in specs:
        run = par.add_run(text)
        _set_run_font(run, size, bold, italic)


def set_text(par, text, size=None):
    if not par.runs:
        run = par.add_run(text)
        if size:
            _set_run_font(run, size)
        return
    par.runs[0].text = text
    for extra in list(par.runs[1:]):
        extra._element.getparent().remove(extra._element)


def find_par(doc, predicate):
    for p in doc.paragraphs:
        if predicate(p.text):
            return p
    raise LookupError("paragraph not found")


def para_after_heading(doc, heading_text):
    paras = doc.paragraphs
    for i, p in enumerate(paras):
        if p.text.strip() == heading_text:
            for q in paras[i + 1:]:
                if q.text.strip():
                    return q
    raise LookupError(f"no paragraph after heading {heading_text!r}")


# --------------------------------------------------------------------------- #
# body-block insertion (everything is inserted immediately before ``anchor``)
# --------------------------------------------------------------------------- #
def add_section_heading(anchor, text):
    p = anchor.insert_paragraph_before()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.0
    pf.keep_with_next = True
    run = p.add_run(text.upper())
    _set_run_font(run, 11, bold=True)
    return p


def add_subheading(anchor, text):
    p = anchor.insert_paragraph_before()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.first_line_indent = Cm(INDENT_CM)
    pf.space_before = Pt(3)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.0
    pf.keep_with_next = True
    run = p.add_run(text)
    _set_run_font(run, 11, bold=True, italic=True)
    return p


def add_body(anchor, text):
    p = anchor.insert_paragraph_before()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.first_line_indent = Cm(INDENT_CM)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0
    run = p.add_run(text)
    _set_run_font(run, 11)
    return p


def add_numbered(anchor, items):
    for i, item in enumerate(items, start=1):
        p = anchor.insert_paragraph_before()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf = p.paragraph_format
        pf.first_line_indent = Cm(INDENT_CM)
        pf.line_spacing = 1.0
        run = p.add_run(f"{i}. {item}")
        _set_run_font(run, 11)


def add_figure(anchor, image_path, caption_num, caption_title, source="compiled by the authors"):
    p = anchor.insert_paragraph_before()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(str(image_path), width=Cm(COL_WIDTH_CM))

    cap = anchor.insert_paragraph_before()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.first_line_indent = Cm(0)
    cap.paragraph_format.keep_with_next = True
    r1 = cap.add_run(f"Fig. {caption_num}. ")
    _set_run_font(r1, 11, italic=True)
    r2 = cap.add_run(caption_title)
    _set_run_font(r2, 11, bold=True)

    src = anchor.insert_paragraph_before()
    src.alignment = WD_ALIGN_PARAGRAPH.CENTER
    src.paragraph_format.first_line_indent = Cm(0)
    src.paragraph_format.space_after = Pt(6)
    rs = src.add_run(f"Source: {source}")
    _set_run_font(rs, 8, bold=True, italic=True)


def add_table(doc, anchor, table_num, title, df, source="compiled by the authors"):
    if table_num in {1, 2, 4}:
        column_break = anchor.insert_paragraph_before()
        column_break.paragraph_format.first_line_indent = Cm(0)
        column_break.add_run().add_break(WD_BREAK.COLUMN)

    # Title above the table.
    tp = anchor.insert_paragraph_before()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tp.paragraph_format.first_line_indent = Cm(0)
    tp.paragraph_format.space_before = Pt(6)
    tp.paragraph_format.keep_with_next = True
    r1 = tp.add_run(f"Table {table_num}. ")
    _set_run_font(r1, 11, italic=True)
    r2 = tp.add_run(title)
    _set_run_font(r2, 11, bold=True)

    n_cols = len(df.columns)
    table = doc.add_table(rows=1, cols=n_cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.allow_autofit = False

    custom_widths = {
        1: [2.8, 2.7, 2.7],
        2: [1.6, 3.6, 3.0],
        3: [2.0, 0.8, 2.2, 3.2],
        4: [1.5, 1.5, 3.3, 1.9],
        5: [2.5, 2.0, 1.7, 2.0],
        6: [2.2, 1.5, 1.9, 2.6],
    }
    if table_num in custom_widths and len(custom_widths[table_num]) == n_cols:
        widths = [Cm(value) for value in custom_widths[table_num]]
    elif n_cols == 1:
        widths = [Cm(COL_WIDTH_CM)]
    else:
        label_w = min(2.8, COL_WIDTH_CM / n_cols + 1.0)
        rest = (COL_WIDTH_CM - label_w) / (n_cols - 1)
        widths = [Cm(label_w)] + [Cm(rest)] * (n_cols - 1)

    hdr = table.rows[0].cells
    for j, col in enumerate(df.columns):
        hdr[j].text = ""
        run = hdr[j].paragraphs[0].add_run(str(col))
        _set_run_font(run, 11, bold=True)
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for j, col in enumerate(df.columns):
            cells[j].text = ""
            run = cells[j].paragraphs[0].add_run(str(row[col]))
            _set_run_font(run, 11)
    for row in table.rows:
        for j, cell in enumerate(row.cells):
            cell.width = widths[j]
    for j, column in enumerate(table.columns):
        column.width = widths[j]
    # Move the appended table to just before the anchor.
    anchor._p.addprevious(table._tbl)

    # Source line below the table.
    src = anchor.insert_paragraph_before()
    src.alignment = WD_ALIGN_PARAGRAPH.CENTER
    src.paragraph_format.first_line_indent = Cm(0)
    src.paragraph_format.space_after = Pt(6)
    rs = src.add_run(f"Source: {source}")
    _set_run_font(rs, 8, bold=True, italic=True)


# --------------------------------------------------------------------------- #
# content
# --------------------------------------------------------------------------- #
TITLE = ("Validation, robustness, and reliability of a markerless "
         "video-based golf-stick motion analysis")

ABSTRACT = (
    "Markerless video analysis is an attractive alternative to marker-based motion capture for "
    "golf-swing assessment because it works with ordinary cameras, yet the measurements it produces "
    "are rarely validated against an independent reference, and their robustness to real recording "
    "conditions is seldom quantified. The aim of this study is to evaluate the accuracy, robustness, "
    "and reliability of a previously described markerless video-based golf-stick motion-analysis "
    "workflow under heterogeneous recording conditions and controlled input perturbations. A reference "
    "subset of twenty-five sessions was drawn from seventy-one processed recordings by stratified "
    "sampling across camera viewpoint, frame rate, resolution, and quality grade. For each session a "
    "single annotator manually marked four swing events and about ten stick-tip control points, giving "
    "one hundred event annotations and two hundred sixty control points. Automatic event times were "
    "compared with the manual reference; geometric trajectory error was computed between processed and "
    "manually annotated stick-tip positions, with swing phase assigned from the manual events; metric "
    "sensitivity was measured under frame thinning, landmark dropout, coordinate jitter, scale "
    "perturbation, and combined degradation; and six processing variants were compared in a controlled "
    "ablation with a shared derivative definition. Event detection showed a large early bias of "
    "approximately one and seven tenths to two seconds and a median absolute error near one second, "
    "which is reported as an honest negative finding rather than as evidence of accurate timing. In "
    "contrast, stick-tip trajectory error was small over the reliably tracked backswing and downswing, "
    "with an overall median near fifteen pixels or about four centimetres, degrading only in the "
    "follow-through where tracking is lost. The smoothness index and path efficiency were the most "
    "stable metrics under perturbation and across sessions, whereas peak derivative and phase-duration "
    "metrics were highly unstable. The novelty of the work is a transparent, reference-based robustness "
    "characterization that separates trustworthy geometric measurements from unreliable event timing "
    "and exploratory derivative metrics. The practical value is a set of explicit recommendations that "
    "indicate which markerless golf-swing indicators can be used for cross-session comparison in "
    "sport-biomechanics research and virtual-reality training and which require controlled acquisition "
    "or external validation."
)

KEYWORDS = "markerless validation; golf swing; event detection; trajectory error; sensitivity analysis; metric robustness"

CITATION_EN = ('Syniuk I. M., Maksymov M. V., Maksymov O. M., Iyer K. "Validation, robustness, and '
               'reliability of a markerless video-based golf-stick motion analysis". Herald of Advanced '
               "Information Technology. - [Year]. - Vol. [..]. - No. [..]. - Pp. [..-..]. "
               "DOI: [assigned by editorial team]")

UA_TITLE = ("Валідація, робастність і надійність безмаркерного відеоаналізу руху ключки для гольфу "
            "за неоднорідних умов зйомки")

UA_ABSTRACT = (
    "Безмаркерний відеоаналіз є привабливою альтернативою маркерним системам захоплення руху для "
    "оцінювання гольф-свінгу, оскільки працює зі звичайними камерами, проте отримані вимірювання рідко "
    "перевіряють щодо незалежного еталона, а їхню стійкість до реальних умов зйомки майже не оцінюють "
    "кількісно. Метою дослідження є оцінювання точності, робастності та надійності раніше описаного "
    "безмаркерного відеопайплайну аналізу руху ключки для гольфу за неоднорідних умов зйомки та "
    "контрольованих збурень вхідних даних. Еталонну підмножину з двадцяти п’яти сесій було відібрано "
    "із сімдесяти однієї опрацьованої сесії стратифікованою вибіркою за ракурсом камери, частотою "
    "кадрів, роздільною здатністю та класом якості. Для кожної сесії один анотатор вручну позначив "
    "чотири події свінгу та близько десяти контрольних точок кінця ключки, що дало сто анотацій подій "
    "і двісті шістдесят контрольних точок. Автоматичні часи подій порівнювали з ручним еталоном; "
    "геометричну похибку траєкторії обчислювали між опрацьованими та вручну позначеними положеннями "
    "кінця ключки, а фазу свінгу визначали за ручними подіями; чутливість метрик вимірювали за "
    "проріджування кадрів, випадання орієнтирів, координатного шуму, збурення масштабу та комбінованої "
    "деградації; шість варіантів обробки порівнювали в контрольованій абляції зі спільним визначенням "
    "похідних. Виявлення подій показало велике раннє зміщення приблизно від однієї цілої семи десятих "
    "до двох секунд і медіанну абсолютну похибку близько однієї секунди, що подано як чесний негативний "
    "результат, а не як свідчення точного хронометражу. Натомість похибка траєкторії кінця ключки була "
    "малою на надійно відстежуваних фазах бек- та даун-свінгу з медіаною близько п’ятнадцяти пікселів, "
    "або близько чотирьох сантиметрів, і зростала лише на фазі супроводу, де відстеження втрачається. "
    "Індекс плавності та ефективність траєкторії були найстабільнішими метриками за збурень і між "
    "сесіями, тоді як пікові похідні та метрики тривалості фаз були вкрай нестабільними. Новизна роботи "
    "полягає у прозорому оцінюванні робастності на основі еталона, що відокремлює достовірні геометричні "
    "вимірювання від ненадійного хронометражу подій та дослідницьких похідних метрик. Практична цінність "
    "— набір явних рекомендацій, які показники безмаркерного гольф-свінгу можна використовувати для "
    "міжсесійного порівняння у спортивній біомеханіці та тренуваннях віртуальної реальності, а які "
    "потребують контрольованої зйомки або зовнішньої валідації."
)

UA_KEYWORDS = ("валідація безмаркерних систем; гольф-свінг; виявлення подій; похибка траєкторії; "
               "аналіз чутливості; робастність метрик")

CITATION_UA = ('Синюк І. М., Максимов М. В., Максимов О. М., Айєр К. «Валідація, робастність і надійність '
               'безмаркерного відеоаналізу руху ключки для гольфу». Herald of Advanced Information '
               "Technology. - [Рік]. - Т. [..]. - № [..]. - С. [..-..]. DOI: [призначається редакцією]")

INTRO = [
    "Quantitative assessment of the golf swing supports coaching, rehabilitation, talent development, and virtual-reality training analytics. Marker-based optical motion capture provides high spatial accuracy, but it requires calibrated laboratory space, synchronized cameras, reflective markers, and trained operators, which restricts repeated field use and reduces ecological validity [1], [2]. Markerless computer-vision methods lower this barrier by estimating body and object landmarks from ordinary video, so a single smartphone recording can in principle yield stick speed, swing tempo, phase timing, and movement-quality indicators [3], [4], [5].",
    "The convenience of markerless capture, however, does not by itself guarantee measurement validity. Monocular landmark trajectories are affected by frame-to-frame noise, missed detections, motion blur, occlusion, and apparent scale change caused by camera geometry, and differentiation amplifies these errors when speed, acceleration, jerk, and angular velocity are computed [6], [7]. A companion methodological study introduced a reproducible processing workflow that combines running median pre-filtering, a confidence-aware constant-velocity Kalman filter, Rauch-Tung-Striebel backward smoothing, trajectory despiking, bounded polynomial smoothing, and dynamic scale calibration, and it reported session-level repeatability together with diagnostic validation, sensitivity, and ablation blocks. Those diagnostics were deliberately framed as preliminary because they were not compared against an independent reference.",
    "The open problem is therefore not the design of the pipeline but its evaluation. Before markerless swing metrics can be used for cross-session comparison, three questions must be answered with evidence: how accurately the workflow locates swing events in time, how closely the processed stick-tip trajectory matches manually annotated positions, and how stable the exported metrics remain when realistic degradations affect the input. The present study addresses these questions directly by constructing a manually annotated reference subset and using it to quantify accuracy, robustness, and reliability. A distinctive feature of the study is that it reports a clear negative finding for event timing alongside encouraging geometric-trajectory results, so that the workflow is characterized honestly rather than promoted uncritically. The overall study design is shown in Fig. 1.",
]

LITREVIEW = [
    "Kinematic analysis has long been central to sports biomechanics, describing movement timing, segment coordination, implement speed, and movement smoothness [1], [2], [8]. In golf, relevant indicators include stick speed, swing tempo, kinematic sequencing, and impact timing [9], [10], [11], [23]. These indicators are traditionally obtained with marker-based systems or, for portable field instrumentation, with wearable inertial sensors [24]; both are more cumbersome than ordinary video for routine use.",
    "Deep-learning pose estimators such as OpenPose, BlazePose, and MediaPipe made markerless analysis practical with ordinary cameras and near-real-time inference [3], [4], [5], [25], [29]. Their accuracy nonetheless depends on camera view, lighting, motion blur, occlusion, and model confidence, and validation studies consistently warn that two-dimensional monocular projections cannot fully replace calibrated three-dimensional systems [12], [13], [26], [27], [28]. This literature establishes that a markerless workflow must be validated against an explicit reference before its measurements are trusted, and that reported error should be interpreted with respect to the specific capture conditions.",
    "Signal conditioning is a second recurring theme. Median filtering suppresses impulse outliers [14]; Kalman filtering combines a dynamic model with noisy measurements to produce a recursive state estimate [15], [16]; and, when offline analysis is acceptable, Rauch-Tung-Striebel smoothing refines earlier estimates using later observations [17]. Polynomial smoothing of the Savitzky-Golay type reduces derivative noise while preserving local shape [18], and jerk-based smoothness metrics are widely used but must be interpreted cautiously because differentiation amplifies noise [19]. For measurement reliability, coefficient of variation, repeatability coefficient, intraclass correlation, and Bland-Altman limits of agreement are the standard tools [20], [21], [22].",
    "Despite this background, most markerless golf-swing reports emphasize plausible trajectories and pipeline design rather than reference-based error. Three gaps remain. First, event-timing accuracy is rarely quantified against manually verified frames. Second, geometric trajectory error is rarely measured against per-frame stick-tip annotations, because no such reference normally exists. Third, metric robustness under realistic degradations, and the resulting distinction between trustworthy and exploratory metrics, is rarely reported. The problem addressed in this article is to close these gaps for the described workflow by building a manual reference subset and using it to quantify event accuracy, trajectory accuracy, sensitivity, and reliability, and then to classify each exported metric by its practical usability.",
]

AIM = "The aim of the research is to evaluate the accuracy, robustness, and reliability of a markerless video-based golf-stick motion-analysis workflow under heterogeneous recording conditions and controlled input perturbations."

OBJECTIVES = [
    "To construct a manually annotated reference subset of swing events and stick-tip control points from a heterogeneous corpus of processed sessions.",
    "To quantify event-detection accuracy for top of backswing, downswing transition, and impact against the manual reference.",
    "To estimate geometric stick-tip trajectory error between the processed trajectory and manually annotated points, resolved by swing phase.",
    "To evaluate the sensitivity of exported metrics to frame thinning, landmark dropout, coordinate jitter, scale perturbation, and combined degradation.",
    "To compare processing variants through a controlled ablation with a shared derivative definition and time base.",
    "To identify which kinematic and movement-quality metrics are robust enough for cross-session comparison and to formulate practical recommendations for their use.",
]

METHODS = {
    "Dataset and reference subset": "The corpus comprises seventy-one markerless golf-swing sessions processed with the scientific filtering profile of the workflow described in the companion methodological study. The recordings are heterogeneous: the frame-rate range is 23.98 to 60.00 frames per second, resolution ranges from below 720 p to 1080 p and above, and camera viewpoint is predominantly down-the-line with a minority of face-on recordings. To obtain a manageable yet representative reference set, twenty-five sessions were selected by stratified sampling across viewpoint, frame-rate bucket, resolution bucket, capture-speed class, and a coarse quality grade that counts the number of adverse tags (keyframe issue, motion blur, occlusion). The stratification balances easy and difficult recordings so that reported error is not dominated by a single favourable condition. Dataset and subset characteristics are summarized in Table 1.",
    "Manual annotation protocol": "Because the corpus contains no per-frame stick-tip ground truth and its automatic keyframes are unreliable, a manual reference was created. A frame-by-frame annotation tool built on an image viewer was used to step through each selected video and record, in original video pixel coordinates, four swing events (address, top of backswing, downswing transition, and impact) and a set of stick-tip control points distributed along the visible swing arc. Clicks were captured at full resolution even when the display was downscaled, so the reference is independent of display size. A single annotator produced one annotation round, yielding one hundred event annotations and two hundred sixty stick-tip control points across the twenty-five sessions, with eight to fourteen points per session. The protocol is summarized in Table 2. A schematic annotated frame is shown in Fig. 2; a drawn schematic is used instead of a real user frame to avoid consent and privacy concerns.",
    "Automatic processing": "Each session was processed with the unmodified scientific profile of the workflow. The processing chain converts normalized landmarks to pixel coordinates, applies a running median filter, a confidence-aware constant-velocity Kalman filter with innovation gating, Rauch-Tung-Striebel smoothing, trajectory despiking, and bounded polynomial smoothing, and derives a per-frame pixel-to-metre scale from the detected stick length. Automatic swing events and the final smoothed stick-tip trajectory were exported for comparison with the manual reference. The pipeline itself is not re-derived here; it is the object under evaluation.",
    "Event validation": "For each session, automatic event times were compared with the manual reference times for top of backswing, downswing transition, and impact. Signed and absolute errors were computed in both milliseconds and frames. Reported statistics are the mean signed error, the median absolute error, the ninety-fifth percentile absolute error, and Bland-Altman bias and ninety-five-percent limits of agreement [22]. The signed error is defined as automatic minus reference, so a negative value indicates that the automatic event fires early.",
    "Trajectory validation": "For each manually annotated control point, the processed stick-tip position at the matching frame was retrieved and the Euclidean error was computed in pixels, in image-diagonal-normalized units, and in metres using the per-frame scale. Each point was assigned to a swing phase (backswing, transition, downswing, impact region, or follow-through) using the manual event times rather than the automatic ones, because the automatic events are biased early and would misclassify most points. Errors were summarized per phase and overall by median, upper quartile, and ninety-fifth percentile.",
    "Sensitivity analysis": "Robustness was assessed by perturbing the input of each of the seventy-one sessions and re-processing it with the same profile. Twelve scenarios were applied: frame thinning by factors of two and three; landmark dropout at five, ten, and twenty percent; zero-mean Gaussian coordinate jitter at normalized standard deviations of 0.004 and 0.008 applied to the stick landmarks; scale perturbation of plus or minus five and ten percent; and a combined degradation that stacks frame thinning, ten-percent dropout, and jitter. For each scenario and metric the signed change, percentage change, and median absolute percentage change relative to the unperturbed baseline were computed, together with a rank-stability coefficient. Metrics were classified as robust, usable, or exploratory when the median absolute change was below ten percent, below twenty-five percent, or above twenty-five percent respectively.",
    "Ablation study": "Six processing variants were reconstructed from the same raw landmarks: raw, median only, Kalman only, Kalman plus RTS, Kalman plus RTS plus despiking, and the full pipeline. To avoid the inconsistency of the earlier diagnostic ablation, all derivative metrics were computed from each variant's final trajectory with one shared derivative function and one time base. For the standalone Kalman-plus-RTS variant the textbook smoother with the process-noise term in the predicted covariance was used, because the production smoother omits that term and relies on a downstream deviation clamp that is absent when the variant is isolated; the production code was left unchanged. Reported per-variant statistics include median deviation from the raw trajectory, median root-mean-square jerk, and the median smoothness index, path efficiency, and maximum speed.",
    "Reliability and statistical analysis": "Cross-session dispersion of eleven exported metrics was summarized by the coefficient of variation and the repeatability coefficient. Because athlete and trial grouping are not encoded in the anonymized export, these statistics describe between-session heterogeneity of the corpus and are not interpreted as within-athlete test-retest repeatability; an intraclass-correlation path is provided in the analysis code for future data with explicit grouping [20], [21]. Agreement between the full pipeline and the Kalman-plus-RTS-plus-despiking variant was additionally summarized with Bland-Altman bias and limits of agreement [22]. A metric robustness ranking combined the sensitivity classification with the cross-session coefficient of variation to assign each metric to a recommended-use category.",
}

RESULTS = {
    "Reference subset": ["All seventy-one sessions processed successfully, and the twenty-five-session reference subset preserved the heterogeneity of the full corpus across viewpoint, frame rate, resolution, and quality grade (Table 1). The manual annotation produced one hundred event annotations and two hundred sixty stick-tip control points (Table 2), which is, to our knowledge, the first per-frame stick-tip reference for this workflow."],
    "Event-timing accuracy": ["Event detection was inaccurate. The median absolute timing error was 817 ms for impact, 920 ms for top of backswing, and 1000 ms for downswing transition, and the ninety-fifth percentile absolute error exceeded 4.7 s for every event (Table 3; Fig. 3). The errors were strongly biased: the mean signed error was -1730 ms for impact, -1914 ms for top of backswing, and -1987 ms for downswing transition, so the automatic events fire roughly one and seven tenths to two seconds early. The Bland-Altman plots confirm a large negative bias with wide limits of agreement that broaden as swing duration increases (Fig. 4). These values are far larger than a normal golf swing and are reported as a negative finding: the current automatic event detector requires recalibration before any timing-based claim can be made."],
    "Trajectory accuracy": ["Geometric trajectory error was, in contrast, small over the reliably tracked phases. The overall median stick-tip error was 14.9 px, corresponding to about 3.8 cm, with an upper quartile of 27.2 px (Table 4). Error was lowest in the backswing (median 12.7 px, about 3.1 cm) and downswing (median 14.5 px, about 4.2 cm) and increased in the impact region and follow-through (medians near 19 px). The ninety-fifth-percentile values are inflated by a small number of sessions in which tracking is lost after impact, which is visible as large whiskers for the downswing and follow-through phases (Fig. 5). The combination of accurate stick-tip positions with grossly inaccurate event timing indicates that the geometric trajectory is trustworthy where the tip is tracked, while the temporal segmentation is not."],
    "Sensitivity": ["Metric sensitivity varied by orders of magnitude across metrics (Table 5; Fig. 6). Scale perturbation had a small and predictable effect on most metrics, with a median absolute change of one percent or less for the smoothness index and path efficiency. The smoothness index was the most stable metric under every perturbation family, with a median absolute change of about 14 percent under frame thinning, 12 percent under landmark dropout, 12 percent under jitter, and 14 percent under combined degradation. Path efficiency was the next most stable. In sharp contrast, peak derivative metrics and phase-duration metrics were highly unstable: maximum acceleration, maximum angular velocity, curvature RMS, swing tempo, and backswing peak speed frequently changed by more than 60 percent, and backswing peak speed changed by several hundred percent under jitter and combined degradation. Rank stability followed the same pattern, remaining moderate for the smoothness index and path efficiency and collapsing for the derivative metrics [30]."],
    "Ablation": ["The controlled ablation showed the expected monotone reduction of jerk along the filtering chain when metrics are computed consistently (Table 6; Fig. 7). Median root-mean-square jerk fell from about 17300 for raw landmarks to about 4600 for the Kalman-plus-RTS variant, while the smoothness index rose correspondingly. The full pipeline deviated from the raw trajectory by a median of only about 2.3 cm, much less than the intermediate variants, because its bounded polynomial smoothing and scale handling keep the final trajectory close to the observed path while still suppressing jerk relative to raw. These results confirm that each stage contributes to trajectory regularization and that the differences between variants are consistent once a shared derivative definition is used."],
    "Metric robustness ranking": ["Combining the sensitivity classification with cross-session dispersion produced a clear ranking (Table 7; Fig. 8). The smoothness index was robust in all twelve perturbation scenarios and had the lowest cross-session coefficient of variation (about 22 percent); it is recommended as robust under heterogeneous capture. Path efficiency was robust or usable in most scenarios (coefficient of variation about 36 percent) and is recommended as usable with controlled acquisition. All remaining metrics, including maximum speed, maximum acceleration, maximum angular velocity, curvature RMS, swing tempo, and the peak-speed and phase-duration metrics, were exploratory, with median changes above 25 percent and cross-session coefficients of variation above 100 percent; they should not be used for cross-session comparison without controlled acquisition and external validation."],
}

DISCUSSION = [
    "The results give a differentiated picture of what the markerless workflow can and cannot measure. The strongest positive finding is geometric: where the stick tip is tracked, the processed trajectory lies within about four centimetres of manually annotated positions during the backswing and downswing, the phases that matter most for swing-path assessment. This is a meaningful accuracy level for coaching feedback and virtual-reality training, and it is supported by an explicit per-frame reference rather than by visual plausibility alone.",
    "The strongest negative finding is temporal. Automatic event detection is biased early by roughly one and seven tenths to two seconds, with median absolute errors near one second and very wide limits of agreement. This is far too large for any timing-dependent metric, and it explains why phase-duration and tempo metrics were among the least reliable. The early bias also motivates the decision to classify trajectory points by manual rather than automatic events: had the automatic events been used, most points would have been misassigned to the follow-through and the trajectory result would have been distorted. Reporting this bias openly is more useful than suppressing it, because it identifies event detection as the single component most in need of recalibration.",
    "The robustness analysis reconciles these findings with the earlier repeatability observations. Global movement-quality metrics, the smoothness index and path efficiency, are stable both under controlled perturbation and across heterogeneous sessions, whereas peak derivative metrics are dominated by noise that differentiation amplifies [6], [7], [19]. Scale perturbation behaves predictably, confirming that the pixel-to-metre calibration propagates linearly and does not introduce nonlinear artefacts, while frame thinning, dropout, and jitter degrade derivative metrics most, consistent with the hypothesis that temporal and high-frequency information is the first to be lost under degradation. These patterns agree with the broader markerless-validation literature, which reports that two-dimensional monocular estimates are usable for global and low-order measures but unreliable for fine temporal and high-order kinematics without controlled capture [12], [13], [26], [27], [28].",
    "These findings translate into concrete guidance for virtual-reality training and coaching applications. A virtual-reality feedback system built on this workflow should present the smoothness index and path efficiency as primary swing-quality indicators, because they remain comparable across sessions recorded on different devices and under different conditions, and it should display stick-tip trajectory overlays for the backswing and downswing, where geometric error is small enough to be visually faithful. Conversely, timing-dependent cues such as tempo, phase durations, and event markers should be withheld or clearly flagged as approximate until event detection is recalibrated, and peak speed and acceleration values should be shown only as within-session trends rather than as absolute measurements to be compared between athletes or sessions. This selective presentation lets a training system exploit the parts of the workflow that are trustworthy while avoiding feedback that the present evidence cannot support.",
    "Several limitations bound these conclusions. The reference was produced by a single annotator in one round, so inter-annotator reliability is not yet available; the analysis code already supports a second round and intraclass-correlation computation for future work. The corpus lacks athlete and trial grouping, so reliability is expressed as cross-session dispersion rather than test-retest repeatability. The system is monocular and two-dimensional, so out-of-plane motion and perspective distortion remain unresolved, and the metric error in metres depends on the stick-length scale assumption. Finally, the trajectory reference covers control points rather than every frame, and follow-through tracking is unreliable. None of these limitations affects the two central, reference-based conclusions: the trajectory is accurate where tracked, and the event timing is not.",
]

CONCLUSIONS = [
    "This study evaluated a markerless video-based golf-stick motion-analysis workflow against a purpose-built manual reference and under controlled perturbations, converting the earlier diagnostic checks into a reference-based validation. A stratified twenty-five-session subset was annotated with one hundred swing events and two hundred sixty stick-tip control points and used to quantify event-timing accuracy, geometric trajectory accuracy, metric sensitivity, ablation consistency, and cross-session reliability.",
    "The evaluation shows that the workflow measures stick-tip geometry accurately where the tip is tracked, with an overall median trajectory error of about four centimetres and best performance in the backswing and downswing, but that its automatic event detection is biased early by roughly one and seven tenths to two seconds and is not yet usable for timing. Among exported metrics, the smoothness index is robust under heterogeneous capture and path efficiency is usable with controlled acquisition, whereas peak derivative and phase-duration metrics remain exploratory.",
    "The scientific novelty is a transparent, reference-based characterization that separates trustworthy geometric measurements from unreliable event timing and exploratory derivative metrics, including an explicitly reported negative finding for event detection. The practical value is a concrete set of recommendations that tell practitioners which markerless golf-swing indicators to trust for cross-session comparison in sport biomechanics and virtual-reality training. Future work will recalibrate event detection, add a second annotator for inter-annotator reliability, and extend the reference with athlete and trial grouping to enable intraclass-correlation and test-retest analysis.",
]

ACK = "The authors thank the research supervisor and collaborators who supported the review of the manuscript and the development and evaluation of the motion-analysis workflow."


def _paragraphs(lines):
    paragraphs = []
    current = []
    for raw in lines:
        line = raw.strip().replace("`", "")
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if re.match(r"^\d+\.\s+", line):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            paragraphs.append(line)
        elif not line.startswith("---"):
            current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def _parse_manuscript(path):
    """Parse the canonical Markdown source into metadata and body sections."""
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata = {}
    current = None
    buffer = []
    body_start = None
    for idx, line in enumerate(lines):
        if line.strip() == "# BODY":
            if current:
                metadata[current] = _paragraphs(buffer)
            body_start = idx + 1
            break
        if line.startswith("## "):
            if current:
                metadata[current] = _paragraphs(buffer)
            current = line[3:].strip()
            buffer = []
        elif current:
            buffer.append(line)
    if body_start is None:
        raise ValueError(f"# BODY marker not found in {path}")

    body = {}
    section = None
    subsection = None
    buffer = []

    def flush():
        nonlocal buffer
        if section is None:
            buffer = []
            return
        paras = _paragraphs(buffer)
        target = body.setdefault(section, {"lead": [], "subsections": {}})
        if subsection is None:
            target["lead"].extend(paras)
        else:
            target["subsections"].setdefault(subsection, []).extend(paras)
        buffer = []

    for line in lines[body_start:]:
        if line.startswith("## "):
            flush()
            section = line[3:].strip()
            subsection = None
        elif line.startswith("### "):
            flush()
            subsection = line[4:].strip()
        else:
            buffer.append(line)
    flush()
    return metadata, body


_META, _BODY = _parse_manuscript(MANUSCRIPT_PATH)


def _meta(name):
    values = _META.get(name, [])
    if not values:
        raise KeyError(f"Missing manuscript metadata section: {name}")
    return " ".join(values)


# Override the legacy inline draft above. The Markdown file is the single
# content source used for every subsequent build.
TITLE = _meta("TITLE")
ABSTRACT = _meta("ABSTRACT")
KEYWORDS = _meta("KEYWORDS")
UA_TITLE = _meta("Ukrainian title")
UA_ABSTRACT = _meta("Ukrainian abstract")
UA_KEYWORDS = _meta("Ukrainian keywords")
CITATION_EN = re.sub(r"^For citation:\s*", "", _meta("For citation (English)"))
CITATION_UA = re.sub(r"^Для цитування:\s*", "", _meta("For citation (Ukrainian)"))

INTRO = _BODY["INTRODUCTION"]["lead"]
LITREVIEW = _BODY["LITERATURE REVIEW AND PROBLEM STATEMENT"]["lead"]
_aim_paras = _BODY["RESEARCH AIM AND OBJECTIVES"]["lead"]
AIM = _aim_paras[0]
OBJECTIVES = [
    re.sub(r"^\d+\.\s*", "", paragraph)
    for paragraph in _aim_paras
    if re.match(r"^\d+\.\s+", paragraph)
]
METHODS = _BODY["MATERIALS AND METHODS"]["subsections"]
RESULTS = _BODY["RESEARCH RESULTS"]["subsections"]
DISCUSSION = _BODY["DISCUSSION OF RESULTS"]["lead"]
CONCLUSIONS = _BODY["CONCLUSIONS"]["lead"]
ACK = " ".join(_BODY["ACKNOWLEDGMENTS"]["lead"])

FIGURES = {
    3: (FIG_DIR / "fig_event_frame_identity.png", "Automatic versus manually annotated event frames"),
    4: (FIG_DIR / "fig_trajectory_error_by_phase.png", "Session-level clubhead agreement by swing phase"),
    5: (FIG_DIR / "fig_sensitivity_metric_heatmap.png", "Metric response by perturbation family"),
    6: (FIG_DIR / "fig_ablation_jerk_reduction.png", "Root-mean-square jerk across production stages"),
}

TABLE_TITLES = {
    1: "Dataset and reference-subset characteristics",
    2: "Operational definitions of manually annotated events",
    3: "Event-frame agreement with the manual reference",
    4: "Clubhead localization agreement by swing phase",
    5: "Sensitivity and rank preservation of exported metrics",
    6: "Nested ablation of actual production stages",
    7: "Study-specific operational response tiers",
}


def load_table(n):
    files = {
        1: "table1_dataset_subset.csv",
        2: "table2_annotation_protocol.csv",
        3: "table3_event_timing.csv",
        4: "table4_trajectory_error.csv",
        5: "table5_sensitivity.csv",
        6: "table6_ablation.csv",
        7: "table7_robustness_ranking.csv",
    }
    return pd.read_csv(TABLES_DIR / files[n])


# --------------------------------------------------------------------------- #
def rewrite_first_page(doc):
    title_p = find_par(doc, lambda t: t.startswith("Markerless video-based golf-stick motion analysis using Kalman"))
    set_text(title_p, TITLE)

    abstract_p = para_after_heading(doc, "ABSTRACT")
    set_text(abstract_p, ABSTRACT)

    kw_p = find_par(doc, lambda t: t.startswith("Keywords:"))
    rebuild_runs(kw_p, [("Keywords: ", True, False, 9), (KEYWORDS, False, False, 9)])

    cite_p = find_par(doc, lambda t: t.startswith("For citation:"))
    rebuild_runs(cite_p, [("For citation: ", True, True, 8), (CITATION_EN, True, False, 8)])


def rewrite_ukrainian(doc):
    ua_title = find_par(doc, lambda t: t.startswith("Безмаркерний відеоаналіз руху ключки"))
    set_text(ua_title, UA_TITLE)

    ua_abs = para_after_heading(doc, "АНОТАЦІЯ")
    set_text(ua_abs, UA_ABSTRACT)

    ua_kw = find_par(doc, lambda t: t.startswith("Ключові слова:"))
    rebuild_runs(ua_kw, [("Ключові слова: ", True, False, 9), (UA_KEYWORDS, False, False, 9)])

    ua_cite = find_par(doc, lambda t: t.startswith("Для цитування:"))
    rebuild_runs(ua_cite, [("Для цитування: ", True, True, 8), (CITATION_UA, True, False, 8)])


def find_body_anchor(doc):
    paras = doc.paragraphs
    intro = None
    for i, p in enumerate(paras):
        if p.text.strip() == "INTRODUCTION":
            intro = p
            intro_i = i
            break
    if intro is None:
        raise LookupError("INTRODUCTION not found")
    for p in paras[intro_i + 1:]:
        if p._p.find(qn("w:pPr")) is not None and p._p.find(qn("w:pPr")).find(qn("w:sectPr")) is not None:
            return intro, p
    raise LookupError("section break after body not found")


def remove_old_body(doc, intro_p, anchor_p):
    body = doc.element.body
    removing = False
    to_remove = []
    for child in list(body.iterchildren()):
        if child is intro_p._p:
            removing = True
        if child is anchor_p._p:
            break
        if removing:
            to_remove.append(child)
    for el in to_remove:
        body.remove(el)


def build_body(doc, anchor):
    add_section_heading(anchor, "INTRODUCTION")
    for t in INTRO:
        add_body(anchor, t)
    add_figure(
        anchor,
        FIG_DIR / "fig_study_design.png",
        1,
        "Study design and evidence scope",
    )

    add_section_heading(anchor, "LITERATURE REVIEW AND PROBLEM STATEMENT")
    for t in LITREVIEW:
        add_body(anchor, t)

    add_section_heading(anchor, "RESEARCH AIM AND OBJECTIVES")
    add_body(anchor, AIM)
    add_body(anchor, "The research objectives are:")
    add_numbered(anchor, OBJECTIVES)

    add_section_heading(anchor, "MATERIALS AND METHODS")
    for sub, texts in METHODS.items():
        add_subheading(anchor, sub)
        for text in texts:
            add_body(anchor, text)
        if sub == "Dataset, sampling, and available metadata":
            add_table(doc, anchor, 1, TABLE_TITLES[1], load_table(1))
        elif sub == "Manual annotation protocol":
            add_table(doc, anchor, 2, TABLE_TITLES[2], load_table(2))
            add_figure(anchor, FIG_DIR / "fig_annotated_frame.png", 2,
                       "Operational event and selected-frame clubhead annotations")

    add_section_heading(anchor, "RESEARCH RESULTS")
    for sub, paras in RESULTS.items():
        add_subheading(anchor, sub)
        for t in paras:
            add_body(anchor, t)
        if sub == "Time-base audit and event disagreement":
            add_table(doc, anchor, 3, TABLE_TITLES[3], load_table(3))
            add_figure(anchor, *((FIGURES[3][0], 3, FIGURES[3][1])))
        elif sub == "Clubhead localization agreement and failure tail":
            add_table(
                doc,
                anchor,
                4,
                TABLE_TITLES[4],
                load_table(4),
                source="compiled by the authors; n_s - sessions; n_p - points",
            )
            add_figure(anchor, *((FIGURES[4][0], 4, FIGURES[4][1])))
        elif sub == "Perturbation sensitivity":
            add_table(doc, anchor, 5, TABLE_TITLES[5], load_table(5))
            add_figure(anchor, *((FIGURES[5][0], 5, FIGURES[5][1])))
        elif sub == "Production-stage ablation":
            add_table(doc, anchor, 6, TABLE_TITLES[6], load_table(6))
            add_figure(anchor, *((FIGURES[6][0], 6, FIGURES[6][1])))

    add_section_heading(anchor, "DISCUSSION OF RESULTS")
    for t in DISCUSSION:
        add_body(anchor, t)

    add_section_heading(anchor, "CONCLUSIONS")
    for t in CONCLUSIONS:
        add_body(anchor, t)

    add_section_heading(anchor, "ACKNOWLEDGMENTS")
    add_body(anchor, ACK)


def _reference_specs(number, authors, title, journal, details):
    return [
        (f"{number}. {authors} “{title}”. ", False, False, 11),
        (journal, False, True, 11),
        (f". {details}", False, False, 11),
    ]


def _format_reference_paragraph(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = paragraph.paragraph_format
    pf.first_line_indent = Cm(INDENT_CM)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0


def rewrite_references_and_declarations(doc):
    replacements = {
        "7. Challis": _reference_specs(
            7,
            "Davis, D. J. & Challis, J. H.",
            "Automatic segment filtering procedure for processing non-stationary signals",
            "Journal of Biomechanics",
            "2020; Vol. 101: 109619. DOI: https://doi.org/10.1016/j.jbiomech.2020.109619.",
        ),
        "24. Godfrey": _reference_specs(
            24,
            "Kim, S. E., Burket Koltsov, J. C., Richards, A. W., Zhou, J., "
            "Schadl, K., Ladd, A. L. & Rose, J.",
            "Validation of inertial measurement units for analyzing golf swing rotational biomechanics",
            "Sensors",
            "2023; Vol. 23, No. 20: 8433. DOI: https://doi.org/10.3390/s23208433.",
        ),
        "30. Sweeting": _reference_specs(
            30,
            "Ingwersen, C. K., Nørtoft Jensen, J., Rieger Hannemose, M. & "
            "Bjorholm Dahl, A.",
            "Evaluating current state of monocular 3D pose models for golf",
            "Proceedings of the Northern Lights Deep Learning Workshop",
            "2023; Vol. 4. DOI: https://doi.org/10.7557/18.6793.",
        ),
    }
    for prefix, specs in replacements.items():
        paragraph = find_par(doc, lambda text, p=prefix: text.startswith(p))
        rebuild_runs(paragraph, specs)
        _format_reference_paragraph(paragraph)

    conflict = find_par(doc, lambda text: text.startswith("Conflicts of Interest:"))
    new_references = [
        _reference_specs(
            31,
            "Yamamoto, K., Hasegawa, Y., Suzuki, T., Suzuki, H., Tanabe, H. & Fujii, K.",
            "Extracting proficiency differences and individual characteristics in golfers' "
            "swing using single-video markerless motion analysis",
            "Frontiers in Sports and Active Living",
            "2023; Vol. 5: 1272038. DOI: https://doi.org/10.3389/fspor.2023.1272038.",
        ),
        _reference_specs(
            32,
            "Syniuk, I. M., Maksymov, M. V., Maksymov, O. M. & Iyer, K.",
            "Markerless video-based golf-stick motion analysis using Kalman filtering "
            "and RTS smoothing",
            "Unpublished manuscript",
            "2026.",
        ),
    ]
    for specs in new_references:
        paragraph = conflict.insert_paragraph_before()
        rebuild_runs(paragraph, specs)
        _format_reference_paragraph(paragraph)

    ai_statement = find_par(
        doc, lambda text: text.startswith("Use of generative AI tools:")
    )

    def insert_statement(text):
        paragraph = ai_statement.insert_paragraph_before()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.0
        run = paragraph.add_run(text)
        _set_run_font(run, 11)

    insert_statement(
        "Ethics and consent: The available project export did not contain source, "
        "consent, waiver, or ethics-committee documentation. No participant image is "
        "reproduced. The manuscript must not be submitted until the authors and "
        "institution verify lawful scientific use, de-identification, and the "
        "applicable ethics decision."
    )
    insert_statement(
        "Data availability: Analysis code, derived aggregate tables, and de-identified "
        "session-level outputs can be made available subject to institutional approval. "
        "Source videos are not publicly released because provenance and participant-use "
        "permissions require verification."
    )
    set_text(
        ai_statement,
        "Use of generative AI tools: AI-assisted language revision, consistency checking, "
        "and code review were performed with GPT-5.6 Sol in Cursor on 28 July 2026. "
        "The authors reviewed the resulting text and remain responsible for the data, "
        "methods, interpretation, references, and final manuscript.",
        size=11,
    )


def remove_missing_photo_placeholders(doc):
    """Clear literal photo prompts without rebuilding the author table."""
    if not doc.tables:
        return
    author_table = doc.tables[-1]
    for row in author_table.rows:
        photo_cell = row.cells[0]
        if photo_cell.text.strip().startswith("[3×4 cm color photo]"):
            # These cells contain no drawing; editing them in place preserves every
            # embedded photograph in the other author rows.
            if not photo_cell._tc.xpath(".//w:drawing"):
                photo_cell.text = ""


def main():
    import shutil

    shutil.copyfile(TEMPLATE, OUTPUT)
    doc = Document(OUTPUT)

    rewrite_first_page(doc)
    intro_p, anchor_p = find_body_anchor(doc)
    remove_old_body(doc, intro_p, anchor_p)
    build_body(doc, anchor_p)
    rewrite_ukrainian(doc)
    rewrite_references_and_declarations(doc)
    remove_missing_photo_placeholders(doc)

    doc.save(OUTPUT)
    print(f"saved {OUTPUT}")


if __name__ == "__main__":
    main()
