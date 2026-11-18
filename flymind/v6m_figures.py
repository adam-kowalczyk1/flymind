"""flymind/v6m_figures.py — V6m figures from analysis.json / raw (descriptive). Run: .venv/bin/python -I -B flymind/v6m_figures.py --run flymind/results/v6m"""
import argparse
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    A = json.load(open(os.path.join(a.run, "analysis.json")))
    fd = os.path.join(a.run, "figures")
    os.makedirs(fd, exist_ok=True)
    # F1 gap per condition (main + replication)
    fig, ax = plt.subplots(figsize=(10, 8))
    g = A["main"]["gaps"]
    names = list(g)
    for j, kind in enumerate(("main", "rep")):
        gg = A[kind]["gaps"]
        for i, c in enumerate(names):
            if c in gg:
                v = gg[c]
                ax.errorbar(v["gap"], i + 0.18 * j, xerr=[[v["gap"] - v["gap_ci95"][0]], [v["gap_ci95"][1] - v["gap"]]], fmt="os"[j],
                            color=f"C{j}", label=("main (B1 8 421 001–010)", "replication (B1 8 421 011–020, new noise)")[j] if i == 0 else None)
    ax.axvline(0, color="k", lw=0.8)
    ax.axvline(g["REF"]["gap"], color="0.6", ls=":")
    ax.set_yticks(range(len(names)), names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("DNa02 ipsi gap, B1 trains − DATA trains [Hz] (CI95)")
    ax.set_title("V6m: gap under each single-factor computational ablation (MODEL)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(fd, "V6m_F1_gaps.png"), dpi=110)
    # F2 Exp 4 dose-response
    e = A["E4"]
    x = np.array(e["lc_sync_by_grid"]["fano10"])
    grid = e["grid"]
    prim = [i for i, gr in enumerate(grid) if gr[0] == 10.0]
    sec = [i for i, gr in enumerate(grid) if gr[0] == 40.0]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    for k, d in enumerate(e["dynamics"]):
        y = np.array(e["dn_mean"][d])
        ax[0].plot(x[prim], y[prim], "o-", color=f"C{k}", label=d)
        ax[0].plot(x[sec], y[sec], "^", color=f"C{k}", mfc="none")
    dD, dB = A["main"]["descr"]["REF"]["lc_sync"]["fano10"], A["main"]["gaps"]["REF"]
    ax[0].plot([dD["data"]], [dB["dn_data"]], "k*", ms=14, label="real DATA trains (REF)")
    ax[0].plot([dD["b1"]], [dB["dn_b1"]], "kX", ms=12, label="real B1 trains (REF)")
    ax[0].set_xlabel("LC10a ipsi Fano (10 ms bins)")
    ax[0].set_ylabel("DNa02 ipsi [Hz]")
    ax[0].set_title("Exp 4: synthetic synchrony (circles 10 Hz events, triangles 40 Hz)")
    ax[0].legend(fontsize=7)
    v = np.array(e["lc_sync_by_grid"]["volley2"])
    for k, d in enumerate(e["dynamics"]):
        y = np.array(e["dn_mean"][d])
        ax[1].plot(v[prim], y[prim], "o-", color=f"C{k}")
        ax[1].plot(v[sec], y[sec], "^", color=f"C{k}", mfc="none")
    ax[1].set_xlabel("LC10a volley participation (2 ms bins ≥ mean + 3 SD)")
    ax[1].set_title("same, other synchrony measure")
    fig.tight_layout()
    fig.savefig(os.path.join(fd, "V6m_F2_dose_response.png"), dpi=110)
    # F3 DNa02 ISI histograms REF vs DN t_ref 0
    raw = os.path.join(a.run, "raw")
    D = np.load(os.path.join(raw, "main_DATA.npz"))
    Bs = [np.load(p) for p in sorted(glob.glob(os.path.join(raw, "main_B1_*.npz")))]
    c = list(D["conds"])
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.5), sharey=True)
    for x_, cn in zip(ax, ("REF", "E1_DN_t0", "E3_MCIRC")):
        hD = D["isi"][c.index(cn)].sum((0, 1, 2))[:30]
        hB = sum(b["isi"][c.index(cn)].sum((0, 1, 2)) for b in Bs)[:30]
        x_.step(range(1, 31), hD / hD.sum(), where="mid", color="k", label="DATA trains")
        x_.step(range(1, 31), hB / hB.sum(), where="mid", color="C3", label="B1 trains (10 inst.)")
        x_.set_title(cn)
        x_.set_xlabel("DNa02 ISI [ms]")
    ax[0].set_ylabel("fraction of ISIs (≤ 30 ms shown)")
    ax[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(fd, "V6m_F3_isi.png"), dpi=110)
    print("figures written")


if __name__ == "__main__":
    main()
