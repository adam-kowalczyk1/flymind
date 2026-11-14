"""RT-7 independent recompute of V7 (no new trials). RNG 8_498_401 (bootstrap), 8_498_402 (seed-level bootstrap)."""
import json, sys
import numpy as np
F = "/Users/admin/so101_fly_project/flymind/"
recs = [json.loads(l) for l in open(F + "results/v7/v7.jsonl")]
drv = {r["seed"]: r for r in json.load(open(F + "results/v61/drive_index.json")) if "block" in r}
v6d = {r["seed"]: r for r in json.load(open(F + "results/v61/drive_index.json")) if "block" not in r}
cal = json.load(open(F + "results/v6/calibration.json"))
print("n", len(recs), "errors", sum(1 for r in recs if r.get("error")), "names unique", len({r["name"] for r in recs}))
# integrity: slope, noise, scene
from collections import Counter
print(Counter((r["config"], r["cond"], r["family"], round(r["slope"], 3), json.dumps(r["alif"])) for r in recs))
print("SG6", cal["SG6"]["slope"], "D0", cal["D0"]["slope"])
T = {}
for r in recs:
    c = "P" if r["cond"] == "classical_p" else r["family"]
    T[(r["config"], c, r["seed"])] = r
# scene consistency across conditions
bad = [s for (b, c, s) in T if c == "DATA" and any(abs(T[(b, x, s)]["rho"] - T[(b, c, s)]["rho"]) > 0 or T[(b, x, s)]["az0_deg"] != T[(b, c, s)]["az0_deg"] for x in ("SWS", "P"))]
print("scene mismatches", len(bad))
rng = np.random.default_rng(8_498_401)
rng2 = np.random.default_rng(8_498_402)
def boot(d, cl, rng, n=10000):
    u = np.unique(cl); idx = {c: np.flatnonzero(cl == c) for c in u}
    bs = [d[np.concatenate([idx[c] for c in rng.choice(u, len(u))])].mean() for _ in range(n)]
    return np.percentile(bs, [2.5, 97.5]).round(3).tolist()
def rows(b, sel):
    seeds = sorted({s for (bb, c, s) in T if bb == b})
    return [s for s in seeds if sel(T[(b, "DATA", s)])]
sub = {"G1": {"ALL": lambda r: True}, "G4": {"ALL": lambda r: True}}
for b in ("G2", "G3"):
    sub[b] = {"ALL": lambda r: True, "near": lambda r: r["rho"] < 0.22, "far": lambda r: r["rho"] >= 0.22}
for b in ("G1", "G2", "G3", "G4"):
    for sn, sel in sub[b].items():
        ss = rows(b, sel)
        D = [T[(b, "DATA", s)] for s in ss]; S = [T[(b, "SWS", s)] for s in ss]; P = [T[(b, "P", s)] for s in ss]
        e = lambda X: np.array([x["final_abs_err"] for x in X])
        d = e(D) - e(S); dp = e(D) - e(P)
        k = np.array([x["k"] for x in S]); sd = np.array(ss)
        g = np.array([max(drv[s]["gL"], drv[s]["gR"]) * 12 for s in ss])
        m = lambda X, f: np.mean([x[f] for x in X])
        print(f"{b} {sn:4s} n {len(ss):3d} drive med {np.median(g):5.2f} [{np.percentile(g,10):.2f},{np.percentile(g,90):.2f}] "
              f"DATA {e(D).mean():.2f}/{np.median(e(D)):.2f} SWS {e(S).mean():.2f} P {e(P).mean():.2f} "
              f"succ D/S/P {m(D,'success'):.2f}/{m(S,'success'):.2f}/{m(P,'success'):.2f} moved {m(D,'moved'):.2f}/{m(S,'moved'):.2f} "
              f"d {d.mean():+.3f} clusterCI {boot(d,k,rng)} seedCI {boot(d,sd,rng2,4000)} med {np.median(d):+.3f} zeros {(d==0).sum()} "
              f"d>0 {(d>0).sum()} d<0 {(d<0).sum()} dP {dp.mean():+.2f} {boot(dp,sd,rng2,2000)} ovD-S {np.mean([x['overshoot_deg'] for x in D])-np.mean([x['overshoot_deg'] for x in S]):+.2f}")
# drive overlap: G2 near vs G4, V6 S1
for lab, gs in [("V6 S1", [max(v6d[s]["gL"], v6d[s]["gR"]) * 12 for s in v6d if s <= 8_600_040]),
                ("V6 S2", [max(v6d[s]["gL"], v6d[s]["gR"]) * 12 for s in v6d if s > 8_600_040])]:
    print(lab, "drive@12 median", round(float(np.median(gs)), 2), "range", round(min(gs), 2), round(max(gs), 2))
for imx in (8, 10, 12, 14, 16):
    gs = [max(v6d[s]["gL"], v6d[s]["gR"]) * imx for s in v6d if s <= 8_600_040]
    print(f"V6 S1 @I{imx} median {np.median(gs):.2f}")
# G1 : nonzero pairs
ss = rows("G1", lambda r: True)
nz = [(s, T[("G1","DATA",s)]["moved"], T[("G1","SWS",s)]["moved"], round(T[("G1","DATA",s)]["final_abs_err"]-T[("G1","SWS",s)]["final_abs_err"],2)) for s in ss if T[("G1","DATA",s)]["final_abs_err"]!=T[("G1","SWS",s)]["final_abs_err"]]
print("G1 nonzero pairs", len(nz), "both moved", sum(1 for x in nz if x[1] and x[2]), "only DATA", sum(1 for x in nz if x[1] and not x[2]), "only SWS", sum(1 for x in nz if x[2] and not x[1]), "neither", sum(1 for x in nz if not x[1] and not x[2]))
print("G1 nonzero d sum", round(sum(x[3] for x in nz), 2), "largest", sorted(x[3] for x in nz)[:5], sorted(x[3] for x in nz)[-5:])
# G1 drive vs moved
g = np.array([max(drv[s]["gL"], drv[s]["gR"]) * 12 for s in ss]); mv = np.array([T[("G1","DATA",s)]["moved"] for s in ss])
print("G1 drive moved med", np.median(g[mv]).round(2), "not moved med", np.median(g[~mv]).round(2))
# G4 success: what is the success criterion? signed final err, overshoot
for b in ("G4", "G2"):
    ss = rows(b, lambda r: True)
    for c in ("DATA", "SWS", "P"):
        X = [T[(b, c, s)] for s in ss]
        print(b, c, "final_abs_err q", np.percentile([x["final_abs_err"] for x in X], [10, 50, 90]).round(2), "e_sd_last1s mean", round(float(np.mean([x["e_sd_last1s"] for x in X])), 3),
              "overshoot mean", round(float(np.mean([x["overshoot_deg"] for x in X])), 2), "signed err mean", round(float(np.mean([x["final_signed_err"]*np.sign(x["az0_deg"]) for x in X])), 2))
# G4 by drive tercile & by rho-split (does reversal hold across G4?)
ss = rows("G4", lambda r: True)
g = np.array([max(drv[s]["gL"], drv[s]["gR"]) * 12 for s in ss]); d = np.array([T[("G4","DATA",s)]["final_abs_err"]-T[("G4","SWS",s)]["final_abs_err"] for s in ss])
for lo, hi in ((0, 33), (33, 67), (67, 100)):
    m = (g >= np.percentile(g, lo)) & (g <= np.percentile(g, hi))
    print(f"G4 drive pct {lo}-{hi}: drive {g[m].min():.2f}-{g[m].max():.2f} d {d[m].mean():+.3f} n {m.sum()}")
# pooled drive-binned d across V7 blocks except G3 (noise) and G1
allr = []
for b in ("G1", "G2", "G4"):
    for s in rows(b, lambda r: True):
        allr.append((max(drv[s]["gL"], drv[s]["gR"]) * 12, T[(b,"DATA",s)]["final_abs_err"]-T[(b,"SWS",s)]["final_abs_err"], b, T[(b,"SWS",s)]["k"]))
allr.sort()
A = np.array([x[:2] for x in allr]); K = np.array([x[3] for x in allr]); B = [x[2] for x in allr]
for lo, hi in ((0, 4), (4, 6), (6, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 99)):
    m = (A[:, 0] >= lo) & (A[:, 0] < hi)
    if m.sum() > 5:
        print(f"drive [{lo},{hi}) n {m.sum():3d} blocks {dict(Counter(np.array(B)[m]))} d {A[m,1].mean():+.3f} CI {boot(A[m,1], K[m], rng, 4000)}")
# G2 near / G3 near vs G4 drive
for b, sn, sel in (("G2","near",lambda r:r["rho"]<0.22),("G2","far",lambda r:r["rho"]>=0.22),("G3","near",lambda r:r["rho"]<0.22),("G3","far",lambda r:r["rho"]>=0.22)):
    ss = rows(b, sel); g = [max(drv[s]["gL"], drv[s]["gR"]) * 12 for s in ss]
    print(b, sn, "drive median", round(float(np.median(g)), 2))
