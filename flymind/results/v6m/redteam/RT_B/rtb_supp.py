"""RT-B supplement: small-sample (rep-unit) intervals, jackknife F, 7 mV denominator, multiplicity-adjusted intervals, E4 per-level curves.
Analysis RNG 8_498_104..105. No simulation."""
import glob, numpy as np
from scipy import stats
RUN = "flymind/results/v6m"
def load(kind):
    D = np.load(f"{RUN}/raw/{kind}_DATA.npz"); Bs = [np.load(p) for p in sorted(glob.glob(f"{RUN}/raw/{kind}_B1_*.npz"))]
    cs = list(D["conds"])
    return {c: (D["summ"][cs.index(c), ..., 0], np.stack([b["summ"][cs.index(c), ..., 0] for b in Bs])) for c in cs}
FREF = {"E3_MCIRC": "E3_M0", "E5a_DN_t0_sub": "E1_DN_t0", "E3_MPOIS": "E3_M0", "E3_MJ20": "E3_M0", "E3_MJ5": "E3_M0", "E3_MJ2": "E3_M0"}
for kind in ("main", "rep"):
    X = load(kind)
    g = {c: X[c][1].mean((0, 1, 2)) - X[c][0].mean((0, 1)) for c in X}      # per-rep paired gap [8]
    dD = {c: X[c][0].mean((0, 1)) for c in X}
    print(f"\n== {kind}: per-rep (n=8) jackknife F and t(7) interval; Bonferroni-type 99.8% crossed-bootstrap interval")
    rng = np.random.default_rng(8_498_104)
    R = 8; B = 20000
    idx = rng.integers(R, size=(B, R)); kk = rng.integers(10, size=(B, 10))
    for c in X:
        ref = FREF.get(c, "REF")
        if c in (ref, "E3_M0"): continue
        F = 1 - g[c].mean() / g[ref].mean()
        jk = np.array([1 - np.delete(g[c], i).mean() / np.delete(g[ref], i).mean() for i in range(R)])
        se = np.sqrt((R - 1) / R * ((jk - jk.mean()) ** 2).sum()); tq = stats.t.ppf(0.975, R - 1)
        # crossed bootstrap (instances + shared reps)
        gb = lambda cc: np.array([X[cc][1][k][:, :, :, r].mean() - X[cc][0][:, :, r].mean() for k, r in zip(kk, idx)])
        Fb = 1 - gb(c) / gb(ref)
        lo, hi = np.percentile(Fb, [0.1, 99.9])
        Fr = 1 - (g[c].mean() / dD[c].mean()) / (g[ref].mean() / dD[ref].mean())
        jkr = np.array([1 - (np.delete(g[c], i).mean() / np.delete(dD[c], i).mean()) / (np.delete(g[ref], i).mean() / np.delete(dD[ref], i).mean()) for i in range(R)])
        ser = np.sqrt((R - 1) / R * ((jkr - jkr.mean()) ** 2).sum())
        print(f" {c:14s} F {F:+.2f} jack-t95 [{F-tq*se:+.2f};{F+tq*se:+.2f}]  boot99.8 [{lo:+.2f};{hi:+.2f}] | Frel {Fr:+.2f} jack-t95 [{Fr-tq*ser:+.2f};{Fr+tq*ser:+.2f}]")
    # 7 mV denominator
    g7 = X["REF"][1][:, 0].mean((0, 1)) - X["REF"][0][0].mean(0)
    print(f" 7 mV REF per-rep gaps {np.round(g7,1).tolist()}  mean {g7.mean():+.2f}  -> F at 7 mV has denominator SE {g7.std(ddof=1)/np.sqrt(8):.2f}")
    for li, lv in enumerate((7, 8, 9)):
        gl = {c: X[c][1][:, li].mean((0, 1)) - X[c][0][li].mean(0) for c in ("REF", "E1c_DN_t0", "E3_MCIRC", "E3_M0", "E2b_MID_b00")}
        print(f" level {lv}: REF gap {gl['REF'].mean():+.1f}  per-rep REF gaps {np.round(gl['REF'],1).tolist()}")
# E4 per level curves
Z = [np.load(p) for p in sorted(glob.glob(f"{RUN}/raw/e4_DATA_L*.npz"))]
cs = list(Z[0]["conds"])
print("\n== E4 per-level DN (mean over sides, reps), 10 Hz grid p 0..1")
for li, z in enumerate(Z):
    for d in ("REF", "DN_t0"):
        y = [z["summ"][cs.index(f"E4_{d}_p{g}"), 0, :, :, 0].mean() for g in range(8)]
        print(f" L{li} {d:6s}", np.round(y, 1).tolist())
