"""flymind/v6m_analysis.py — pre-specified analysis of V6m (protocol §5). Written before the full run's results were opened.
Run: .venv/bin/python -I -B flymind/v6m_analysis.py --run flymind/results/v6m --v43 flymind/results/v5v43
"""
import argparse
import glob
import json
import os

import numpy as np

RNG_GAP, RNG_E4 = 8_419_060, 8_419_061
NBOOT = 10_000
F_REF = {"E3_MCIRC": "E3_M0", "E3_MJ2": "E3_M0", "E3_MJ5": "E3_M0", "E3_MJ20": "E3_M0", "E3_MPOIS": "E3_M0", "E5a_DN_t0_sub": "E1_DN_t0"}
DESCR = ("dn", "mid", "dn_a_mean", "mid_a_mean", "lat0", "dn_ref_frac", "dn_excess", "dn_isi_floor_frac", "dn_isi_le4_frac", "lc_win", "mid_ss", "lost")


def label(F, ci):
    if F >= 0.5 and ci[0] > 0.25:
        return "removes most of the gap"
    if ci[0] > 0 or ci[1] < 0:
        return "contributes (F>0)" if F > 0 else "ablation ENLARGES the gap (F<0)"
    return "not supported (CI includes 0)"


def per_rep(z, cond, name):
    c = list(z["conds"]).index(cond)
    j = list(z["sum_names"]).index(name)
    return np.nanmean(z["summ"][c, ..., j], axis=(0, 1))                   # mean over levels, sides → [reps]


def gaps(D, Bs, conds, rng):
    """Paired hierarchical bootstrap over B1 instances, reps within instance, DATA reps; same indices for every condition."""
    xD = {c: per_rep(D, c, "dn") for c in conds}
    xB = {c: np.stack([per_rep(b, c, "dn") for b in Bs]) for c in conds}
    K, R = xB[conds[0]].shape
    RD = len(xD[conds[0]])
    pt = {c: xB[c].mean() - xD[c].mean() for c in conds}
    bs = {c: np.empty(NBOOT) for c in conds}
    bsD = {c: np.empty(NBOOT) for c in conds}
    for i in range(NBOOT):
        k = rng.integers(K, size=K)
        r = rng.integers(R, size=(K, R))
        d = rng.integers(RD, size=RD)
        for c in conds:
            bs[c][i] = np.take_along_axis(xB[c][k], r, 1).mean() - xD[c][d].mean()
            bsD[c][i] = xD[c][d].mean()
    out = {}
    for c in conds:
        ref = F_REF.get(c, "REF")
        e = dict(dn_data=float(xD[c].mean()), dn_b1=float(xB[c].mean()), gap=float(pt[c]),
                 gap_ci95=[float(np.percentile(bs[c], 2.5)), float(np.percentile(bs[c], 97.5))],
                 rel_gap=float(pt[c] / xD[c].mean()), rel_gap_ci95=[float(np.percentile(bs[c] / bsD[c], q)) for q in (2.5, 97.5)],
                 gap_inst=[float(x) for x in xB[c].mean(1) - xD[c].mean()])
        if c != ref and ref in conds:
            Fb = 1 - bs[c] / bs[ref]
            F = 1 - pt[c] / pt[ref]
            ci = [float(np.percentile(Fb, 2.5)), float(np.percentile(Fb, 97.5))]
            e.update(F_vs=ref, F=float(F), F_ci95=ci, label=label(F, ci))
        out[c] = e
    return out


def descriptives(D, Bs, conds):
    out = {}
    for c in conds:
        e = {}
        for n in DESCR:
            e[n] = dict(data=float(np.nanmean(per_rep(D, c, n))), b1=float(np.nanmean([np.nanmean(per_rep(b, c, n)) for b in Bs])))
        ci = list(D["conds"]).index(c)
        isiD = D["isi"][ci].sum((0, 1, 2))
        isiB = sum(b["isi"][ci].sum((0, 1, 2)) for b in Bs)
        e["isi_hist_frac_1to10"] = dict(data=(isiD[:10] / max(isiD.sum(), 1)).round(3).tolist(), b1=(isiB[:10] / max(isiB.sum(), 1)).round(3).tolist())
        sn = list(D["sync_names"])
        for pop, key in (("lc", "lcsync"), ("mid", "midsync")):
            e[f"{pop}_sync"] = {s: dict(data=float(np.nanmean(D[key][ci][..., j])), b1=float(np.nanmean([np.nanmean(b[key][ci][..., j]) for b in Bs])))
                                for j, s in enumerate(sn)}
        out[c] = e
    return out


def e4(run, rng):
    Z = [np.load(p) for p in sorted(glob.glob(os.path.join(run, "raw", "e4_DATA_L*.npz")))]
    if not Z:
        return None
    conds = list(Z[0]["conds"])
    grid = [tuple(g) for g in Z[0]["p_sync"]]
    dyn = sorted({c.split("_p")[0][3:] for c in conds}, key=lambda d: (d != "REF", d))   # REF first (bug fix 14:57: ratios need REF slope)
    sn = list(Z[0]["sync_names"])
    jdn = list(Z[0]["sum_names"]).index("dn")
    # DN per rep [dyn][grid][rep], averaged over the 3 levels (one per file) and 2 sides
    dn = {d: np.array([np.mean([z["summ"][conds.index(f"E4_{d}_p{g}"), 0, :, :, jdn].mean(0) for z in Z], 0) for g in range(len(grid))]) for d in dyn}
    syn = {s: np.array([np.nanmean([np.nanmean(z["lcsync"][conds.index(f"E4_REF_p{g}")][..., j]) for z in Z]) for g in range(len(grid))])
           for j, s in enumerate(sn)}
    prim = [i for i, g in enumerate(grid) if g[0] == 10.0]
    out = dict(grid=grid, dynamics=dyn, dn_mean={d: dn[d].mean(1).tolist() for d in dyn}, lc_sync_by_grid={s: v.tolist() for s, v in syn.items()},
               slopes={}, monotonic={})
    R = dn[dyn[0]].shape[1]
    for s in ("fano10", "chi2_5", "paircorr5", "volley2"):
        x = syn[s][prim]
        e = {}
        bsl = {d: np.empty(NBOOT) for d in dyn}
        for i in range(NBOOT):
            r = rng.integers(R, size=R)
            for d in dyn:
                bsl[d][i] = np.polyfit(x, dn[d][prim][:, r].mean(1), 1)[0]
        for d in dyn:
            sl = np.polyfit(x, dn[d][prim].mean(1), 1)[0]
            e[d] = dict(slope=float(sl), ci95=[float(np.percentile(bsl[d], 2.5)), float(np.percentile(bsl[d], 97.5))])
            if d != "REF":
                ratio = bsl[d] / bsl["REF"]
                e[d].update(ratio_vs_REF=float(sl / e["REF"]["slope"]), ratio_ci95=[float(np.percentile(ratio, 2.5)), float(np.percentile(ratio, 97.5))])
        out["slopes"][s] = e
    for d in dyn:
        y = dn[d][prim].mean(1)
        out["monotonic"][d] = bool(np.all(np.diff(y) <= 0)), int(np.sum(np.diff(y) > 0))
    sec = [i for i, g in enumerate(grid) if g[0] == 40.0]
    out["ev40_vs_ev10"] = [dict(grid=grid[i], fano10=float(syn["fano10"][i]), volley2=float(syn["volley2"][i]), dn_REF=float(dn["REF"][i].mean()))
                           for i in sec]
    return out


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    ap.add_argument("--v43", required=True)
    a = ap.parse_args()
    raw = os.path.join(a.run, "raw")
    res = {}
    # T3: REF == v4.3 V0 for every main source, all levels × sides × reps
    t3 = {}
    for p in sorted(glob.glob(os.path.join(raw, "main_*.npz"))):
        z = np.load(p)
        n = os.path.basename(p)[5:-4]
        old = np.load(os.path.join(a.v43, "raw", f"{n}.npz"))
        ref = z["summ"][list(z["conds"]).index("REF"), ..., 0] * 0.5
        t3[n] = bool(np.array_equal(ref, old["replay"][..., 0, 0]))
    res["T3_ref_equals_v43_V0"] = t3
    rng = np.random.default_rng(RNG_GAP)
    for kind in ("main", "rep"):
        D = np.load(os.path.join(raw, f"{kind}_DATA.npz"))
        Bs = [np.load(p) for p in sorted(glob.glob(os.path.join(raw, f"{kind}_B1_*.npz")))]
        conds = list(D["conds"])
        res[kind] = dict(n_b1=len(Bs), gaps=gaps(D, Bs, conds, rng), descr=descriptives(D, Bs, conds))
    res["E4"] = e4(a.run, np.random.default_rng(RNG_E4))
    # pre-registered hypothesis read-out (protocol §5)
    m, r, e = res["main"]["gaps"], res["rep"]["gaps"], res["E4"]
    sl = e["slopes"]["fano10"] if e else {}

    def rule(g, c):
        return g[c].get("label") if c in g else None
    res["hypotheses"] = {
        "H1_DN_refractory": dict(E1c_t0=rule(m, "E1c_DN_t0"), E1_t0=rule(m, "E1_DN_t0"), rep_E1c_t0=rule(r, "E1c_DN_t0"),
                                 E4_slope_ratio_DN_t0=sl.get("DN_t0", {}).get("ratio_ci95"),
                                 supported=bool(rule(m, "E1c_DN_t0") == "removes most of the gap" and rule(r, "E1c_DN_t0") == "removes most of the gap"
                                                and sl.get("DN_t0", {}).get("ratio_ci95", [1, 1])[1] < 0.5)),
        "H2a_DN_adaptation": dict(main=rule(m, "E2a_DN_b00"), rep=rule(r, "E2a_DN_b00"), E4_slope_ratio_DN_b0=sl.get("DN_b0", {}).get("ratio_ci95")),
        "H2b_mid_adaptation": dict(main=rule(m, "E2b_MID_b00"), rep=rule(r, "E2b_MID_b00")),
        "H3_mid_timing": dict(main=rule(m, "E3_MCIRC"), rep=rule(r, "E3_MCIRC"), M0_identity="see run validity m0_eq_ref"),
        "H5_mid_refractory": dict(main=rule(m, "E1b_MID_t0"), E4_slope_ratio_MID_t0=sl.get("MID_t0", {}).get("ratio_ci95")),
        "H5_DN_reset": dict(main=rule(m, "E5a_DN_t0_sub"), rep=rule(r, "E5a_DN_t0_sub")),
        "H5_mid_inhibition": dict(main=rule(m, "E5b_noinh")),
        "LCIRC_reference": dict(main=rule(m, "LCIRC"), rep=rule(r, "LCIRC")),
    }
    with open(os.path.join(a.run, "analysis.json"), "x") as f:
        json.dump(res, f, indent=1, default=float)
    print("T3", res["T3_ref_equals_v43_V0"])
    for kind in ("main", "rep"):
        print(f"== {kind} (B1 n = {res[kind]['n_b1']})")
        for c, g in res[kind]["gaps"].items():
            d = res[kind]["descr"][c]
            print(f"{c:15s} DN {g['dn_data']:6.1f}/{g['dn_b1']:6.1f} gap {g['gap']:+6.1f} [{g['gap_ci95'][0]:+.1f};{g['gap_ci95'][1]:+.1f}] rel {g['rel_gap']:+.3f}"
                  + (f" | F {g['F']:+.2f} [{g['F_ci95'][0]:+.2f};{g['F_ci95'][1]:+.2f}] vs {g['F_vs']}: {g['label']}" if "F" in g else "")
                  + f" | mid {d['mid']['data']:.1f}/{d['mid']['b1']:.1f} a_DN {d['dn_a_mean']['data']:.1f}/{d['dn_a_mean']['b1']:.1f}"
                  f" isi≤4 {d['dn_isi_le4_frac']['data']:.2f}/{d['dn_isi_le4_frac']['b1']:.2f} midFano10 {d['mid_sync']['fano10']['data']:.1f}/{d['mid_sync']['fano10']['b1']:.1f}")
    if e:
        print("E4 grid", e["grid"])
        for d in e["dynamics"]:
            print(" DN", d, np.round(e["dn_mean"][d], 1), "monotonic", e["monotonic"][d])
        print(" LC fano10 by grid", np.round(e["lc_sync_by_grid"]["fano10"], 1))
        for s, v in e["slopes"].items():
            print(" slope vs", s, {d: (round(x["slope"], 3), x.get("ratio_ci95")) for d, x in v.items()})
    print(json.dumps(res["hypotheses"], indent=1))


if __name__ == "__main__":
    main()
