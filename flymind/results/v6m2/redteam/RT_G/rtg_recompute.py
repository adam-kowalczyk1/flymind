"""RT-G independent recomputation of V6m2 statistics from raw npz. RNG 8 498 701-7xx. No simulation."""
import glob, json, os, sys
import numpy as np
from scipy import stats
RUN = "flymind/results/v6m2"
SMOKE = sys.argv[1] if len(sys.argv) > 1 else None
A = json.load(open(f"{RUN}/analysis.json"))
DYN = ["REF", "T0", "T0B", "T1", "T6", "NOLEAK"]; INP = ["M0", "MCIRC", "MASYNC"]
d = {n: i for i, n in enumerate(DYN)}; ii = {n: i for i, n in enumerate(INP)}

def load(arm):
    D = np.load(f"{RUN}/raw/{arm}_DATA.npz")
    Bp = sorted(glob.glob(f"{RUN}/raw/{arm}_B1_*.npz"))
    B = [np.load(p) for p in Bp]
    assert list(D["dyn"]) == DYN and list(D["inputs"]) == INP
    for b in B:
        assert np.array_equal(b["seeds"], D["seeds"]) and float(b["bias"]) == float(D["bias"])
    return D, B, Bp

def S(mD, mB):
    """mD, mB: [dyn, inp] means -> dict"""
    o = {}
    for dn in DYN:
        for x in INP:
            o[f"gap|{dn}|{x}"] = mB[d[dn], ii[x]] - mD[d[dn], ii[x]]
            o[f"L|{dn}|{x}"] = np.log(mB[d[dn], ii[x]] / mD[d[dn], ii[x]])
        for x in ("MASYNC", "MCIRC"):
            o[f"dt|{dn}|{x}"] = o[f"gap|{dn}|{x}"] - o[f"gap|{dn}|M0"]
            o[f"dtL|{dn}|{x}"] = o[f"L|{dn}|{x}"] - o[f"L|{dn}|M0"]
    for dn in DYN[1:]:
        for x in ("MASYNC", "MCIRC"):
            o[f"I|{dn}|{x}"] = o[f"dt|REF|{x}"] - o[f"dt|{dn}|{x}"]
            o[f"IL|{dn}|{x}"] = o[f"dtL|REF|{x}"] - o[f"dtL|{dn}|{x}"]
        o[f"Fmatch|{dn}"] = 1 - o[f"gap|{dn}|M0"] / o["gap|REF|M0"]
        o[f"FmatchL|{dn}"] = 1 - o[f"L|{dn}|M0"] / o["L|REF|M0"]
    for dn in DYN:
        with np.errstate(divide="ignore", invalid="ignore"):
            o[f"countshare|{dn}"] = o[f"gap|{dn}|MASYNC"] / o[f"gap|{dn}|M0"]
    return o

def jack(xD, xB, keys, tq_alpha=0.05):
    R = xD.shape[-1]
    pt = S(xD.mean(-1), xB.mean((0, -1)))
    J = []
    for i in range(R):
        m = np.arange(R) != i
        J.append(S(xD[..., m].mean(-1), xB[..., m].mean((0, -1))))
    tq = stats.t.ppf(1 - tq_alpha / 2, R - 1)
    out = {}
    for k in keys:
        j = np.array([s[k] for s in J]); se = np.sqrt((R - 1) / R * ((j - j.mean()) ** 2).sum())
        out[k] = (pt[k], pt[k] - tq * se, pt[k] + tq * se, se)
    return out

def boot(xD, xB, keys, rng, crossed, nb=10000, inst=True):
    K, R = xB.shape[0], xB.shape[-1]
    bs = {k: np.empty(nb) for k in keys}
    for b in range(nb):
        k = rng.integers(K, size=K) if inst else np.arange(K)
        if crossed:
            r = rng.integers(R, size=R)
            sel = xB[k][..., r]; dd = xD[..., r]
        else:
            rr = rng.integers(R, size=(K, R))
            sel = np.stack([xB[k[j]][..., rr[j]] for j in range(K)]); dd = xD[..., rng.integers(R, size=R)]
        s = S(dd.mean(-1), sel.mean((0, -1)))
        for kk in keys:
            bs[kk][b] = s[kk]
    return {kk: (np.percentile(v, 2.5), np.percentile(v, 97.5), int((~np.isfinite(v)).sum()), float(np.std(v[np.isfinite(v)]))) for kk, v in bs.items()}

KEYS = ["gap|REF|M0", "dt|REF|MASYNC", "dt|T0B|MASYNC", "I|T0B|MASYNC", "IL|T0B|MASYNC", "I|T0B|MCIRC", "IL|T0B|MCIRC",
        "I|T0|MASYNC", "IL|T0|MASYNC", "I|T0|MCIRC", "dt|T0|MASYNC", "dt|T0|MCIRC", "dt|T1|MASYNC", "dt|T6|MASYNC", "dt|NOLEAK|MASYNC",
        "I|T1|MASYNC", "IL|T1|MASYNC", "I|T6|MASYNC", "IL|T6|MASYNC", "I|NOLEAK|MASYNC", "I|NOLEAK|MCIRC", "IL|NOLEAK|MASYNC",
        "Fmatch|T0B", "FmatchL|T0B", "countshare|REF", "countshare|T0B", "gap|T0B|M0", "gap|T0B|MASYNC"]
rng_nested = np.random.default_rng(8_498_701); rng_crossed = np.random.default_rng(8_498_702)
rng_lvl = np.random.default_rng(8_498_703)
np.set_printoptions(precision=3, suppress=True)
summary = {}
for arm in ("MAIN", "BA1", "J025"):
    D, B, Bp = load(arm)
    xD = D["dn"].mean((2, 3)); xB = np.stack([b["dn"].mean((2, 3)) for b in B])
    K, R = xB.shape[0], xB.shape[-1]
    print(f"\n==== {arm}: K={K} B1, R={R} reps, levels {D['levels'].tolist()}, bias {float(D['bias'])}, seeds {D['seeds'].tolist()}")
    # 1. reproduction of point estimates + jackknife (deterministic) vs analysis.json
    allk = list(S(xD.mean(-1), xB.mean((0, -1))).keys())
    jk = jack(xD, xB, allk)
    mx_pt = max(abs(jk[k][0] - A[arm]["stats"][k]["est"]) for k in allk if np.isfinite(jk[k][0]))
    mx_jk = max(max(abs(jk[k][1] - A[arm]["stats"][k]["ci_jackt"][0]), abs(jk[k][2] - A[arm]["stats"][k]["ci_jackt"][1])) for k in allk if np.isfinite(jk[k][1]))
    print(f"[repro] {len(allk)} stats; max |point diff| {mx_pt:.2e}; max |jack-t bound diff| {mx_jk:.2e}")
    # 2. bootstraps: nested (as analysis, own RNG) vs crossed (shared reps) vs crossed reps only (instances fixed)
    bn = boot(xD, xB, KEYS, rng_nested, crossed=False)
    bc = boot(xD, xB, KEYS, rng_crossed, crossed=True)
    print(f"{'stat':20s} {'est':>8s} | {'json pct':>17s} | {'RT-G nested pct':>17s} | {'crossed pct':>17s} | {'jack-t':>17s} | se_j  se_n  se_c | inf")
    for k in KEYS:
        e, lo, hi, se = jk[k]; js = A[arm]["stats"][k]
        print(f"{k:20s} {e:+8.3f} | {js['ci_pct'][0]:+7.3f};{js['ci_pct'][1]:+7.3f} | {bn[k][0]:+7.3f};{bn[k][1]:+7.3f} | {bc[k][0]:+7.3f};{bc[k][1]:+7.3f} | {lo:+7.3f};{hi:+7.3f} | {se:.3f} {bn[k][3]:.3f} {bc[k][3]:.3f} | {bn[k][2]},{bc[k][2]}")
    # 3. variance components / crossing
    gB = xB.mean(-1)  # [K, dyn, inp]
    for k, (dn, x) in {"REF|M0": ("REF", "M0"), "REF|MASYNC": ("REF", "MASYNC"), "T0B|MASYNC": ("T0B", "MASYNC")}.items():
        y = xB[:, d[dn], ii[x], :]  # [K, R]
        ms_i = R * y.mean(1).var(ddof=1); resid = y - y.mean(1, keepdims=True) - y.mean(0, keepdims=True) + y.mean()
        ms_e = (resid ** 2).sum() / ((K - 1) * (R - 1)); ms_r = K * y.mean(0).var(ddof=1)
        sd_i = np.sqrt(max(0, (ms_i - ms_e) / R)); sd_r = np.sqrt(max(0, (ms_r - ms_e) / K))
        c = np.corrcoef(xD[d[dn], ii[x]], y.mean(0))[0, 1]
        print(f"[varcomp {k}] B1 between-instance SD {sd_i:.2f} Hz, shared-rep SD {sd_r:.2f}, residual SD {np.sqrt(ms_e):.2f}; corr(DATA rep, B1 rep-mean) {c:+.2f}")
    # interaction contrast per rep (crossed unit) and per instance
    def Ivec(xd, xb):  # xd [dyn,inp,R], xb [dyn,inp,R] -> I per rep (Hz)
        g = xb - xd
        return (g[d["REF"], ii["MASYNC"]] - g[d["REF"], ii["M0"]]) - (g[d["T0B"], ii["MASYNC"]] - g[d["T0B"], ii["M0"]])
    Ir = Ivec(xD, xB.mean(0)); Ik = np.array([Ivec(xD, xB[j]).mean() for j in range(K)])
    c_Ik = np.corrcoef(Ivec(xD, xB.mean(0)), (xD[d['REF'],ii['MASYNC']]-xD[d['REF'],ii['M0']])-(xD[d['T0B'],ii['MASYNC']]-xD[d['T0B'],ii['M0']]))[0,1]
    print(f"[I per shared rep] {Ir.round(1).tolist()}  (all>0: {bool((Ir>0).all())}); paired t7 CI {Ir.mean():+.2f} ± {stats.t.ppf(.975,R-1)*Ir.std(ddof=1)/np.sqrt(R):.2f}")
    print(f"[I per B1 instance] {Ik.round(1).tolist()}  range {Ik.min():+.1f}..{Ik.max():+.1f}")
    # leave-one-instance-out
    loo = [S(xD.mean(-1), np.delete(xB, j, 0).mean((0, -1)))["I|T0B|MASYNC"] for j in range(K)]
    print(f"[leave-one-B1-out I] {np.round(loo,2).tolist()}")
    # 4. rate match check
    for lv in range(len(D["levels"])):
        ref = D["dn"][d["REF"], 0, lv].mean(); t0b = D["dn"][d["T0B"], 0, lv].mean(); t0 = D["dn"][d["T0"], 0, lv].mean()
        print(f"[rate-match DATA M0 level {D['levels'][lv]}] REF {ref:6.1f}  T0B {t0b:6.1f} ({100*(t0b/ref-1):+.0f} %)  T0 {t0:6.1f}")
    # 5. per-level and per-side
    lvl = {}
    for lv in range(len(D["levels"])):
        pD = D["dn"][:, :, lv].mean(2); pB = np.stack([b["dn"][:, :, lv].mean(2) for b in B])
        ks = ["gap|REF|M0", "dt|REF|MASYNC", "dt|T0B|MASYNC", "I|T0B|MASYNC", "IL|T0B|MASYNC", "I|T0B|MCIRC", "I|T0|MASYNC", "Fmatch|T0B", "countshare|REF"]
        j = jack(pD, pB, ks); bl = boot(pD, pB, ks, rng_lvl, crossed=True, nb=4000)
        s = "  ".join(f"{k}={j[k][0]:+.2f}[{min(j[k][1],bl[k][0]):+.2f};{max(j[k][2],bl[k][1]):+.2f}]" for k in ks)
        print(f"[level {D['levels'][lv]}] {s}")
        mismatch = {k: abs(j[k][0] - A[arm]['per_level'][str(float(D['levels'][lv]))][k]) for k in ks if k in A[arm]['per_level'][str(float(D['levels'][lv]))]}
        print(f"   (max diff vs analysis.json per_level: {max(mismatch.values()):.1e})")
        lvl[str(D['levels'][lv])] = {k: j[k][:3] for k in ks}
    for si, side in enumerate("LR"):
        pD = D["dn"][:, :, :, si].mean(2); pB = np.stack([b["dn"][:, :, :, si].mean(2) for b in B])
        j = jack(pD, pB, ["I|T0B|MASYNC", "IL|T0B|MASYNC", "dt|REF|MASYNC"])
        print(f"[side {side}] " + "  ".join(f"{k}={v[0]:+.2f}[{v[1]:+.2f};{v[2]:+.2f}]" for k, v in j.items()))
    # 6. level x condition cells (DATA and B1 rates) for countshare instability
    print(f"[countshare|T0B denominator gap|T0B|M0] {jk['gap|T0B|M0'][0]:+.3f} (jack [{jk['gap|T0B|M0'][1]:+.2f};{jk['gap|T0B|M0'][2]:+.2f}])")
    # 7. Multiplicity: Bonferroni m=60 jackknife-t (t7) for reported claims
    m = 60
    jb = jack(xD, xB, KEYS, tq_alpha=0.05 / m)
    print(f"[Bonferroni m={m}, t7 q={stats.t.ppf(1-0.025/m,R-1):.2f}] " + "  ".join(f"{k}=[{v[1]:+.2f};{v[2]:+.2f}]{'*' if (v[1]>0 or v[2]<0) else ''}" for k, v in jb.items()))
    summary[arm] = dict(K=K, R=R)
    # decision re-check per arm (all criteria) with wider intervals
    W = lambda k: (min(A[arm]['stats'][k]['ci_pct'][0], A[arm]['stats'][k]['ci_jackt'][0]), max(A[arm]['stats'][k]['ci_pct'][1], A[arm]['stats'][k]['ci_jackt'][1]))
    dR, dB = A[arm]['stats']['dt|REF|MASYNC'], A[arm]['stats']['dt|T0B|MASYNC']
    crit = dict(a=W('dt|REF|MASYNC')[0] > 0, bHz=W('I|T0B|MASYNC')[0] > 0, bL=W('IL|T0B|MASYNC')[0] > 0,
                c=dB['est'] <= 0.5 * dR['est'] and W('dt|T0B|MASYNC')[1] < dR['est'])
    print(f"[full H-RS criteria applied to {arm}] {crit}  (ci_wide in json == recomputed: {all(np.allclose(W(k), A[arm]['stats'][k]['ci_wide']) for k in allk)})")

# 8. smoke vs main rep 1
if SMOKE:
    for nm in ("MAIN_DATA", "MAIN_B1_8421001"):
        s = np.load(f"{SMOKE}/raw/{nm}.npz"); mn = np.load(f"{RUN}/raw/{nm}.npz")
        print(f"[smoke {nm}] smoke shape {s['dn'].shape} seeds {s['seeds'].tolist()}; equal to main rep 1: {np.array_equal(s['dn'][..., 0], mn['dn'][..., 0])}")
