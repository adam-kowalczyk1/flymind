"""Kontrola G: obwód nogi przetasowany (stopnie i wagi zachowane) z WYRÓWNANĄ siłą wyjścia. SYMULACJA, percept-wyrocznia,
te same 135 prób co B (90/135). Uruchom z katalogu tymczasowego:
    .venv/bin/python -I -B flymind/results/shuffle_matched/shuffle_matched.py <ziarno tasowania> <sufiks>

Po co: w etapie dotyku przetasowane sieci wypadły gorzej (74/49/82), ale ściskały słabiej, więc różnicy nie dało się przypisać
topologii. Tu wzmocnienie dekodera k każdej przetasowanej sieci jest skalowane tak, żeby jej ustalony moment na bodziec
odniesienia (0,5 N na obu padach, 1,2 s) był równy momentowi sieci z danych. Kalibracja jest wykonywana BEZ robota i przed próbami.
Jeżeli przetasowana sieć na bodziec odniesienia nie daje dodatniego momentu, wyrównanie jest niemożliwe (zapisane, próby i tak
biegną z k bez zmian). Ziarna tasowania: 17 100 011 – 17 100 020 (nowa pula; 17 100 001–003 zużyte w etapie dotyku).
PRZEWIDYWANIE zapisane przed uruchomieniem: jeśli liczy się tylko „głośność” drogi dotyk → MN, przetasowane sieci po wyrównaniu
dadzą wynik w pobliżu 90 (różnica w granicach rozrzutu między instancjami); jeśli liczy się topologia — wyraźnie poniżej.
"""
import json
import os
import sys
from dataclasses import replace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402

seed, suf = int(sys.argv[1]), sys.argv[2]
out = os.path.join(HERE, f"shuffle_{seed}_{suf}.json")
if os.path.exists(out) or not 17_100_011 <= seed <= 17_100_020:
    sys.exit(f"istnieje {out} albo ziarno spoza puli 17 100 011–020")
fc = sm.FlyCfg(trigger="search")


def ref(drv):
    drv.reset()
    t = [drv.step(np.array([0.5, 0.5, 0.0]), 0.5, 0.0) for _ in range(120)]
    return float(np.mean(t[60:]))


t_data = ref(sm.LegJaw(fc))
drv = sm.LegJaw(fc, shuffle_seed=seed)
t_shuf = ref(drv)
scale = t_data / t_shuf if t_shuf > 1e-3 else None
if scale:
    drv.c = replace(drv.c, k=drv.c.k * scale)
print(f"bodziec odniesienia: sieć z danych {t_data:.3f} N·m, przetasowana {t_shuf:.3f} N·m → skala k {scale}; po skalowaniu {ref(drv):.3f}", flush=True)
items, T = oh.SETS["base"], []
for it in items:
    for k in range(3):
        r = sm.run_trial(it, 100 * 1000 + items.index(it) * 10 + k, drv, "snn:legT2L_shuffled_matched", fc)
        o = r["objects"][0]
        T.append(dict(shape=it[0], material=it[1], x=o["spawn"]["x"], y=o["spawn"]["y"], success=bool(o["success"]), truth=o["truth"],
                      reasons=[x["reason"] for x in o["attempt_log"] if not x["ok"]], pen_mm=o.get("pen_mm"),
                      tau_carry=[x.get("tau_carry") for x in o["attempt_log"]]))
k = sum(t["success"] for t in T)
tc = [x for t in T for x in t["tau_carry"] if x is not None]
json.dump(dict(shuffle_seed=seed, tau_ref_data=t_data, tau_ref_shuffled=t_shuf, k_scale=scale, code=oh.code_state(), success=k, n=len(T),
               tau_carry_median=float(np.median(tc)) if tc else None, trials=T), open(out, "x"), indent=1, default=float)
print(f"tasowanie {seed}: w pudełku {k}/{len(T)}, moment w transporcie mediana {np.median(tc) if tc else float('nan'):.2f} N·m")
