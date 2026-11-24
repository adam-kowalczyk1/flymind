"""Lewy i prawy sygnał oka v2 w czterech sytuacjach. plot0.py sygnaly.npz OUT.png"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

z = {k.replace("__", "/"): v for k, v in np.load(sys.argv[1]).items()}
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 10.5, "text.color": "#0b0b0b", "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.edgecolor": "#c9c8c2"})
t, C = np.arange(350) * 0.01, dict(S="#77756f", K="#2a78d6", R="#1baf7a", KR="#eb6834")
fig, ax = plt.subplots(2, 3, figsize=(13.5, 7.6), sharex=True, sharey=True, facecolor="#fcfcfb")
for c, sc in enumerate((1, 5, 20)):
    rot = [z[f"R_{sc}_{k:02d}/rot"].max() for k in range(15)]
    for r, side in enumerate(("Lewy", "Prawy")):
        a = ax[r, c]
        a.set_facecolor("#fcfcfb")
        a.axvspan(1.367, 2.0, color="#0b0b0b", alpha=0.05, lw=0)
        for nm in ("R", "KR"):
            X = np.array([z[f"{nm}_{sc}_{k:02d}/v2"][:, r] for k in range(15)])
            a.plot(t, X.T, color=C[nm], lw=0.8, alpha=0.75 if sc == 20 else 0.4, zorder=3)
            if sc < 20 or nm == "R":                            # przy ×20 mediana różnych kształtów wprowadza w błąd
                a.plot(t, np.median(X, 0), color=C[nm], lw=2.2, zorder=4)
        a.plot(t, z["S/v2"][:, r], color=C["S"], lw=2.2, zorder=2)
        a.plot(t, z["K/v2"][:, r], color=C["K"], lw=2.4, zorder=5)
        a.set_ylim(-1.5, 46)
        a.set_xlim(1.0, 2.6)
        a.set_xticks([1.2, 1.6, 2.0, 2.4], ["1,2", "1,6", "2,0", "2,4"])
        a.axhline(40, color="#52514e", lw=0.8, ls=(0, (4, 3)))
        a.axhline(7, color="#52514e", lw=0.8, ls=(0, (1, 2)))
        a.grid(axis="y", color="#e8e7e2", lw=0.8)
        a.set_axisbelow(True)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        if c == 0:
            a.set_ylabel(f"{side} sygnał [mV]")
            a.text(1.02, 41, "40 mV = najwyższy możliwy", fontsize=9, color="#52514e", va="bottom")
            a.text(1.02, 7.5, "7 mV = próg neuronu w modelu", fontsize=9, color="#52514e", va="bottom")
        if r == 0:
            f = lambda x: f"{x:.2f}".replace(".", ",") if x < 1 else f"{x:.1f}".replace(".", ",")  # noqa: E731
            a.set_title({1: "Zapisany mały ruch ramienia", 5: "Kontrola: ruch ×5", 20: "Kontrola: ruch ×20"}[sc] + f"\nobrót kamery {f(min(rot))}–{f(max(rot))}°", fontsize=11, fontweight="bold", loc="left")
            a.text(1.68, 44.6, "kula się zbliża", ha="center", va="center", fontsize=9, color="#52514e")
        else:
            a.set_xlabel("czas próby [s]")
H = lambda c, l: plt.Line2D([], [], color=C[c], lw=2.4, label=l)  # noqa: E731
fig.legend(handles=[H("S", "wszystko nieruchome"), H("K", "sama kula"), H("R", "sama kamera"), H("KR", "kula i kamera")], loc="upper left", bbox_to_anchor=(0.052, 0.935), ncol=4, frameon=False, fontsize=10.5)
fig.suptitle("Sygnał oka, który trafiłby do neuronów (MuJoCo, kamera nadgarstka, bez sieci)", x=0.06, ha="left", fontsize=14, fontweight="bold", y=0.985)
fig.text(0.06, 0.012, "Cienkie linie = 15 zapisanych trajektorii (Glu −1, sam wzrok), gruba = mediana (przy ×20 bez mediany). „Nieruchome” i „sama kamera” leżą na zerze. Bez szumu kamery.", fontsize=9.5, color="#52514e")
fig.subplots_adjust(left=0.06, right=0.985, top=0.835, bottom=0.115, wspace=0.06, hspace=0.12)
fig.savefig(sys.argv[2], dpi=140)
