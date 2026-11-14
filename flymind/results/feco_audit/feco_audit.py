"""Audyt kanału propriocepcji FeCO (P3). SYMULACJA, percept-wyrocznia jak w etapie dotyku (żeby porównanie z B 90/135
i C 83/135 było sparowane: te same przedmioty i położenia, ziarna 100 000–100 442). Uruchom z katalogu tymczasowego:
    .venv/bin/python -I -B flymind/results/feco_audit/feco_audit.py <wariant> <sufiks>

Warianty (wszystkie: sieć nogi T2 L, dotyk włączony, wyzwalanie „search”, Glu −1):
  scale_0.25, scale_0.5   prąd FeCO 10 i 20 mV zamiast 40 mV (skalowanie kontrolowane)
  claw_only               tylko kanał położenia (claw), bez kanału ruchu (hook)
  hook_only               tylko kanał ruchu (hook), bez kanału położenia
  swap                    przypisanie flex/ext odwrócone w obu kanałach (sprawdzenie, czy wynik zależy od niepewnego przypisania)

PRZEWIDYWANIA zapisane przed uruchomieniem (2026-11-10), z analizy znakowanego wpływu w danych (feco_offline.txt):
  FeCO w obecnym przypisaniu działa jak odruch oporowy (ujemne sprzężenie położenia wokół q_mid = 0,8 rad i tłumienie ruchu).
  1. scale: wynik rośnie monotonicznie ku B, gdy prąd maleje (0,25 ≥ 0,5 ≥ pełne C = 83).
  2. claw_only ≈ C (to kanał położenia osłabia ścisk na małych przedmiotach); hook_only ≈ B (samo tłumienie nie szkodzi).
  3. swap: sprzężenie dodatnie — mocniejszy ścisk małych przedmiotów; wynik ≥ C, ale to wariant biologicznie nieuzasadniony.
Żaden wariant nie jest wybierany „bo lepszy”: to test, skąd bierze się strata 90 → 83.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402

var, suf = sys.argv[1], sys.argv[2]
out = os.path.join(HERE, f"{var}_{suf}.json")
if os.path.exists(out):
    sys.exit(f"istnieje {out}")
mv = 40.0 * float(var.split("_")[1]) if var.startswith("scale_") else 40.0
fc = sm.FlyCfg(trigger="search", feco_mV=mv)
drv = sm.LegJaw(fc, touch=True, proprio=True)
f = drv.feco
if var == "claw_only":
    f["hook_ext"], f["hook_flex"] = [], []
elif var == "hook_only":
    f["claw_ext"], f["claw_flex"] = [], []
elif var == "swap":
    f["claw_ext"], f["claw_flex"], f["hook_ext"], f["hook_flex"] = f["claw_flex"], f["claw_ext"], f["hook_flex"], f["hook_ext"]
elif not var.startswith("scale_"):
    sys.exit("nieznany wariant")
items, T = oh.SETS["base"], []
for it in items:
    for k in range(3):
        r = sm.run_trial(it, 100 * 1000 + items.index(it) * 10 + k, drv, "snn:legT2L+FeCO", fc)
        o = r["objects"][0]
        a = o["attempt_log"]
        T.append(dict(shape=it[0], material=it[1], x=o["spawn"]["x"], y=o["spawn"]["y"], success=bool(o["success"]), truth=o["truth"],
                      reasons=[x["reason"] for x in a if not x["ok"]], tau_carry=[x.get("tau_carry") for x in a],
                      q_jaw_grasp=[x.get("q_jaw_grasp") for x in a], pen_mm=o.get("pen_mm")))
k = sum(t["success"] for t in T)
tc = [x for t in T for x in t["tau_carry"] if x is not None]
json.dump(dict(variant=var, feco_mV=mv, feco_sizes={a: len(b) for a, b in f.items()}, fly_cfg=sm.asdict(fc), code=oh.code_state(),
               success=k, n=len(T), tau_carry_median=float(np.median(tc)) if tc else None, trials=T), open(out, "x"), indent=1, default=float)
print(f"{var}: w pudełku {k}/{len(T)}, mediana momentu w transporcie {np.median(tc) if tc else float('nan'):.2f} N·m")
