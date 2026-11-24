"""Każda sieć w jednym wierszu: różnica ruchu między palcami, SI, aktywność. plot_tas.py analysis_tasowania.json OUT.png"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = json.load(open(sys.argv[1]))["sieci"]
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 9.5, "text.color": "#0b0b0b", "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "axes.edgecolor": "#c9c8c2"})
rows, y = [], 0
for fam, name in (("N", "sieć z danych muchy"), ("LS", "LS: zachowana klasa neuronu i strona (główna)"), ("LSN", "LSN: LS + rozdzielone nogi"), ("L", "L: zachowane warstwy"), ("F", "F: swobodne")):
    tags = sorted(t for t in R if t.rstrip("0123456789") == fam)
    rows.append((y, None, name))
    y += 1
    for t in tags:
        rows.append((y, t, "dane" if t == "N" else f"{fam} {int(t[-3:])}"))
        y += 1
    y += 0.5
fig, ax = plt.subplots(1, 3, figsize=(12, 14), sharey=True, facecolor="#fcfcfb", gridspec_kw=dict(width_ratios=[2.2, 1.1, 1.3], wspace=0.08))
N, kw = R["N"], dict(edgecolor="#fcfcfb", linewidth=0.8, s=46, zorder=3)
for a in ax:
    a.set_facecolor("#fcfcfb")
    a.grid(axis="x", color="#e8e7e2", lw=0.8)
    a.set_axisbelow(True)
    a.tick_params(left=False)
    for s in ("top", "right", "left"):
        a.spines[s].set_visible(False)
for yy, t, lab in rows:
    if t is None:
        ax[0].text(-0.235, yy, lab, transform=ax[0].get_yaxis_transform(), fontweight="bold", va="center", fontsize=10.5)
        continue
    r = R[t]
    ax[0].text(-0.02, yy, lab, transform=ax[0].get_yaxis_transform(), ha="right", va="center", color="#52514e", fontweight="bold" if t == "N" else None)
    for k, (c, m) in enumerate((("#1baf7a", "o"), ("#6250d6", "s"))):
        ax[0].plot(np.degrees([r["D_min"][k], r["D_max"][k]]), [yy, yy], color=c, lw=1.4, alpha=0.5, zorder=2)
        ax[0].scatter(np.degrees(r["D"][k]), yy, color=c, marker=m, **kw)
    if r["SI"] is None:
        ax[1].text(0.02, yy, "nie reaguje ruchem", va="center", fontsize=8.5, color="#52514e")
    else:
        ax[1].scatter(r["SI"], yy, color="#52514e", **kw)
    for c, col, m in (("palec1", "#2a78d6", "o"), ("palec2", "#eb6834", "s")):
        ax[2].scatter(r["akt"][c]["nacisk"], yy, color=col, marker=m, **kw)
ax[0].axvline(0, color="#52514e", lw=1)
ax[1].axvline(N["SI"], color="#0b0b0b", lw=1, ls=(0, (4, 3)))
for c in ("palec1", "palec2"):
    ax[2].axvline(N["akt"][c]["nacisk"], color="#0b0b0b", lw=1, ls=(0, (4, 3)))
ax[0].set_xlabel("palec 1 − palec 2 [°]: mediana 10 ziaren, kreska = min…max")
ax[1].set_xlabel("SI (0 = ten sam ruch, 1 = inny)")
ax[2].set_xlabel("średnia aktywność sieci [Hz]")
for k, t in enumerate(("Różnica ruchu między palcami", "Względem ruchu (SI)", "Aktywność podczas nacisku")):
    ax[k].set_title(t, loc="left", fontsize=11, fontweight="bold", pad=26)
H = lambda c, m, l: plt.Line2D([], [], color=c, marker=m, ls="", markersize=7, label=l)  # noqa: E731
L = dict(loc="lower left", bbox_to_anchor=(-0.02, 1.0), frameon=False, ncol=2, fontsize=9.5, handletextpad=0.2, columnspacing=1.2, borderpad=0)
ax[0].legend(handles=[H("#1baf7a", "o", "bark"), H("#6250d6", "s", "łokieć")], **L)
ax[2].legend(handles=[H("#2a78d6", "o", "palec 1"), H("#eb6834", "s", "palec 2")], **L)
ax[1].text(0, 1.004, "przerywana = sieć z danych", transform=ax[1].transAxes, va="bottom", fontsize=9.5, color="#52514e")
ax[1].set_xlim(0, 1.08)
ax[1].xaxis.set_major_formatter(lambda v, _: f"{v:g}".replace(".", ","))
ax[2].set_xlim(0, 3.7)
ax[0].set_ylim(y, -1)
ax[0].set_yticks([])
fig.suptitle("Sieci potasowane też różnie reagują na oba palce (MuJoCo, Glu −1)", x=0.055, ha="left", fontsize=14, fontweight="bold", y=0.975)
fig.subplots_adjust(left=0.175, right=0.975, top=0.915, bottom=0.05)
fig.savefig(sys.argv[2], dpi=130)
