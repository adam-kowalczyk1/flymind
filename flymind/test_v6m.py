"""flymind/test_v6m.py — V6m engine checks (protocol §6 T1, T2, T5 and the Exp 5a null-manipulation fact).
Run: .venv/bin/python -I -B flymind/test_v6m.py   (smoke seeds 8 490 040–049 only)"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v5v41 as V  # noqa: E402
import v5v43 as R  # noqa: E402
import v6m as M  # noqa: E402
from alif import ALIF, ALIFParams  # noqa: E402

data, idx, _, _ = V.make_net("DATA", None)
b1 = R._b1(8_490_040)[0]
P = ALIFParams(noise=2.0)
N = len(data.bodies)
lc = np.r_[idx["in_L"], idx["in_R"]]
dn, mid = np.r_[idx["DNa02_L"], idx["DNa02_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
I = R.current(idx, "L", 8.0, N)
tref, ba, sub = M.vectors(M.C(), N, dn, mid)
probe = np.array([dn[0]])
# T1a free run (nothing clamped) == alif.ALIF.step
for name, spec in (("DATA", data), ("B1", b1)):
    ref = ALIF(spec, P, 8_490_041).run(I, M.T)
    net = ALIF(spec, P, 8_490_041, b_a=ba)
    out = np.array([M.step(net, I[t], np.zeros(0, bool), np.zeros(0, int), tref, sub, probe) for t in range(M.T)])
    assert np.array_equal(out, ref), f"T1a {name}"
    # T1b clamped == v5v43.step_clamped
    n1, n2 = ALIF(data, P, 8_490_042), ALIF(data, P, 8_490_042, b_a=ba)
    a1 = np.array([R.step_clamped(n1, I[t], ref[t, lc], lc) for t in range(M.T)])
    a2 = np.array([M.step(n2, I[t], ref[t, lc], lc, tref, sub, probe) for t in range(M.T)])
    assert np.array_equal(a1, a2) and np.allclose(n1.a, n2.a, 0, 0) and np.array_equal(n1.v, n2.v), f"T1b {name}"
    print(name, "T1 identity OK; DN_L spikes", int(ref[500:, dn[0]].sum()))
# T2 every condition changes only its intended entries
for cn, cd in {**M.CONDS_MAIN, **M.CONDS_E4}.items():
    M.check_vectors(cn, cd, *M.vectors(cd, N, dn, mid), N, dn, mid)
print("T2 parameter vectors OK for", len(M.CONDS_MAIN) + len(M.CONDS_E4), "conditions")
# Exp 5a premise: subtractive reset with t_ref 2.2 is a null manipulation (v held at v_reset during refractoriness)
c_sub = M.C(sub_dn=True)
t_s, b_s, s_s = M.vectors(c_sub, N, dn, mid)
ref = ALIF(data, P, 8_490_043).run(I, M.T)
n1, n2 = ALIF(data, P, 8_490_043, b_a=b_s), ALIF(data, P, 8_490_043, b_a=b_s)
x1 = np.array([M.step(n1, I[t], ref[t, lc], lc, t_s, None, probe) for t in range(M.T)])
x2 = np.array([M.step(n2, I[t], ref[t, lc], lc, t_s, s_s, probe) for t in range(M.T)])
print("subtractive reset at t_ref 2.2 identical to hard reset:", bool(np.array_equal(x1, x2)))
t0v, _, _ = M.vectors(M.C(dn_tref=0.0), N, dn, mid)
n1, n2 = ALIF(data, P, 8_490_043, b_a=b_s), ALIF(data, P, 8_490_043, b_a=b_s)
x1 = np.array([M.step(n1, I[t], ref[t, lc], lc, t0v, None, probe) for t in range(M.T)])
x2 = np.array([M.step(n2, I[t], ref[t, lc], lc, t0v, s_s, probe) for t in range(M.T)])
print("at t_ref 0: DN_L spikes hard", int(x1[500:, dn[0]].sum()), "subtractive", int(x2[500:, dn[0]].sum()))
# T5 synthetic generator: exact per-neuron counts, ISI ≥ 4, pre-window untouched, synchrony rises with p
tr = ref[:, idx["in_L"]]
rng = np.random.default_rng(8_490_044)
f = []
for ev, p in M.P_SYNC:
    x = M.synth(tr, p, rng, ev)
    assert np.array_equal(x[:M.W0], tr[:M.W0]) and np.array_equal(x[M.W0:M.W1].sum(0), tr[M.W0:M.W1].sum(0)), "T5 counts"
    for j in range(x.shape[1]):
        t = np.flatnonzero(x[M.W0:M.W1, j])
        assert (np.diff(t) >= 4).all(), "T5 ISI"
    f.append(M.sync_metrics(x)[2])
print("T5 synth OK; Fano10 by p", np.round(f, 1), "| source", round(M.sync_metrics(tr)[2], 1))
assert f[-1] > f[0]
print("test_v6m: OK")
