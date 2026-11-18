"""flymind/v6_figures.py — figures for V6 from results/v6/analysis.json (descriptive; no new statistics).
Run: .venv/bin/python -I -B flymind/v6_figures.py --run flymind/results/v6
"""
import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v6 import LV  # noqa: E402


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    A = json.load(open(os.path.join(a.run, "analysis.json")))
    os.makedirs(os.path.join(a.run, "figures"), exist_ok=True)
    ol = A["openloop"]
    fig, ax = plt.subplots(4, 4, figsize=(13, 11), sharex=True)
    for x, (c, r) in zip(ax.flat, ol.items()):
        x.plot(LV, r["dn_curve_data"], "k-", label="DATA")
        x.plot(LV, r["dn_curve_sws_mean"], "C3--", label="SWS mean (50)")
        x.axvspan(*r["own_window"], color="0.9")
        x.set_title(f"{c}  ΔDN own {r['families']['SWS']['dn|own']['delta']:+.1f} Hz", fontsize=9)
        x.set_ylim(0, 260)
    ax[0, 0].legend(fontsize=7)
    for x in ax[-1]:
        x.set_xlabel("LC10a current, unilateral [mV]")
    for x in ax[:, 0]:
        x.set_ylabel("DNa02 ipsi [Hz]")
    fig.suptitle("V6 open loop: DNa02 ipsi steady state (E1, 4 reps); grey = DATA own window (MODEL)")
    fig.tight_layout()
    fig.savefig(os.path.join(a.run, "figures", "V6_F1_openloop_curves.png"), dpi=110)
    cl = A["closedloop"]["per_config"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for x, st in zip(ax, ("S1", "S2")):
        for j, fam in enumerate(("SWS", "B1")):
            for i, c in enumerate(cl):
                v = cl[c].get(f"{fam}|{st}")
                if v:
                    y = i + (0.15 if fam == "B1" else -0.15)
                    x.errorbar(v["mean_d"], y, xerr=[[v["mean_d"] - v["ci95_cluster"][0]], [v["ci95_cluster"][1] - v["mean_d"]]],
                               fmt="o" if fam == "SWS" else "s", color=f"C{j}", label=fam if i == 0 else None)
        for s in (-0.5, 0.5):
            x.axvline(s, color="0.7", ls=":")
        x.axvline(0, color="k", lw=0.8)
        x.set_yticks(range(len(cl)), list(cl))
        x.set_title(f"{st}: d = err(DATA) − err(ctrl) [°], CI95 cluster")
        x.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(a.run, "figures", "V6_F2_closedloop_d.png"), dpi=110)
    print("figures written")


if __name__ == "__main__":
    main()
