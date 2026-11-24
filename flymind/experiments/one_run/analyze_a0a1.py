"""Pary A0/A1 (plan: PLAN_A0_A1.md). analyze_a0a1.py DIR_WYNIK → analysis.json, pary.csv, pary.png"""
import csv
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

D = sys.argv[1]
S = range(27602001, 27602011)
A0 = {s: dict(np.load(f"{D}/../seeds10_20261124/raw/{s}.npz")) for s in S}
A1 = {s: dict(np.load(f"{D}/raw/{s}.npz")) for s in S}
J = {"bark": 1, "podstawa": 0, "łokieć": 2}
res = dict(zgodnosc={}, sila={}, ograniczenia_A1={})
for s in S:
    a, b = A0[s], A1[s]
    eq = {k: bool(np.array_equal(a[k][:2000], b[k][:2000])) for k in a if k not in ("q0", "klatki")}
    eq["q0"], eq["klatki (przed 20 s)"] = bool(np.array_equal(a["q0"], b["q0"])), bool(np.array_equal(a["klatki"][:3], b["klatki"][:3]))
    fd = {}
    for k in ("felt", "feco", "fcrc", "loom", "cnt", "dq_net", "q_all", "qt"):
        x = (a[k][:2200] != b[k][:2200]).reshape(2200, -1).any(1)
        fd[k] = round(float(a["t"][x.argmax()]), 2) if x.any() else None
    res["zgodnosc"][s] = dict(wszystko_zgodne_0_20s=all(eq.values()), niezgodne=[k for k, v in eq.items() if not v], liczba_pol=len(eq), pierwszy_takt_roznicy_s=fd)
    f0, f1 = a["felt"][2000:2200], b["felt"][:2200][2000:2200]
    res["sila"][s] = dict(A0_kanal0_rowne_A1_kanal1=bool(np.array_equal(f0[:, 0], f1[:, 1])), A0_kanal1_zero=bool((f0[:, 1] == 0).all()), A1_kanal0_zero=bool((f1[:, 0] == 0).all()), maks_N=round(float(f1[:, 1].max()), 3),
                          suma_N_takt=round(float(f0[:, 0].sum()), 3), suma_N_takt_A1=round(float(f1[:, 1].sum()), 3))
    res["ograniczenia_A1"][s] = dict(flagi=int((b["flag"] > 0).sum()), straznik=int(b["guard"].sum()), kontakty=int(b["ncon"].max()), flagi_A0=int((a["flag"][:2200] > 0).sum()))
ang = lambda z: np.degrees(np.vstack([z["q0"], z["q_all"]]))  # noqa: E731
mv = lambda z, k: ang(z)[2200, k] - ang(z)[2000, k]           # noqa: E731
M = {}
for j, k in J.items():
    x0, x1 = np.array([mv(A0[s], k) for s in S]), np.array([mv(A1[s], k) for s in S])
    d = x1 - x0
    M[j] = (x0, x1, d)
    res[j] = dict(A0=x0.round(3).tolist(), A1=x1.round(3).tolist(), roznica_A1_minus_A0=d.round(3).tolist(), mediana_A0=round(float(np.median(x0)), 3), mediana_A1=round(float(np.median(x1)), 3), mediana_roznicy=round(float(np.median(d)), 3),
                  zakres_A0=[round(float(x0.min()), 3), round(float(x0.max()), 3)], zakres_A1=[round(float(x1.min()), 3), round(float(x1.max()), 3)], zakres_roznicy=[round(float(d.min()), 3), round(float(d.max()), 3)],
                  roznica_dodatnia=int((d > .05).sum()), roznica_ujemna=int((d < -.05).sum()), roznica_ponizej_0_05=int((np.abs(d) <= .05).sum()),
                  ten_sam_kierunek_co_A0=int(((np.sign(x0) == np.sign(x1)) & (np.abs(x0) >= .05) & (np.abs(x1) >= .05)).sum()))
json.dump(res, open(D + "/analysis.json", "x"), indent=1, ensure_ascii=False)
with open(D + "/pary.csv", "x", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ziarno"] + [f"{j} {n}" for j in J for n in ("A0", "A1", "A1−A0")])
    for i, s in enumerate(S):
        w.writerow([s] + [round(float(M[j][n][i]), 4) for j in J for n in range(3)])
INK, BL, OR = "#52514e", "#2a78d6", "#eb6834"
pl = lambda v, _=None: f"{v:g}".replace(".", ",").replace("-", "−")  # noqa: E731
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 11})
fig, ax = plt.subplots(1, 3, figsize=(14, 5.6), facecolor="#fcfcfb", gridspec_kw=dict(wspace=.2))
for a, j in zip(ax, J):
    x0, x1, d = M[j]
    for p, q in zip(x0, x1):
        a.plot([0, 1], [p, q], color="#c9c8c2", lw=1.4, zorder=1)
    a.scatter(np.zeros(10), x0, s=52, color=BL, edgecolor="#fcfcfb", lw=1.4, zorder=3)
    a.scatter(np.ones(10), x1, s=52, color=OR, edgecolor="#fcfcfb", lw=1.4, zorder=3)
    for i, x in ((0, x0), (1, x1)):
        a.plot([i - .13, i + .13], [np.median(x)] * 2, color=INK, lw=2.4, zorder=4)
    a.axhline(0, color="#8a8983", lw=1)
    a.set_xticks([0, 1], ["A0", "A1"])
    a.set_xlim(-.45, 1.45)
    a.set_title(f"{j}: różnica {pl(round(float(np.median(d)), 2))}° (mediana)", loc="left", fontsize=11.5)
    a.set_facecolor("#fcfcfb")
    a.grid(axis="y", color="#e8e7e2", lw=.8)
    a.set_axisbelow(True)
    a.yaxis.set_major_formatter(pl)
    for s_ in ("top", "right"):
        a.spines[s_].set_visible(False)
ax[0].set_ylabel("ruch stawu 20–22 s [°]")
fig.suptitle("Pierwszy dotyk A0 a A1: te same 10 ziaren, ta sama siła i czas (MuJoCo, Glu −1)", x=0.06, ha="left", fontsize=14, fontweight="bold", y=0.98)
fig.text(0.06, 0.9, "Linia = jedno ziarno, kreska = mediana. Bark: + w dół. Podstawa: + promotor. Łokieć: − prostowanie. Skale osi różnią się.", fontsize=9.5, color=INK)
fig.subplots_adjust(left=.06, right=.985, top=.82, bottom=.08)
fig.savefig(D + "/pary.png", dpi=120)
for k, v in res.items():
    print(k)
    [print("   ", a, b) for a, b in v.items()]
