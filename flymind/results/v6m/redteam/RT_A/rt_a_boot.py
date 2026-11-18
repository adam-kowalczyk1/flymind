"""RT-A: noise-seed pairing check of the V6m bootstrap (no simulation; reads results/v6m/raw). Bootstrap RNG 8 498 090."""
import glob
import numpy as np
RAW = "/Users/admin/so101_fly_project/flymind/results/v6m/raw"
for kind in ("main", "rep"):
    D = np.load(f"{RAW}/{kind}_DATA.npz")
    Bs = [np.load(p) for p in sorted(glob.glob(f"{RAW}/{kind}_B1_*.npz"))]
    C = list(D["conds"]); j = list(D["sum_names"]).index("dn")
    pr = lambda z, c: np.nanmean(z["summ"][C.index(c), ..., j], axis=(0, 1))
    print(f"== {kind}; seeds", D["seeds"][:2], "... same seeds in every B1 file:", all(np.array_equal(b["seeds"], D["seeds"]) for b in Bs))
    rng = np.random.default_rng(8_498_090)
    for c, ref in (("REF", None), ("LCIRC", "REF"), ("E1c_DN_t0", "REF"), ("E3_MCIRC", "E3_M0"), ("E2a_DN_b00", "REF")):
        if c not in C:
            continue
        xD = pr(D, c); xB = np.stack([pr(b, c) for b in Bs])
        rho = np.corrcoef(xD, xB.mean(0))[0, 1]
        rhoBB = np.mean([np.corrcoef(xB[a], xB[b])[0, 1] for a in range(len(Bs)) for b in range(a + 1, len(Bs))])
        # seed-paired bootstrap: resample instances and ONE set of seed indices shared by DATA and all B1 instances
        K, R = xB.shape
        g, gr = [], []
        if ref:
            yD = pr(D, ref); yB = np.stack([pr(b, ref) for b in Bs])
        for _ in range(10_000):
            k = rng.integers(K, size=K); r = rng.integers(R, size=R)
            gc = xB[k][:, r].mean() - xD[r].mean(); g.append(gc)
            if ref:
                gr.append(1 - gc / (yB[k][:, r].mean() - yD[r].mean()))
        pt = xB.mean() - xD.mean()
        s = f"{c:11s} gap {pt:+6.1f} paired-seed CI [{np.percentile(g, 2.5):+.1f};{np.percentile(g, 97.5):+.1f}]  corr(DATA,B1mean) over seeds {rho:+.2f}  mean corr B1-B1 {rhoBB:+.2f}"
        if ref:
            F = 1 - pt / (yB.mean() - yD.mean())
            s += f" | F {F:+.2f} paired-seed CI [{np.percentile(gr, 2.5):+.2f};{np.percentile(gr, 97.5):+.2f}]"
        print(s)
