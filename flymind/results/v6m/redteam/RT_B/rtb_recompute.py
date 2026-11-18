"""RT-B independent recomputation from raw npz (no analysis.json). Analysis RNG seeds 8_498_101.. only. No simulation."""
import glob, os, numpy as np
RUN = "flymind/results/v6m"
NB = 10_000
COND = ["REF", "LCIRC", "E1c_DN_t0", "E1_DN_t0", "E2a_DN_b00", "E2b_MID_b00", "E3_M0", "E3_MCIRC", "E1b_MID_t0", "E5a_DN_t0_sub",
        "E1_DN_t1", "E1_DN_t2", "E1_DN_t4", "E1_DN_t6", "E1c_DN_t6", "E3_MPOIS", "E3_MJ20", "E5b_noinh"]
FREF = {"E3_MCIRC": "E3_M0", "E3_MPOIS": "E3_M0", "E3_MJ20": "E3_M0", "E5a_DN_t0_sub": "E1_DN_t0"}


def load(kind):
    D = np.load(f"{RUN}/raw/{kind}_DATA.npz")
    Bp = sorted(glob.glob(f"{RUN}/raw/{kind}_B1_*.npz"))
    Bs = [np.load(p) for p in Bp]
    conds = list(D["conds"])
    assert all(list(b["conds"]) == conds for b in Bs)
    assert all(np.array_equal(b["seeds"], D["seeds"]) for b in Bs), "noise seeds differ"
    j = list(D["sum_names"]).index("dn")
    out = {}
    for c in conds:
        ci = conds.index(c)
        out[c] = (D["summ"][ci, ..., j], np.stack([b["summ"][ci, ..., j] for b in Bs]))   # [L,S,R], [K,L,S,R]
    return out, D["seeds"], [os.path.basename(p) for p in Bp]


def ci(x):
    return np.percentile(x, [2.5, 97.5])


def boot(X, conds, scheme, rng, sel=(slice(None), slice(None))):
    """returns dict cond -> (point gap, boot gaps, point dnD, boot dnD). sel selects (level, side)."""
    xD = {c: X[c][0][sel].reshape(-1, X[c][0].shape[-1]).mean(0) for c in conds}            # [R]
    xB = {c: X[c][1][(slice(None),) + sel].reshape(X[c][1].shape[0], -1, X[c][1].shape[-1]).mean(1) for c in conds}  # [K,R]
    K, R = xB[conds[0]].shape
    pt = {c: (xB[c].mean() - xD[c].mean(), xD[c].mean()) for c in conds}
    g = {c: np.empty(NB) for c in conds}; d0 = {c: np.empty(NB) for c in conds}
    for i in range(NB):
        k = rng.integers(K, size=K)
        if scheme == "orig":          # as v6m_analysis: reps within instance independent, DATA reps independent
            r = rng.integers(R, size=(K, R)); d = rng.integers(R, size=R)
            for c in conds:
                g[c][i] = np.take_along_axis(xB[c][k], r, 1).mean() - xD[c][d].mean(); d0[c][i] = xD[c][d].mean()
        elif scheme == "crossed":     # reps are a crossed factor shared by DATA and all B1 (common seeds): resample jointly
            r = rng.integers(R, size=R)
            for c in conds:
                g[c][i] = xB[c][k][:, r].mean() - xD[c][r].mean(); d0[c][i] = xD[c][r].mean()
        elif scheme == "reponly":     # B1 instances fixed (conditional on these 10), paired reps
            r = rng.integers(R, size=R)
            for c in conds:
                g[c][i] = xB[c][:, r].mean() - xD[c][r].mean(); d0[c][i] = xD[c][r].mean()
    return pt, g, d0


def varcomp(X, c):
    xD, xB = X[c][0].mean((0, 1)), X[c][1].mean((1, 2))      # [R], [K,R]
    K, R = xB.shape
    gm = xB.mean()
    inst = xB.mean(1) - gm; rep = xB.mean(0) - gm
    res = xB - gm - inst[:, None] - rep[None, :]
    ms_i = R * (inst ** 2).sum() / (K - 1); ms_r = K * (rep ** 2).sum() / (R - 1); ms_e = (res ** 2).sum() / ((K - 1) * (R - 1))
    s2_i = max((ms_i - ms_e) / R, 0); s2_r = max((ms_r - ms_e) / K, 0)
    rho = np.corrcoef(xD, xB.mean(0))[0, 1]
    return dict(inst_sd=np.sqrt(s2_i), rep_sd=np.sqrt(s2_r), resid_sd=np.sqrt(ms_e), F_inst=ms_i / ms_e, ms_i=ms_i, ms_e=ms_e,
                data_rep_sd=xD.std(ddof=1), corr_DATA_vs_B1mean_over_reps=rho, inst_means=xB.mean(1).round(2).tolist())


def report(kind, rng):
    X, seeds, bn = load(kind)
    cs = [c for c in COND if c in X]
    print(f"\n######## {kind}: seeds {seeds.tolist()}, B1 files {len(bn)}")
    res = {}
    for sch in ("orig", "crossed", "reponly"):
        pt, g, d0 = boot(X, cs, sch, rng)
        res[sch] = (pt, g, d0)
    pt = res["orig"][0]
    print(f"{'cond':14s} {'DATA':>6s} {'B1':>6s} {'gap':>6s} | gapCI orig | crossed | reponly || F  Fci orig | crossed | reponly || relgap  Frel  FrelCI(crossed)")
    for c in cs:
        ref = FREF.get(c, "REF")
        line = f"{c:14s} {pt[c][1]:6.1f} {pt[c][1]+pt[c][0]:6.1f} {pt[c][0]:+6.1f} |"
        for sch in res:
            line += " [{:+.1f};{:+.1f}]".format(*ci(res[sch][1][c]))
        if c != ref:
            F = 1 - pt[c][0] / pt[ref][0]
            line += f" || {F:+.2f}"
            for sch in res:
                line += " [{:+.2f};{:+.2f}]".format(*ci(1 - res[sch][1][c] / res[sch][1][ref]))
            rg, rr = pt[c][0] / pt[c][1], pt[ref][0] / pt[ref][1]
            _, g, d0 = res["crossed"]
            Fr = 1 - (g[c] / d0[c]) / (g[ref] / d0[ref])
            line += f" || {rg:+.3f} {1-rg/rr:+.2f} [{ci(Fr)[0]:+.2f};{ci(Fr)[1]:+.2f}]"
        print(line)
    # ratio well-behavedness: denominator distribution
    for ref in ("REF", "E3_M0", "E1_DN_t0"):
        if ref in cs:
            gr = res["orig"][1][ref]
            print(f"denominator {ref}: gap boot mean {gr.mean():+.2f} sd {gr.std():.2f} CV {abs(gr.std()/gr.mean()):.3f}, max {gr.max():+.2f}")
    print("\nvariance components (DN Hz, per rep averaged over levels x sides), two-way instance x rep (seed shared):")
    for c in ("REF", "LCIRC", "E1c_DN_t0", "E3_MCIRC"):
        if c in X:
            v = varcomp(X, c)
            print(f" {c:12s} inst_sd {v['inst_sd']:.2f} rep_sd {v['rep_sd']:.2f} resid_sd {v['resid_sd']:.2f}  MS_inst/MS_resid {v['F_inst']:.2f}  "
                  f"DATA rep sd {v['data_rep_sd']:.2f}  corr(DATA_r, B1mean_r) {v['corr_DATA_vs_B1mean_over_reps']:+.2f}\n    instance means {v['inst_means']}")
    # paired per-rep gap and F (unit = rep, n=8) + t-interval
    print("\nper-rep paired gaps (unit = shared noise seed, n=8; B1 averaged over instances):")
    from math import sqrt
    for c in ("REF", "E1c_DN_t0", "E1_DN_t0", "E3_MCIRC", "E2a_DN_b00", "LCIRC"):
        if c in X:
            gr = X[c][1].mean((0, 1, 2)) - X[c][0].mean((0, 1))
            print(f" {c:12s} gaps/rep {np.round(gr,1).tolist()}  mean {gr.mean():+.2f} sd {gr.std(ddof=1):.2f}  t95 ±{2.365*gr.std(ddof=1)/sqrt(len(gr)):.2f}")
    # per-level and per-side heterogeneity (crossed bootstrap within cell)
    print("\nper-level / per-side gaps and F (crossed bootstrap):")
    for lab, sel in [("7mV", (0, slice(None))), ("8mV", (1, slice(None))), ("9mV", (2, slice(None))), ("L", (slice(None), 0)), ("R", (slice(None), 1))]:
        pt2, g2, d02 = boot(X, cs, "crossed", rng, sel)
        s = f" {lab:4s} REF gap {pt2['REF'][0]:+5.1f} (DATA {pt2['REF'][1]:.1f}) |"
        for c in ("LCIRC", "E1c_DN_t0", "E1_DN_t0", "E2a_DN_b00", "E2b_MID_b00", "E3_MCIRC", "E1b_MID_t0", "E5a_DN_t0_sub"):
            if c in cs:
                ref = FREF.get(c, "REF")
                F = 1 - pt2[c][0] / pt2[ref][0]
                Fr = 1 - (pt2[c][0] / pt2[c][1]) / (pt2[ref][0] / pt2[ref][1])
                q = ci(1 - g2[c] / g2[ref])
                s += f" {c} F {F:+.2f} [{q[0]:+.2f};{q[1]:+.2f}] Frel {Fr:+.2f} |"
        print(s)
    return X


def e4(rng):
    Z = [np.load(p) for p in sorted(glob.glob(f"{RUN}/raw/e4_DATA_L*.npz"))]
    conds = list(Z[0]["conds"]); grid = [tuple(g) for g in Z[0]["p_sync"]]
    jd = list(Z[0]["sum_names"]).index("dn"); sn = list(Z[0]["sync_names"])
    dyn = ["REF", "DN_t0", "DN_b0", "MID_t0"]
    # dn[d] [grid, level, side, rep]
    dn = {d: np.array([[z["summ"][conds.index(f"E4_{d}_p{g}"), 0, :, :, jd] for z in Z] for g in range(len(grid))]) for d in dyn}
    sy = {s: np.array([[z["lcsync"][conds.index(f"E4_REF_p{g}"), 0, :, :, sn.index(s)] for z in Z] for g in range(len(grid))]) for s in sn}
    prim = [i for i, g in enumerate(grid) if g[0] == 10.0]
    print("\n######## E4")
    x = sy["fano10"][prim].mean((1, 2, 3))
    print("fano10 grid means", x.round(2).tolist())
    print("fano10 sd across level/side/rep per grid point", sy["fano10"][prim].std((1, 2, 3)).round(2).tolist())
    for d in dyn:
        y = dn[d][prim].mean((1, 2, 3))
        sl, ic = np.polyfit(x, y, 1)
        q = np.polyfit(x, y, 2)
        resid = y - (sl * x + ic)
        print(f" {d:7s} y {y.round(1).tolist()}  OLS slope {sl:+.3f} R2 {1-resid.var()/y.var():.3f} quad coef {q[0]:+.4f}  rel slope (÷y[p0]) {sl/y[0]*100:+.3f} %/Fano")
    # bootstrap variants: rep-only (as original), and rep x (level,side) cells as 48 units ignoring that levels/sides share seeds -> show pseudo-rep shrink
    R = dn["REF"].shape[-1]
    bs = {k: {d: np.empty(NB) for d in dyn} for k in ("abs", "rel", "absR", "relR", "cell")}
    for i in range(NB):
        r = rng.integers(R, size=R)
        cells = rng.integers(3 * 2 * R, size=3 * 2 * R)
        for d in dyn:
            y = dn[d][prim][..., r].mean((1, 2, 3))
            xs = sy["fano10"][prim][..., r].mean((1, 2, 3))
            bs["abs"][d][i] = np.polyfit(x, y, 1)[0]
            bs["rel"][d][i] = np.polyfit(x, y / y[0], 1)[0]
            bs["absR"][d][i] = np.polyfit(xs, y, 1)[0]          # x resampled together with y
            bs["relR"][d][i] = np.polyfit(xs, y / y[0], 1)[0]
            yc = dn[d][prim].reshape(len(prim), -1)[:, cells].mean(1)
            bs["cell"][d][i] = np.polyfit(x, yc, 1)[0]
    for d in dyn[1:]:
        for k in bs:
            rt = bs[k][d] / bs[k]["REF"]
            print(f" slope ratio {d}/REF [{k:4s}] median {np.median(rt):.3f} CI [{ci(rt)[0]:.3f};{ci(rt)[1]:.3f}]")
    # restricted range: grid points spanning the DATA..B1 interval only (p 0.35..0.9)
    sub = [i for i in prim if 0.35 <= grid[i][1] <= 0.9]
    xs = sy["fano10"][sub].mean((1, 2, 3))
    for d in dyn:
        y = dn[d][sub].mean((1, 2, 3)); print(f" restricted p .35-.9 {d:7s} slope {np.polyfit(xs, y, 1)[0]:+.3f} rel {np.polyfit(xs, y / y[0], 1)[0]*100:+.3f}%")
    # 85 % claim: interpolate REF synthetic curve at real DATA / B1 synchrony, per metric
    main = {k: np.load(f"{RUN}/raw/main_{k}.npz") for k in ["DATA"] + [os.path.basename(p)[5:-4] for p in sorted(glob.glob(f'{RUN}/raw/main_B1_*.npz'))]}
    ci0 = list(main["DATA"]["conds"]).index("REF")
    print("\n85% claim, interpolation of REF synthetic curve (10 Hz events) at real synchrony values:")
    yR = dn["REF"][prim].mean((1, 2, 3))
    for s in ("fano10", "fano5", "fano20", "chi2_5", "paircorr5", "volley2", "cv5"):
        xg = sy[s][prim].mean((1, 2, 3))
        vD = np.nanmean(main["DATA"]["lcsync"][ci0][..., sn.index(s)])
        vB = np.mean([np.nanmean(main[k]["lcsync"][ci0][..., sn.index(s)]) for k in main if k != "DATA"])
        o = np.argsort(xg)
        iD, iB = np.interp(vD, xg[o], yR[o]), np.interp(vB, xg[o], yR[o])
        print(f" {s:9s} DATA {vD:.3f} -> {iD:.1f} Hz ; B1 {vB:.3f} -> {iB:.1f} Hz ; synthetic gap {iB-iD:+.1f} = {(iB-iD)/-19.9*100:.0f}% of real -19.9 ; out of grid range? {vB > xg.max() or vD < xg.min()}")
    # per level E4 slope/ratio heterogeneity
    for li in range(3):
        xl = sy["fano10"][prim][:, li].mean((1, 2))
        yl = {d: dn[d][prim][:, li].mean((1, 2)) for d in dyn}
        s = {d: np.polyfit(xl, yl[d], 1)[0] for d in dyn}
        print(f" level {li}: slopes {{{', '.join(f'{d}: {v:+.3f}' for d, v in s.items())}}}  ratio DN_t0 abs {s['DN_t0']/s['REF']:.2f} rel {(s['DN_t0']/yl['DN_t0'][0])/(s['REF']/yl['REF'][0]):.2f}")
    # within-rep per-level cell (level x side) means: DATA source counts identical across dyn
    print(" E4 real-train anchors: DATA REF (main) DN", round(float(main['DATA']['summ'][ci0, ..., 0].mean()), 2))


if __name__ == "__main__":
    rng = np.random.default_rng(8_498_101)
    report("main", rng)
    report("rep", np.random.default_rng(8_498_102))
    e4(np.random.default_rng(8_498_103))
