"""Spectral predictor engine — extracted verbatim (logic) from
SpectralPredictor v15 (three_systems_blanket.py, VERDICT.md).

Two primitives reused across EXP-BALANCE-002/003/004:
  change_op  — stable low-rank DMD change operator D:  x(t+1) = x(t) + D x(t)
               This is System B (self-evidencing anchor), the version that
               won both accuracy and safety in the v15 verdict.
  blanket_diag — Markov-blanket spectral decomposition of the reduced Koopman
               operator: order (mu_pp, predictable interior), boundary (mu_sc),
               chaos (mu_ac). 'order' fraction correlates with predictability
               (r=+0.42 in v15) — this is the *measured* confidence, the honest
               replacement for a declared "97.5%".
"""
import numpy as np


def skill(t, p, ref):
    d = np.sum((t - ref) ** 2)
    return 1 - np.sum((t - p) ** 2) / d if d > 1e-9 else np.nan


def change_op(Ztr, r):
    """Low-rank change operator (verified stable DMD-change, no eigendecomp)."""
    X = Ztr[:-1].T
    Df = np.diff(Ztr, axis=0).T
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    rr = min(r, len(S) - 1, X.shape[0] - 1)
    if rr < 1:
        return np.zeros((Ztr.shape[1], Ztr.shape[1]))
    Ur, Sr, Vr = U[:, :rr], S[:rr], Vt[:rr].T
    return Ur @ (Ur.T @ Df @ Vr @ np.diag(1 / Sr)) @ Ur.T


def predict_next(Ztr, state, r):
    """Conditional forecast: given current state vector, next = state + D·state."""
    D = change_op(Ztr, r)
    return state + D @ state


def forecast_skill(Ztr, Zte, r):
    D = change_op(Ztr, r)
    return skill(Zte[1:], Zte[:-1] + (D @ Zte[:-1].T).T, Zte[:-1])


def blanket_diag(Ztr, r):
    """Order / boundary / chaos fractions + EWS, via ResDMD-style residuals."""
    mu = Ztr.mean(0)
    Xc = Ztr - mu
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    rr = min(r, len(S) - 1, Xc.shape[1])
    if rr < 1:
        return 0.0, 0.0, 1.0, 0.0
    A = Xc @ Vt[:rr].T
    K = np.linalg.lstsq(A[:-1], A[1:], rcond=None)[0]
    G = A[:-1].T @ A[:-1]
    A1 = A[:-1].T @ A[1:]
    A2 = A[1:].T @ A[1:]
    lam, W = np.linalg.eig(K)
    res = np.zeros(len(lam))
    for i in range(len(lam)):
        w = W[:, i]
        gg = np.real(np.conj(w) @ G @ w) + 1e-12
        num = np.real(np.conj(w) @ A2 @ w
                      - np.conj(lam[i]) * (np.conj(w) @ A1 @ w)
                      - lam[i] * (np.conj(w) @ A1.T @ w)
                      + abs(lam[i]) ** 2 * (np.conj(w) @ G @ w))
        res[i] = np.sqrt(max(num, 0) / gg)
    am = np.abs(lam)
    rn = res / (res.max() + 1e-9)
    order = float(((rn < 0.5) & (am > 0.85)).mean())
    boundary = float(((rn >= 0.3) & (rn < 0.7) & (am > 0.9)).mean())
    chaos = float(1 - order - boundary)
    ews = float(am[(rn >= 0.3) & (am > 0.9)].max()
                if ((rn >= 0.3) & (am > 0.9)).any() else 0.0)
    return order, boundary, chaos, ews


def confidence(Ztr, r):
    """Measured predictability = order-mass (mu_pp). The honest '97.5%'."""
    return blanket_diag(Ztr, r)[0]
