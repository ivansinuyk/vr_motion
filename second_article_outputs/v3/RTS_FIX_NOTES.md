# RTS production fix (author-approved 2026-09-01)

## Defect
`rts_smoother.rts_smooth` computed predicted covariance as `F P F'` only.
The forward filter (`Kalman2D.predict`) uses `F P F' + Q`. Omitting `Q`
made the smoother overconfident and caused trajectory collapse in the
production ablation (Article 2 v2 finding).

## Fix
- `rts_smoother.py`: optional `Q` argument added to `P_pred = F P F' + Q`.
- `swing_analyzer._rts_smoothed_points`: passes `Q=self.kalman.Q_diag`.
- Ablation continues to use production RTS arrays (no separate textbook substitute).
- Synthetic tests: `test_rts_smoother.py`.

## Parameters
No Kalman `q_pos` / `q_vel` / `r` retune in this change. Despiking thresholds
unchanged; re-check activation counts in v3 ablation outputs.
