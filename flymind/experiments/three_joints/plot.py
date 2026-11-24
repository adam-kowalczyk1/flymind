"""Wykres rzeczywistych kątów trzech stawów. plot.py DIR_RAW GLU OUT.png"""
import glob
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

d, g, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
C = [("spokoj", "spokój", "#77756f"), ("palec1", "palec 1 (szczęka stała)", "#2a78d6"), ("palec2", "palec 2 (szczęka ruchoma)", "#eb6834")]
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 11, "text.color": "#0b0b0b", "axes.labelcolor": "#52514e",
                     "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.edgecolor": "#c9c8c2"})
fig, ax = plt.subplots(3, 1, figsize=(10, 9.4), sharex=True, facecolor="#fcfcfb")
t = np.arange(0, 801) * 0.01
Q = {c: np.degrees([np.vstack([z["q0"][1:4], z["q"]]) for z in map(np.load, sorted(glob.glob(f"{d}/g{g:+.0f}_*_{c}.npz")))]) for c, _, _ in C}
span = max(np.ptp(np.concatenate([Q[c][:, :, k] for c in Q])) for k in range(3)) * 1.18
for k, name in enumerate(("Bark", "Łokieć", "Nadgarstek")):
    a = ax[k]
    a.set_facecolor("#fcfcfb")
    a.axvspan(3, 5, color="#0b0b0b", alpha=0.05, lw=0)
    for x in (3, 5):
        a.axvline(x, color="#52514e", lw=1)
    for c, lab, col in C:
        a.plot(t, Q[c][:, :, k].T, color=col, lw=0.8, alpha=0.35)
        a.plot(t, np.median(Q[c][:, :, k], 0), color=col, lw=2.4, label=lab if k == 0 else None)
    al = np.concatenate([Q[c][:, :, k] for c in Q])
    m = (al.min() + al.max()) / 2
    a.set_ylim(m - span / 2, m + span / 2)
    a.set_title(name, loc="left", fontsize=12, fontweight="bold", pad=4)
    a.set_ylabel("kąt [°]")
    a.grid(axis="y", color="#e8e7e2", lw=0.8)
    a.set_axisbelow(True)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    ends = sorted((float(np.median(Q[c][:, -1, k])), n) for c, n in (("spokoj", "spokój"), ("palec1", "palec 1"), ("palec2", "palec 2")))
    grp = []                                                    # etykiety na końcach linii; bliskie sobie łączone w jedną
    for v, n in ends:
        if grp and v - grp[-1][0][-1] < span * 0.05:
            grp[-1][0].append(v)
            grp[-1][1].append(n)
        else:
            grp.append(([v], [n]))
    for v, n in grp:
        a.text(8.06, np.mean(v), " ≈ ".join(n) if len(n) > 1 else n[0], va="center", fontsize=9.5, color="#0b0b0b")
ax[0].text(4, ax[0].get_ylim()[1] - span * 0.05, "nacisk 3 N", ha="center", va="top", fontsize=10.5, color="#0b0b0b")
ax[0].text(1.5, ax[0].get_ylim()[1] - span * 0.05, "przed dotykiem", ha="center", va="top", fontsize=10.5, color="#52514e")
ax[2].set_xlabel("czas [s]")
ax[2].set_xlim(0, 8)
fig.suptitle(f"Rzeczywiste kąty stawów w MuJoCo, sieć bez sekwencji zadania (Glu {'−1' if g < 0 else '+1'})", x=0.075, ha="left", fontsize=14, fontweight="bold", y=0.985)
fig.text(0.075, 0.945, f"cienkie linie = {len(Q['spokoj'])} ziaren szumu, gruba = mediana; każdy panel ma tę samą rozpiętość osi ({span:.1f}°)".replace(".", ","), fontsize=10.5, color="#52514e")
fig.legend(loc="upper left", bbox_to_anchor=(0.068, 0.94), ncol=3, frameon=False, fontsize=10.5, handlelength=1.6)
fig.subplots_adjust(left=0.085, right=0.83, top=0.87, bottom=0.07, hspace=0.24)
fig.savefig(out, dpi=150)
