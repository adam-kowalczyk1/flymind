"""flymind/v5v41_e6_analysis.py — analysis of V5 v4.1 amendment A1 / E6 (pre-specified in V5v41_PROTOCOL_AMENDMENT_A1.md).
Run: .venv/bin/python -I -B flymind/v5v41_e6_analysis.py --run flymind/results/v5v41/E6
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v5v41_analysis import SLOPE, compare  # noqa: E402

SEED = 8_419_003


def per_net(z):
    c = z["counts"].astype(float) * 1000.0 / 10                      # [I0, δ, R, 100, 6] → Hz (DN pops have 1 neuron)
    ss = c[..., 50:100, :].mean(-2)                                  # [I0, δ, R, 6]
    D = ss[..., 4] - ss[..., 5]
    dl = z["deltas"]
    small = np.abs(dl) <= 1.0 + 1e-9

    def slope(y, m):
        x = dl[m]
        return ((y[..., m] - y[..., m].mean(-1, keepdims=True)) * (x - x.mean())).sum(-1) / ((x - x.mean()) ** 2).sum()
    Dr = np.moveaxis(D, 1, -1)                                       # [I0, R, δ]
    silent = (ss[..., 4] == 0) & (ss[..., 5] == 0)                   # [I0, δ, R]
    lc = np.moveaxis(ss[..., 0] / z["n_pop"][0] - ss[..., 1] / z["n_pop"][1], 1, -1)
    return dict(G_small=slope(Dr, small), G_all=slope(Dr, np.ones(len(dl), bool)), bias0=Dr[..., dl == 0][..., 0],
                silent_frac=silent.mean(1), G_lc_small=slope(lc, small), D=Dr, dn_sum=np.moveaxis(ss[..., 4] + ss[..., 5], 1, -1))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    nets = {os.path.basename(p)[:-4]: dict(np.load(p)) for p in sorted(glob.glob(os.path.join(a.run, "raw", "*.npz")))}
    D = per_net(nets["DATA"])
    names = sorted(k for k in nets if k.startswith("SWS_"))
    K = [per_net(nets[k]) for k in names]
    I0 = nets["DATA"]["I0"]
    rng = np.random.default_rng(SEED)
    out = dict(I0=I0.tolist(), deltas=nets["DATA"]["deltas"].tolist(), n_ctrl=len(names), per_I0={})
    for i, x in enumerate(I0):
        row = {}
        for m in ("G_small", "G_all", "bias0", "silent_frac", "G_lc_small"):
            row[m] = compare(D[m][i], np.stack([k[m][i] for k in K]), rng)
        row["G_small_deg_per_mV"] = {k: (np.degrees(v / SLOPE) if isinstance(v, float) else v) for k, v in row["G_small"].items()
                                     if k in ("delta", "data", "ctrl_mean")}
        row["D_curve_data"] = D["D"][i].mean(0).tolist()
        row["D_curve_ctrl_mean"] = np.mean([k["D"][i].mean(0) for k in K], 0).tolist()
        out["per_I0"][str(float(x))] = row
    with open(os.path.join(a.run, "analysis_E6.json"), "x") as f:
        json.dump(out, f, indent=1, default=float)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    for k in K:
        ax[0].plot(I0, k["G_small"].mean(1), color="0.6", lw=0.5)
    ax[0].plot(I0, np.mean([k["G_small"].mean(1) for k in K], 0), "b", lw=2, label="SWS mean")
    ax[0].plot(I0, D["G_small"].mean(1), "r", lw=2, label="DATA")
    ax[0].set_xlabel("I0 (symmetric operating point) [mV]"); ax[0].set_ylabel("small-signal gain dD/dδ [Hz/mV]"); ax[0].legend()
    d = [out["per_I0"][str(float(x))]["G_small"] for x in I0]
    ax[1].errorbar(I0, [r["delta"] for r in d], yerr=np.abs(np.array([r["ci95"] for r in d]).T - [r["delta"] for r in d]), fmt="o-")
    ax[1].axhline(0, color="k", lw=0.5); ax[1].set_title("Δ gain (SWS − DATA), CI95"); ax[1].set_xlabel("I0 [mV]")
    for k in K:
        ax[2].plot(I0, k["silent_frac"].mean(1), color="0.6", lw=0.5)
    ax[2].plot(I0, D["silent_frac"].mean(1), "r", lw=2); ax[2].set_title("fraction of δ with both DNa02 silent"); ax[2].set_xlabel("I0 [mV]")
    fig.tight_layout()
    os.makedirs(os.path.join(a.run, "figures"), exist_ok=True)
    fig.savefig(os.path.join(a.run, "figures", "F6_E6_small_signal_gain.png"), dpi=110)
    for x in I0:
        r = out["per_I0"][str(float(x))]["G_small"]
        if r.get("delta") is not None:
            print(f"I0 {x:4.1f}: G DATA {r['data']:7.2f} SWS {r['ctrl_mean']:7.2f} Hz/mV Δ {r['delta']:+6.2f} CI [{r['ci95'][0]:+.2f}; {r['ci95'][1]:+.2f}] "
                  f"ctrl≥DATA {r['frac_ctrl_ge_data']:.2f} | silent DATA {out['per_I0'][str(float(x))]['silent_frac']['data']:.2f}")


if __name__ == "__main__":
    main()
