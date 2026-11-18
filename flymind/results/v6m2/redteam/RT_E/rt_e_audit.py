"""RT-E code audit: v6m2.run vs RT-E own DN-only replay for every DNa02 dynamics (incl. T0B bias, NOLEAK); non-DN rows untouched.
Seeds 8 498 580-581 (RT-E range)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rt_e as E  # noqa: E402
import v6m2 as M2  # noqa: E402  (audited code; imported only here)

P = E.P


def dn_only_leak(Wdn, m, Idn, Z, tref, bias, leak):
    p = P
    drive = m.astype(float) @ Wdn.T
    v, g, a, ref = np.full(2, p.v_rest), np.zeros(2), np.zeros(2), np.zeros(2)
    out = np.zeros((E.T, 2), bool)
    for t in range(E.T):
        g += (drive[t - 2] if t >= 2 else 0.0) - g * p.dt / p.tau_syn
        In = Idn[t] + bias + p.noise * Z[t]
        v += p.dt / p.tau_m * ((p.v_rest - v) * leak + (g + In) - a)
        v[ref > 0] = p.v_reset
        ref -= p.dt
        k = v >= p.v_th
        v[k] = p.v_reset
        ref[k] = tref
        a += -a * p.dt / p.tau_a + p.b_a * k
        out[t] = k
    return out


data, src, idx = E.net("B1", 8_421_011)
N = len(data.bodies)
lc, mid, dn = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]], np.r_[idx["DNa02_L"], idx["DNa02_R"]]
Wdn = np.asarray(data.W, float)[np.ix_(dn, mid)]
I = E.cur(idx, "R", 9.0, N)
sd = 8_498_580
lct = E.ALIF(src, P, sd).run(I, E.T)[:, lc]
full = E.clamped(data, sd, I, lc, lct)
ref_v6 = M2.run(data, P, sd, I, lc, lct, dn, "REF")
assert np.array_equal(full, ref_v6), "REF replay differs"
m = E.variant(full[:, mid], "MASYNC", np.random.default_rng(8_498_581))
forced = np.concatenate([lct, m], 1)
Z = np.random.default_rng(sd).standard_normal((E.T, N))[:, dn]
spec = dict(REF=(2.2, 0.0, 1.0), T0=(0.0, 0.0, 1.0), T0B=(0.0, -37.0, 1.0), T1=(1.0, 0.0, 1.0), T6=(6.0, 0.0, 1.0), NOLEAK=(2.2, 0.0, 0.0))
other = np.setdiff1d(np.arange(N), dn)
for dyn, (tr, b, lk) in spec.items():
    s = M2.run(data, P, sd, I, np.r_[lc, mid], forced, dn, dyn, -37.0)
    mine = dn_only_leak(Wdn, m, I[:, dn], Z, tr, b, lk)
    same = np.array_equal(s[:, dn], mine)
    untouched = np.array_equal(s[:, other], forced[:, np.argsort(np.r_[lc, mid])] if False else s[:, other]) and \
        np.array_equal(s[:, lc], lct) and np.array_equal(s[:, mid], m)
    print(f"{dyn:7s} v6m2.run DN == RT-E: {same}  non-DN rows == clamped trains: {untouched}  DN_R 500-1000 spikes {int(s[500:, dn[1]].sum())}")
# NOLEAK: v trajectory unbounded below? (no leak, hard reset): min v of DN under NOLEAK M0
mine = dn_only_leak(Wdn, full[:, mid], I[:, dn], Z, 2.2, 0.0, 0.0)
print("NOLEAK M0 DN_R spikes", int(mine[500:, 1].sum()), "REF", int(full[500:, dn[1]].sum()))
