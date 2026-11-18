"""RT-61 re-analysis (read-only). RNG 8 498 401 (cell CIs), 8 498 402 (drive models), 8 498 403 (matched-drive)."""
import json, collections
import numpy as np
R = "/Users/admin/so101_fly_project/flymind/results/"
recs = [json.loads(l) for l in open(R+"v61/v61.jsonl") if l.strip()]
v6 = [json.loads(l) for l in open(R+"v6/closedloop.jsonl") if l.strip()]
recs += [dict(r, config="I12", i_max=12.0) for r in v6 if r["config"] == "D0"]
by = {(r["i_max"], r["family"], r["seed"]): r for r in recs}
drv = {x["seed"]: x for x in json.load(open(R+"v61/drive_index.json")) if "block" not in x}
IM = (8.0, 10.0, 12.0, 14.0, 16.0)
def rows(fam):
    out = []
    for im in IM:
        for s in range(8600001, 8600121):
            a, c = by[(im, "DATA", s)], by[(im, fam, s)]
            g = drv[s]; gm = max(g["gL"], g["gR"])
            out.append(dict(im=im, s=s, st=c["stratum"], k=c["k"], rho=c["rho"], az=c["az0_deg"], d=a["final_abs_err"]-c["final_abs_err"],
                            mA=a["moved"], mC=c["moved"], eA=a["final_abs_err"], eC=c["final_abs_err"], drive=gm*im, g=gm,
                            gsum=(g["gL"]+g["gR"])*im, gdiff=abs(g["gL"]-g["gR"])*im, absaz=abs(c["az0_deg"])))
    return out
def cboot(d, cl, rng, n=10000):
    u = np.unique(cl); ix = {c: np.flatnonzero(cl == c) for c in u}
    bs = np.array([d[np.concatenate([ix[c] for c in rng.choice(u, len(u))])].mean() for _ in range(n)])
    return np.percentile(bs, [2.5, 97.5])
rng = np.random.default_rng(8498401)
print("== cells: n, mean d, CI (RNG 8498401), median, zero, bothmoved n & mean d, onlyDATA, onlyCTRL, neither, mean d among both-moved, contribution of one-moved to sum d")
for fam in ("SWS", "B1"):
    R_ = rows(fam)
    for im in IM:
        for st in ("S1", "S2"):
            x = [r for r in R_ if r["im"] == im and r["st"] == st]
            d = np.array([r["d"] for r in x]); cl = np.array([r["k"] for r in x])
            ci = cboot(d, cl, rng)
            both = [r["d"] for r in x if r["mA"] and r["mC"]]
            oA = [r["d"] for r in x if r["mA"] and not r["mC"]]; oC = [r["d"] for r in x if r["mC"] and not r["mA"]]
            nei = [r["d"] for r in x if not r["mA"] and not r["mC"]]
            share = (sum(oA)+sum(oC))/d.sum() if d.sum() else float("nan")
            print(f"{fam:3s} I{im:<4g}{st} n{len(d):3d} d{d.mean():+.3f} [{ci[0]:+.3f};{ci[1]:+.3f}] med{np.median(d):+.3f} zero{int((d==0).sum()):3d} "
                  f"both{len(both):3d} dboth{(np.mean(both) if both else float('nan')):+.3f} onlyD{len(oA):2d}({sum(oA):+.1f}) onlyC{len(oC):2d}({sum(oC):+.1f}) neither{len(nei):3d}(nonzero {sum(1 for v in nei if v!=0)}) "
                  f"sum_d_both{sum(both):+.1f} share_onemoved {share:.2f}")
print("== drive index per I_max x stratum (mV), corr(drive, rho) within cell, corr(g, |az|)")
R_ = rows("SWS")
for im in IM:
    for st in ("S1", "S2"):
        x = [r for r in R_ if r["im"] == im and r["st"] == st]
        dv = np.array([r["drive"] for r in x]); rh = np.array([r["rho"] for r in x]); aa = np.array([r["absaz"] for r in x])
        print(f"I{im:<4g}{st} drive med {np.median(dv):.2f} [{dv.min():.2f},{dv.max():.2f}] r(drive,rho) {np.corrcoef(dv,rh)[0,1]:+.2f} r(drive,|az|) {np.corrcoef(dv,aa)[0,1]:+.2f}")
g = np.array([drv[s]["gL"] for s in range(8600001,8600121)]), np.array([drv[s]["gR"] for s in range(8600001,8600121)])
gm = np.maximum(*g); rho = np.array([by[(12.0,"DATA",s)]["rho"] for s in range(8600001,8600121)])
print("scene-level g_max range", gm.min(), gm.max(), "r(g_max, rho) all scenes", np.corrcoef(gm, rho)[0,1], "within S1", np.corrcoef(gm[:40], rho[:40])[0,1], "within S2", np.corrcoef(gm[40:], rho[40:])[0,1])
# pooled design collinearity
X = np.array([[r["drive"], r["rho"]] for r in R_])
print("pooled r(drive, rho)", np.corrcoef(X.T)[0,1], "VIF", 1/(1-np.corrcoef(X.T)[0,1]**2))
def ols(rows_, cols, rng, n=5000):
    y = np.array([r["d"] for r in rows_]); cl = np.array([r["k"] for r in rows_])
    X = np.c_[np.ones(len(y)), np.array([[c(r) if callable(c) else r[c] for c in cols] for r in rows_], float)]
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    u = np.unique(cl); ix = {c: np.flatnonzero(cl == c) for c in u}
    bs = np.array([np.linalg.lstsq(X[i], y[i], rcond=None)[0] for i in (np.concatenate([ix[c] for c in rng.choice(u, len(u))]) for _ in range(n))])
    lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
    return " ".join(f"{nm} {bb:+.3f} [{l:+.3f};{h:+.3f}]" for nm, bb, l, h in zip(["int"]+[c if isinstance(c,str) else "f" for c in cols], b, lo, hi))
rng2 = np.random.default_rng(8498402)
print("== drive models (RNG 8498402)")
for fam in ("SWS", "B1"):
    R_ = rows(fam)
    print(fam, "replicate  d~drive+rho          :", ols(R_, ["drive", "rho"], rng2))
    print(fam, "excl I8                          :", ols([r for r in R_ if r["im"] != 8], ["drive", "rho"], rng2))
    print(fam, "excl I8,I10                      :", ols([r for r in R_ if r["im"] >= 12], ["drive", "rho"], rng2))
    print(fam, "both moved only                  :", ols([r for r in R_ if r["mA"] and r["mC"]], ["drive", "rho"], rng2))
    print(fam, "rho per 0.1 m (scaled) all       :", ols([dict(r, rho10=r["rho"]*10) for r in R_], ["drive", "rho10"], rng2))
    print(fam, "d~drive+S2 indicator             :", ols([dict(r, S2=float(r["st"]=="S2")) for r in R_], ["drive", "S2"], rng2))
    print(fam, "d~drive+drive^2+rho              :", ols([dict(r, dr2=r["drive"]**2) for r in R_], ["drive", "dr2", "rho"], rng2))
    print(fam, "d~I_max+rho (manipulated factor) :", ols(R_, ["im", "rho"], rng2))
    print(fam, "d~I_max dummies+drive+rho        :", ols([dict(r, **{f"i{int(m)}": float(r["im"]==m) for m in IM[1:]}) for r in R_], ["i10","i12","i14","i16","drive","rho"], rng2))
    print(fam, "within I_max (cell) drive+rho:")
    for im in IM:
        x = [r for r in R_ if r["im"] == im]
        print("   I%g" % im, ols(x, ["drive", "rho"], rng2, n=2000))
# matched-drive comparison: bin drive, compare S1 vs S2 cells in the overlap
print("== matched-drive S1 vs S2 (SWS), bins of drive_index [mV]; all I_max pooled")
for fam in ("SWS","B1"):
    R_ = rows(fam)
    for lo, hi in ((6,7),(7,8),(8,9),(9,10),(10,11),(11,12),(12,13),(13,14),(14,15),(15,16)):
        s1 = [r for r in R_ if lo <= r["drive"] < hi and r["st"]=="S1"]; s2 = [r for r in R_ if lo <= r["drive"] < hi and r["st"]=="S2"]
        f = lambda x: f"n{len(x):3d} d{np.mean([r['d'] for r in x]):+.2f} I_max{sorted({int(r['im']) for r in x})}" if x else "n  0"
        print(f"{fam} drive[{lo},{hi}) S1 {f(s1):40s} S2 {f(s2)}")
