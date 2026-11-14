"""flymind/v5v4_power_r2.py — symulacja mocy V5 v4 r2 (po Red Team r1, M2): n S1 = 150, S2 = 300; tabela wrażliwości na SD.
Rozkład bazowy: d = DATA − SWS z V5 v3 w warstwie (kształt, w tym zera), wycentrowany, przeskalowany do zadanego SD, + δ.
Równoważność: CI95 t ⊂ ±0,5° (bootstrap pominięty w symulacji dla szybkości — w protokole wymagane OBA CI, więc moc może być
nieco niższa). Przewaga: test t, α Holm ≈ 0,025 (najgorszy przypadek dla 2 warstw). Ziarno 7002. Uruchom: .venv/bin/python -I -B flymind/v5v4_power_r2.py"""
import json, os
import numpy as np
from scipy import stats
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "results", "v5v3", "v5v3_20261029T210706.json")))
E = {(r["cond"], r["seed"]): r for r in d["runs"]}
S = sorted({r["seed"] for r in d["runs"]})
rng = np.random.default_rng(7002)
for name, (lo, hi), n, sds in (("S1", (0.16, 0.22), 150, (0.64, 1.0, 1.6, 2.0)), ("S2", (0.22, 0.28), 300, (1.86, 2.3, 2.64, 3.0))):
    x = np.array([E[("DATA", s)]["final_abs_err"] - E[("SWS" if False else "SHUF_WITHIN_SIDE", s)]["final_abs_err"]
                  for s in S if lo <= E[("DATA", s)]["rho"] < hi])
    z = (x - x.mean()) / x.std(ddof=1)
    for sd in sds:
        row = []
        for delta in (0.0, -0.2, -0.5, -1.0):
            eq = sup = 0
            for _ in range(3000):
                y = rng.choice(z, n) * sd + delta
                m, se = y.mean(), y.std(ddof=1) / np.sqrt(n)
                h = stats.t.ppf(0.975, n - 1) * se
                eq += (-0.5 < m - h) and (m + h < 0.5)
                sup += (2 * stats.t.sf(abs(m / se), n - 1) < 0.025) and m < 0
            row.append(f"δ={delta:+.1f}: eq {eq / 3000:.2f} sup {sup / 3000:.2f}")
        print(f"{name} n={n} SD={sd:.2f}: " + " | ".join(row))
