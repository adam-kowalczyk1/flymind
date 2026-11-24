"""Wspólna oś czasu: sygnał oka, komendy, kąty; A (na żywo) vs B (nagranie). plot_ab.py DIR_RAW OUT.png"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

d, seeds = sys.argv[1], range(27501001, 27501011)
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 10, "text.color": "#0b0b0b", "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.edgecolor": "#c9c8c2"})
C, t = dict(A="#2a78d6", B="#eb6834"), np.arange(700) * 0.01
ROWS = [("Oko: lewy\n[mV]", lambda z: z["loom"][:, 0]), ("Oko: prawy\n[mV]", lambda z: z["loom"][:, 1])] + \
       [(f"Komenda: {n}\n[°/s]", (lambda k: lambda z: np.degrees(z["dq"][:, k]) / 0.01)(k)) for k, n in enumerate(("bark", "łokieć", "nadgarstek"))] + \
       [(f"Kąt: {n}\n[° od startu]", (lambda k: lambda z: np.degrees(z["q"][:, k] - z["q0"][1 + k]))(k)) for k, n in enumerate(("bark", "łokieć", "nadgarstek"))]
fig, ax = plt.subplots(len(ROWS), 2, figsize=(13.5, 15.5), sharex=True, facecolor="#fcfcfb")
for c, g in enumerate((-1, 1)):
    Z = {k: [np.load(f"{d}/g{g:+.0f}_{s}_{k}.npz") for s in seeds] for k in "AB"}
    for r, (lab, f) in enumerate(ROWS):
        a = ax[r, c]
        a.set_facecolor("#fcfcfb")
        for x0 in (1.0, 4.27):
            a.axvspan(x0, x0 + 0.633, color="#0b0b0b", alpha=0.08, lw=0)
        for k in "BA":
            X = np.array([f(z) for z in Z[k]])
            if 2 <= r <= 4:                                        # komendy: średnia z 100 ms, żeby pojedyncze impulsy były czytelne
                X = np.array([np.convolve(x, np.ones(10) / 10, "same") for x in X])
            a.plot(t, X.T, color=C[k], lw=0.7, alpha=0.28)
            a.plot(t, np.median(X, 0), color=C[k], lw=2.2, ls="-" if k == "B" else (0, (4, 1.2)))
        a.grid(axis="y", color="#e8e7e2", lw=0.8)
        a.set_axisbelow(True)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        if c == 0:
            a.set_ylabel(lab, rotation=0, ha="right", va="center", labelpad=12)
        if r < 2:
            a.set_ylim(-2, 46)
        if g == -1:
            if 2 <= r <= 4:
                a.set_ylim(-3, 3)
            if r >= 5:
                a.set_ylim(-0.8, 0.8)
        a.margins(x=0)
        a.yaxis.set_major_formatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))
        if r == 0:
            a.set_title("Glu −1 (glutaminian hamuje)" if g < 0 else "Glu +1 (glutaminian pobudza)", fontsize=12, fontweight="bold", loc="left", pad=18)
            a.text(1.32, 47, "1. zbliżenie", ha="center", va="bottom", fontsize=9, color="#52514e")
            a.text(4.59, 47, "2. zbliżenie", ha="center", va="bottom", fontsize=9, color="#52514e")
    ax[-1, c].set_xlabel("czas [s]")
    ax[-1, c].set_xlim(0, 7)
fig.align_ylabels(ax[:, 0])
H = [plt.Line2D([], [], color=C["A"], lw=2.2, ls=(0, (4, 1.2)), label="A: obraz na żywo z nadgarstka"), plt.Line2D([], [], color=C["B"], lw=2.2, label="B: nagranie z nieruchomej kamery")]
fig.legend(handles=H, loc="upper left", bbox_to_anchor=(0.135, 0.968), ncol=2, frameon=False, fontsize=10.5)
fig.suptitle("Dwa zbliżenia kuli: oko, komendy, ruch (MuJoCo, te same ziarna w parze A/B)", x=0.14, ha="left", fontsize=14, fontweight="bold", y=0.985)
fig.text(0.14, 0.008, "Cienkie linie = 10 ziaren, gruba = mediana; komendy wygładzone 100 ms; skale osi różne dla Glu −1 i Glu +1. Szare pasy = kula się zbliża.", fontsize=9.5, color="#52514e")
fig.subplots_adjust(left=0.145, right=0.985, top=0.915, bottom=0.05, wspace=0.1, hspace=0.22)
fig.savefig(sys.argv[2], dpi=125)
