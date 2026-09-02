import numpy as np


def rts_smooth(states, covs, Fs, Q=None):
    """Rauch–Tung–Striebel smoother.

    Predicted covariance must include process noise when the forward filter
    used ``P <- F P F' + Q`` (as ``Kalman2D.predict`` does). Omitting ``Q``
    makes the smoother overconfident and can collapse trajectories toward a
    near-linear path.
    """
    xs = [np.array(x, dtype=float, copy=True) for x in states]
    Ps = [np.array(p, dtype=float, copy=True) for p in covs]
    for k in range(len(xs) - 2, -1, -1):
        P_pred = Fs[k] @ Ps[k] @ Fs[k].T
        if Q is not None:
            P_pred = P_pred + Q
        # Small regularizer to avoid numerical issues on near-singular covariances.
        P_pred = P_pred + np.eye(P_pred.shape[0]) * 1e-9
        G = np.linalg.solve(P_pred.T, (Ps[k] @ Fs[k].T).T).T
        xs[k] = xs[k] + G @ (xs[k + 1] - Fs[k] @ xs[k])
        Ps[k] = Ps[k] + G @ (Ps[k + 1] - P_pred) @ G.T
    return xs, Ps