"""RT-61 scratch re-analysis of V6.1 (no simulation). RNG 8 498 401 (cell CIs), 8 498 402 (models), 8 498 403 (drive bins)."""
import json, collections, sys
import numpy as np
B = "flymind/results/"
L = lambda p: [json.loads(l) for l in open(B + p)]
R = L("v61/v61.jsonl")
D0 = [dict(r, config="I12", i_max=12.0) for r in L("v6/closedloop.jsonl") if r["config"] == "D0"]
A = json.load(open(B + "v61/analysis.json"))
DI = {r["seed"]: r for r in json.load(open(B + "v61/drive_index.json")) if "block" not in r}
by = {(r["config"], r["family"], r["seed"]): r for r in R + D0}
IM = (8, 10, 12, 14, 16)

def rows(im, fam, st="ALL"):
    out = []
    for s in range(8_600_001, 8_600_121):
        a, c = by[(f"I{im}", "DATA", s)], by[(f"I{im}", fam, s)]
        if st != "ALL" and a["stratum"] != st: continue
        g = DI[s]; out.append(dict(seed=s, k=c["k"], st=a["stratum"], rho=a["rho"], az=a["az0_deg"], im=im,
             drive=max(g["gL"], g["gR"]) * im, gdiff=abs(g["gL"] - g["gR"]) * im,
             d=a["final_abs_err"] - c["final_abs_err"], ea=a["final_abs_err"], ec=c["final_abs_err"],
             ma=a["moved"], mc=c["moved"], sa=a["final_signed_err"], sc=c["final_signed_err"]))
    return out

def cboot(x, k, rng, n=10000, f=np.mean):
    u = np.unique(k); idx = {c: np.flatnonzero(k == c) for c in u}
    bs = [f(x[np.concatenate([idx[c] for c in rng.choice(u, len(u))])]) for _ in range(n)]
    return np.percentile(bs, [2.5, 97.5])

rng = np.random.default_rng(8_498_401)
print("== cell recompute (RNG 8498401) vs analysis.json; both-moved subset; discordant")
for im in IM:
    for fam in ("SWS", "B1"):
        for st in ("S1", "S2"):
            x = rows(im, fam, st); d = np.array([r["d"] for r in x]); k = np.array([r["k"] for r in x])
            ci = cboot(d, k, rng); a = A["per_imax"][f"I{im}|{fam}|{st}"]
            bm = np.array([r["ma"] and r["mc"] for r in x]); nm = np.array([not r["ma"] and not r["mc"] for r in x])
            oa = sum(r["ma"] and not r["mc"] for r in x); oc = sum(r["mc"] and not r["ma"] for r in x)
            dbm = d[bm]; cib = cboot(dbm, k[bm], rng, 4000) if bm.sum() > 3 else [np.nan, np.nan]
            print(f"I{im:2d} {fam:3s} {st} n{len(d)} d {d.mean():+.3f} [{ci[0]:+.3f};{ci[1]:+.3f}] (json {a['mean_d']:+.3f} [{a['ci95_cluster'][0]:+.3f};{a['ci95_cluster'][1]:+.3f}]) "
                  f"zeros {(d==0).sum()} neither-moved {nm.sum()} onlyDATA {oa} onlyCTRL {oc} | both-moved n{bm.sum()} d {dbm.mean() if bm.any() else np.nan:+.3f} [{cib[0]:+.3f};{cib[1]:+.3f}] "
                  f"| discordant sum d {d[~bm & ~nm].sum():+.2f} of total {d.sum():+.2f}")
print("== zero pairs identical to neither-moved?")
for im in IM:
    x = rows(im, "SWS"); print(im, sum(r["d"] == 0 for r in x), sum((not r["ma"]) and (not r["mc"]) for r in x), "zero&both moved", sum(r["d"] == 0 and r["ma"] and r["mc"] for r in x))
print("== SWS vs B1 share the DATA arm: corr of per-scene d, and direct err(SWS)-err(B1)")
rng2 = np.random.default_rng(8_498_402)
for im in IM:
    s, b = rows(im, "SWS"), rows(im, "B1")
    ds, db = np.array([r["d"] for r in s]), np.array([r["d"] for r in b])
    sb = np.array([r["ec"] for r in s]) - np.array([r["ec"] for r in b])
    print(im, "corr(d_SWS,d_B1) %.2f" % np.corrcoef(ds, db)[0, 1], "corr(ctrl errs) %.2f" % np.corrcoef([r["ec"] for r in s], [r["ec"] for r in b])[0, 1],
          "mean err(SWS)-err(B1) %+.3f" % sb.mean())
print("== drive model variants (cluster bootstrap over control instance, RNG 8498402, 2000 reps)")
def ols(x, cols, fam, n=2000):
    X = np.c_[[np.ones(len(x))] + [[c(r) for r in x] for c in cols]].T if False else np.column_stack([np.ones(len(x))] + [np.array([c(r) for r in x], float) for c in cols])
    y = np.array([r["d"] for r in x]); k = np.array([r["k"] for r in x])
    b = np.linalg.lstsq(X, y, rcond=None)[0]; u = np.unique(k); idx = {c: np.flatnonzero(k == c) for c in u}
    bs = np.array([np.linalg.lstsq(X[i], y[i], rcond=None)[0] for i in (np.concatenate([idx[c] for c in rng2.choice(u, len(u))]) for _ in range(n))])
    return b, np.percentile(bs, [2.5, 97.5], 0), X
for fam in ("SWS", "B1"):
    x = [r for im in IM for r in rows(im, fam)]
    b, ci, X = ols(x, [lambda r: r["drive"], lambda r: r["rho"]], fam)
    print(fam, "replicate drive,rho", b.round(4), ci.round(3).tolist())
    Z = (X[:, 1:] - X[:, 1:].mean(0)) / X[:, 1:].std(0); c = np.corrcoef(Z.T)[0, 1]; print("   corr(drive,rho) pooled %.3f VIF %.2f" % (c, 1 / (1 - c * c)))
    for im in IM:
        xi = [r for r in x if r["im"] == im]; dr = [r["drive"] for r in xi]; rh = [r["rho"] for r in xi]
        print("   I%d corr(drive,rho) %.3f" % (im, np.corrcoef(dr, rh)[0, 1]))
    b, ci, _ = ols(x, [lambda r: r["drive"], lambda r: r["drive"] ** 2, lambda r: r["rho"]], fam)
    print(fam, "quadratic drive + rho", b.round(4), ci.round(3).tolist())
    b, ci, _ = ols(x, [lambda r: r["drive"], lambda r: r["st"] == "S2"], fam)
    print(fam, "drive + S2 dummy", b.round(4), ci.round(3).tolist())
    b, ci, _ = ols(x, [lambda r, m=m: r["im"] == m for m in (10, 12, 14, 16)] + [lambda r: r["rho"]], fam)
    print(fam, "I_max fixed effects + rho (within-I_max rho)", b.round(3), ci.round(3).tolist())
    xn = [r for r in x if r["im"] != 8]
    b, ci, _ = ols(xn, [lambda r: r["drive"], lambda r: r["rho"]], fam)
    print(fam, "drive+rho excl I8", b.round(4), ci.round(3).tolist())
    for im in IM:
        xi = [r for r in x if r["im"] == im]
        b, ci, _ = ols(xi, [lambda r: r["drive"], lambda r: r["rho"]], fam, 1000)
        print(f"   within I{im}: drive {b[1]:+.3f} [{ci[0,1]:+.3f};{ci[1,1]:+.3f}] rho {b[2]:+.2f} [{ci[0,2]:+.2f};{ci[1,2]:+.2f}]")
print("== matched-drive S1 vs S2 (drive bins, pooled I_max; RNG 8498403)")
rng3 = np.random.default_rng(8_498_403)
for fam in ("SWS", "B1"):
    x = [r for im in IM for r in rows(im, fam)]
    for lo, hi in ((4, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12.5)):
        line = f"{fam} drive [{lo},{hi})"
        for st in ("S1", "S2"):
            xi = [r for r in x if lo <= r["drive"] < hi and r["st"] == st]
            if len(xi) < 8: line += f" | {st} n{len(xi)}"; continue
            d = np.array([r["d"] for r in xi]); k = np.array([r["k"] for r in xi]); ci = cboot(d, k, rng3, 3000)
            ims = collections.Counter(r["im"] for r in xi)
            line += f" | {st} n{len(d)} d {d.mean():+.3f} [{ci[0]:+.3f};{ci[1]:+.3f}] I_max {dict(sorted(ims.items()))}"
        print(line)
print("== same scene across I_max: sign pattern per scene (SWS)")
for st in ("S1", "S2"):
    M = np.array([[r["d"] for r in rows(im, "SWS", st)] for im in IM])
    print(st, "frac d>0 per I_max", ((M > 0).mean(1)).round(2), "frac d<0", ((M < 0).mean(1)).round(2))
print("== DATA vs ctrl moved fractions & mean err per I_max (both strata), signed error bias")
for im in IM:
    for st in ("S1", "S2"):
        x = rows(im, "SWS", st)
        print(im, st, "DATA moved %.2f SWS moved %.2f  DATA err %.2f SWS err %.2f  mean signed DATA %+.2f SWS %+.2f  mean|az0| %.2f"
              % (np.mean([r["ma"] for r in x]), np.mean([r["mc"] for r in x]), np.mean([r["ea"] for r in x]), np.mean([r["ec"] for r in x]),
                 np.mean([r["sa"] for r in x]), np.mean([r["sc"] for r in x]), np.mean([abs(r["az"]) for r in x])))
