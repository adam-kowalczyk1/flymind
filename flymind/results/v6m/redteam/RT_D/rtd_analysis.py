"""RT-D analysis: (1) RT-D mini-experiment table; (2) relative-gap F with paired hierarchical bootstrap on the V6m main raw npz
(same scheme as v6m_analysis.gaps, own RNG 8 498 399); (3) Exp 4 re-reads: equal-p comparison of 10 vs 40 Hz events, synthetic
gap under each synchrony axis. Read-only on V6m files. Run: .venv/bin/python -I -B flymind/results/v6m/redteam/RT_D/rtd_analysis.py"""
import glob
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V6M = os.path.abspath(os.path.join(HERE, "..", ".."))

# (1) mini-experiment
Z = {os.path.basename(p)[:-4]: np.load(p) for p in sorted(glob.glob(os.path.join(HERE, "raw", "*.npz")))}
keys = list(Z["DATA"]["keys"])
per = {k: Z[k]["out"].mean((1, 2)) for k in Z}                      # [key, rep] mean over levels × sides
B = [k for k in Z if k != "DATA"]
rng = np.random.default_rng(8_498_399)
print("(1) RT-D DN-only test, intermediates clamped (M0 = REF trains, MCIRC = circular shift); DN Hz DATA / B1, gap, rel gap")
res = {}
for ki, k in enumerate(keys):
    d, b = per["DATA"][ki], np.stack([per[x][ki] for x in B])
    res[k] = (d.mean(), b.mean(), b.mean() - d.mean(), (b.mean() - d.mean()) / d.mean())
    print(f"  {k:32s} {d.mean():7.1f} / {b.mean():7.1f}  gap {res[k][2]:+6.1f}  rel {res[k][3]:+.3f}")
print("  timing share at DN = 1 - gap(MCIRC)/gap(M0), with rep bootstrap (B1 instances + reps, DATA reps):")
for v in sorted({k.split('|')[0] for k in keys if k.endswith('MCIRC')}):
    i0, i1 = keys.index(f"{v}|M0"), keys.index(f"{v}|MCIRC")
    bs = []
    for _ in range(5000):
        kk = rng.integers(len(B), size=len(B))
        rr = rng.integers(4, size=(len(B), 4))
        dd = rng.integers(4, size=4)
        g = [np.mean([per[B[a]][i][rr[j]] for j, a in enumerate(kk)]) - per["DATA"][i][dd].mean() for i in (i0, i1)]
        bs.append(1 - g[1] / g[0])
    F = 1 - res[f"{v}|MCIRC"][2] / res[f"{v}|M0"][2]
    print(f"   {v:26s} F_timing {F:+.2f} [{np.percentile(bs, 2.5):+.2f}; {np.percentile(bs, 97.5):+.2f}]")

# (2) relative-gap F on V6m main/rep raw
print("\n(2) F on the RELATIVE gap (secondary metric), paired hierarchical bootstrap as v6m_analysis.gaps, 10 000 draws, RNG 8 498 399")
F_REF = {"E3_MCIRC": "E3_M0", "E3_MPOIS": "E3_M0", "E3_MJ20": "E3_M0", "E5a_DN_t0_sub": "E1_DN_t0"}
out2 = {}
for kind in ("main", "rep"):
    D = np.load(os.path.join(V6M, "raw", f"{kind}_DATA.npz"))
    Bs = [np.load(p) for p in sorted(glob.glob(os.path.join(V6M, "raw", f"{kind}_B1_*.npz")))]
    conds = list(D["conds"])
    j = list(D["sum_names"]).index("dn")
    xD = {c: np.nanmean(D["summ"][conds.index(c), ..., j], (0, 1)) for c in conds}
    xB = {c: np.stack([np.nanmean(b["summ"][conds.index(c), ..., j], (0, 1)) for b in Bs]) for c in conds}
    K, Rr = xB["REF"].shape
    rel = {c: np.empty(10_000) for c in conds}
    lr = {c: np.empty(10_000) for c in conds}
    for i in range(10_000):
        k = rng.integers(K, size=K)
        r = rng.integers(Rr, size=(K, Rr))
        d = rng.integers(len(xD["REF"]), size=len(xD["REF"]))
        for c in conds:
            bm, dm = np.take_along_axis(xB[c][k], r, 1).mean(), xD[c][d].mean()
            rel[c][i] = (bm - dm) / dm
            lr[c][i] = np.log(bm / dm)
    for c in conds:
        ref = F_REF.get(c, "REF")
        if c == ref:
            continue
        pt = (xB[c].mean() - xD[c].mean()) / xD[c].mean() / ((xB[ref].mean() - xD[ref].mean()) / xD[ref].mean())
        Fb = 1 - rel[c] / rel[ref]
        out2[f"{kind}:{c}"] = (1 - pt, np.percentile(Fb, 2.5), np.percentile(Fb, 97.5))
        print(f"  {kind:4s} {c:15s} vs {ref:8s} F_rel {1 - pt:+.2f} [{np.percentile(Fb, 2.5):+.2f}; {np.percentile(Fb, 97.5):+.2f}]"
              f"   log(B1/DATA) {np.log(xB[c].mean() / xD[c].mean()):+.3f}")

# (3) Exp 4 re-reads
a = json.load(open(os.path.join(V6M, "analysis.json")))
e = a["E4"]
grid = [tuple(g) for g in e["grid"]]
dnR = np.array(e["dn_mean"]["REF"])
print("\n(3a) Exp 4, REF dynamics: 10 Hz vs 40 Hz events at EQUAL participation p")
for p in (0.35, 0.7, 1.0):
    i10, i40 = grid.index((10.0, p)), grid.index((40.0, p))
    print(f"  p {p:4.2f}: DN 10 Hz {dnR[i10]:5.1f}  40 Hz {dnR[i40]:5.1f}   fano10 {e['lc_sync_by_grid']['fano10'][i10]:5.1f} / {e['lc_sync_by_grid']['fano10'][i40]:5.1f}")
prim = [i for i, g in enumerate(grid) if g[0] == 10.0]
dsc = a["main"]["descr"]["REF"]["lc_sync"]
gR = a["main"]["gaps"]["REF"]
print("(3b) synthetic gap (10 Hz family, interpolated at the real DATA and B1 values) under each synchrony axis; real gap", round(gR["gap"], 1))
for s in ("fano2", "fano5", "fano10", "fano20", "chi2_5", "paircorr5", "volley2", "cv5"):
    x = np.array(e["lc_sync_by_grid"][s])[prim]
    y = dnR[prim]
    o = np.argsort(x)
    xd, xb = dsc[s]["data"], dsc[s]["b1"]
    yd, yb = np.interp(xd, x[o], y[o]), np.interp(xb, x[o], y[o])
    extrap = xb > x.max() or xd < x.min()
    print(f"  {s:9s} DATA {xd:6.3f} -> {yd:5.1f} (real {gR['dn_data']:.1f})  B1 {xb:6.3f} -> {yb:5.1f} (real {gR['dn_b1']:.1f})  synth gap {yb - yd:+5.1f}"
          f" = {100 * (yb - yd) / gR['gap']:4.0f} %{'  (outside grid, clipped)' if extrap else ''}")
