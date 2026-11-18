"""F1 analysis core: FA-matched criterion, BSC, SDT measures, paired unit bootstrap. Pure numpy, no I/O."""
import math

import numpy as np
from scipy.stats import norm


def criterion(d_none, fa=0.05):
    """Smallest c ≥ 0 with P(|D| > c | no target) ≤ fa (see PROTOCOL §5)."""
    a = np.sort(np.abs(np.asarray(d_none, float)))[::-1]
    m = int(math.floor(fa * len(a)))
    return float(a[m]) if m < len(a) else 0.0


def responses(D, c):
    """+1 left, −1 right, 0 none."""
    D = np.asarray(D, float)
    return np.where(D > c, 1, np.where(D < -c, -1, 0))


def bsc(DL, DR, DN, fa=0.05):
    """DL, DR: [units, levels] (left / right targets), DN: [units] no target. Returns per-level BSC [levels] and c."""
    c = criterion(DN, fa)
    return 0.5 * ((responses(DL, c) == 1).mean(0) + (responses(DR, c) == -1).mean(0)), c


def auc(x, y):
    """P(x > y) + ½P(x = y) for samples x (positives) and y."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if not len(x) or not len(y):
        return np.nan
    allv = np.r_[x, y]
    from scipy.stats import rankdata
    r = rankdata(allv)
    return float((r[:len(x)].sum() - len(x) * (len(x) + 1) / 2) / (len(x) * len(y)))


def dprime_from_auc(a, n):
    a = min(max(a, 1 / (2 * n)), 1 - 1 / (2 * n))
    return float(math.sqrt(2) * norm.ppf(a))


def mi_bits(side, resp):
    """Plug-in mutual information between side (±1) and response (−1, 0, +1)."""
    side, resp = np.asarray(side), np.asarray(resp)
    out = 0.0
    for s in np.unique(side):
        for r in (-1, 0, 1):
            p = np.mean((side == s) & (resp == r))
            if p > 0:
                out += p * math.log2(p / (np.mean(side == s) * np.mean(resp == r)))
    return out


def holm(ps, alpha=0.05):
    """Holm step-down: adjusted p-values and reject flags in the input order."""
    ps = np.asarray(ps, float)
    o = np.argsort(ps)
    adj = np.empty_like(ps)
    run = 0.0
    for k, i in enumerate(o):
        run = max(run, min(1.0, (len(ps) - k) * ps[i]))
        adj[i] = run
    return adj.tolist(), (adj < alpha).tolist()


if __name__ == "__main__":                            # self-check
    assert criterion(np.zeros(100)) == 0.0
    assert criterion(np.arange(100)) == 94.0 and (np.abs(np.arange(100)) > 94).mean() <= 0.05
    DL = np.array([[1, 0], [2, 0]]); DR = np.array([[-1, 0], [0, 0]]); DN = np.zeros(2)
    b, c = bsc(DL, DR, DN)
    assert c == 0 and np.allclose(b, [0.75, 0.0])
    assert auc([1, 2], [0, 0]) == 1.0 and auc([0], [0]) == 0.5
    assert abs(mi_bits([1, 1, -1, -1], [1, 1, -1, -1]) - 1) < 1e-12
    adj, rej = holm([0.01, 0.04, 0.03])
    assert np.allclose(adj, [0.03, 0.06, 0.06]) and rej == [True, False, False]
    print("analysis_core self-check OK")
