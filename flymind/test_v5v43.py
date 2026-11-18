"""flymind/test_v5v43.py — exactness of the clamped replay (protocol §4). Run: .venv/bin/python -I -B flymind/test_v5v43.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v5v41 as V  # noqa: E402
import v5v43 as R  # noqa: E402
from alif import ALIF, ALIFParams  # noqa: E402

data, idx, _, _ = V.make_net("DATA", None)
b1, _, _, _ = R._b1(8_490_030)                     # smoke-pool B1 instance
P = ALIFParams(noise=2.0)
lc = np.r_[idx["in_L"], idx["in_R"]]
N = len(data.bodies)
I = R.current(idx, "L", 8.0, N)
for name, src in (("DATA", data), ("B1", b1)):
    s = ALIF(src, P, 8_490_031).run(I, R.T)
    net = ALIF(data, P, 8_490_031)
    rep = np.array([R.step_clamped(net, I[t], s[t, lc], lc) for t in range(R.T)])
    nonlc = np.setdiff1d(np.arange(N), lc)
    assert np.array_equal(rep[:, nonlc], s[:, nonlc]), f"T1 {name}: identity replay != free run"
    assert np.array_equal(rep[:, lc], s[:, lc])
    print(name, "identity replay exact; DN_L spikes", int(s[500:, idx['DNa02_L']].sum()))
rng = np.random.default_rng(8_490_032)
tr = np.random.default_rng(1).random((R.T, 275)) < 0.013
for v in R.VARIANTS:
    x, lost = R.manipulate(tr, v, rng)
    assert np.array_equal(x[:R.W0], tr[:R.W0]), f"T2 {v} touched pre-window"
    if v == "CIRC":
        assert np.array_equal(x.sum(0), tr.sum(0)), "T3 circ counts"
    if v.startswith("J"):
        assert x[R.W0:].sum() + lost == tr[R.W0:].sum(), "T4 jitter accounting"
print("test_v5v43: OK")
