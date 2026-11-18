"""Tabele do raportu etapu „wzrok w pętli” (tylko czyta JSON-y). Uruchom:
    .venv/bin/python -I -B flymind/results/vision_manipulation/tables.py [sufiks=v2]"""
import glob
import json
import os
import sys

import numpy as np
from scipy.stats import binomtest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..")
SUF = (sys.argv + ["v2"])[1]
sys.path.insert(0, os.path.join(HERE, "..", ".."))


def wilson(k, n, z=1.96):
    p, d = k / n, 1 + z * z / n
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{100 * ((p + z * z / (2 * n)) / d - h):.0f}–{100 * ((p + z * z / (2 * n)) / d + h):.0f} %"


def trials(j):
    return {(o["shape"], o["material"], round(o["spawn"]["x"], 6), round(o["spawn"]["y"], 6)): bool(o["success"])
            for r in j["runs"] for o in r["objects"]}


ARMS = ("A_cam", "B_cam", "D_vis", "E_vis_touch", "E_blind_grasp", "F_vis_touch_feco")
J = {a: json.load(open(p)) for a in ARMS if os.path.exists(p := os.path.join(HERE, f"{a}_{SUF}.json"))}
OLD = {"A wyrocznia (etap dotyku)": os.path.join(RES, "object_handling", "B_base_v2.json"),
       "B wyrocznia (etap dotyku)": os.path.join(RES, "sensory_manipulation", "B_fly_search_glu-1_v1.json"),
       "C wyrocznia (etap dotyku)": os.path.join(RES, "sensory_manipulation", "C_fly_feco_search_v1.json")}
T = {a: trials(j) for a, j in J.items()}
T.update({n: trials(json.load(open(p))) for n, p in OLD.items()})

print("| Ramię | Szczęka | Obrót bazy przy patrzeniu | Chwyt | Podniesienie | Transport | Odłożenie | **W pudełku** | 95 % CI | "
      "Mediana operacji [s sym.] | Przyczyny porażek |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for a, j in J.items():
    s = j["summary"]
    print(f"| {a} | {j['jaw_source']} | {j['pan_source']} | {s['grasp']['k']} | {s['lift']['k']} | {s['transport']['k']} | {s['placed']['k']} | "
          f"**{s['success']['k']}/{s['success']['n']}** | {wilson(s['success']['k'], s['success']['n'])} | {s['op_sim_s']['median']} | "
          f"{', '.join(f'{k} {v}' for k, v in sorted(s['controller_fails'].items()))} |")
for n in OLD:
    k = sum(T[n].values())
    print(f"| {n} | — | położenie z symulatora | | | | | **{k}/{len(T[n])}** | {wilson(k, len(T[n]))} | | |")

print("\nPercepcja z kamery względem prawdy symulatora (błąd bezwzględny; liczony po fakcie):\n")
print("| Ramię | Percepty | Ustalone | Czas ustawiania mediana / p95 [s] | Położenie med / p95 / max [mm] | Szerokość med / p95 / max [mm] | "
      "Wysokość med / p95 / max [mm] | Orientacja med / p95 [°] | Brak perceptu (próby) |")
print("|---|---|---|---|---|---|---|---|---|")
for a, j in J.items():
    v = j["summary"]["vision"]
    f = lambda d, ks=("median", "p95", "max"): " / ".join(f"{d[k]:.1f}" for k in ks) if d else "—"  # noqa: E731
    nop = sum(1 for r in j["runs"] if not r["vision"])
    print(f"| {a} | {v['percepts']} | {v['converged']} | {f(v['t_orient_s'], ('median', 'p95'))} | {f(v['pos_mm'])} | {f(v['w_mm'])} | {f(v['h_mm'])} | "
          f"{f(v['yaw_deg'], ('median', 'p95'))} | {nop} |")

print("\nSukces według kształtów (w pudełku / próby):\n")
SH = ("cube_S", "cube_M", "cube_L", "cyl", "sphere", "flat", "long", "L", "wedge")
MT = ("hard_grip", "hard_slick", "heavy", "light", "mid")
for key, cols in (("by_shape", SH), ("by_material", MT)):
    print("| Ramię | " + " | ".join(cols) + " |\n|---|" + "---|" * len(cols))
    for a, j in J.items():
        g = j["summary"][key]
        print(f"| {a} | " + " | ".join(f"{g[c]['success']}/{g[c]['n']}" for c in cols) + " |")
    print()

print("Porównania sparowane (te same przedmioty i położenia; test dokładny McNemara, dwustronny):\n")
print("| Porównanie | tylko pierwsze | tylko drugie | oba | żadne | p |\n|---|---|---|---|---|---|")
for a, b in (("E_vis_touch", "A_cam"), ("E_vis_touch", "B_cam"), ("E_vis_touch", "E_blind_grasp"), ("E_vis_touch", "D_vis"),
             ("F_vis_touch_feco", "E_vis_touch"), ("A_cam", "A wyrocznia (etap dotyku)"), ("B_cam", "B wyrocznia (etap dotyku)"),
             ("E_vis_touch", "B wyrocznia (etap dotyku)"), ("F_vis_touch_feco", "C wyrocznia (etap dotyku)")):
    if a not in T or b not in T:
        continue
    assert set(T[a]) == set(T[b]), f"{a} i {b}: inne przedmioty lub położenia"
    x = sum(T[a][k] and not T[b][k] for k in T[a])
    y = sum(T[b][k] and not T[a][k] for k in T[a])
    both = sum(T[a][k] and T[b][k] for k in T[a])
    print(f"| {a} vs {b} | {x} | {y} | {both} | {len(T[a]) - x - y - both} | {binomtest(x, x + y, 0.5).pvalue if x + y else 1.0:.3f} |")
print("\nUwaga: 3 położenia tego samego przedmiotu nie są niezależne — p i przedziały są orientacyjne.")

print("\nRuch, bezpieczeństwo, fizyka, czas reakcji:\n")
print("| Ramię | max prędkość [rad/s] | interwencje warstwy bezp. | kontakty niepożądane | wnikanie padu > 2 mm (próby) | "
      "dotyk → komenda zaciskania mediana / p95 [ms sym.] | moment w transporcie mediana [N·m] |\n|---|---|---|---|---|---|---|")
for a, j in J.items():
    s = j["summary"]
    r = s.get("contact_to_close_command_sim_ms")
    tc = [x.get("tau_carry") for q in j["runs"] for o in q["objects"] for x in o["attempt_log"] if x.get("tau_carry") is not None]
    print(f"| {a} | {s['max_qd']:.3f} | {s['safety_flags'] or 0} | {sum(s['unwanted_contacts'].values())} | {s.get('pad_penetration_gt2mm')} | "
          f"{f'{r['median']:.0f} / {r['p95']:.0f}' if r else '—'} | {f'{np.median(tc):.2f}' if tc else '—'} |")

lat = os.path.join(HERE, f"latency_{SUF}.json")
if os.path.exists(lat):
    s = json.load(open(lat))["summary"]
    print(f"\nCzas obliczeń na takt (zegar komputera; osobny przebieg `latency_{SUF}`, {s['process']['ticks']} taktów, ramię F):\n")
    print("| Etap | mediana [ms] | p95 | p99 | max |\n|---|---|---|---|---|")
    for k, v in s["compute_ms_per_tick"].items():
        print(f"| {k} | {v['median']} | {v['p95']} | {v['p99']} | {v['max']} |")
    print(f"\nproces: {s['process']}")

tr = sorted(glob.glob(os.path.join(HERE, f"tracking_*_{SUF}.json")))
if tr:
    print("\nŚledzenie (20 scen na scenariusz; sukces = |az| < 5° przez ostatnie 0,5 s):\n")
    print("| Warunek | Scenariusz | Sukces | 95 % CI | Końcowy \\|az\\| mediana [°] | Ustalenie po zdarzeniu mediana [s] | Przesunięcie przedmiotu mediana [mm] | Uwagi |")
    print("|---|---|---|---|---|---|---|---|")
    for p in tr:
        j = json.load(open(p))
        for sc in dict.fromkeys(r["scen"] for r in j["runs"]):
            s = [r for r in j["runs"] if r["scen"] == sc]
            k = sum(r["success"] for r in s)
            ts = [r["t_settle"] for r in s if r["t_settle"] is not None]
            note = ""
            if sc == "none":
                note = f"dryf obrotu bez bodźca: mediana {np.median([abs(r['pan_drift']) for r in s]):.3f}, max {max(abs(r['pan_drift']) for r in s):.3f} rad"
            if sc in ("occlude", "occl_push"):
                note = f"dryf w czasie zasłonięcia: mediana {np.median([r['pan_drift_blank'] for r in s]):.3f} rad"
            if sc == "rotate":
                ye = [abs(y) for r in s for y in r.get("yaw_err_deg", []) if y is not None]
                dy = [abs(r["yaw_truth_deg"][1] - r["yaw_truth_deg"][0]) for r in s if len(r.get("yaw_truth_deg", [])) == 2]
                note = f"obrót przedmiotu mediana {np.median(dy):.0f}°; błąd orientacji z kamery mediana {np.median(ye) if ye else float('nan'):.1f}° (n={len(ye)})"
            if sc == "loss":
                tl = [r["t_loss_detect"] for r in s if r.get("t_loss_detect") is not None]
                note = (f"utrata wykryta w {len(tl)}/{len(s)}, mediana {np.median(tl) if tl else float('nan'):.2f} s; "
                        f"|ω| po utracie mediana {np.median([r['omega_abs_after_loss'] for r in s]):.3f} rad/s")
            print(f"| {j['cond']} | {sc} | {k}/{len(s)} | {wilson(k, len(s))} | {np.median([r['final_abs_err'] for r in s]):.2f} | "
                  f"{np.median(ts) if ts else float('nan'):.2f} | {np.median([r['moved_mm'] for r in s]):.0f} | {note} |")

fa = sorted(glob.glob(os.path.join(RES, "feco_audit", "*_v1.json")))
if fa:
    B, C = T["B wyrocznia (etap dotyku)"], T["C wyrocznia (etap dotyku)"]
    print("\nAudyt FeCO (percept-wyrocznia, te same 135 prób co B = 90 i C = 83):\n")
    print("| Wariant | W pudełku | Mediana momentu w transporcie [N·m] | vs B: tylko wariant / tylko B | vs C: tylko wariant / tylko C | cube_S | cube_M | sphere |")
    print("|---|---|---|---|---|---|---|---|")
    for p in fa:
        j = json.load(open(p))
        t = {(x["shape"], x["material"], round(x["x"], 6), round(x["y"], 6)): x["success"] for x in j["trials"]}
        sh = lambda n: f"{sum(x['success'] for x in j['trials'] if x['shape'] == n)}/{sum(1 for x in j['trials'] if x['shape'] == n)}"  # noqa: E731
        print(f"| {j['variant']} ({j['feco_mV']:.0f} mV) | {j['success']}/{j['n']} | {j['tau_carry_median']:.2f} | "
              f"{sum(t[k] and not B[k] for k in t)} / {sum(B[k] and not t[k] for k in t)} | {sum(t[k] and not C[k] for k in t)} / {sum(C[k] and not t[k] for k in t)} | "
              f"{sh('cube_S')} | {sh('cube_M')} | {sh('sphere')} |")
ca = sorted(glob.glob(os.path.join(RES, "contact_audit", "stiff_*_v1.json")))
if ca:
    print("\nAudyt kontaktu (kontakt sztywniejszy: stała czasowa 0,002 s; te same 135 prób):\n")
    print("| Ramię | W pudełku (sztywny) | W pudełku (dotychczas) | tylko sztywny / tylko dotychczasowy | wnikanie > 2 mm (próby) | wnikanie mediana / max [mm] | light | mid |")
    print("|---|---|---|---|---|---|---|---|")
    for p in ca:
        j = json.load(open(p))
        ref = T["A wyrocznia (etap dotyku)" if j["arm"] == "A" else "B wyrocznia (etap dotyku)"]
        t = {(x["shape"], x["material"], round(x["x"], 6), round(x["y"], 6)): x["success"] for x in j["trials"]}
        mt = lambda n: f"{sum(x['success'] for x in j['trials'] if x['material'] == n)}/27"  # noqa: E731
        print(f"| {j['arm']} | {j['success']}/{j['n']} | {sum(ref.values())}/{len(ref)} | {sum(t[k] and not ref[k] for k in t)} / {sum(ref[k] and not t[k] for k in t)} | "
              f"{j['pen_gt2mm']} | {j['pen_median_mm']:.2f} / {j['pen_max_mm']:.2f} | {mt('light')} | {mt('mid')} |")
