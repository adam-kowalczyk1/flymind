"""Grafiki plakatu FlyMind (16 XI 2026). Każda liczba czytana wprost z pliku wyników — nic nie jest wpisane ręcznie.
Uruchom:  .venv/bin/python -I -B flymind/results/poster_20261114/make_figures.py
Wyjście: PNG 300 dpi w tym katalogu (odmowa nadpisania) + figures_sources.json (liczby i pliki źródłowe)."""
import glob
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
DPI = 300
BLUE, ORANGE, GREY, DARK, GREEN = "#0072B2", "#E69F00", "#8C8C8C", "#222222", "#009E73"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 26, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.linewidth": 2, "xtick.major.width": 2, "ytick.major.width": 2})
SRC = {}


def J(rel):
    return json.load(open(os.path.join(RES, rel)))


def save(fig, name):
    p = os.path.join(HERE, name)
    if os.path.exists(p):
        sys.exit(f"istnieje {p}")
    fig.savefig(p, dpi=DPI, facecolor="white")
    plt.close(fig)
    print(name, "zapisany")


def bars(ax, labels, vals, n, colors):
    b = ax.bar(range(len(vals)), vals, color=colors, width=0.68, zorder=3)
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + n * 0.02, f"{v}", ha="center", va="bottom", fontsize=30, fontweight="bold")
    ax.set_xticks(range(len(vals)), labels)
    ax.set_ylim(0, n * 1.13)
    ax.set_yticks([0, n // 2, n] if n == 40 else [0, 45, 90, 135])
    ax.grid(axis="y", color="#DDDDDD", lw=1.5, zorder=0)


# ---------------------------------------------------------------- G1: obrót bazy do piłeczki (V5)
a = J("v5/analysis_confirm.json")["conds"]
v = {k: a[f"{k}|delay0ms"]["success"] for k in ("snn", "snn_shuffle", "snn_swap", "no_vision", "classical_p")}
SRC["G1"] = dict(file="results/v5/analysis_confirm.json", n=40, values=v)
fig, ax = plt.subplots(figsize=(11.6, 7.4))
bars(ax, ["sieć\nz danych", "połączenia\nprzetasowane", "strony\nzamienione", "bez\nwzroku", "klasyczny\nregulator"],
     [v["snn"], v["snn_shuffle"], v["snn_swap"], v["no_vision"], v["classical_p"]], 40, [BLUE, ORANGE, ORANGE, GREY, DARK])
ax.set_ylabel("trafienia na 40 prób")
ax.set_title("Obrót ramienia w stronę piłeczki", fontsize=32, fontweight="bold", pad=18)
fig.tight_layout()
save(fig, "G1_obrot_do_pileczki.png")

# ---------------------------------------------------------------- G2: chwyt sterowany dotykiem
s = lambda rel: J(rel)["summary"]["success"]["k"]  # noqa: E731
net = s("sensory_manipulation/B_fly_search_glu-1_v1.json")
reflex = s("sensory_manipulation/D_reflex_search_v1.json")
classical = s("object_handling/B_base_v2.json")
sh3 = [s(f"sensory_manipulation/S_shuffle{i}_search_v1.json") for i in (1, 2, 3)]
sh10 = [J(os.path.relpath(p, RES))["success"] for p in sorted(glob.glob(os.path.join(RES, "shuffle_matched", "shuffle_171000*_v1.json")))]
SRC["G2"] = dict(n=135, classical=dict(file="results/object_handling/B_base_v2.json", k=classical),
                 net=dict(file="results/sensory_manipulation/B_fly_search_glu-1_v1.json", k=net),
                 reflex=dict(file="results/sensory_manipulation/D_reflex_search_v1.json", k=reflex),
                 shuffles_3=dict(files="results/sensory_manipulation/S_shuffle{1,2,3}_search_v1.json", k=sh3),
                 shuffles_10_matched=dict(files="results/shuffle_matched/shuffle_171000{11..20}_v1.json", k=sh10))
fig, ax = plt.subplots(figsize=(11.6, 7.4))
bars(ax, ["klasyczny\nsterownik", "sieć\nz danych", "prosty\nodruch", "sieci\nprzetasowane"], [classical, net, reflex, 0], 135,
     [DARK, BLUE, GREY, "white"])
ax.texts[-1].remove()
allsh = sorted(sh3 + sh10)
xs = [3 + (i % 5 - 2) * 0.09 for i in range(len(allsh))]
ax.scatter(xs, allsh, s=330, color=ORANGE, edgecolor="black", linewidth=1.5, zorder=4)
ax.text(3, 135 * 1.03, f"13 wersji:\nod {min(allsh)} do {max(allsh)}", ha="center", va="bottom", fontsize=24)
ax.set_ylim(0, 135 * 1.22)
ax.set_ylabel("przedmioty w pudełku na 135 prób")
ax.set_title("Chwyt sterowany „dotykiem”", fontsize=32, fontweight="bold", pad=18)
fig.tight_layout()
save(fig, "G2_chwyt_dotykiem.png")

# ---------------------------------------------------------------- G3: całe ramię (krok 2) — wynik negatywny
T = "step2_whole_arm_20261113/whole_arm_5/test/"
pl = lambda tag: sum(bool(r["truth"]["placed"]) for r in J(T + f"arm_test_{tag}.json")["runs"])  # noqa: E731
g3 = {g: dict(N=pl(f"N_{g}"), K=pl(f"K_{g}"), S=[pl(f"S{i}_{g}") for i in range(1, 6)]) for g in ("g-1", "g1")}
SRC["G3"] = dict(files="results/step2_whole_arm_20261113/whole_arm_5/test/arm_test_{N,K,S1..S5}_g{-1,1}.json", n=135,
                 outcome="truth.placed", values=g3)
fig, ax = plt.subplots(figsize=(11.6, 7.4))
x0 = {"g-1": 0, "g1": 4.2}
for g, lab in (("g-1", "wariant A znaku"), ("g1", "wariant B znaku")):
    x = x0[g]
    b = ax.bar([x, x + 1], [g3[g]["K"], g3[g]["N"]], color=[DARK, BLUE], width=0.68, zorder=3)
    for r, val in zip(b, [g3[g]["K"], g3[g]["N"]]):
        ax.text(r.get_x() + r.get_width() / 2, val + 3, f"{val}", ha="center", va="bottom", fontsize=30, fontweight="bold")
    ss = sorted(g3[g]["S"])
    ax.scatter([x + 2 + (i - 2) * 0.1 for i in range(5)], ss, s=330, color=ORANGE, edgecolor="black", linewidth=1.5, zorder=4)
    ax.text(x + 1, -8, lab, ha="center", va="top", fontsize=24, style="italic")
ax.set_xticks([])
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
ax.legend(handles=[Patch(color=DARK, label="klasyczny sterownik"), Patch(color=BLUE, label="sieć z danych"),
                   Line2D([], [], marker="o", ls="", ms=18, mfc=ORANGE, mec="black", label="5 sieci przetasowanych")],
          loc="upper left", ncol=3, fontsize=18, frameon=False, bbox_to_anchor=(0.0, 1.02), columnspacing=0.9, handletextpad=0.35, handlelength=1.2)
ax.set_ylim(0, 165)
ax.set_yticks([0, 45, 90, 135])
ax.grid(axis="y", color="#DDDDDD", lw=1.5, zorder=0)
ax.set_ylabel("odłożone na 135 prób")
ax.set_title("Całe ramię sterowane siecią nogi muchy", fontsize=32, fontweight="bold", pad=18)
fig.tight_layout()
fig.subplots_adjust(bottom=0.14)
save(fig, "G3_cale_ramie.png")

# ---------------------------------------------------------------- G4: schemat metody
fig, ax = plt.subplots(figsize=(15.0, 5.2))
ax.set_xlim(0, 15)
ax.set_ylim(0, 5.2)
ax.axis("off")
boxes = [(0.2, "ZMYSŁY\nkamera,\ndotyk chwytaka", "#DDEBF7"), (3.2, "RECEPTORY\nmuchy\n(wejście sieci)", "#DDEBF7"),
         (6.2, "SIEĆ\nZ KONEKTOMU\npołączenia\nz mapy MaleCNS", "#FCE4B6"),
         (9.2, "NEURONY\nRUCHOWE\n(wyjście sieci)", "#DDEBF7"), (12.2, "STAW\nROBOTA\nSO-101", "#D9EAD3")]
for x, t, c in boxes:
    ax.add_patch(FancyBboxPatch((x, 1.9), 2.5, 2.6, boxstyle="round,pad=0.06,rounding_size=0.18", fc=c, ec=DARK, lw=2.5))
    ax.text(x + 1.25, 3.2, t, ha="center", va="center", fontsize=17, fontweight="bold" if "SIEĆ" in t else "normal")
for x in (2.76, 5.76, 8.76, 11.76):
    ax.add_patch(FancyArrowPatch((x, 3.2), (x + 0.4, 3.2), arrowstyle="-|>", mutation_scale=34, lw=3, color=DARK))
ax.add_patch(FancyBboxPatch((0.2, 0.25), 14.5, 1.05, boxstyle="round,pad=0.06,rounding_size=0.18", fc="#F2F2F2", ec=GREY, lw=2, ls="--"))
ax.text(7.45, 0.78, "kod klasyczny (nie mucha): dojazd ramienia, kolejność faz, warstwa bezpieczeństwa", ha="center", va="center", fontsize=16)
fig.tight_layout()
save(fig, "G4_schemat_metody.png")

with open(os.path.join(HERE, "figures_sources.json"), "x") as f:
    json.dump(SRC, f, indent=1, ensure_ascii=False)
print(json.dumps(SRC, ensure_ascii=False)[:1500])
