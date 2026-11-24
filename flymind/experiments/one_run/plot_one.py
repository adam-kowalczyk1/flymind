"""Pełny przebieg na jednej osi czasu. plot_one.py DIR_RAW OUT.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from one_run import PRESS, LEG  # noqa: E402

z = np.load(sys.argv[1] + "/pelny.npz")
t = z["t"]
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 10.5, "text.color": "#0b0b0b", "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.edgecolor": "#c9c8c2"})
V = [(6, 8.5, "w poprzek"), (10, 11.25, "na środek"), (12, 12 + LEG, "zbliżenie"), (13.2, 13.2 + LEG, ""), (14.5, 15.75, "wyjazd"), (34, 35.25, "na środek"), (36, 36 + LEG, "zbliżenie"), (38.5, 38.5 + LEG, ""), (40, 41.25, "wyjazd")]
BL, OR, GR, VI, INK = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#52514e"


def rows(fig, ax):
    a = ax[0]
    for u, v, s in V:
        a.axvspan(u, v, color=VI, alpha=0.85 if s.startswith("zbli") else 0.3, lw=0, ymin=0.42, ymax=0.6)
        a.text((u + v) / 2, 1.04 if s.startswith("zbli") else 0.83, s, ha="center", va="bottom", fontsize=8.5)
    for u, v, k in PRESS:
        a.axvspan(u, v, color=(BL, OR)[k], alpha=0.8, lw=0, ymin=0.04, ymax=0.22)
        a.text((u + v) / 2, 0.31, f"dotyk A{k}", ha="center", va="bottom", fontsize=8.5)
    a.set_yticks([0.17, 0.67], ["dotyk", "kula"])
    a.set_ylim(0, 1.32)
    ax[1].plot(t, z["loom"][:, 0], color=VI, lw=1.8, label="lewy")
    ax[1].plot(t, z["loom"][:, 1], color=GR, lw=1.2, ls=(0, (3, 1.5)), label="prawy")
    ax[1].set_ylabel("oko [mV]")
    ax[1].set_ylim(-2, 46)
    for k in (0, 1):
        ax[2].plot(t, z["felt"][:, k], color=(BL, OR)[k], lw=1.8, label=f"A{k}")
    ax[2].set_ylabel("dotyk [N]")
    for k, (n, c) in enumerate((("bark", BL), ("łokieć", OR), ("nadgarstek", GR))):
        ax[3].plot(t, np.convolve(np.degrees(z["dq"][:, k]) / .01, np.ones(5) / 5, "same"), color=c, lw=1.6, label=n, zorder=3 + (k == 2))
        ax[4].plot(t, np.degrees(z["q_all"][:, 1 + k] - z["q0"][1 + k]), color=c, lw=2, label=n, zorder=3 + (k == 2))
        ax[4].text(45.2, np.degrees(z["q_all"][-1, 1 + k] - z["q0"][1 + k]) + (0.12 if k == 0 else -0.12 if k == 1 else 0), n, va="center", fontsize=9.5)
    ax[3].set_ylabel("komenda sieci\n[°/s]")
    ax[4].set_ylabel("kąt stawu\n[° od startu]")
    st = np.degrees(np.abs(z["dq"])).max(1) / .01 < 0.05
    d = np.diff(np.r_[0, st.astype(int), 0])
    for u, v in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
        if v - u >= 30:
            ax[4].axvspan(u * .01, v * .01, color="#0b0b0b", alpha=0.045, lw=0)
    for a in ax:
        a.set_facecolor("#fcfcfb")
        a.grid(axis="y" if a is not ax[0] else "x", color="#e8e7e2", lw=0.8)
        a.set_axisbelow(True)
        a.set_xlim(0, 45)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
    for a in ax[1:]:
        a.yaxis.set_major_formatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))
    for a in ax[1:4]:
        a.legend(loc="upper left", ncol=3, frameon=False, fontsize=9, borderpad=0)
    ax[-1].set_xlabel("czas próby [s]  (szare tło = trzy stawy bez ruchu)")


if __name__ == "__main__":
    fig, ax = plt.subplots(5, 1, figsize=(14, 9.6), sharex=True, facecolor="#fcfcfb", gridspec_kw=dict(height_ratios=[0.75, 1, 0.8, 1.2, 1.4], hspace=0.16))
    rows(fig, ax)
    fig.suptitle("Jeden ciągły przebieg 45 s: bodźce, wejścia, komendy sieci i rzeczywisty ruch (MuJoCo, Glu −1)", x=0.075, ha="left", fontsize=14, fontweight="bold", y=0.975)
    fig.subplots_adjust(left=0.085, right=0.935, top=0.93, bottom=0.06)
    fig.savefig(sys.argv[2], dpi=125)
