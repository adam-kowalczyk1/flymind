"""Audyt fizyki kontaktu (P4): czy wnikanie padów > 2 mm i wyniki zależą od miękkości kontaktu MuJoCo. SYMULACJA.
    .venv/bin/python -I -B flymind/results/contact_audit/contact_audit.py <A|B> <sufiks>      (z katalogu tymczasowego)

Wariant „stiff”: stała czasowa kontaktu wszystkich materiałów 0,002 s (najmniejsza dopuszczalna przy kroku 1 ms; dotąd 0,004,
drewno 0,010) → kontakt ok. 4× sztywniejszy (drewno 25×). NIC innego się nie zmienia: te same przedmioty, położenia (ziarna
100 000–100 442), kontrolery i kryteria. A = klasyczny kontroler, B = sieć nogi (sam dotyk, „search”, Glu −1), percept-wyrocznia.
To nowy, oznaczony wariant fizyki — nie zastępuje wyników v2/v1 i nie służy do ich poprawiania.
PRZEWIDYWANIE (zapisane przed uruchomieniem): wnikanie spada kilkukrotnie; jeśli wyniki sieci zależały od miękkiego kontaktu,
liczba sukcesów B zmieni się wyraźnie (> 10 prób), jeśli nie — zostanie w granicach kilku prób.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402

arm, suf = sys.argv[1], sys.argv[2]
out = os.path.join(HERE, f"stiff_{arm}_{suf}.json")
if os.path.exists(out):
    sys.exit(f"istnieje {out}")
for m in oh.MATERIALS.values():
    m["solref"] = (0.002, 1)
fc = sm.FlyCfg(trigger="search")
drv = sm.LegJaw(fc) if arm == "B" else None
items, T = oh.SETS["base"], []
for it in items:
    for k in range(3):
        seed = 100 * 1000 + items.index(it) * 10 + k
        r = sm.run_trial(it, seed, drv, "snn:legT2L", fc) if arm == "B" else oh.run([it], seed)
        o = r["objects"][0]
        T.append(dict(shape=it[0], material=it[1], x=o["spawn"]["x"], y=o["spawn"]["y"], success=bool(o["success"]), truth=o["truth"],
                      reasons=[x["reason"] for x in o["attempt_log"] if not x["ok"]], pen_mm=o.get("pen_mm"),
                      tau_carry=[x.get("tau_carry") for x in o["attempt_log"]]))
k = sum(t["success"] for t in T)
pen = np.array([t["pen_mm"] or 0.0 for t in T])
json.dump(dict(arm=arm, solref=(0.002, 1), code=oh.code_state(), success=k, n=len(T), pen_gt2mm=int((pen > 2).sum()),
               pen_median_mm=float(np.median(pen)), pen_max_mm=float(pen.max()), trials=T), open(out, "x"), indent=1, default=float)
print(f"stiff {arm}: w pudełku {k}/{len(T)}; wnikanie > 2 mm w {int((pen > 2).sum())} próbach, mediana {np.median(pen):.2f} mm, maks. {pen.max():.2f} mm")
