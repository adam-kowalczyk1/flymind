"""flymind/test_v6m2.py — V6m2 V1: step2 with default options == v6m.step; NOLEAK/bias touch only DNa02. Smoke seeds 8 490 060–069.
Run: .venv/bin/python -I -B flymind/test_v6m2.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v5v43 as R  # noqa: E402
import v6m as M  # noqa: E402
import v6m2 as M2  # noqa: E402
from alif import ALIF  # noqa: E402

data, src, idx, P = M2.nets("MAIN", "B1", 8_490_060)
N = len(data.bodies)
lc, mid = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
dn = np.r_[idx["DNa02_L"], idx["DNa02_R"]]
I = R.current(idx, "L", 8.0, N)
lc_tr = ALIF(src, P, 8_490_061).run(I, M.T)[:, lc]
tref, ba, _ = M.vectors(M.C(), N, dn, mid)
n1 = ALIF(data, P, 8_490_061, b_a=ba)
a = np.array([M.step(n1, I[t], lc_tr[t], lc, tref, None, np.array([dn[0]])) for t in range(M.T)])
b = M2.run(data, P, 8_490_061, I, lc, lc_tr, dn, "REF")
assert np.array_equal(a, b), "V1 step2 != v6m.step"
# DN-only clamp: NOLEAK / T0B change only DNa02 spikes; with everything else clamped all other rows are identical
forced = np.concatenate([lc_tr, b[:, mid]], 1)
lcmid = np.r_[lc, mid]
for dyn in ("NOLEAK", "T0B", "T0", "T6"):
    s = M2.run(data, P, 8_490_061, I, lcmid, forced, dn, dyn, -20.0)
    other = np.setdiff1d(np.arange(N), dn)
    assert np.array_equal(s[:, other], b[:, other]), f"V1 {dyn} changed non-DN neurons"
    print(dyn, "DN_L", int(s[500:, dn[0]].sum()), "vs REF", int(b[500:, dn[0]].sum()))
m = M2.mid_variant(b[:, mid], "MASYNC", np.random.SeedSequence([8_490_062]))
assert np.array_equal(m[M.W0:M.W1].sum(0), b[M.W0:M.W1, mid].sum(0)) and np.array_equal(m[:M.W0], b[:M.W0, mid])
print("test_v6m2: OK")
