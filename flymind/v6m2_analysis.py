"""flymind/v6m2_analysis.py — pre-specified analysis of V6m2 (protocol §2). Written before the main-run results were opened.
Run: .venv/bin/python -I -B flymind/v6m2_analysis.py --run flymind/results/v6m2
"""
import argparse
import glob
import json
import os

import numpy as np
from scipy import stats

NBOOT = 10_000


def load(run, arm):
    D = np.load(os.path.join(run, "raw", f"{arm}_DATA.npz"))
    B = [np.load(p) for p in sorted(glob.glob(os.path.join(run, "raw", f"{arm}_B1_*.npz")))]
    dyn, inp = list(D["dyn"]), list(D["inputs"])
    xD = D["dn"].mean((2, 3))                                   # [dyn, inp, rep]
    xB = np.stack([b["dn"].mean((2, 3)) for b in B])           # [k, dyn, inp, rep]
    return dict(D=D, B=B, dyn=dyn, inp=inp, xD=xD, xB=xB)


def stat_fn(dyn, inp):
    """Returns f(mD[dyn, inp], mB[dyn, inp]) → dict of statistics (Hz and log-ratio)."""
    d, i = {n: k for k, n in enumerate(dyn)}, {n: k for k, n in enumerate(inp)}

    def f(mD, mB):
        out = {}
        for dn in dyn:
            for x in inp:
                out[f"gap|{dn}|{x}"] = mB[d[dn], i[x]] - mD[d[dn], i[x]]
                out[f"L|{dn}|{x}"] = np.log(mB[d[dn], i[x]] / mD[d[dn], i[x]])
            for x in ("MASYNC", "MCIRC"):
                out[f"dt|{dn}|{x}"] = out[f"gap|{dn}|{x}"] - out[f"gap|{dn}|M0"]
                out[f"dtL|{dn}|{x}"] = out[f"L|{dn}|{x}"] - out[f"L|{dn}|M0"]
        for dn in dyn:
            if dn != "REF":
                for x in ("MASYNC", "MCIRC"):
                    out[f"I|{dn}|{x}"] = out[f"dt|REF|{x}"] - out[f"dt|{dn}|{x}"]
                    out[f"IL|{dn}|{x}"] = out[f"dtL|REF|{x}"] - out[f"dtL|{dn}|{x}"]
                out[f"Fmatch|{dn}"] = 1 - out[f"gap|{dn}|M0"] / out["gap|REF|M0"]
                out[f"FmatchL|{dn}"] = 1 - out[f"L|{dn}|M0"] / out["L|REF|M0"]
            out[f"countshare|{dn}"] = out[f"gap|{dn}|MASYNC"] / out[f"gap|{dn}|M0"]
        return out
    return f


def analyse(run, arm, rng):
    S = load(run, arm)
    xD, xB = S["xD"], S["xB"]
    f = stat_fn(S["dyn"], S["inp"])
    pt = f(xD.mean(-1), xB.mean((0, -1)))
    K, R = xB.shape[0], xB.shape[-1]
    bs = {k: np.empty(NBOOT) for k in pt}
    for b in range(NBOOT):
        k = rng.integers(K, size=K)
        r = rng.integers(R, size=(K, R))
        sel = np.stack([xB[k[j]][..., r[j]] for j in range(K)])
        dd = xD[..., rng.integers(xD.shape[-1], size=xD.shape[-1])]
        s = f(dd.mean(-1), sel.mean((0, -1)))
        for key in pt:
            bs[key][b] = s[key]
    # jackknife over reps (reps are crossed with source by common noise seeds: leave rep i out everywhere)
    jk = {key: [] for key in pt}
    for i in range(R):
        m = np.ones(R, bool)
        m[i] = False
        s = f(xD[..., m].mean(-1), xB[..., m].mean((0, -1)))
        for key in pt:
            jk[key].append(s[key])
    tq = stats.t.ppf(0.975, R - 1)
    out = {}
    for key, v in pt.items():
        j = np.array(jk[key])
        se = np.sqrt((R - 1) / R * ((j - j.mean()) ** 2).sum())
        p = [float(np.percentile(bs[key], 2.5)), float(np.percentile(bs[key], 97.5))]
        jt = [float(v - tq * se), float(v + tq * se)]
        out[key] = dict(est=float(v), ci_pct=p, ci_jackt=jt, ci_wide=[min(p[0], jt[0]), max(p[1], jt[1])])
    means = {f"{dn}|{x}": dict(data=float(xD[a, b].mean()), b1=float(xB[:, a, b].mean())) for a, dn in enumerate(S["dyn"]) for b, x in enumerate(S["inp"])}
    # per level (descriptive)
    lv = S["D"]["levels"].tolist()
    per_level = {}
    for li, L in enumerate(lv):
        pD = S["D"]["dn"][:, :, li].mean(2)                      # [dyn, inp, rep]
        pB = np.stack([b["dn"][:, :, li].mean(2) for b in S["B"]])
        s = f(pD.mean(-1), pB.mean((0, -1)))
        per_level[str(L)] = {k: float(s[k]) for k in s if k.startswith(("dt|", "I|", "gap|REF|M0", "gap|T0B|M0"))}
    shortD = {dn: float(np.nanmean(S["D"]["short_isi"][a, 0])) for a, dn in enumerate(S["dyn"])}
    shortB = {dn: float(np.nanmean([np.nanmean(b["short_isi"][a, 0]) for b in S["B"]])) for a, dn in enumerate(S["dyn"])}
    return dict(n_b1=K, n_reps=R, levels=lv, bias=float(S["D"]["bias"]), means=means, stats=out, per_level=per_level,
                short_isi_M0=dict(data=shortD, b1=shortB))


def decide(a):
    s = a["stats"]
    ex0 = lambda k: s[k]["ci_wide"][0] > 0 or s[k]["ci_wide"][1] < 0   # noqa: E731
    dtR, dtB = s["dt|REF|MASYNC"], s["dt|T0B|MASYNC"]
    crit = dict(a_dt_REF_pos=bool(dtR["est"] > 0 and dtR["ci_wide"][0] > 0),
                b_I_pos_Hz=bool(s["I|T0B|MASYNC"]["est"] > 0 and s["I|T0B|MASYNC"]["ci_wide"][0] > 0),
                b_I_pos_L=bool(s["IL|T0B|MASYNC"]["est"] > 0 and s["IL|T0B|MASYNC"]["ci_wide"][0] > 0),
                c_dt_T0B_small=bool(dtB["est"] <= 0.5 * dtR["est"] and dtB["ci_wide"][1] < dtR["est"]))
    falsified = bool(not ex0("I|T0B|MASYNC") or not ex0("IL|T0B|MASYNC") or dtB["est"] >= dtR["est"])
    return dict(criteria=crit, supported=all(crit.values()), falsified=falsified)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(8_419_070)
    res = {arm: analyse(a.run, arm, rng) for arm in ("MAIN", "BA1", "J025") if os.path.exists(os.path.join(a.run, "raw", f"{arm}_DATA.npz"))}
    res["decision_MAIN"] = decide(res["MAIN"])
    res["generalises"] = {arm: bool(res[arm]["stats"]["I|T0B|MASYNC"]["est"] > 0 and res[arm]["stats"]["I|T0B|MASYNC"]["ci_wide"][0] > 0)
                          for arm in ("BA1", "J025") if arm in res}
    with open(os.path.join(a.run, "analysis.json"), "x") as f:
        json.dump(res, f, indent=1)
    for arm in ("MAIN", "BA1", "J025"):
        if arm not in res:
            continue
        r = res[arm]
        print(f"== {arm} (B1 n={r['n_b1']}, reps {r['n_reps']}, levels {r['levels']}, bias {r['bias']})")
        for k, v in r["means"].items():
            print(f"  {k:14s} DATA {v['data']:6.1f} B1 {v['b1']:6.1f}")
        for k, v in r["stats"].items():
            if k.startswith(("dt|", "I|", "IL|", "Fmatch", "countshare", "gap|REF|M0", "gap|T0B|M0")):
                print(f"  {k:22s} {v['est']:+8.3f}  pct [{v['ci_pct'][0]:+.3f};{v['ci_pct'][1]:+.3f}]  jack-t [{v['ci_jackt'][0]:+.3f};{v['ci_jackt'][1]:+.3f}]")
        print("  short ISI (M0) DATA", {k: round(v, 2) for k, v in r["short_isi_M0"]["data"].items()}, "B1", {k: round(v, 2) for k, v in r["short_isi_M0"]["b1"].items()})
    print("decision MAIN", res["decision_MAIN"], "generalises", res["generalises"])


if __name__ == "__main__":
    main()
