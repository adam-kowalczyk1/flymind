"""Etap 4 — ablacja neuronów: jak liczba neuronów obwodu wpływa na skuteczność chwytu, czas reakcji
i koszt obliczeń.

A) Ablacja warstwowa: pełny obwód 348 neuronów (332 z MaleCNS + 16 modelowych) → 300 → 150 → 60 →
   30 → 20. Z każdej z 20 populacji usuwamy losowo tyle samo procent neuronów, ale zostaje ≥ 1 w każdej
   (przy 20 neuronach: dokładnie 1 na populację — minimum strukturalne). 3 losowania × 10 prób.
   Dwa warianty: bez kompensacji oraz z kompensacją homeostatyczną (ocalałe neurony przejmują synapsy
   usuniętych — patrz FlyController(compensate=True)). Różnica rozdziela efekt LICZBY neuronów od
   efektu utraty łącznego pobudzenia.
B) Nokauty pojedynczych populacji (pełny obwód minus jedna grupa), 10 prób każdy.
C) Koszt CPU: czas jednego cyklu 10 ms (10 kroków SNN po 1 ms) mierzony osobno, sekwencyjnie.

Próby: ziarna 0–9 (te same co test Etapu 3), nic tu nie jest strojone.
Wyniki: ../results/ablation.json, ../ablation_results.png
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from circuit import POPULATIONS, FlyController, full_circuit, make_groups
from stage3 import run_trial

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES = [348, 300, 150, 60, 30, 20]
DRAWS = 3
TRIALS = range(10)

NEURONS, _ = full_circuit()
GROUPS = make_groups(NEURONS)
N_FULL = len(NEURONS)


def stratified_keep(n_keep, draw):
    """Maska: z każdej populacji ten sam odsetek (≥ 1 neuron), losowo które."""
    assert n_keep >= len(POPULATIONS), "minimum strukturalne: 1 neuron na populację"
    sizes = np.array([len(GROUPS[p]) for p in POPULATIONS])
    want = sizes * n_keep / N_FULL
    alloc = np.maximum(1, np.floor(want)).astype(int)
    while alloc.sum() < n_keep:                       # największe reszty
        alloc[np.argmax(np.where(alloc < sizes, want - alloc, -np.inf))] += 1
    while alloc.sum() > n_keep:                       # nadmiar z minimum 1 → zabierz z największych
        alloc[np.argmax(np.where(alloc > 1, alloc, -1))] -= 1
    rng = np.random.default_rng(1000 + draw)
    keep = np.zeros(N_FULL, bool)
    for p, a in zip(POPULATIONS, alloc):
        keep[rng.choice(GROUPS[p], a, replace=False)] = True
    return keep


def knockouts():
    fc = FlyController(params=dict(calibrate=False))
    cls = fc.mn_class
    ko = {"AOTU019 (GABA, L+P)": list(GROUPS["AOTU019_L"]) + list(GROUPS["AOTU019_R"]),
          "AOTU025 (ACh, L+P)": list(GROUPS["AOTU025_L"]) + list(GROUPS["AOTU025_R"]),
          "IN_GABA nogi (10)": list(GROUPS["IN_GABA"]),
          "RR_assist (6)": list(GROUPS["RR_assist"]),
          "RR_resist (6)": list(GROUPS["RR_resist"]),
          "RR_hold (4)": list(GROUPS["RR_hold"]),
          "wolne MN (4)": [i for i, c in cls.items() if c == "slow"],
          "szybki MN zginacza (1)": [i for i, c in cls.items() if c == "fast" and i in GROUPS["MN_flex"]]}
    out = {}
    for name, ids in ko.items():
        keep = np.ones(N_FULL, bool)
        keep[ids] = False
        out[name] = keep
    return out


def trial_task(args):
    label, keep, draw, seed = args
    r = run_trial(seed, FlyController(seed=seed + 100 * draw, keep=keep, compensate=label.startswith("C")))
    return label, draw, {k: v for k, v in r.items() if k not in ("log", "F")}


def cpu_ms(keep, cycles=300):
    fc = FlyController(keep=keep, params=dict(calibrate=False))   # kompensacja nie zmienia kosztu
    fc.control_step(0.0, (0, 0, 0))
    t0 = time.perf_counter()
    for k in range(cycles):
        fc.control_step(0.1 * np.sin(k / 20), (0.5, 0.5, 0.2), True, jaw_vel=-0.1)
    return 1000 * (time.perf_counter() - t0) / cycles


def summarize(rs):
    ok = [r for r in rs if r["success"]]
    rt = [r["reaction_ms"] for r in ok]
    az = [abs(r["az_err_deg"]) for r in rs if r["az_err_deg"] is not None]
    return dict(n=len(rs), success_pct=100 * len(ok) / len(rs),
                crushed=sum(r["crushed"] for r in rs), missed=sum(r["miss"] for r in rs),
                dropped=sum((not r["miss"]) and (not r["crushed"]) and (not r["success"]) for r in rs),
                reaction_ms=float(np.mean(rt)) if rt else None, reaction_sd=float(np.std(rt)) if rt else None,
                aim_err_deg=float(np.mean(az)) if az else None,
                peak_force=float(np.mean([r["peak_force"] for r in rs if not r["miss"]] or [0])))


def main():
    tasks = []
    keeps = {}
    for n in SIZES:
        for d in range(DRAWS):
            keeps[(n, d)] = stratified_keep(n, d) if n < N_FULL else np.ones(N_FULL, bool)
            tasks += [(f"N={n}", keeps[(n, d)], d, s) for s in TRIALS]
            if n < N_FULL:
                tasks += [(f"C N={n}", keeps[(n, d)], d, s) for s in TRIALS]
    kos = knockouts()
    tasks += [(f"KO {name}", keep, 0, s) for name, keep in kos.items() for s in TRIALS]
    t0 = time.time()
    with Pool(8) as pool:
        res = pool.map(trial_task, tasks)
    print(f"{len(tasks)} prób w {time.time() - t0:.0f} s")

    by = {}
    for label, draw, r in res:
        by.setdefault(label, {}).setdefault(draw, []).append(r)
    table = {}
    for n in SIZES:
        per_draw = [summarize(by[f"N={n}"][d]) for d in range(DRAWS)]
        allr = sum((by[f"N={n}"][d] for d in range(DRAWS)), [])
        s = summarize(allr)
        s["success_sd_draws"] = float(np.std([p["success_pct"] for p in per_draw]))
        s["success_per_draw"] = [p["success_pct"] for p in per_draw]
        s["cpu_ms"] = float(np.mean([cpu_ms(keeps[(n, d)]) for d in range(DRAWS)]))
        if n < N_FULL:
            allc = sum((by[f"C N={n}"][d] for d in range(DRAWS)), [])
            c = summarize(allc)
            c["success_sd_draws"] = float(np.std([summarize(by[f"C N={n}"][d])["success_pct"] for d in range(DRAWS)]))
        else:
            c = dict(s)
        s["comp"] = c
        table[n] = s
        print(f"N={n:3d}: sukces {s['success_pct']:5.1f}% (losowania {s['success_per_draw']}), "
              f"zgniecione {s['crushed']}, chybione {s['missed']}, upuszczone {s['dropped']}, "
              f"reakcja {s['reaction_ms'] if s['reaction_ms'] is None else round(s['reaction_ms'])} ms, "
              f"błąd celowania {s['aim_err_deg']:.1f}°, CPU {s['cpu_ms']:.3f} ms/cykl")
        print(f"  z kompensacją: sukces {c['success_pct']:5.1f}%, zgniecione {c['crushed']}, chybione {c['missed']}, "
              f"upuszczone {c['dropped']}, reakcja {c['reaction_ms'] if c['reaction_ms'] is None else round(c['reaction_ms'])} ms, "
              f"błąd celowania {c['aim_err_deg']:.1f}°")
    ko_table = {}
    for name in kos:
        s = summarize(by[f"KO {name}"][0])
        ko_table[name] = s
        print(f"KO {name:24s}: sukces {s['success_pct']:5.1f}%, zgniecione {s['crushed']}, chybione {s['missed']}, "
              f"upuszczone {s['dropped']}, błąd celowania {s['aim_err_deg']:.1f}°, szczyt {s['peak_force']:.2f} N")
    json.dump(dict(sizes=table, knockouts=ko_table), open(os.path.join(ROOT, "results", "ablation.json"), "w"),
              indent=1)
    plot(table, ko_table)


INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"


X = np.arange(len(SIZES))   # równe odstępy w kolejności redukcji 348 → 20 (jak na słupkach)


def _logx(a, n):
    a.set_xticks(X, [str(k) for k in n])
    a.set_xlim(-0.4, len(SIZES) - 0.6)
    a.set_xlabel("liczba neuronów w obwodzie (redukcja →)")
    a.grid(axis="y", color=GRID)


def _outcomes(a, rows, title):
    x = np.arange(len(SIZES))
    bottom = np.zeros(len(SIZES))
    for key, lab, col in [("success", "sukces", BLUE), ("crushed", "zgniecione", ORANGE),
                          ("dropped", "upuszczone / brak chwytu", YELLOW), ("missed", "chybione", AQUA)]:
        v = np.array([r["success_pct"] * r["n"] / 100 if key == "success" else r[key] for r in rows], float)
        a.bar(x, v, bottom=bottom, color=col, label=lab, width=0.6, edgecolor=SURF, linewidth=2)
        bottom += v
    a.set_xticks(x, [str(k) for k in SIZES])
    a.set_xlabel("liczba neuronów w obwodzie")
    a.set_ylabel("liczba prób (z 30)")
    a.set_title(title, color=INK)


def plot(table, ko):
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.facecolor": SURF,
                         "figure.facecolor": SURF, "axes.spines.top": False, "axes.spines.right": False})
    n = np.array(SIZES)
    fig, ax = plt.subplots(2, 3, figsize=(18, 10))
    series = [("bez kompensacji", lambda k: table[k], BLUE, "o"),
              ("z kompensacją homeostatyczną", lambda k: table[k]["comp"], ORANGE, "s")]
    a = ax[0, 0]
    for lab, get, col, mk in series:
        y = [get(k)["success_pct"] for k in SIZES]
        a.errorbar(X, y, yerr=[get(k)["success_sd_draws"] for k in SIZES], color=col, lw=2, marker=mk, ms=8,
                   capsize=4, label=lab)
    _logx(a, n)
    a.set_ylim(0, 105)
    a.set_ylabel("skuteczność chwytu [%]")
    a.set_title("Skuteczność vs liczba neuronów\n(śr. ± odch. std. z 3 losowań × 10 prób)", color=INK)
    a.legend(frameon=False, fontsize=9, loc="upper right")

    a = ax[0, 1]
    for lab, get, col, mk in series:
        pts = [(X[i], get(k)["reaction_ms"], get(k)["reaction_sd"]) for i, k in enumerate(SIZES)
               if get(k)["reaction_ms"] is not None]
        if pts:
            a.errorbar([p[0] for p in pts], [p[1] for p in pts], yerr=[p[2] for p in pts], color=col, lw=2,
                       marker=mk, ms=8, capsize=4, label=lab)
    _logx(a, n)
    a.set_ylim(bottom=0)
    a.set_ylabel("kontakt → pewny chwyt [ms]")
    a.set_title("Czas reakcji (tylko udane próby;\nbrak punktu = 0 udanych)", color=INK)
    a.legend(frameon=False, fontsize=9, loc="lower left")

    a = ax[0, 2]
    for lab, get, col, mk in series:
        a.plot(X, [get(k)["aim_err_deg"] for k in SIZES], color=col, lw=2, marker=mk, ms=8, label=lab)
    a.axhline(5.3, color=INK2, ls="--", lw=1)
    a.text(X[0] - 0.3, 5.5, "tolerancja paszczy ±5,3°", color=INK2, fontsize=9, ha="left", va="bottom")
    _logx(a, n)
    a.set_ylim(bottom=0)
    a.set_ylabel("|błąd celowania| tuż przed paszczą [°]")
    a.set_title("Śledzenie (LC10a → AOTU → DNa02)", color=INK)
    a.legend(frameon=False, fontsize=9, loc="upper left")

    _outcomes(ax[1, 0], [table[k] for k in SIZES], "Wyniki prób — bez kompensacji")
    _outcomes(ax[1, 1], [table[k]["comp"] for k in SIZES], "Wyniki prób — z kompensacją")
    h, l = ax[1, 0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=10, loc="lower center", ncol=4, bbox_to_anchor=(0.36, 0.0))

    a = ax[1, 2]
    names = list(ko)
    vals = [ko[k]["success_pct"] for k in names]
    full = table[348]["success_pct"]
    y = np.arange(len(names))
    a.barh(y, vals, color=BLUE, height=0.6)
    a.axvline(full, color=INK2, ls="--", lw=1)
    a.text(full, len(names) - 0.35, f" pełny obwód {full:.0f}%", color=INK2, fontsize=9, va="top")
    for yy, v in zip(y, vals):
        a.text(v + 1, yy, f"{v:.0f}%", va="center", color=INK, fontsize=9)
    a.set_yticks(y, names)
    a.invert_yaxis()
    a.set_xlim(0, 105)
    a.set_xlabel("skuteczność chwytu [%] (10 prób)")
    a.set_title("Nokauty pojedynczych populacji (pełny obwód)", color=INK)
    fig.suptitle("Ablacja neuronów w biologicznym sterowniku SO-101 (MaleCNS v1.0)", color=INK, fontsize=14)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(os.path.join(ROOT, "ablation_results.png"), dpi=130)

    # CPU osobno (inna wielkość → osobny wykres, nie druga oś)
    fig, a = plt.subplots(figsize=(6.5, 4))
    cpu = [table[k]["cpu_ms"] for k in SIZES]
    a.plot(X, cpu, color=BLUE, lw=2, marker="o", ms=8)
    for xx, c in zip(X, cpu):
        a.annotate(f"{c:.2f}", (xx, c), textcoords="offset points", xytext=(0, 8), ha="center", color=INK, fontsize=9)
    _logx(a, n)
    a.set_ylim(bottom=0)
    a.set_ylabel("czas CPU na cykl 10 ms [ms]")
    a.set_title("Koszt obliczeń SNN (10 kroków po 1 ms, 1 rdzeń)", color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "results", "ablation_cpu.png"), dpi=140)

def protected_task(args):
    n, d, seed, comp = args
    keep = stratified_keep(n, d)
    for p in ("RR_assist", "RR_resist", "RR_hold"):   # moduł odruchu nietknięty
        keep[GROUPS[p]] = True
    r = run_trial(seed, FlyController(seed=seed + 100 * d, keep=keep, compensate=comp))
    return n, comp, int(keep.sum()), r


def protected():
    """D) Kontrola hipotezy „zatrzask potrzebuje ≥ 2 neuronów”: ablacja jak w A, ale moduł odruchu
    (16 neuronów) zostaje w całości."""
    tasks = [(n, d, s, c) for n in (150, 60, 30) for d in range(DRAWS) for s in TRIALS for c in (False, True)]
    with Pool(8) as pool:
        res = pool.map(protected_task, tasks)
    for n in (150, 60, 30):
        for c in (False, True):
            rs = [r for nn, cc, _, r in res if nn == n and cc == c]
            k = [kk for nn, cc, kk, _ in res if nn == n][0]
            az = np.mean([abs(r["az_err_deg"]) for r in rs if r["az_err_deg"] is not None])
            print(f"N={k} (moduł odruchu nietknięty) kompensacja={c}: sukces {100 * np.mean([r['success'] for r in rs]):.0f}%, "
                  f"zgniecione {sum(r['crushed'] for r in rs)}, chybione {sum(r['miss'] for r in rs)}, błąd celowania {az:.1f}°")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--protected":
        protected()
    elif len(sys.argv) > 1 and sys.argv[1] == "--plot":
        d = json.load(open(os.path.join(ROOT, "results", "ablation.json")))
        plot({int(k): v for k, v in d["sizes"].items()}, d["knockouts"])
    else:
        main()
