"""flymind/v6m3_figures.py — V6m3 figure (Part A drive deficit; Part B count/timing decomposition) from analysis.json.
Run: .venv/bin/python -I -B flymind/v6m3_figures.py --run flymind/results/v6m3"""
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
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for j, s in enumerate(("MAIN", "REP")):
    st = A[s]["partA"]["stats"]
    for i, c in enumerate(("REF", "MT0", "MT0G", "MT0B", "LCIRC")):
        v = st[f"Drel|{c}"]
        ax[0].errorbar(i + 0.15 * (2 * j - 1), 100 * v["est"], yerr=[[100 * (v["est"] - v["ci"][0])], [100 * (v["ci"][1] - v["est"])]], fmt="os"[j],
                       color=f"C{j}", label=s if i == 0 else None)
    sb = A[s]["partB"]["stats"]
    for i, d in enumerate(("REF", "T0", "T0G")):
        for k, (key, col) in enumerate((("C", "C2"), ("T", "C3"))):
            v = sb[f"{key}|{d}"]
            ax[1].errorbar(i + 0.1 * (2 * k - 1) + 0.25 * j, v["est"], yerr=[[v["est"] - v["ci"][0]], [v["ci"][1] - v["est"]]], fmt="os"[j], color=col,
                           label=f"{'count' if key == 'C' else 'timing'} effect ({s})" if i == 0 else None)
ax[0].axhline(0, color="k", lw=0.8)
ax[0].set_xticks(range(5), ["REF", "mid t_ref 0", "mid t_ref 0\n+ gain match", "mid t_ref 0\n+ bias match", "LC10a circ.\nshift"], fontsize=8)
ax[0].set_ylabel("B1 vs DATA rate-weighted excitatory\nintermediate drive to DNa02 [%]")
ax[0].set_title("Part A: intermediate count deficit", fontsize=10)
ax[0].legend(fontsize=8)
ax[1].axhline(0, color="k", lw=0.8)
ax[1].set_xticks(range(3), ["DNa02 REF", "DNa02 t_ref 0", "DNa02 t_ref 0\n+ gain match"], fontsize=8)
ax[1].set_ylabel("effect on DNa02 ipsi [Hz]")
ax[1].set_title("Part B: 2×2 count-swap (real intermediate trains)", fontsize=10)
ax[1].legend(fontsize=7)
fig.suptitle("V6m3 (MODEL): CI95 = wider of nested bootstrap / jackknife-t", fontsize=10)
fig.tight_layout()
os.makedirs(os.path.join(a.run, "figures"), exist_ok=True)
fig.savefig(os.path.join(a.run, "figures", "V6m3_F1.png"), dpi=110)
print("ok")
