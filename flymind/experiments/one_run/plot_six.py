"""Wykresy odczytu sześciu osi. plot_six.py DIR_RAW_ORYGINAŁU DIR_RAW OUT_45s.png OUT_obrot.png"""
import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import plot_one as PO  # rcParams, kolory, bodźce; czyta raw/pelny.npz z sys.argv[1]
from analyze_six import AXES, load
from one_run import PRESS, LEG

z, meta, col, S, R, C = load(sys.argv[2])
t, BL, OR, GR, VI, INK, GY = z["t"], PO.BL, PO.OR, PO.GR, PO.VI, PO.INK, "#8a8983"
pl = lambda v, _=None: f"{v:g}".replace(".", ",").replace("-", "−")  # noqa: E731


def stim(a):
    for u, v, s in PO.V:
        a.axvspan(u, v, color=VI, alpha=0.85 if s.startswith("zbli") else 0.3, lw=0, ymin=0.42, ymax=0.6)
        a.text((u + v) / 2, 1.04 if s.startswith("zbli") else 0.83, s, ha="center", va="bottom", fontsize=8.5)
    for u, v, k in PRESS:
        a.axvspan(u, v, color=(BL, OR)[k], alpha=0.8, lw=0, ymin=0.04, ymax=0.22)
        a.text((u + v) / 2, 0.31, f"dotyk A{k}", ha="center", va="bottom", fontsize=8.5)
    a.set_yticks([0.17, 0.67], ["dotyk", "kula"])
    a.set_ylim(0, 1.32)


def base(a):
    a.set_facecolor("#fcfcfb")
    a.grid(axis="y", color="#e8e7e2", lw=0.8)
    a.set_axisbelow(True)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.yaxis.set_major_formatter(pl)


fig, ax = plt.subplots(9, 1, figsize=(14, 15.5), sharex=True, facecolor="#fcfcfb", gridspec_kw=dict(height_ratios=[.75, 1, 1, 1, 1, 1, .9, .9, .8], hspace=0.2))
stim(ax[0])
for i, (n, lab) in enumerate((("podstawa", "podstawa\npromotor − remotor"), ("bark", "bark (krętarz)\nzginacze − prostowniki"), ("łokieć", "łokieć\nzginacze − prostownik"), ("nadgarstek zgięcie", "zgięcie nadgarstka\nlevator − depressor")), 1):
    if n == "bark":
        ax[i].plot(t, np.degrees(z["dq"][:, 0]) / .01, color=GY, lw=1.2, ls=(0, (3, 1.5)), label="dzisiejszy bark (wysłany, znak serwa)")
        ax[i].plot([], [], color=BL, lw=1.6, label="nowa mapa (niewysłany, znak mięśni)")
        ax[i].legend(loc="upper left", ncol=2, frameon=False, fontsize=9, borderpad=0)
    ax[i].plot(t, C[n], color=BL, lw=1.6)
    ax[i].set_ylabel(lab + "\n[°/s]", fontsize=9.5)
ax[4].text(0.4, 1.2, "0 impulsów w 7 neuronach przez 45 s", fontsize=9, color=INK)
ax[3].text(0.4, 5.2, "te same neurony i ta sama komenda co dziś", fontsize=9, color=INK)
ax[5].plot(t, C["podstawa"], color=BL, lw=1.6, label="podstawa")
ax[5].plot(t, C["nadgarstek obrót"], color=OR, lw=1.6, label="rotatory (obrót)")
ax[5].set_ylabel("rotatory: przedni − tylny\na podstawa [°/s]", fontsize=9.5)
ax[5].legend(loc="upper left", ncol=2, frameon=False, fontsize=9, borderpad=0)
for a in ax[1:6]:
    a.set_ylim(-14, 11)
    a.axhline(0, color="#c9c8c2", lw=0.8, zorder=0)
for k, (g, lab, c) in enumerate((("6 chwytak|ltm", "ltm (4)", GR), ("6 chwytak|ltm1-tibia", "ltm1 goleń (2)", BL), ("6 chwytak|ltm2-femur", "ltm2 udo (2)", OR))):
    n = int(S[g].sum())
    ax[6].plot(t, R[g], color=c, lw=1.6, label=f"{lab}: {n} " + ("impulsy" if 2 <= n <= 4 else "impulsów"))
ax[6].set_ylabel("chwytak T1\nśr. na neuron [Hz]", fontsize=9.5)
for g, lab, c in (("szczęka T2|zaciskanie (Ti extensor)", "T2 zaciskanie (2)", BL), ("szczęka T2|zwalnianie (Ti flexor + Acc)", "T2 zwalnianie (11)", OR)):
    n = int(S[g].sum())
    ax[7].plot(t, R[g], color=c, lw=1.6, label=f"{lab}: {n} " + ("impulsy" if n % 10 in (2, 3, 4) else "impulsów"))
ax[7].set_ylabel("szczęka T2\nśr. na neuron [Hz]", fontsize=9.5)
for a in ax[6:8]:
    a.set_ylim(-8, 200)
    a.legend(loc="upper left", ncol=3, frameon=False, fontsize=9, borderpad=0)
ax[8].plot(t, C["szczęka T2"], color=BL, lw=1.6)
ax[8].axhline(0, color="#c9c8c2", lw=0.8, zorder=0)
ax[8].set_ylabel("szczęka T2\nmoment [N·m]", fontsize=9.5)
ax[8].set_xlabel("czas próby [s]")
for a in ax:
    base(a)
    a.set_xlim(0, 45)
ax[0].yaxis.set_major_formatter(matplotlib.ticker.FixedFormatter(["dotyk", "kula"]))
fig.suptitle("Komendy kandydackie sześciu osi w próbie 45 s — tylko odczyt, nic nie wysłano do stawów (MuJoCo, Glu −1, ziarno 27 601 001)", x=0.085, ha="left", fontsize=13, fontweight="bold", y=0.99)
fig.text(0.085, 0.967, "Pięć paneli w °/s ma jedną skalę; obie częstości chwytaka mają jedną skalę. Filtr 50 ms i wzmocnienie 0,005 jak w modelu; bez skalowania kanałów. Plus = pierwsza grupa mięśni.", fontsize=9.5, color=INK)
fig.subplots_adjust(left=0.085, right=0.985, top=0.95, bottom=0.035)
fig.savefig(sys.argv[3], dpi=115)

W = [(11.8, 13.4, "zbliżenie 1"), (19.8, 22.6, "A0 (20–22 s)"), (26.8, 29.6, "A1 (27–29 s)"), (35.8, 38.6, "zbliżenie 2 + A1 (36–38 s)")]
fig, ax = plt.subplots(2, 4, figsize=(14, 6.2), facecolor="#fcfcfb", sharex="col", gridspec_kw=dict(width_ratios=[v - u for u, v, _ in W], height_ratios=[1.3, 1], hspace=0.1, wspace=0.07))
grp = [("1 podstawa|+ promotor", "promotor", BL), ("1 podstawa|- remotor", "remotor", BL), ("5 nadg. obrót|Sternal ant. rotator", "rotator przedni", OR), ("5 nadg. obrót|Sternal post. rotator", "rotator tylny", OR)]
for c, (u, v, s) in enumerate(W):
    w = (t >= u) & (t <= v)
    a, b = ax[:, c]
    a.plot(t[w], C["podstawa"][w], color=BL, lw=1.8, label="podstawa")
    a.plot(t[w], C["nadgarstek obrót"][w], color=OR, lw=1.8, label="rotatory")
    op = w & (np.abs(C["podstawa"]) > .05) & (np.abs(C["nadgarstek obrót"]) > .05) & (C["podstawa"] * C["nadgarstek obrót"] < 0)
    for x in t[op]:
        a.axvspan(x, x + .01, color="#0b0b0b", alpha=0.13, lw=0)
    a.axhline(0, color="#c9c8c2", lw=0.8, zorder=0)
    a.set_ylim(-5, 10)
    a.set_title(s, fontsize=11, loc="left")
    y, yt = 0, []
    for g, n, k in grp:
        for j in range(S[g].shape[1]):
            x = t[w][S[g][w, j] > 0]
            b.scatter(x, np.full(len(x), -y), marker="|", s=55, color=k, lw=1.3)
            yt.append((-y, n if j == 0 else ""))
            y += 1
        y += 0.6
    b.set_yticks([p for p, _ in yt], [n for _, n in yt])
    b.set_ylim(-y + .2, 0.8)
    b.set_xlabel("czas [s]")
    b.set_xlim(u, v)
    for q in (a, b):
        base(q)
        if c:
            q.set_yticklabels([])
    b.yaxis.set_major_formatter(matplotlib.ticker.FixedFormatter([n for _, n in yt] if c == 0 else [""] * len(yt)))
    b.xaxis.set_major_formatter(pl)
    b.set_ylabel("impulsy (wiersz = neuron)" if c == 0 else "")
ax[0, 0].set_ylabel("komenda [°/s]")
ax[0, 0].legend(loc="upper left", frameon=False, fontsize=9.5)
fig.suptitle("Podstawa a rotatory w czterech oknach, w których cokolwiek się dzieje (poza nimi po 0 impulsów; + = do przodu, − = do tyłu)", x=0.095, ha="left", fontsize=12.5, fontweight="bold")
fig.text(0.095, 0.905, "Szare pasy = oba > 0,05 °/s i przeciwny kierunek. Jedna skala we wszystkich oknach.", fontsize=9.5, color=INK)
fig.subplots_adjust(left=0.095, right=0.99, top=0.84, bottom=0.08)
fig.savefig(sys.argv[4], dpi=115)
