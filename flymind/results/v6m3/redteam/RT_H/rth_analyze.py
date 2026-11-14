import json, os, sys, numpy as np
from scipy import stats
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "../../../.."))
import v6m3 as M3
data, idx, N, lc, mid, dn = M3.setup()
W = np.asarray(data.W, float); out = W[:, mid]
inh = (out < 0).sum(0) > (out > 0).sum(0)
J = json.load(open(os.path.join(HERE, "rth_partA_raw.json")))
runs = J["runs"]; conds = [c for c in runs[0]["res"] if not c.startswith("_")]
print("cal", {k: J["cal"][k] for k in ("ref_mid", "s_cal")}, "engine identity all:", all(r["res"]["_engine_identity"] for r in runs), len(runs))
srcs = [None, 8499001, 8499002, 8499003]
def arr(c, f):  # [src, lv, side, rep]
    a = np.full((4, 2, 2, 8), np.nan)
    for r in runs:
        a[srcs.index(r["k"]), [8.0, 9.0].index(r["lv"]), "LR".index(r["side"]), r["r"]] = f(r["res"][c])
    return a
def drel(x, lev=None):  # x [src, lv, side, rep]; pooled ratio B1/DATA - 1 with jackknife-t over reps
    if lev is not None: x = x[:, lev:lev + 1]
    est = lambda m: x[1:][..., m].mean() / x[0][..., m].mean() - 1
    allm = np.ones(8, bool); e = est(allm)
    jk = np.array([est(np.arange(8) != i) for i in range(8)])
    se = np.sqrt(7 / 8 * ((jk - jk.mean()) ** 2).sum()); q = stats.t.ppf(.975, 7)
    return e, e - q * se, e + q * se, jk
ref = drel(arr("REF", lambda d: d["dexc"]))
print(f"{'cond':11s} {'Drel':>7s} {'CI':>17s} {'F_A':>6s} {'F_A jk CI':>15s} {'midD Hz':>7s} {'midB Hz':>7s} {'midrel':>7s} {'DinhD':>7s} {'DinhB':>7s} {'I-mid D Hz':>9s} {'rD':>5s} {'rB':>5s} {'ISI<=4 D':>8s} {'ISI<=4 B':>8s} {'DN gap':>7s}")
q = stats.t.ppf(.975, 7)
for c in conds:
    x = arr(c, lambda d: d["dexc"]); e, lo, hi, jk = drel(x)
    fa = 1 - e / ref[0]; fjk = 1 - jk / ref[3]; se = np.sqrt(7 / 8 * ((fjk - fjk.mean()) ** 2).sum())
    mD = arr(c, lambda d: d["mid_ipsi"]); midr = drel(mD)[0]
    nmid_ipsi = lambda side: len(idx[f"mid_{side}"])
    hzD = np.mean([r["res"][c]["mid_ipsi"] / (len(idx[f"mid_{r['side']}"]) * .5) for r in runs if r["k"] is None])
    hzB = np.mean([r["res"][c]["mid_ipsi"] / (len(idx[f"mid_{r['side']}"]) * .5) for r in runs if r["k"] is not None])
    ihz = np.mean([np.array(r["res"][c]["n"])[inh].mean() / .5 for r in runs if r["k"] is None])
    dinh = arr(c, lambda d: d["dinh"]); pr = arr(c, lambda d: d["pr"]); isi = arr(c, lambda d: d["isi"][0]); dnr = arr(c, lambda d: d["dn"])
    print(f"{c:11s} {e:+7.3f} [{lo:+.3f};{hi:+.3f}] {fa:6.2f} [{fa-q*se:5.2f};{fa+q*se:5.2f}] {hzD:7.2f} {hzB:7.2f} {midr:+7.3f} {dinh[0].mean():7.1f} {dinh[1:].mean():7.1f} {ihz:9.2f} {pr[0].mean():5.2f} {pr[1:].mean():5.2f} {isi[0].mean():8.3f} {isi[1:].mean():8.3f} {dnr[1:].mean()-dnr[0].mean():+7.1f}")
print("per level Drel (8 | 9 mV):")
for c in conds:
    x = arr(c, lambda d: d["dexc"]); a8, a9 = drel(x, 0)[0], drel(x, 1)[0]
    hz = [np.mean([r["res"][c]["mid_ipsi"] / (len(idx[f"mid_{r['side']}"]) * .5) for r in runs if r["k"] is None and r["lv"] == lv]) for lv in (8.0, 9.0)]
    hzb = [np.mean([r["res"][c]["mid_ipsi"] / (len(idx[f"mid_{r['side']}"]) * .5) for r in runs if r["k"] is not None and r["lv"] == lv]) for lv in (8.0, 9.0)]
    print(f"  {c:11s} {a8:+.3f} | {a9:+.3f}   DATA mid Hz {hz[0]:.2f} | {hz[1]:.2f}   B1 mid Hz {hzb[0]:.2f} | {hzb[1]:.2f}")
print("per side Drel (L | R):")
for c in ("REF", "MT0", "MT0G", "MT0B", "MT0S", "MT1"):
    x = arr(c, lambda d: d["dexc"]); print(f"  {c:6s} {drel(x[:, :, 0:1])[0]:+.3f} | {drel(x[:, :, 1:2])[0]:+.3f}")
print("per B1 instance Drel REF / MT0G / MT0B:")
for k in range(1, 4):
    print("  ", srcs[k], [round(arr(c, lambda d: d["dexc"])[k].mean() / arr(c, lambda d: d["dexc"])[0].mean() - 1, 3) for c in ("REF", "MT0G", "MT0B", "MT1")])
# E-only mid rate match: excitatory mids only DATA rates per cond
print("DATA excitatory-mid mean Hz (all 147 mids, E only) per cond:", {c: round(np.mean([np.array(r['res'][c]['n'])[~inh].mean() / .5 for r in runs if r['k'] is None]), 2) for c in conds})
print("DATA inhibitory-mid mean Hz per cond:", {c: round(np.mean([np.array(r['res'][c]['n'])[inh].mean() / .5 for r in runs if r['k'] is None]), 2) for c in conds})
print("B1 inhibitory-mid mean Hz per cond:", {c: round(np.mean([np.array(r['res'][c]['n'])[inh].mean() / .5 for r in runs if r['k'] is not None]), 2) for c in conds})
