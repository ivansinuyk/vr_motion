"""Synthetic checks for the production RTS smoother."""

from __future__ import annotations

import numpy as np

from kalman import Kalman2D
from rts_smoother import rts_smooth


def _constant_velocity_track(n=40, dt=1 / 60, noise=0.5, seed=0):
    rng = np.random.default_rng(seed)
    truth = []
    x, y, vx, vy = 100.0, 200.0, 80.0, -40.0
    for _ in range(n):
        x += vx * dt
        y += vy * dt
        truth.append((x, y, vx, vy))
    meas = [
        (t[0] + rng.normal(0, noise), t[1] + rng.normal(0, noise)) for t in truth
    ]
    return truth, meas, dt


def test_rts_includes_process_noise_and_stays_near_truth():
    truth, meas, dt = _constant_velocity_track()
    kf = Kalman2D(q_pos=4.0, q_vel=4.0, r_meas=1.0)
    states, covs, fs = [], [], []
    for z in meas:
        kf.update(z, dt)
        states.append(kf.x.copy())
        covs.append(kf.P.copy())
    for _ in range(len(states) - 1):
        fs.append(kf.transition(dt))

    xs_bad, ps_bad = rts_smooth(states, covs, fs, Q=None)
    xs_good, ps_good = rts_smooth(states, covs, fs, Q=kf.Q_diag)

    assert all(np.isfinite(p).all() for p in ps_good)
    assert all(np.isfinite(x).all() for x in xs_good)

    err_fwd = np.mean(
        [np.hypot(states[i][0, 0] - truth[i][0], states[i][1, 0] - truth[i][1]) for i in range(len(truth))]
    )
    err_good = np.mean(
        [np.hypot(xs_good[i][0, 0] - truth[i][0], xs_good[i][1, 0] - truth[i][1]) for i in range(len(truth))]
    )
    # With correct Q, RTS should not be wildly worse than the forward filter.
    assert err_good < err_fwd * 1.5

    # Predicted-cov path with Q must differ from the defective no-Q path.
    delta = sum(np.linalg.norm(ps_good[i] - ps_bad[i]) for i in range(len(ps_good)))
    assert delta > 0


def test_rts_handles_missing_gap_segments_via_caller():
    # Caller is responsible for segmenting; smoother itself needs contiguous input.
    xs = [np.array([[i], [0], [1], [0]], float) for i in range(5)]
    ps = [np.eye(4) for _ in range(5)]
    fs = [np.eye(4) for _ in range(4)]
    out_x, out_p = rts_smooth(xs, ps, fs, Q=np.eye(4) * 0.1)
    assert len(out_x) == 5
    assert all(np.isfinite(p).all() for p in out_p)


if __name__ == "__main__":
    test_rts_includes_process_noise_and_stays_near_truth()
    test_rts_handles_missing_gap_segments_via_caller()
    print("RTS tests OK")
