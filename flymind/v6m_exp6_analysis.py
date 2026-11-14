"""flymind/v6m_exp6_analysis.py — analysis of V6m addendum A1 (POST HOC). Run: .venv/bin/python -I -B flymind/v6m_exp6_analysis.py --run flymind/results/v6m"""
import argparse
import glob
import json
import os

import numpy as np


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    ex = os.path.join(a.run, "exp6")
    Z = {os.path.basename(p)[:-4]: np.load(p) for p in sorted(glob.glob(os.path.join(ex, "*.npz")))}
    conds = list(Z["DATA"]["conds"])
    res = dict(consistency={}, per_cond={})
    for n, z in Z.items():                                   # DN counts must equal the V6m main run
        m = np.load(os.path.join(a.run, "raw", f"main_{n}.npz"))
        mc = list(m["conds"])
        res["consistency"][n] = all(bool(np.array_equal(z["out"][ci, ..., 0], m["summ"][mc.index(c), ..., 0] * 0.5)) for ci, c in enumerate(conds))
    B = [Z[k] for k in Z if k.startswith("B1_")]
    rng = np.random.default_rng(8_419_062)
    names = ("dn_count", "D_exc", "D_inh", "n_exc_partners", "n_mid")
    for ci, c in enumerate(conds):
        e = {}
        for qi, q in enumerate(names):
            xD = Z["DATA"]["out"][ci, ..., qi].mean((0, 1))           # per rep
            xB = np.stack([b["out"][ci, ..., qi].mean((0, 1)) for b in B])
            gap = xB.mean() - xD.mean()
            bs = []
            for _ in range(5000):
                k = rng.integers(len(B), size=len(B))
                r = rng.integers(xB.shape[1], size=(len(B), xB.shape[1]))
                bs.append(np.take_along_axis(xB[k], r, 1).mean() - xD[rng.integers(len(xD), size=len(xD))].mean())
            e[q] = dict(data=float(xD.mean()), b1=float(xB.mean()), gap=float(gap), rel=float(gap / xD.mean()),
                        ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
        res["per_cond"][c] = e
    with open(os.path.join(a.run, "exp6_analysis.json"), "x") as f:
        json.dump(res, f, indent=1)
    print("consistency with V6m main:", res["consistency"])
    for c, e in res["per_cond"].items():
        print(c, " | ".join(f"{q} {v['data']:.1f}/{v['b1']:.1f} rel {v['rel']:+.3f} [{v['ci95'][0]:+.1f};{v['ci95'][1]:+.1f}]" for q, v in e.items()))


if __name__ == "__main__":
    main()
