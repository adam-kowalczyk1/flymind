"""Miary planu PLAN_10_ZIAREN.md. analyze_10.py DIR_WYNIK → analysis.json, ruch_10_ziaren.csv, ruch_10_ziaren.png"""
import csv
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

D = sys.argv[1]
S = range(27602001, 27602011)
J = ("podstawa", "bark", "łokieć", "nadgarstek zgięcie")
Z = {s: dict(np.load(f"{D}/raw/{s}.npz")) for s in S}
ang = lambda z: np.degrees(np.vstack([z["q0"], z["q_all"]]))[:, :4]  # noqa: E731 — wiersz i = stan w chwili i·10 ms
mv = lambda z, a, b: ang(z)[int(b * 100)] - ang(z)[int(a * 100)]     # noqa: E731
res, rows = dict(n=len(Z)), []
WINS = {"A0 (20–22 s)": (20, 22), "A1 (27–29 s)": (27, 29), "spokój (0–6 s)": (0, 6), "drugie A1 ze zbliżeniem (36–38,5 s), poza miarami": (36, 38.5), "cała scena": (0, 45)}
for w, (a, b) in WINS.items():
    M = np.array([mv(z, a, b) for z in Z.values()])
    res[w] = {}
    for k, j in enumerate(J):
        x = M[:, k]
        mov = np.abs(x) >= 0.05
        pos, neg = int((x[mov] > 0).sum()), int((x[mov] < 0).sum())
        res[w][j] = dict(wartosci=x.round(3).tolist(), mediana=round(float(np.median(x)), 3), zakres=[round(float(x.min()), 3), round(float(x.max()), 3)], plus=pos, minus=neg, bez_ruchu=int((~mov).sum()))
res["spokoj_szczegoly"] = dict(maks_wychylenie_stopnie={j: round(float(max(np.abs(ang(z)[:601] - ang(z)[0])[:, k].max() for z in Z.values())), 4) for k, j in enumerate(J)},
                               impulsy_76_neuronow_0_6_s=[int(z["cnt"][:600, 5:].sum()) for z in Z.values()], impulsy_calej_sieci_5_grup_0_6_s=[int(z["cnt"][:600, :5].sum()) for z in Z.values()],
                               komendy_podst_bark_lok_nadg_maks_stopnie_s=[np.degrees(np.abs(z["dq_net"][:600, :4])).max(0).round(4).tolist() for z in Z.values()])
res["ograniczenia"] = {str(s): dict(flagi_SafetyLayer_na_staw=(z["flag"] > 0).sum(0).astype(int).tolist(), straznik_stolu=int(z["guard"].sum()), kontakty=int(z["ncon"].max()), maks_wyprzedzenie_celu_rad=np.abs(z["qt"][:, :4] - z["q_all"][:, :4]).max(0).round(4).tolist(),
                                          min_przerwa_kula_kamera_mm=round(float(z["gap"].min() * 1e3), 1)) for s, z in Z.items()}
res["kat_wobec_sumy_komend_maks_blad_stopnie"] = round(max(float(np.abs((ang(z)[1:] - ang(z)[0]) - np.degrees(np.cumsum(z["dq_net"][:, :4], 0))).max()) for z in Z.values()), 4)
json.dump(res, open(D + "/analysis.json", "x"), indent=1, ensure_ascii=False)
with open(D + "/ruch_10_ziaren.csv", "x", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ziarno"] + [f"{j} {x}" for x in WINS for j in J])
    for i, s in enumerate(S):
        w.writerow([s] + [res[x][j]["wartosci"][i] for x in WINS for j in J])
INK, BL, OR, GR, VI = "#52514e", "#2a78d6", "#eb6834", "#1baf7a", "#6250d6"
pl = lambda v, _=None: f"{v:g}".replace(".", ",").replace("-", "−")  # noqa: E731
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 11})
fig, ax = plt.subplots(1, 3, figsize=(14, 5.4), facecolor="#fcfcfb", gridspec_kw=dict(width_ratios=[1.15, 1, 1], wspace=0.12), sharey=False)
rng = np.arange(10)
for a, (t, win, js) in zip(ax, (("Bark przy A0 (główna miara)", "A0 (20–22 s)", ["bark"]), ("Podstawa i łokieć przy A0", "A0 (20–22 s)", ["podstawa", "łokieć"]), ("Podstawa, łokieć i bark przy pierwszym A1", "A1 (27–29 s)", ["podstawa", "łokieć", "bark"]))):
    a.set_facecolor("#fcfcfb")
    a.grid(axis="y", color="#e8e7e2", lw=.8)
    a.set_axisbelow(True)
    a.axhline(0, color="#8a8983", lw=1)
    for i, j in enumerate(js):
        x = np.array(res[win][j]["wartosci"])
        c = {"bark": BL, "podstawa": OR, "łokieć": GR}[j]
        xs = i + np.linspace(-.28, .28, 10)
        a.plot([i - .36, i + .36], [np.median(x)] * 2, color=INK, lw=2)
        a.scatter(xs, x, s=46, color=c, edgecolor="#fcfcfb", lw=1.4, zorder=3)
        a.text(i + .38, np.median(x), f" {pl(round(float(np.median(x)), 2))}°", va="center", fontsize=10, color=INK)
    a.set_xticks(range(len(js)), js)
    a.set_xlim(-.55, len(js) - .2)
    a.set_title(t, loc="left", fontsize=11.5)
    a.yaxis.set_major_formatter(pl)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
ax[0].set_ylabel("ruch stawu w czasie nacisku [°]")
ax[0].set_ylim(-1, 14.5)
ax[1].set_ylim(-4, 3)
fig.suptitle("Zamrożona nowa podstawa i bark: 10 nowych ziaren szumu (MuJoCo, Glu −1)", x=0.06, ha="left", fontsize=14, fontweight="bold", y=0.98)
fig.text(0.06, 0.9, "Każda kropka = jedno ziarno, kreska = mediana. Plus = bark w dół, podstawa promotorem, łokieć zgina. Skale osi różnią się między panelami.", fontsize=9.5, color=INK)
fig.subplots_adjust(left=0.06, right=0.985, top=0.82, bottom=0.08)
fig.savefig(D + "/ruch_10_ziaren.png", dpi=120)
for k, v in res.items():
    if isinstance(v, dict):
        print(k)
        [print("   ", a, b) for a, b in v.items()]
    else:
        print(k, v)
