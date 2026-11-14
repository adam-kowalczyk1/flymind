"""flymind/v6m3_analysis.py — pre-specified analysis of V6m3 (protocol §2–§4). Written and hashed before the main run.
Run: .venv/bin/python -I -B flymind/v6m3_analysis.py --run flymind/results/v6m3
"""
import argparse
import glob
import json
import os

import numpy as np
from scipy import stats

NBOOT = 10_000
A_IDX = dict(dn=0, mid=1, dexc=2, dinh=3, pairr=4, lc=5)


def boot_ci(f, xD, xB, rng):
    """f(xD_rep_means, xB_inst_rep) → dict. xD [..., R], xB [K, ..., R]. Wider of nested bootstrap and jackknife-t over reps."""
    pt = f(xD, xB)
    K, R = xB.shape[0], xB.shape[-1]
    bs = {k: np.empty(NBOOT) for k in pt}
    for b in range(NBOOT):
        k = rng.integers(K, size=K)
        r = rng.integers(R, size=(K, R))
        sel = np.stack([xB[k[j]][..., r[j]] for j in range(K)])
        s = f(xD[..., rng.integers(R, size=R)], sel)
        for key in pt:
            bs[key][b] = s[key]
    jk = {key: [] for key in pt}
    for i in range(R):
        m = np.arange(R) != i
        s = f(xD[..., m], xB[..., m])
        for key in pt:
            jk[key].append(s[key])
    tq = stats.t.ppf(0.975, R - 1)
    out = {}
    for key, v in pt.items():
        j = np.array(jk[key])
        se = np.sqrt((R - 1) / R * ((j - j.mean()) ** 2).sum())
        p = [float(np.nanpercentile(bs[key], 2.5)), float(np.nanpercentile(bs[key], 97.5))]
        jt = [float(v - tq * se), float(v + tq * se)]
        out[key] = dict(est=float(v), ci_pct=p, ci_jackt=jt, ci=[min(p[0], jt[0]), max(p[1], jt[1])])
    return out


def part_a(D, B, conds, rng, lev=None):
    sl = slice(None) if lev is None else slice(lev, lev + 1)

    def m(x, q):                                   # [cond, lv, side, rep, q] → [cond, rep]
        return x[:, sl, :, :, A_IDX[q]].mean((1, 2))
    xD = np.stack([m(D["A"], q) for q in A_IDX])                       # [q, cond, rep]
    xB = np.stack([np.stack([m(b["A"], q) for q in A_IDX]) for b in B])  # [k, q, cond, rep]
    qi = {q: i for i, q in enumerate(A_IDX)}
    ci = {c: i for i, c in enumerate(conds)}

    def f(d, b):
        dm, bm = d.mean(-1), b.mean((0, -1))
        o = {}
        for c in conds:
            o[f"Drel|{c}"] = bm[qi["dexc"], ci[c]] / dm[qi["dexc"], ci[c]] - 1
            o[f"midrel|{c}"] = bm[qi["mid"], ci[c]] / dm[qi["mid"], ci[c]] - 1
            o[f"dngap|{c}"] = bm[qi["dn"], ci[c]] - dm[qi["dn"], ci[c]]
            o[f"pairr_B1minusD|{c}"] = bm[qi["pairr"], ci[c]] - dm[qi["pairr"], ci[c]]
        for c in ("MT0", "MT0G", "MT0B", "LCIRC"):
            o[f"FA|{c}"] = 1 - o[f"Drel|{c}"] / o["Drel|REF"]
        return o
    st = boot_ci(f, xD, xB, rng)
    means = {c: {q: dict(data=float(xD[qi[q], ci[c]].mean()), b1=float(xB[:, qi[q], ci[c]].mean())) for q in A_IDX} for c in conds}
    return st, means


def part_b(B, cells, dyn, rng, lev=None):
    sl = slice(None) if lev is None else slice(lev, lev + 1)
    X = np.stack([b["B"][:, :, sl].mean((2, 3)) for b in B])           # [k, dyn, cell, rep]
    c = {n: i for i, n in enumerate(cells)}

    def f(_d, x):
        y = x.mean((0, -1))                                             # [dyn, cell]
        o = {}
        for di, dn in enumerate(dyn):
            Y = {n: y[di, c[n]] for n in cells}
            L = {n: np.log(Y[n]) for n in cells}
            for tag, Z in (("", Y), ("log", L)):
                C = 0.5 * ((Z["DB"] - Z["DD"]) + (Z["BB"] - Z["BD"]))
                Tm = 0.5 * ((Z["BD"] - Z["DD"]) + (Z["BB"] - Z["DB"]))
                o[f"C{tag}|{dn}"], o[f"T{tag}|{dn}"] = C, Tm
                o[f"gap{tag}|{dn}"] = Z["BB"] - Z["DD"]
                o[f"inter{tag}|{dn}"] = Z["BB"] - Z["BD"] - Z["DB"] + Z["DD"]
                o[f"Cshare{tag}|{dn}"] = C / (C + Tm)
        return o
    dummy = np.zeros((1, X.shape[-1]))
    st = boot_ci(f, dummy, X, rng)
    means = {dn: {n: float(X[:, di, c[n]].mean()) for n in cells} for di, dn in enumerate(dyn)}
    return st, means


def decide(st):
    ex = lambda k: st[k]["ci"]   # noqa: E731
    qa_ok = ex("Drel|REF")[1] < 0
    hits = [bool(st[f"FA|{c}"]["est"] >= 0.5 and ex(f"FA|{c}")[0] > 0.25) for c in ("MT0G", "MT0B")]
    cat = "SUPPORTED" if qa_ok and all(hits) else "PARTIAL" if qa_ok and any(hits) else "NOT SUPPORTED"
    return dict(Drel_REF_neg=bool(qa_ok), MT0G_hit=hits[0], MT0B_hit=hits[1], H_IR=cat)


def routes(st):
    out = {}
    for tag in ("", "log"):
        for r in ("C", "T"):
            k = f"{r}{tag}|REF"
            out[f"{r}{tag}_present"] = bool(st[k]["ci"][1] < 0)
        out[f"count_dominant{tag}"] = bool(st[f"Cshare{tag}|REF"]["ci"][0] > 0.5)
        out[f"timing_dominant{tag}"] = bool(st[f"Cshare{tag}|REF"]["ci"][1] < 0.5)
    return out


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    raw = os.path.join(a.run, "raw")
    res = {}
    for sname, seed in (("MAIN", 8_419_080), ("REP", 8_419_081)):
        if not os.path.exists(os.path.join(raw, f"{sname}_DATA.npz")):
            continue
        rng = np.random.default_rng(seed)
        D = np.load(os.path.join(raw, f"{sname}_DATA.npz"))
        B = [np.load(p) for p in sorted(glob.glob(os.path.join(raw, f"{sname}_B1_*.npz")))]
        conds, cells, dyn = list(D["a_conds"]), list(B[0]["b_cells"]), list(B[0]["b_dyn"])
        stA, mA = part_a(D, B, conds, rng)
        stB, mB = part_b(B, cells, dyn, rng)
        per_level = {}
        for li, lv in enumerate(D["levels"].tolist()):
            sa, _ = part_a(D, B, conds, np.random.default_rng(seed + 10 + li), li)
            sb, _ = part_b(B, cells, dyn, np.random.default_rng(seed + 20 + li), li)
            per_level[str(lv)] = {k: v["est"] for k, v in {**sa, **sb}.items() if k.startswith(("Drel|", "FA|", "C|", "T|", "gap|", "Cshare|"))}
        added = np.stack([b["added"] for b in B])
        res[sname] = dict(n_b1=len(B), partA=dict(stats=stA, means=mA), partB=dict(stats=stB, means=mB), per_level=per_level,
                          decision_QA=decide(stA), routes_QB=routes(stB),
                          added_frac=dict(DB=float(added[:, 0].mean()), BD=float(added[:, 1].mean())))
    res["calibration"] = json.load(open(os.path.join(a.run, "calibration.json")))
    res["calibration"].pop("curves", None)
    with open(os.path.join(a.run, "analysis.json"), "x") as f:
        json.dump(res, f, indent=1)
    for sname in ("MAIN", "REP"):
        if sname not in res:
            continue
        r = res[sname]
        print(f"===== {sname} (B1 n = {r['n_b1']}); added spikes DB {r['added_frac']['DB']:.3f} BD {r['added_frac']['BD']:.3f}")
        for c, m in r["partA"]["means"].items():
            print(f"  A {c:6s} mid ipsi count D/B {m['mid']['data']:7.1f}/{m['mid']['b1']:7.1f} | Dexc {m['dexc']['data']:7.1f}/{m['dexc']['b1']:7.1f}"
                  f" | DN {m['dn']['data']:6.1f}/{m['dn']['b1']:6.1f} | pair r {m['pairr']['data']:.3f}/{m['pairr']['b1']:.3f}")
        for k, v in r["partA"]["stats"].items():
            print(f"  A {k:24s} {v['est']:+8.3f} CI [{v['ci'][0]:+.3f};{v['ci'][1]:+.3f}]")
        for dn, m in r["partB"]["means"].items():
            print(f"  B {dn:4s} " + " ".join(f"{n} {v:6.1f}" for n, v in m.items()))
        for k, v in r["partB"]["stats"].items():
            print(f"  B {k:16s} {v['est']:+8.3f} CI [{v['ci'][0]:+.3f};{v['ci'][1]:+.3f}]")
        print("  per level", json.dumps({lv: {k: round(x, 3) for k, x in d.items() if k.startswith(("Drel|REF", "FA|MT0G", "FA|MT0B", "C|REF", "T|REF", "Cshare|REF"))} for lv, d in r["per_level"].items()}))
        print("  decision QA", r["decision_QA"], "| routes QB", r["routes_QB"])
    print("calibration", res["calibration"])


if __name__ == "__main__":
    main()
