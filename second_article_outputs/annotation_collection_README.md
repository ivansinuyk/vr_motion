# Annotation collection — **complete**

Collection finished **2026-09-01**. Provenance gate: `python audit_rater_independence.py` (exit 0).

## Live rater files

| File | Role | Status |
|---|---|---|
| `reference_annotations.csv` | Ivan Syniuk round 1 | **Frozen** — do not overwrite |
| `reference_annotations_annotator2_round1.csv` | Daria Plokhotniuk round 1 | Complete (25 sessions) |
| `reference_annotations_ivan_round2.csv` | Ivan Syniuk round 2 (intra-rater) | Complete (10 sessions) |

Downstream (regenerated from live raters):

- `reference_annotations_multirater.csv`
- `reference_annotations_consensus.csv`
- `annotation_adjudication.csv` (mean rule)
- `annotation_agreement/`

## Integrity check

```powershell
python audit_rater_independence.py
```

## Re-annotate only if restarting from scratch

```powershell
python init_blank_rater_outputs.py --which both
```

Then re-run Phases 2–3 commands below. **Do not** do this unless deliberately rebuilding the reference.

### Phase 2 — Daria Plokhotniuk round 1 (25 sessions, 100 events + 150 points)

```powershell
python annotate_reference.py `
  --dataset-root "C:\Users\isinu\Downloads\Telegram Desktop\7a0c087a-b6c7-42ea-bc67-63453d4cac7f" `
  --annotator "Daria Plokhotniuk" `
  --round 1 `
  --restart `
  --point-plan "second_article_outputs\second_annotator_frame_plan.csv" `
  --output "second_article_outputs\reference_annotations_annotator2_round1.csv" `
  --require-complete
```

### Phase 3 — Ivan round 2 (10 sessions from intrarater plan)

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

Mark **events (keys 1–4) by eye** every session. Do not reuse event frames from any prior CSV.

See also: `article_package/research_publication_status.md`, `v3/annotation_provenance_blocker.md`.
