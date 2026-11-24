"""Wykresy nowej podstawy i barku. plot_bs.py DIR_WYNIK (czyta raw/ oraz sąsiednie one_run i six_readout)"""
import sys
D = sys.argv[1]
sys.path.insert(0, __file__.rsplit("/", 1)[0])
sys.argv[1] = D + "/../one_run_20261124/raw"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import plot_one as PO  # rcParams, kolory
from analyze_six import load
from base_shoulder import KEEP
from one_run import PRESS

N, B = (dict(np.load(f"{D}/raw/{k}.npz")) for k in ("nowa", "zablokowane"))
_, _, _, _, _, C = load(D + "/../six_readout_20261124/raw")
PROG = np.vstack([C["podstawa"], -C["bark"], C["łokieć"], -C["nadgarstek zgięcie"]]).T
t, BL, OR, GR, VI, INK = N["t"], PO.BL, PO.OR, PO.GR, PO.VI, PO.INK
pl = lambda v, _=None: f"{v:g}".replace(".", ",").replace("-", "−")  # noqa: E731


def base(a):
    a.set_facecolor("#fcfcfb")
    a.grid(axis="y", color="#e8e7e2", lw=0.8)
    a.set_axisbelow(True)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.yaxis.set_major_formatter(pl)


def shade(a):
    for u, v in ((12, 12.53), (36, 36.53)):
        a.axvspan(u, v, color=VI, alpha=0.22, lw=0)
    for u, v, k in PRESS:
        a.axvspan(u, v, color="#0b0b0b", alpha=0.05, lw=0)
        a.text((u + v) / 2, 1.0, f"A{k}", transform=a.get_xaxis_transform(), ha="center", va="bottom", fontsize=8, color=INK)
    a.axhline(0, color="#c9c8c2", lw=0.8, zorder=0)


fig, ax = plt.subplots(4, 3, figsize=(15, 11), sharex=True, facecolor="#fcfcfb", gridspec_kw=dict(hspace=0.3, wspace=0.16))
cum = lambda x: np.cumsum(x, 0)  # noqa: E731
d = np.degrees(N["q_all"] - N["q0"])[:, :4]
cols = ("wcześniejsza prognoza (bez ruchu)", "komendy w nowej próbie", "faktyczny kąt stawu")
for k, j in enumerate(("podstawa", "bark", "łokieć", "zgięcie nadgarstka")):
    for c, y in enumerate((cum(PROG[:, k]) * .01, cum(np.degrees(N["dq_net"][:, k])), d[:, k])):
        a = ax[k, c]
        a.plot(t, y, color=(INK, OR, BL)[c], lw=2)
        a.text(44.6, y[-1] + (1.0 if y[-1] >= 0 else -1.0), pl(round(float(y[-1]), 2) + 0.0).replace("−0", "0") if abs(y[-1]) < .005 else pl(round(float(y[-1]), 2)) + "°", ha="right", va="bottom" if y[-1] >= 0 else "top", fontsize=10)
        a.set_ylim(-9, 25)
        a.set_xlim(0, 45)
        shade(a)
        base(a)
        if k == 0:
            a.set_title(cols[c], fontsize=12, loc="left", pad=18)
        if c == 0:
            a.set_ylabel(j + "\n[° od startu]")
        else:
            a.set_yticklabels([])
        if k == 3:
            a.set_xlabel("czas próby [s]")
fig.suptitle("Prognoza, komendy i faktyczne kąty przy nowej podstawie i nowym barku (MuJoCo, Glu −1, jedno ziarno)", x=0.07, ha="left", fontsize=14, fontweight="bold", y=0.985)
fig.text(0.07, 0.945, "Jedna skala we wszystkich panelach. Fiolet = zbliżenie kuli, szare = nacisk A0/A1. Komendy = suma przyrostów, kąty = MuJoCo; błąd kąta wobec sumy komend ≤ 0,03°.", fontsize=9.5, color=INK)
fig.subplots_adjust(left=0.07, right=0.985, top=0.885, bottom=0.06)
fig.savefig(D + "/trzy_rzeczy_obok_siebie.png", dpi=115)

fig = plt.figure(figsize=(14, 10.5), facecolor="#fcfcfb")
g = fig.add_gridspec(4, 4, height_ratios=[1, 1, 1, 1.15], hspace=0.42, wspace=0.12, left=0.07, right=0.985, top=0.9, bottom=0.04)
for c, (u, v, s) in enumerate(((11.9, 13.3, "zbliżenie 1 (12–12,53 s)"), (35.9, 38.6, "zbliżenie 2 + A1 (36–36,53 s)"))):
    w = (t >= u) & (t <= v)
    a1, a2, a3 = (fig.add_subplot(g[r, 2 * c:2 * c + 2]) for r in range(3))
    for z, ls, lab, al in ((N, "-", "nowa: podstawa i bark ruszają", 1), (B, (0, (3, 1.5)), "kontrola: zablokowane", 1)):
        a1.plot(t[w], z["loom"][w, 0], color=VI, ls=ls, lw=1.8, label="oko L " + ("(nowa)" if z is N else "(zablok.)"))
        a1.plot(t[w], z["loom"][w, 1], color=GR, ls=ls, lw=1.8, label="oko P " + ("(nowa)" if z is N else "(zablok.)"))
        a2.plot(t[w], np.degrees(np.cumsum(z["dq_net"][w, 0])), color=BL, ls=ls, lw=1.8, label="podstawa " + ("(nowa)" if z is N else "(zablok.)"))
        a2.plot(t[w], np.degrees(np.cumsum(z["dq_net"][w, 1])), color=OR, ls=ls, lw=1.8, label="bark " + ("(nowa)" if z is N else "(zablok.)"))
        a3.plot(t[w], 1e3 * z["gap"][w], color=INK, ls=ls, lw=1.8, label="nowa" if z is N else "zablokowane")
    a1.set_title(s, loc="left", fontsize=12)
    for a in (a1, a2, a3):
        base(a)
        a.set_xlim(u, v)
        a.xaxis.set_major_formatter(pl)
    a3.axhline(5, color="#c0392b", lw=1)
    a3.set_xlabel("czas [s]")
    if c == 0:
        a1.set_ylabel("oko [mV]")
        a2.set_ylabel("suma komend\nw oknie [°]")
        a3.set_ylabel("kamera–kula\n[mm]")
        a1.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")
        a2.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")
    a1.set_ylim(-3, 46)
    a2.set_ylim(-1.0, 4.2)
    a3.set_ylim(-10, 250)
K = [KEEP.index(x) for x in (12.5, 35.9, 36.3, 36.6)]
for i, k in enumerate(K):
    a = fig.add_subplot(g[3, i])
    a.imshow(np.vstack([N["klatki"][k], np.full((4, 160), 255), B["klatki"][k]]), cmap="gray", vmin=0, vmax=255, aspect="auto")
    a.set_xticks([])
    a.set_yticks([50, 154], ["nowa", "zablok."] if i == 0 else ["", ""])
    a.set_title(f"{KEEP[k]:g} s".replace(".", ","), fontsize=10)
fig.suptitle("Co widziała kamera na chwytaku: nowa próba a kontrola z zablokowaną podstawą i barkiem", x=0.07, ha="left", fontsize=14, fontweight="bold", y=0.975)
fig.text(0.07, 0.93, "Czerwona linia = 5 mm (próg artefaktu). Przyczyny różnicy (kamera, łokieć, stan sieci) nie są rozdzielone: wpływ kamery to HIPOTEZA.", fontsize=9.5, color=INK)
fig.savefig(D + "/kamera_i_zblizenia.png", dpi=110)
