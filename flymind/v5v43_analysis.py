"""flymind/v5v43_analysis.py — analysis of V5 v4.3 replay (protocol §3). Run: .venv/bin/python -I -B flymind/v5v43_analysis.py --run flymind/results/v5v43"""
import argparse
import glob
import json
import os

import numpy as np

SEED = 8_419_050


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    Z = {os.path.basename(p)[:-4]: np.load(p) for p in sorted(glob.glob(os.path.join(a.run, "raw", "*.npz")))}
    D = Z["DATA"]
    B = [Z[k] for k in Z if k.startswith("B1_")]
    var = [str(v) for v in D["variants"]]
    lv = D["levels"]
    nmid = D["n_mid"].astype(float)
    rng = np.random.default_rng(SEED)

    def rates(z):
        r = z["replay"].copy()                        # [lv, side, rep, var, 5]
        dn = r[..., 0] / 0.5
        mid = np.stack([r[:, 0, ..., 1] / (nmid[0] * 0.5), r[:, 1, ..., 1] / (nmid[1] * 0.5)], 1)
        return dn, mid, r[..., 2], r[..., 3], r[..., 4]
    dD, mD, fD, lD, cD = rates(D)
    Bs = [rates(z) for z in B]
    dB = np.stack([b[0] for b in Bs])                 # [k, lv, side, rep, var]
    out = dict(levels=lv.tolist(), variants=var, n_b1=len(B), validation={}, per_variant={})
    # validation: V0 replay == free run
    for name, z in Z.items():
        out["validation"][name] = bool(np.array_equal(z["replay"][..., 0, 0], z["free"][..., 0]) and np.array_equal(z["replay"][..., 0, 1], z["free"][..., 1]))
    for vi, v in enumerate(var):
        xD = dD[..., vi].mean((0, 1))                 # per rep, averaged over levels and sides → [R]
        xB = dB[..., vi].mean((1, 2))                 # [k, R]
        gap = xB.mean() - xD.mean()
        bs = []
        for _ in range(10_000):
            k = rng.integers(len(xB), size=len(xB))
            r = rng.integers(xB.shape[1], size=(len(xB), xB.shape[1]))
            bs.append(np.take_along_axis(xB[k], r, 1).mean() - xD[rng.integers(len(xD), size=len(xD))].mean())
        out["per_variant"][v] = dict(dn_data=float(xD.mean()), dn_b1=float(xB.mean()), gap=float(gap),
                                     gap_ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                                     gap_per_level=[float(dB[:, li, :, :, vi].mean() - dD[li, :, :, vi].mean()) for li in range(len(lv))],
                                     mid_data=float(mD[..., vi].mean()), mid_b1=float(np.mean([b[1][..., vi].mean() for b in Bs])),
                                     lc_fano_data=float(np.nanmean(fD[..., vi])), lc_fano_b1=float(np.nanmean([np.nanmean(b[2][..., vi]) for b in Bs])),
                                     spikes_lost_frac_data=float(lD[..., vi].sum() / max(cD[..., 0].sum(), 1)),
                                     lc_ipsi_spikes_data=float(cD[..., vi].mean()), lc_ipsi_spikes_b1=float(np.mean([b[4][..., vi].mean() for b in Bs])))
    g0 = out["per_variant"]["V0"]["gap"]
    for v in var:
        out["per_variant"][v]["gap_frac_of_V0"] = out["per_variant"][v]["gap"] / g0 if g0 else None
    fr = [out["per_variant"][v]["gap_frac_of_V0"] for v in ("CIRC", "POIS")]
    out["rule"] = ("timing route supported" if all(abs(f) <= 0.25 for f in fr) else
                   "rate route" if all(f >= 0.75 for f in fr) else "partial")
    with open(os.path.join(a.run, "analysis.json"), "x") as f:
        json.dump(out, f, indent=1)
    print("validation", out["validation"])
    for v in var:
        p = out["per_variant"][v]
        print(f"{v:5s} DN DATA {p['dn_data']:6.1f} B1 {p['dn_b1']:6.1f} gap {p['gap']:+6.2f} [{p['gap_ci95'][0]:+.2f};{p['gap_ci95'][1]:+.2f}] "
              f"frac {p['gap_frac_of_V0']:+.2f} | mid {p['mid_data']:.2f}/{p['mid_b1']:.2f} | LC Fano {p['lc_fano_data']:.1f}/{p['lc_fano_b1']:.1f} "
              f"| lost {p['spikes_lost_frac_data']:.3f} | LC spikes {p['lc_ipsi_spikes_data']:.0f}/{p['lc_ipsi_spikes_b1']:.0f}")
    print("rule:", out["rule"])


if __name__ == "__main__":
    main()
