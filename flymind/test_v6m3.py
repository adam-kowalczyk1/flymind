"""flymind/test_v6m3.py — V6m3 V1 (engine identity, population-restricted ablations) and V4 (count-swap). Smoke seeds 8 490 070–079.
Run: .venv/bin/python -I -B flymind/test_v6m3.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v5v43 as R  # noqa: E402
import v6m3 as M3  # noqa: E402
from alif import ALIF  # noqa: E402

data, idx, N, lc, mid, dn = M3.setup()
I = R.current(idx, "L", 8.0, N)
free = ALIF(data, M3.P, 8_490_071).run(I, M3.T)
tref = np.full(N, M3.P.t_ref)
s = M3.run3(data, 8_490_071, I, np.zeros(0, int), np.zeros((M3.T, 0), bool), tref, np.ones(N), None)
assert np.array_equal(s, free), "V1 free run"
c = M3.run3(data, 8_490_071, I, lc, free[:, lc], tref, np.ones(N), None)
assert np.array_equal(c, free), "V1 clamped identity"
cal = dict(mid_gain=0.5, mid_bias=-5.0, dn_gain=0.6)
for cond in M3.A_CONDS[:-1]:
    t, g, b = M3.a_vectors(cond, N, mid, cal)
    other = np.setdiff1d(np.arange(N), mid)
    assert (t[other] == M3.P.t_ref).all() and (g[other] == 1).all() and (b is None or (b[other] == 0).all()), f"V1 {cond} touches non-mid"
for dyn in M3.B_DYN:
    t, g = M3.b_vectors(dyn, N, dn, cal)
    other = np.setdiff1d(np.arange(N), dn)
    assert (t[other] == M3.P.t_ref).all() and (g[other] == 1).all(), f"V1 {dyn} touches non-DN"
# V4 count-swap
rng = np.random.default_rng(8_490_072)
XD = free[:, mid]
XB = ALIF(data, M3.P, 8_490_073).run(I, M3.T)[:, mid]
for tsrc, csrc in ((XD, XB), (XB, XD)):
    x, n_add, n_fb = M3.count_swap(tsrc, csrc, rng)
    assert np.array_equal(x[M3.W0:M3.W1].sum(0), csrc[M3.W0:M3.W1].sum(0)), "V4 counts"
    assert np.array_equal(x[:M3.W0], tsrc[:M3.W0]), "V4 pre-window"
    kept = x[M3.W0:M3.W1] & tsrc[M3.W0:M3.W1]
    assert np.array_equal(kept.sum(0), np.minimum(tsrc[M3.W0:M3.W1].sum(0), csrc[M3.W0:M3.W1].sum(0))), "V4 subset"
    print("count_swap OK; added", n_add, "of", int(csrc[M3.W0:M3.W1].sum()))
print("test_v6m3: OK")
