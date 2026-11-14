"""flymind/v6m2_figures.py — V6m2 figure: timing effect Δt = gap(MASYNC) − gap(M0) per DNa02 dynamics and arm (from analysis.json).
Run: .venv/bin/python -I -B flymind/v6m2_figures.py --run flymind/results/v6m2"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ap = argparse.ArgumentParser(allow_abbrev=False)
ap.add_argument("--run", required=True)
a = ap.parse_args()
A = json.load(open(os.path.join(a.run, "analysis.json")))
dyn = ["REF", "T6", "T1", "NOLEAK", "T0", "T0B"]
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for j, arm in enumerate(("MAIN", "BA1", "J025")):
    for i, d in enumerate(dyn):
        for k, (key, x_) in enumerate((("dt|{}|MASYNC", ax[0]), ("gap|{}|M0", ax[1]))):
            v = A[arm]["stats"][key.format(d)]
            x_.errorbar(i + 0.2 * (j - 1), v["est"], yerr=[[v["est"] - v["ci_wide"][0]], [v["ci_wide"][1] - v["est"]]], fmt="osD"[j],
                        color=f"C{j}", label=arm if i == 0 else None)
for x_, t in zip(ax, ("timing effect Δt = gap(MASYNC) − gap(M0) [Hz]\n(> 0: intermediate synchrony harmful)",
                      "gap B1 − DATA with intact intermediate trains (M0) [Hz]")):
    x_.axhline(0, color="k", lw=0.8)
    x_.set_xticks(range(len(dyn)), ["REF\n(3 blk)", "T6\n(6 blk)", "T1\n(1 blk)", "NOLEAK", "T0\n(0 blk)", "T0B\n(0 blk,\nrate-matched)"], fontsize=8)
    x_.set_title(t, fontsize=9)
    x_.legend(fontsize=8)
fig.suptitle("V6m2: DNa02-only factorial (intermediates clamped); CI95 = wider of percentile / jackknife-t (MODEL)", fontsize=10)
fig.tight_layout()
os.makedirs(os.path.join(a.run, "figures"), exist_ok=True)
fig.savefig(os.path.join(a.run, "figures", "V6m2_F1_interaction.png"), dpi=110)
print("ok")
