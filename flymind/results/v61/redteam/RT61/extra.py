"""RT-61 extra checks (read-only). RNG 8 498 404 (models), 8 498 405 (band contrasts)."""
import json, sys
import numpy as np
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind/results/v61/redteam/RT61")
exec(open("/Users/admin/so101_fly_project/flymind/results/v61/redteam/RT61/reanalysis.py").read().split("rng = np.random.default_rng(8498401)")[0])
def ols(rows_, cols, rng, n=4000):
    y = np.array([r["d"] for r in rows_]); cl = np.array([r["k"] for r in rows_])
    X = np.c_[np.ones(len(y)), np.array([[r[c] for c in cols] for r in rows_], float)]
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    u = np.unique(cl); ix = {c: np.flatnonzero(cl == c) for c in u}
    bs = np.array([np.linalg.lstsq(X[i], y[i], rcond=None)[0] for i in (np.concatenate([ix[c] for c in rng.choice(u, len(u))]) for _ in range(n))])
    lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
    return " ".join(f"{nm} {bb:+.3f} [{l:+.3f};{h:+.3f}]" for nm, bb, l, h in zip(["int"]+cols, b, lo, hi))
rng = np.random.default_rng(8498404)
for fam in ("SWS", "B1"):
    R_ = [dict(r, S2=float(r["st"]=="S2"), **{f"i{int(m)}": float(r["im"]==m) for m in IM[1:]}) for r in rows(fam)]
    print(fam, "d~Imax dummies+drive+S2      :", ols(R_, ["i10","i12","i14","i16","drive","S2"], rng))
    print(fam, "d~Imax dummies+gsum+rho      :", ols(R_, ["i10","i12","i14","i16","gsum","rho"], rng))
    print(fam, "d~Imax dummies+gsum+|az|+rho :", ols(R_, ["i10","i12","i14","i16","gsum","absaz","rho"], rng))
    print(fam, "Imax>=12: d~drive+S2         :", ols([r for r in R_ if r["im"]>=12], ["drive","S2"], rng))
    print(fam, "Imax>=12: d~Imax dum+drive+S2:", ols([r for r in R_ if r["im"]>=12], ["i14","i16","drive","S2"], rng))
# progress at low drive: travelled = |az0| - err ; DATA vs ctrl
print("== I8/I10 progress (deg of initial error removed) DATA vs SWS, both-moved pairs")
R_ = rows("SWS")
for im in (8.0, 10.0):
    for st in ("S1","S2"):
        x = [r for r in R_ if r["im"]==im and r["st"]==st]
        pA = np.array([r["absaz"]-r["eA"] for r in x]); pC = np.array([r["absaz"]-r["eC"] for r in x])
        nz = [r for r in x if r["d"] != 0]
        print(f"I{im:g}{st} mean|az0| {np.mean([r['absaz'] for r in x]):.2f} progress DATA {pA.mean():.2f} SWS {pC.mean():.2f}; nonzero pairs {len(nz)}; "
              f"of which |d|>1deg {sum(abs(r['d'])>1 for r in nz)}; err==|az0|(no progress) DATA {int(np.sum(np.isclose(pA,0,atol=0.05)))} SWS {int(np.sum(np.isclose(pC,0,atol=0.05)))}")
# nonzero-pair distribution at I8 S2
x = [r for r in R_ if r["im"]==8.0 and r["st"]=="S2" and r["d"]!=0]
print("I8 S2 nonzero pairs:", [(r["s"], round(r["d"],2), r["mA"], r["mC"], round(r["absaz"],1)) for r in x])
# shared-DATA term: corr between SWS and B1 d per cell
RS, RB = rows("SWS"), rows("B1")
print("== corr(d_SWS, d_B1) and corr(err_SWS, err_B1) per cell; share var(d) from DATA err")
for im in IM:
    for st in ("S1","S2"):
        a = [r for r in RS if r["im"]==im and r["st"]==st]; b = [r for r in RB if r["im"]==im and r["st"]==st]
        dS = np.array([r["d"] for r in a]); dB = np.array([r["d"] for r in b]); eS = np.array([r["eC"] for r in a]); eB = np.array([r["eC"] for r in b])
        dd = dB - dS   # = err_SWS - err_B1
        print(f"I{im:<4g}{st} r(d) {np.corrcoef(dS,dB)[0,1]:+.2f} r(errctrl) {np.corrcoef(eS,eB)[0,1]:+.2f} mean(err_SWS-err_B1) {dd.mean():+.3f}")
# zero pairs: are they exactly equal errors (identical trajectories)?
R_ = rows("SWS")
z = [r for r in R_ if r["d"]==0]
print("zero pairs", len(z), "of which neither moved", sum(1 for r in z if not r["mA"] and not r["mC"]))
# wall time by config (restart sanity)
recs61 = [json.loads(l) for l in open(R+"v61/v61.jsonl") if l.strip()]
for c in ("I8","I10","I14","I16"):
    w = [r["wall_s"] for r in recs61 if r["config"]==c]; print(c, "wall mean %.2f" % np.mean(w))
print("order of configs in file (run-length):", [(c, n) for c, n in __import__("itertools").groupby(r["config"] for r in recs61) for n in [len(list(n))]][:12])
# determinism: same scene, DATA at different I_max is distinct; check DATA I12 v6 vs nothing. Check moved / omega for I8 'neither' pairs: final err == |az0| ?
x = [r for r in R_ if r["im"]==8.0 and not r["mA"]]
print("I8 DATA not moved: max |err-|az0|| =", max(abs(r["eA"]-r["absaz"]) for r in x))
# matched-drive band contrast S1-S2 with cluster bootstrap (by k), band 8-11 mV
rng5 = np.random.default_rng(8498405)
for fam in ("SWS","B1"):
    R_ = rows(fam)
    for lo, hi in ((6,8),(8,11),(11,13)):
        x = [r for r in R_ if lo <= r["drive"] < hi]
        y = np.array([r["d"] for r in x]); s2 = np.array([r["st"]=="S2" for r in x]); cl = np.array([r["k"] for r in x])
        u = np.unique(cl); ix = {c: np.flatnonzero(cl==c) for c in u}
        bs = []
        for _ in range(4000):
            i = np.concatenate([ix[c] for c in rng5.choice(u, len(u))])
            if s2[i].any() and (~s2[i]).any(): bs.append(y[i][~s2[i]].mean() - y[i][s2[i]].mean())
        print(f"{fam} band [{lo},{hi}) S1-S2 diff {y[~s2].mean()-y[s2].mean():+.3f} CI [{np.percentile(bs,2.5):+.3f};{np.percentile(bs,97.5):+.3f}] nS1 {(~s2).sum()} nS2 {s2.sum()}")
