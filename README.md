# VR Motion Analysis

Python/OpenCV project for markerless golf-stick motion analysis from preprocessed MediaPipe-style landmark data and video. The code loads a swing session, tracks the golf-stick tip, filters/smooths the trajectory, computes kinematic and biomechanical metrics, displays an annotated playback, and exports CSV/figure outputs used for research articles.

## What The Project Does

- Loads per-session inputs: `mediapipe_data_full.json` and `video_processed.mp4`.
- Draws body landmarks, golf-stick landmarks, ball/impact cues, trajectories, and metric overlays.
- Tracks stick-tip motion using a filtering pipeline:
  - running median pre-filter;
  - 2D constant-velocity Kalman filtering;
  - RTS backward smoothing for offline/scientific analysis;
  - trajectory despiking and bounded polynomial smoothing;
  - dynamic pixel-to-metre scale calibration from detected stick length.
- Computes metrics such as speed, angular velocity, acceleration, jerk, phase timing, smoothness index, path efficiency, curvature, X-factor, wrist angle, and arc radius.
- Generates research outputs for manuscript preparation: CSV summaries, validation/sensitivity/ablation diagnostics, and PNG figures.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `main.py` | Interactive video analysis/player. Exports `swing_analysis.csv`. |
| `swing_analyzer.py` | Core frame-by-frame analysis, filtering chain, metrics, and final CSV rows. |
| `loader.py` | Loads a session folder containing `mediapipe_data_full.json` and `video_processed.mp4`. |
| `config.py` | Colors, physical constants, filter profiles, and `set_filter_profile()`. |
| `analysis.py` | Kinematic helpers, angles, impact selection, running median utilities. |
| `kalman.py` | 2D constant-velocity Kalman filter. |
| `rts_smoother.py` | Rauch-Tung-Striebel smoothing. |
| `utils_filter.py` | Median filter, trajectory smoothing, despiking, physical plausibility helpers. |
| `drawing.py` | OpenCV drawing for body, stick, ball, and trajectory overlays. |
| `stats_overlay.py` | On-frame metric/HUD overlay. |
| `batch_article_evaluation.py` | Batch processing for article CSVs and figures across many sessions. |
| `evaluate_filters.py` | Quick raw-vs-filtered trajectory deviation/jerk checks from `swing_analysis.csv`. |
| `parameter_sweep.py` | Parameter sweep for filter settings and Pareto-style comparison CSVs. |
| `visualize.py` | Plots exported `swing_analysis.csv`. |
| `article_package/` | Manuscript drafts, final DOCX candidates, article figures, evaluation outputs, and second-article plan. |
| `paper_assets/` | Supporting article/media assets. |

## Session Data Format

A session folder should contain:

```text
session_folder/
  mediapipe_data_full.json
  video_processed.mp4
```

`mediapipe_data_full.json` is expected to contain a top-level `values` array. Each frame contains landmark data used by `SwingAnalyzer`.

Batch processing expects a dataset root with multiple subfolders in that same layout.

## Main Commands

Run commands from the repository root.

### Interactive Analysis

```powershell
python main.py --folder "path\to\session" --profile scientific
```

If `--folder` is omitted, a folder picker opens.

Profiles:

- `scientific`: stronger smoothing and stricter constraints for offline analysis/export quality.
- `realtime`: lower latency and closer-to-raw trajectory behavior.

Keyboard controls in the OpenCV window:

- `Space`: pause/resume.
- `R`: restart with `realtime` profile.
- `S`: restart with `scientific` profile.
- `Esc`: exit.

Output:

- `swing_analysis.csv` in the current working directory.

### Batch Article Evaluation

```powershell
python batch_article_evaluation.py --dataset-root "path\to\dataset_root" --out-dir "article_package\evaluation_outputs"
```

Useful options:

```powershell
python batch_article_evaluation.py --dataset-root "path\to\dataset_root" --limit 10
python batch_article_evaluation.py --dataset-root "path\to\dataset_root" --skip-sensitivity
python batch_article_evaluation.py --dataset-root "path\to\dataset_root" --skip-ablation
```

Typical outputs:

- `dataset_summary.csv`
- `validation_keyframe_errors.csv`
- `sensitivity_results.csv`
- `ablation_results.csv`
- `repeatability_repeatability.csv`
- `trajectory_deviation_summary.csv`
- `batch_evaluation_summary.md`
- `figures/*.png`

### Visualize CSV Output

```powershell
python visualize.py --csv swing_analysis.csv
```

### Raw vs Filtered QA

```powershell
python evaluate_filters.py
```

Expects `swing_analysis.csv` in the working directory.

### Filter Parameter Sweep

```powershell
python parameter_sweep.py --folder "path\to\session"
```

Produces sweep CSVs such as `sweep_results.csv` and `sweep_pareto.csv`.

## Filter Profiles And Configuration

`config.py` defines project constants and filter profiles. The active profile can be selected by:

- `--profile realtime|scientific` for `main.py`;
- calling `config.set_filter_profile(...)`;
- environment variable `VR_MOTION_FILTER_PROFILE`.

Important: `config.set_filter_profile()` mutates module-level constants. Be careful when running multiple analyses in the same Python process.

## Research Article Assets

The `article_package/` directory contains manuscript materials and generated figures. Important files include:

- final HAIT candidate with figures: `Стаття_Аспірант_Синюк_HAIT_aligned_final_with_figures_wordsafe.docx`;
- second article planning prompt: `second_article_plan_and_prompt.md`;
- generated evaluation outputs: `evaluation_outputs/`;
- generated article figures: `evaluation_outputs/figures/`.

For the first article, Fig. 2 is an illustrative landmark-model frame and can be replaced independently if a privacy-safe screenshot is needed. Replacing Fig. 2 does not require recalculating the quantitative CSVs/graphs unless the evaluation dataset itself changes.

## Scientific Interpretation Notes

- The pipeline supports markerless 2D video analysis, not laboratory-grade 3D motion capture.
- Raw landmark data are not ground truth.
- Validation/sensitivity/ablation outputs should be interpreted carefully unless a controlled reference subset exists.
- Smoothness index and path efficiency were treated as more stable indicators in the article; derivative-heavy metrics such as acceleration, angular velocity, and curvature are more exploratory under heterogeneous recordings.
- If writing a second article, focus on validation/robustness with manual event and trajectory annotations instead of repeating the pipeline article.

## Dependencies

There is currently no pinned `requirements.txt` or `pyproject.toml`. The code imports:

- `opencv-python` (`cv2`)
- `numpy`
- `pandas`
- `matplotlib`
- `python-docx` for document utilities used during article work
- `tkinter` for folder selection in `main.py`

Install into your preferred Python environment as needed.

## Generated Files And Git Hygiene

Regeneratable/local outputs include:

- `swing_analysis.csv`
- `evaluation_outputs_test/`
- `article_package/evaluation_outputs_test/`
- `__pycache__/`
- Office lock files such as `~$*.docx`

Avoid committing temporary Word lock files or scratch extraction files. Treat final DOCX manuscripts and article assets deliberately because they are binary and hard to diff.

## Known Cautions

- `main.py` executes at import time; run it as a script rather than importing it.
- `main.py` writes `swing_analysis.csv` to the current working directory on exit.
- Some Word/DOCX edits can break embedded images if image-containing runs are overwritten. When changing manuscripts programmatically, preserve drawing runs and validate with Word.
- For publication work, use the Word-safe manuscript version that has both figures and final text fixes.
