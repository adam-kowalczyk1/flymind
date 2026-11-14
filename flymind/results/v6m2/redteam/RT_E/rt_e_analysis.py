"""RT-E analysis of rt_e_raw.json (own code; same estimands as v6m2_analysis: gap = B1 - DATA, dt = gap(X) - gap(M0), I = dt(REF) - dt(dyn))."""
import json
import os

import numpy as np
from scipy import stats

D = "/Users/admin/so101_fly_project/flymind/results/v6m2/redteam/RT_E"
R = json.load(open(os.path.join(D, "rt_e_raw.json")))
INP, DYN = R["inputs"], R["dyns"]
res = {r["name"]: r for r in R["res"]}
rate = {n: np.array(r["rate"]) for n, r in res.items()}       # [dyn, inp, lv, side, rep]
xD = rate["DATA"].mean((2, 3))                                   # [dyn, inp, rep]
xB = np.stack([rate[n].mean((2, 3)) for n in sorted(res) if n != "DATA"])
d, i = {n: k for k, n in enumerate(DYN)}, {n: k for k, n in enumerate(INP)}


def f(mD, mB):
    o = {}
    for dn in DYN:
        for x in INP:
            o[f"gap|{dn}|{x}"] = mB[d[dn], i[x]] - mD[d[dn], i[x]]
            o[f"L|{dn}|{x}"] = np.log(mB[d[dn], i[x]] / mD[d[dn], i[x]])
        for x in INP[1:]:
            o[f"dt|{dn}|{x}"] = o[f"gap|{dn}|{x}"] - o[f"gap|{dn}|M0"]
            o[f"dtL|{dn}|{x}"] = o[f"L|{dn}|{x}"] - o[f"L|{dn}|M0"]
    for dn in ("T0", "T0B"):
        for x in INP[1:]:
            o[f"I|{dn}|{x}"] = o[f"dt|REF|{x}"] - o[f"dt|{dn}|{x}"]
            o[f"IL|{dn}|{x}"] = o[f"dtL|REF|{x}"] - o[f"dtL|{dn}|{x}"]
    return o


pt = f(xD.mean(-1), xB.mean((0, -1)))
rng = np.random.default_rng(8_498_599)
K, Rr = xB.shape[0], xB.shape[-1]
bs = {k: [] for k in pt}
for _ in range(10000):
    kk = rng.integers(K, size=K)
    sel = np.stack([xB[kk[j]][..., rng.integers(Rr, size=Rr)] for j in range(K)])
    s = f(xD[..., rng.integers(Rr, size=Rr)].mean(-1), sel.mean((0, -1)))
    for k in pt:
        bs[k].append(s[k])
jk = {k: [] for k in pt}
for r in range(Rr):
    m = np.arange(Rr) != r
    s = f(xD[..., m].mean(-1), xB[..., m].mean((0, -1)))
    for k in pt:
        jk[k].append(s[k])
tq = stats.t.ppf(0.975, Rr - 1)
print(f"bias {R['cal']['bias']}  (V6m2 MAIN -38)  B1 {R['b1']}  reps {Rr}")
print("means (DATA / B1):")
for dn in DYN:
    print("  ", dn, "  ".join(f"{x} {xD[d[dn], i[x]].mean():6.1f}/{xB[:, d[dn], i[x]].mean():6.1f}" for x in INP))
V6 = {"gap|REF|M0": -20.7, "dt|REF|MASYNC": 8.1, "dt|T0|MASYNC": -7.2, "dt|T0B|MASYNC": -13.0, "I|T0B|MASYNC": 21.2, "IL|T0B|MASYNC": 0.55,
      "I|T0|MASYNC": 15.4, "dt|REF|MCIRC": 6.6, "dt|T0B|MCIRC": -11.6, "I|T0B|MCIRC": 18.2, "gap|T0B|M0": -4.0}
for k in pt:
    if k.startswith(("gap|", "dt|", "dtL|", "I|", "IL|")) and not k.startswith("gap|T0|"):
        j = np.array(jk[k])
        se = np.sqrt((Rr - 1) / Rr * ((j - j.mean()) ** 2).sum())
        p = np.percentile(bs[k], [2.5, 97.5])
        lo, hi = min(p[0], pt[k] - tq * se), max(p[1], pt[k] + tq * se)
        print(f"  {k:20s} {pt[k]:+8.3f}  wide CI [{lo:+.3f}; {hi:+.3f}]  pct [{p[0]:+.3f}; {p[1]:+.3f}]" + (f"   V6m2 {V6[k]:+.2f}" if k in V6 else ""))
# per level / per side (point)
for li, lv in enumerate(R["levels"]):
    pD = rate["DATA"][:, :, li].mean(2)
    pB = np.stack([rate[n][:, :, li].mean(2) for n in res if n != "DATA"])
    s = f(pD.mean(-1), pB.mean((0, -1)))
    print(f"  level {lv}: dt REF {s['dt|REF|MASYNC']:+.1f}  dt T0B {s['dt|T0B|MASYNC']:+.1f}  I {s['I|T0B|MASYNC']:+.1f}  IL {s['IL|T0B|MASYNC']:+.3f}")
for si, sd in enumerate("LR"):
    pD = rate["DATA"][:, :, :, si].mean(2)
    pB = np.stack([rate[n][:, :, :, si].mean(2) for n in res if n != "DATA"])
    s = f(pD.mean(-1), pB.mean((0, -1)))
    print(f"  side {sd}: dt REF {s['dt|REF|MASYNC']:+.1f}  dt T0B {s['dt|T0B|MASYNC']:+.1f}  I {s['I|T0B|MASYNC']:+.1f}")
# per B1 instance I
for n in sorted(res):
    if n != "DATA":
        s = f(xD.mean(-1), rate[n].mean((2, 3)).mean(-1))
        print(f"  {n}: gap REF M0 {s['gap|REF|M0']:+.1f}  I {s['I|T0B|MASYNC']:+.1f}")
# count redistribution into the analysis window (ipsi-DN drive in [SS-2, W1-2))
drv = {n: np.array(r["drv"]) for n, r in res.items()}            # [inp, lv, side, rep, (exc, inh, nspk)]
print("ipsi-DN presyn drive in 500-1000 ms (exc sum W, inh sum W, n mid spikes), mean over lv/side/rep:")
for x in INP:
    a = drv["DATA"][i[x]].mean((0, 1, 2))
    b = np.mean([drv[n][i[x]].mean((0, 1, 2)) for n in res if n != "DATA"], 0)
    print(f"  {x:9s} DATA exc {a[0]:8.0f} inh {a[1]:8.0f} n {a[2]:6.0f} | B1 exc {b[0]:8.0f} inh {b[1]:8.0f} n {b[2]:6.0f}")
