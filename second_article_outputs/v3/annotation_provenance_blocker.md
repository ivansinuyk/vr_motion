# CLEARED — annotation provenance blocker (2026-09-01 evening)

**Status: CLEARED for multi-rater v3 manuscript/DOCX rebuild.**

Genuine blind re-annotation completed for:

- `second_article_outputs/reference_annotations_annotator2_round1.csv` — Daria Plokhotniuk round 1
- `second_article_outputs/reference_annotations_ivan_round2.csv` — Ivan Syniuk round 2

Prior synthetic/derivative drafts are gone (archive folder deleted). Do **not** reuse any
pre-2026-09-01 19:19 rater CSVs, old consensus, or old agreement outputs.

## Checks that passed (2026-09-01 ~19:22)

```powershell
python audit_rater_independence.py   # exit 0 — no synthetic signature
```

Additional structure / independence checks (22/22):

- Completeness: Daria 100 events + 150 planned points (25 sessions); Ivan R2 40 + 60 (10 sessions)
- 100% integer pixel clicks; no duplicate event labels or point frames
- Event signed-diff fingerprints **changed** vs prior INVALID/synthetic event labels
- Same-frame point distance vs Ivan R1: median ~77 px (Daria) / ~79 px (Ivan R2); not ±4 copy box
- Planned-point and intrarater-session coverage complete

## Downstream regenerated after clearance

| Artifact | Regenerated |
|---|---|
| `annotation_disagreements.csv` | yes |
| `annotation_adjudication.csv` (disclosed **mean** rule) | yes |
| `reference_annotations_multirater.csv` | yes |
| `reference_annotations_consensus.csv` | yes |
| `annotation_agreement/**` | yes |
| v3 event / trajectory / timebase / tables / schematics vs **new** consensus | yes |

Sensitivity / ablation / baseline batch were **not** re-run (algorithm unchanged; RTS fix already in v3).

## Honest scientific caveats for the manuscript agent

1. Inter-rater **point** median disagreement is large (~77 px / ~4% image diagonal). Report as human
   reference uncertainty; do **not** overclaim trajectory “accuracy.”
2. Consensus uses the disclosed **mean / midpoint** rule (`annotation_adjudication.csv`). Algorithm-vs-consensus
   trajectory error is therefore larger than algorithm-vs-Ivan-R1 alone (~44 px session-median-of-medians
   vs ~15 px). Disclose this.
3. Event inter-rater median abs difference ~4 frames; Ivan intra-rater ~2 frames. Exact-frame rates are low;
   report honestly with Bland–Altman / CIs from agreement CSVs.
4. `audit_consensus_contamination.py` still prints diagnostic contrasts (Ivan-only vs consensus). That is
   expected under large human disagreement + mean rule — not a re-block if independence audit exits 0.

## Owner-blocked (unchanged for metadata/photos)

Ethics and AI disclosure were owner-supplied in **v4 DOCX** (2026-09-02). Participant
acquisition metadata and co-author photos remain owner-supplied if required for final
HAIT upload; do not invent them.

Master publication sync: `article_package/research_publication_status.md`.
