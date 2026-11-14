"""RT-C supplement: F on the RELATIVE gap (gap/DN_DATA), paired hierarchical bootstrap as v6m_analysis.gaps (RNG 8 498 231).
Also applied to the V6m main raw files (no simulation). Run: .venv/bin/python -I -B flymind/results/v6m/redteam/RT_C/rtc_relF.py"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FM = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, FM)
import v6m_analysis as A  # noqa: E402

CONDS = ["REF", "E1c_DN_t0", "E1_DN_t0", "E3_M0", "E3_MCIRC", "E1b_MID_t0", "E2a_DN_b00", "LCIRC"]
REFC = {"E3_MCIRC": "E3_M0"}


def relF(D, Bs, rng, nboot=10_000):
    xD = {c: A.per_rep(D, c, "dn") for c in CONDS}
    xB = {c: np.stack([A.per_rep(b, c, "dn") for b in Bs]) for c in CONDS}
    K, R = xB["REF"].shape
    RD = len(xD["REF"])
    bs = {c: np.empty(nboot) for c in CONDS}
    for i in range(nboot):
        k, r, d = rng.integers(K, size=K), rng.integers(R, size=(K, R)), rng.integers(RD, size=RD)
        for c in CONDS:
            m = xD[c][d].mean()
            bs[c][i] = (np.take_along_axis(xB[c][k], r, 1).mean() - m) / m
    out = {}
    for c in CONDS:
        ref = REFC.get(c, "REF")
        if c == ref or c == "E3_M0":
            continue
        pt = 1 - ((xB[c].mean() - xD[c].mean()) / xD[c].mean()) / ((xB[ref].mean() - xD[ref].mean()) / xD[ref].mean())
        Fb = 1 - bs[c] / bs[ref]
        out[c] = (pt, np.percentile(Fb, 2.5), np.percentile(Fb, 97.5))
    return out


sets = {"V6m_main(D0,7-9mV,10 B1,8 reps)": (os.path.join(FM, "results", "v6m", "raw", "main_DATA.npz"),
                                            [os.path.join(FM, "results", "v6m", "raw", f"main_B1_{k}.npz") for k in range(8_421_001, 8_421_011)])}
for cfg in ("D0", "TH8", "BA1", "J025"):
    sets[f"RT-C {cfg}"] = (os.path.join(HERE, "raw", f"{cfg}_DATA.npz"), [os.path.join(HERE, "raw", f"{cfg}_B1_{k}.npz") for k in (8_421_001, 8_421_002, 8_421_003)])
for name, (d, bs) in sets.items():
    o = relF(dict(np.load(d)), [dict(np.load(b)) for b in bs], np.random.default_rng(8_498_231))
    print(name)
    for c, (f, lo, hi) in o.items():
        print(f"  relF {c:11s} {f:+.3f} ({lo:+.2f};{hi:+.2f}) {A.label(f, [lo, hi])}")
