"""flymind/v5v4_power.py — symulacja mocy dla protokołu V5 v4 PRZED zamrożeniem. Założenia jawne:
  rozkłady różnic sparowanych d = DATA − SWS z V5 v3 (ziarna 3051–3100, już opublikowane) w warstwach ρ [0,16; 0,22) i [0,22; 0,28),
  wycentrowane i przesunięte o założony efekt δ; resampling z powtórzeniami (kształt rozkładu, w tym zera, zachowany);
  H2: rozkłady z eksploracji `v5v3_gain_check.py` (ziarna dev 1501–1520, n = 20). Ziarno symulacji 7001 (poza pulami eksperymentów).
Reguła decyzji jak w protokole V5 v4: TOST per warstwa przy α = 0,025 (Bonferroni na 2 warstwy) ⇔ CI95 ⊂ (−SESOI; +SESOI);
  przewaga per warstwa: test permutacyjny (tu przybliżony testem t), Holm na 2 warstwach. Uruchom: .venv/bin/python -I -B flymind/v5v4_power.py"""
import json
import os

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "results", "v5v3", "v5v3_20261029T210706.json")))
E = {(r["cond"], r["seed"]): r for r in d["runs"]}
S = sorted({r["seed"] for r in d["runs"]})
strata = {}
for lo, hi in ((0.16, 0.22), (0.22, 0.28)):
    ss = [s for s in S if lo <= E[("DATA", s)]["rho"] < hi]
    x = np.array([E[("DATA", s)]["final_abs_err"] - E[("SHUF_WITHIN_SIDE", s)]["final_abs_err"] for s in ss])
    strata[f"{lo}-{hi}"] = x - x.mean()
rng = np.random.default_rng(7001)
SESOI, REPS = 0.5, 4000


def decide(x):
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(len(x))
    lo, hi = m + np.array([-1, 1]) * stats.t.ppf(0.975, len(x) - 1) * se
    p = 2 * stats.t.sf(abs(m / se), len(x) - 1) if se > 0 else 1.0
    return (-SESOI < lo and hi < SESOI), p, hi < 0


print("H1 per warstwa: P(równoważność ±0,5° przy α 0,025) / P(przewaga DATA przy α Holm ≈ 0,025)")
for n in (60, 100, 120, 150):
    row = []
    for name, base in strata.items():
        for delta in (0.0, -0.5, -1.0):
            eq = sup = 0
            for _ in range(REPS):
                x = rng.choice(base, n) + delta
                e, p, neg = decide(x)
                eq += e
                sup += (p < 0.025) and neg
            row.append(f"{name} δ={delta:+.1f}: eq {eq / REPS:.2f} sup {sup / REPS:.2f}")
    print(f"n/warstwę={n}: " + " | ".join(row))
g = json.load(open(os.path.join(HERE, "results", "v5v3", "post_gain_check_dev1501_1520.json")))
for a, b in (("DATA", "STR_own"), ("STR_shared", "STR_own")):
    base = np.array([r[a] - r[b] for r in g])
    for n in (100, 200, 240):
        for shrink in (1.0, 0.5):
            sup = np.mean([stats.ttest_1samp(rng.choice(base - base.mean(), n) + shrink * base.mean(), 0).pvalue < 0.025 for _ in range(2000)])
            print(f"H2 {a}−{b}: n={n}, efekt = {shrink:.1f}× dev ({shrink * base.mean():+.2f}°): moc {sup:.2f}")
