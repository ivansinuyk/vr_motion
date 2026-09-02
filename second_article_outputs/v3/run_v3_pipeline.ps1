$ErrorActionPreference = "Stop"
cd "C:\Users\isinu\programming\study\vr_motion"

$DATASET_ROOT = "C:\Users\isinu\Downloads\Telegram Desktop\7a0c087a-b6c7-42ea-bc67-63453d4cac7f"
$OUT = "second_article_outputs\v3"
New-Item -ItemType Directory -Force -Path $OUT | Out-Null

Write-Host "=== 1/7 batch baseline ==="
python batch_article_evaluation.py `
  --dataset-root "$DATASET_ROOT" `
  --out-dir "$OUT\baseline" `
  --skip-sensitivity `
  --skip-ablation
if ($LASTEXITCODE -ne 0) { throw "batch failed" }

Write-Host "=== 2/7 validate events ==="
python validate_events_against_reference.py `
  --dataset-root "$DATASET_ROOT" `
  --annotations-csv "second_article_outputs\reference_annotations_consensus.csv" `
  --out-dir "$OUT"
if ($LASTEXITCODE -ne 0) { throw "events failed" }

Write-Host "=== 3/7 validate trajectory ==="
python validate_trajectory_against_reference.py `
  --dataset-root "$DATASET_ROOT" `
  --annotations-csv "second_article_outputs\reference_annotations_consensus.csv" `
  --out-dir "$OUT"
if ($LASTEXITCODE -ne 0) { throw "trajectory failed" }

Write-Host "=== 4/7 sensitivity ==="
python run_sensitivity_study.py `
  --dataset-root "$DATASET_ROOT" `
  --out-dir "$OUT"
if ($LASTEXITCODE -ne 0) { throw "sensitivity failed" }

Write-Host "=== 5/7 ablation ==="
python run_ablation_study.py `
  --dataset-root "$DATASET_ROOT" `
  --out-dir "$OUT"
if ($LASTEXITCODE -ne 0) { throw "ablation failed" }

Write-Host "=== 6/7 timebase audit ==="
python audit_article2_timebase.py `
  --annotations "second_article_outputs\reference_annotations_consensus.csv" `
  --dataset-summary "$OUT\baseline\dataset_summary.csv" `
  --out-dir "$OUT"
if ($LASTEXITCODE -ne 0) { throw "audit failed" }

Write-Host "=== 7/7 tables + schematics ==="
python build_article_tables.py `
  --input-dir "$OUT" `
  --out-dir "$OUT\article_tables"
if ($LASTEXITCODE -ne 0) { throw "tables failed" }

python make_article2_schematic_figures.py --out-dir "$OUT"
if ($LASTEXITCODE -ne 0) { throw "figures failed" }

Write-Host "V3 PIPELINE COMPLETE"
Get-ChildItem $OUT -Recurse -File | Select-Object FullName, Length | Format-Table -AutoSize
