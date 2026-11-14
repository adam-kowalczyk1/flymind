"""RT-I scratch: independent recomputation of V6m3 Part B from raw npz + analysis of swap_sim.json.
Run: .venv/bin/python -I -B flymind/results/v6m3/redteam/RT_I/s3_stats.py"""
import glob
import json
import os

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.abspath(os.path.join(HERE, "..", ".."))
an = json.load(open(os.path.join(RUN, "analysis.json")))
tq = lambda n: stats.t.ppf(0.975, n - 1)  # noqa: E731


def dec(Z):
    C = 0.5 * ((Z["DB"] - Z["DD"]) + (Z["BB"] - Z["BD"]))
    g = Z["BB"] - Z["DD"]
    return dict(C=C, T=g - C, gap=g, inter=Z["BB"] - Z["BD"] - Z["DB"] + Z["DD"], share=C / g,
                cnt_first=(Z["DB"] - Z["DD"]) / g, tim_first=(Z["BB"] - Z["BD"]) / g,
                T_Dcnt=Z["BD"] - Z["DD"], T_Bcnt=Z["BB"] - Z["DB"])


def ci(fn, X, nboot=10_000, seed=8_499_190):
    """X: dict cell -> [..., R] arrays (rep last). est on means; jackknife-t over reps; rep-only paired bootstrap (percentile)."""
    m = lambda sel: fn({c: v[..., sel].mean() for c, v in X.items()})  # noqa: E731
    R = next(iter(X.values())).shape[-1]
    est = m(slice(None))
    jk = [m(np.arange(R) != i) for i in range(R)]
    rng = np.random.default_rng(seed)
    bs = [m(rng.integers(R, size=R)) for _ in range(nboot)]
    out = {}
    for key in est:
        j = np.array([x[key] for x in jk])
        se = np.sqrt((R - 1) / R * ((j - j.mean()) ** 2).sum())
        b = np.array([x[key] for x in bs])
        out[key] = dict(est=est[key], jt=(est[key] - tq(R) * se, est[key] + tq(R) * se), bs=tuple(np.percentile(b, [2.5, 97.5])))
    return out


def show(title, o, keys=("C", "T", "share", "inter", "gap", "cnt_first", "tim_first", "T_Dcnt", "T_Bcnt")):
    print(title)
    for k in keys:
        v = o[k]
        print(f"   {k:10s} {v['est']:+8.3f}  jack-t [{v['jt'][0]:+.3f};{v['jt'][1]:+.3f}]  rep-boot [{v['bs'][0]:+.3f};{v['bs'][1]:+.3f}]")


# ---------- 1. recompute from raw ----------
for S in ("MAIN", "REP"):
    B = [np.load(p) for p in sorted(glob.glob(os.path.join(RUN, "raw", f"{S}_B1_*.npz")))]
    X = np.stack([b["B"] for b in B])              # k, dyn, cell, lv, side, rep
    cells = list(B[0]["b_cells"])
    for di, dyn in enumerate(B[0]["b_dyn"]):
        o = ci(dec, {c: X[:, di, i] for i, c in enumerate(cells)})
        show(f"[raw {S} {dyn}] (all lv/side/inst)", o)
        st = an[S]["partB"]["stats"]
        for a, b in (("C", "C"), ("T", "T"), ("share", "Cshare"), ("inter", "inter"), ("gap", "gap")):
            ref = st[f"{b}|{dyn}"]
            assert abs(ref["est"] - o[a]["est"]) < 1e-9, (S, dyn, a)
            assert abs(ref["ci_jackt"][0] - o[a]["jt"][0]) < 1e-9 and abs(ref["ci_jackt"][1] - o[a]["jt"][1]) < 1e-9
    # heterogeneity, REF
    print(f"[raw {S} REF] per level x side:")
    for li in range(2):
        for si in range(2):
            o = ci(dec, {c: X[:, 0, i, li, si] for i, c in enumerate(cells)}, nboot=2000)
            print(f"   lv {8 + li} {'LR'[si]}: C {o['C']['est']:+6.2f} [{o['C']['jt'][0]:+.2f};{o['C']['jt'][1]:+.2f}]  T {o['T']['est']:+6.2f} "
                  f"[{o['T']['jt'][0]:+.2f};{o['T']['jt'][1]:+.2f}]  share {o['share']['est']:.3f} [{o['share']['jt'][0]:.3f};{o['share']['jt'][1]:.3f}]  gap {o['gap']['est']:+.2f}")
    for si in range(2):
        o = ci(dec, {c: X[:, 0, i, :, si] for i, c in enumerate(cells)}, nboot=2000)
        print(f"   side {'LR'[si]}: share {o['share']['est']:.3f} [{o['share']['jt'][0]:.3f};{o['share']['jt'][1]:.3f}]  C {o['C']['est']:+.2f} T {o['T']['est']:+.2f}")
    sh = [dec({c: X[k, 0, i].mean() for i, c in enumerate(cells)}) for k in range(len(B))]
    print(f"   per instance share: min {min(s['share'] for s in sh):.3f} max {max(s['share'] for s in sh):.3f}; gap {min(s['gap'] for s in sh):+.1f}..{max(s['gap'] for s in sh):+.1f}")
    pr = [dec({c: X[:, 0, i, ..., r].mean() for i, c in enumerate(cells)}) for r in range(8)]
    print(f"   per rep share: {[round(s['share'], 3) for s in pr]}")
    # variance components of the share estimate: instance-only bootstrap (reps fixed)
    rng = np.random.default_rng(8_499_191)
    bk = [dec({c: X[rng.integers(len(B), size=len(B)), 0, i].mean() for i, c in enumerate(cells)})["share"] for _ in range(4000)]
    print(f"   instance-only bootstrap share CI {np.percentile(bk, [2.5, 97.5]).round(3)}")
    for di, dyn in enumerate(B[0]["b_dyn"]):
        for li in range(2):
            o = ci(dec, {c: X[:, di, i, li] for i, c in enumerate(cells)}, nboot=2000)
            print(f"   {dyn} lv {8 + li}: T {o['T']['est']:+.2f} jt [{o['T']['jt'][0]:+.2f};{o['T']['jt'][1]:+.2f}] T_Dcnt {o['T_Dcnt']['est']:+.2f} "
                  f"[{o['T_Dcnt']['jt'][0]:+.2f};{o['T_Dcnt']['jt'][1]:+.2f}] T_Bcnt {o['T_Bcnt']['est']:+.2f} [{o['T_Bcnt']['jt'][0]:+.2f};{o['T_Bcnt']['jt'][1]:+.2f}]")

# ---------- 2. alternative swaps ----------
sim = json.load(open(os.path.join(HERE, "swap_sim.json")))
print("repro with original seeds equal:", [x["equal"] for x in sim["repro"]])
CELLS, DYN = sim["cells"], sim["dyn"]
Y = np.array([r["Y"] for r in sim["res"]])            # job, dyn, cell, rep
PR = np.array([r["PR"] for r in sim["res"]])          # job, cell, rep
ADD = np.array([r["ADD"] for r in sim["res"]])
FB = np.array([r["FB"] for r in sim["res"]])
CNT = np.array([r["CNT"] for r in sim["res"]])
ci_ = {c: i for i, c in enumerate(CELLS)}
print("added frac (DB_U BD_U DB_CT BD_CT DB_CC BD_CC):", ADD.mean((0, 2)).round(4), "fallbacks", FB.sum((0, 2)))
print("ipsi pairwise r 5 ms:", {c: round(float(np.nanmean(PR[:, ci_[c]])), 3) for c in CELLS})
print("ipsi mid count 500-1000:", {c: round(float(CNT[:, ci_[c]].mean()), 1) for c in CELLS})
for di, dyn in enumerate(DYN):
    print(f"[sim {dyn}] cell means:", {c: round(float(Y[:, di, ci_[c]].mean()), 2) for c in CELLS})
    for v in ("U", "CT", "CC"):
        o = ci(dec, dict(DD=Y[:, di, ci_["DD"]], BB=Y[:, di, ci_["BB"]], DB=Y[:, di, ci_[f"DB_{v}"]], BD=Y[:, di, ci_[f"BD_{v}"]]))
        show(f"[sim {dyn} swap {v}]", o)
    # MTHIN: gap = (BB - BBm) - (DD - DDm) + (BBm - DDm)
    f = lambda Z: dict(T_thin=Z["BBm"] - Z["DDm"], gap=Z["BB"] - Z["DD"], Tshare_thin=(Z["BBm"] - Z["DDm"]) / (Z["BB"] - Z["DD"]),  # noqa: E731
                       Cshare_thin=1 - (Z["BBm"] - Z["DDm"]) / (Z["BB"] - Z["DD"]), DD_minus_DDm=Z["DD"] - Z["DDm"], BB_minus_BBm=Z["BB"] - Z["BBm"])
    o = ci(f, {c: Y[:, di, ci_[c]] for c in ("DD", "BB", "DDm", "BBm")})
    show(f"[sim {dyn} MTHIN]", o, keys=tuple(o))
    # common-preamble variants
    for v in ("U", "CT"):
        o = ci(dec, dict(DD=Y[:, di, ci_["DD"]], BB=Y[:, di, ci_["BB_pre"]], DB=Y[:, di, ci_[f"DB_{v}"]], BD=Y[:, di, ci_[f"BD_{v}_pre"]]))
        show(f"[sim {dyn} swap {v}, common DATA 0-300 ms preamble]", o, keys=("C", "T", "share", "gap"))
