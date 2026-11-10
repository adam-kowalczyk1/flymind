"""Tabele do raportu etapu z plików wynikowych (tylko czyta JSON-y). Uruchom:
    .venv/bin/python -I -B flymind/results/sensory_manipulation/tables.py [sufiks_ramion=v1] [sufiks_bazy=v2]"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUF, BASE = (sys.argv + ["v1", "v2"])[1:3]
runs = [("A klasyczny (baza)", os.path.join(HERE, "..", "object_handling", f"B_base_{BASE}.json"))]
runs += [(os.path.basename(p)[:-len(f"_{SUF}.json")], p) for p in sorted(glob.glob(os.path.join(HERE, f"*_{SUF}.json")))
         if not os.path.basename(p).startswith("latency")]
J = [(n, json.load(open(p))) for n, p in runs]
SH = ("cube_S", "cube_M", "cube_L", "cyl", "sphere", "flat", "long", "L", "wedge")
MT = ("hard_grip", "hard_slick", "heavy", "light", "mid")

print("| Ramię | Źródło komendy szczęki | Chwyt | Podniesienie | Transport | Odłożenie | **W pudełku** | Upuszczone | "
      "Mediana operacji [s sym.] | Udane/h czasu sym. | Przyczyny porażek prób |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for n, j in J:
    s = j["summary"]
    print(f"| {n} | {j.get('jaw_source', 'classical:object_handling')} | {s['grasp']['k']} | {s['lift']['k']} | {s['transport']['k']} | "
          f"{s['placed']['k']} | **{s['success']['k']}/{s['success']['n']}** ({s['success']['pct']} %) | {s['dropped']} | "
          f"{s['op_sim_s']['median']} | {round(s['success']['k'] / s['T_sim_s'] * 3600)} | "
          f"{', '.join(f'{k} {v}' for k, v in sorted(s['controller_fails'].items()))} |")
for key, cols, title in (("by_shape", SH, "kształtów"), ("by_material", MT, "materiałów")):
    print(f"\nSukces według {title} (w pudełku / próby):\n")
    print("| Ramię | " + " | ".join(cols) + " |")
    print("|---|" + "---|" * len(cols))
    for n, j in J:
        g = j["summary"][key]
        print(f"| {n} | " + " | ".join(f"{g[c]['success']}/{g[c]['n']}" for c in cols) + " |")
print("\nRuch, bezpieczeństwo, fizyka:\n")
print("| Ramię | max prędkość [rad/s] | max przysp. [rad/s²] | takty > 1,5 rad/s | interwencje warstwy bezp. | kontakty niepożądane | "
      "resety | serie przerwane | wnikanie padu > 2 mm (próby) | fałszywe przekonanie kontrolera |")
print("|---|---|---|---|---|---|---|---|---|---|")
for n, j in J:
    s = j["summary"]
    print(f"| {n} | {s['max_qd']:.3f} | {s['max_qdd']:.1f} | {s['v_exceed_ticks']} | {s['safety_flags'] or 0} | "
          f"{sum(s['unwanted_contacts'].values())} | {s['resets'] + s['auto_resets']} | {s['interrupted_series']} | "
          f"{s.get('pad_penetration_gt2mm')} | {s['false_belief']} |")
lat = os.path.join(HERE, f"latency_{SUF}.json")
if os.path.exists(lat):
    s = json.load(open(lat))["summary"]
    print(f"\nCzas obliczeń na takt (zegar komputera, przebieg pojedynczy `latency_{SUF}`, {s['process']['ticks']} taktów):\n")
    print("| Etap | mediana [ms] | p95 | p99 | max |\n|---|---|---|---|---|")
    for k, v in s["compute_ms_per_tick"].items():
        print(f"| {k} | {v['median']} | {v['p95']} | {v['p99']} | {v['max']} |")
    print(f"\nproces: {s['process']}; dotyk → komenda zaciskania sterownika (czas symulacji): {s['contact_to_close_command_sim_ms']}")

# Porównania sparowane: te same przedmioty i te same położenia startowe w każdym ramieniu (sprawdzane poniżej).
from scipy.stats import binomtest  # noqa: E402


def trials(j):
    return [(o["shape"], o["material"], round(o["spawn"]["x"], 6), round(o["spawn"]["y"], 6), bool(o["success"]))
            for r in j["runs"] for o in r["objects"]]


T = {n: trials(j) for n, j in J}
print("\nPorównania sparowane (próba po próbie; test dokładny McNemara na parach niezgodnych, dwustronny):\n")
print("| Porównanie | tylko pierwsze udane | tylko drugie udane | oba | żadne | p |\n|---|---|---|---|---|---|")
names = [n for n, _ in J]
pairs = [(a, b) for a, b in (("B_fly_search_glu-1", "A klasyczny (baza)"), ("B_fly_search_glu-1", "D_reflex_search"),
                             ("B_fly_search_glu-1", "S_shuffle1_search"), ("B_fly_search_glu-1", "S_shuffle2_search"),
                             ("B_fly_search_glu-1", "S_shuffle3_search"), ("C_fly_feco_search", "B_fly_search_glu-1"),
                             ("B_fly_search_glu+1", "B_fly_search_glu-1"), ("B_fly_push", "D_reflex_push"),
                             ("B_fly_search_glu-1", "B_fly_push")) if a in names and b in names]
for a, b in pairs:
    assert [t[:4] for t in T[a]] == [t[:4] for t in T[b]], f"{a} i {b}: inne przedmioty lub położenia"
    x = sum(p[4] and not q[4] for p, q in zip(T[a], T[b]))
    y = sum(q[4] and not p[4] for p, q in zip(T[a], T[b]))
    both = sum(p[4] and q[4] for p, q in zip(T[a], T[b]))
    p = binomtest(x, x + y, 0.5).pvalue if x + y else 1.0
    print(f"| {a} vs {b} | {x} | {y} | {both} | {len(T[a]) - x - y - both} | {p:.3f} |")
print("\nUwaga: 3 położenia tego samego przedmiotu nie są niezależne, a sieć i fizyka są deterministyczne — p jest orientacyjne.")
