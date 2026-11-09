"""Wykres wariantów Etapu 1 z plików S*_*.json. Uruchom: .venv/bin/python -I flymind/results/pick_place/plot_variants.py"""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

H = os.path.dirname(os.path.abspath(__file__))
L = {"S0_baseline": "S0 bazowy\nv 1,0", "S1_v1.45": "S1\nv 1,45", "S2_v1.45_jaw0.65": "S2\nv 1,45\nszczęka 0,65",
     "S3_v1.45_jaw0.65_homemid": "S3\nv 1,45\nszczęka 0,65\ndom-środek",
     "S4_v1.0_jaw0.65_homemid": "S4\nv 1,0\nszczęka 0,65\ndom-środek"}
D = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(H, "S[0-4]_*.json")))]
D = [d for d in D if d["tag"] in L]
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), dpi=130)
for i, d in enumerate(D):
    ok = [c for r in d["runs"] for c in r["cycles"] if c["ok"]]
    for a, v in ((ax[0], [c["cycle_sim"] for c in ok]), (ax[1], [c["place_err_mm"] for c in ok])):
        a.scatter(i + np.random.default_rng(0).uniform(-0.18, 0.18, len(v)), v, s=8, color="#2a6fdb", alpha=0.35, lw=0)
        a.plot([i - 0.28, i + 0.28], [np.median(v)] * 2, color="#111", lw=2)
    ax[0].text(i, max(c["cycle_sim"] for c in ok) + 0.15, f"{d['summary']['ok']}/{d['summary']['attempts']}",
               ha="center", fontsize=8, color="#333")
for a, y in ((ax[0], "czas cyklu [s czasu symulacji]"), (ax[1], "błąd odłożenia [mm]")):
    a.set_xticks(range(len(D)))
    a.set_xticklabels([L[d["tag"]] for d in D], fontsize=7)
    a.set_ylabel(y)
    a.grid(axis="y", color="#ddd", lw=0.6)
    a.set_axisbelow(True)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
ax[1].axhline(10, color="#999", ls="--", lw=1)
ax[1].text(len(D) - 0.5, 9.6, "granica strefy 10 mm", ha="right", fontsize=7, color="#666")
ax[0].set_ylim(0, 10.2)
ax[1].set_ylim(0, 10.5)
ax[0].set_title("Czas cyklu (kreska = mediana; liczby = sukcesy/próby)", fontsize=9)
ax[1].set_title("Błąd położenia kostki po odłożeniu", fontsize=9)
fig.suptitle("Etap 1 — warianty na tych samych ziarnach 1–5 × 50 cykli (MuJoCo 3.17.0)", fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(H, "variants.png"))
