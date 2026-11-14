"""Testy syntetyczne analizy V5 v3 (bez symulacji). Uruchom: .venv/bin/python -I -B flymind/test_v5v3_analysis.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v5v3 import CONDS, analyze, boot_ci, decide, holm, perm_test  # noqa: E402

n = 0
rng = np.random.default_rng(1001)
assert perm_test(np.zeros(30)) == 1.0; n += 1                                            # same zera → p = 1
assert perm_test(-np.ones(20)) < 1e-4; n += 1                                            # wszystkie ujemne → p ≈ 2^-19
x = rng.normal(0, 1, 50)
assert abs(perm_test(x) - perm_test(-x)) < 1e-12 and perm_test(x) == perm_test(x); n += 1   # symetria, determinizm
assert perm_test(np.r_[np.zeros(40), -np.ones(10)]) < 0.01; n += 1                      # zera nie znoszą efektu
assert np.allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06]); n += 1               # Holm: wartości ręczne
assert np.allclose(holm([0.5, 0.001]), [0.5, 0.002]); n += 1
lo, hi = boot_ci(np.full(40, -2.0), 0.95)
assert lo == hi == -2.0; n += 1
assert decide(-1.5, [-2.2, -0.8], [-2.0, -1.0], 0.001) == "pierwszy lepszy, efekt ≥ SESOI"; n += 1
assert decide(-0.5, [-0.9, -0.1], [-0.8, -0.2], 0.01) == "pierwszy lepszy, efekt < SESOI"; n += 1
assert decide(0.8, [0.2, 1.4], [0.3, 1.3], 0.01) == "drugi lepszy"; n += 1
assert decide(0.1, [-0.6, 0.8], [-0.5, 0.7], 0.6) == "równoważne w granicach SESOI"; n += 1
assert decide(-0.8, [-2.5, 0.4], [-2.2, 0.1], 0.2) == "nierozstrzygnięte"; n += 1
# analyze: znak d = pierwszy − drugi; wykluczenie sparowane ziaren z błędem
runs = []
for s in range(1001, 1041):
    base = rng.uniform(1, 10)
    off = dict(DATA=0.0, SHUF_WITHIN_SIDE=2.0, SHUF_STR=3.0, TOY_RELAY=1.5, P_CTRL=-4.0)
    for c in CONDS:
        runs.append(dict(cond=c, seed=s, rho=0.16 + (s - 1001) * 0.0047, final_abs_err=max(0.0, base + off[c]), success=False,
                         error="SimError" if (s == 1005 and c == "SHUF_STR") else None))
a = analyze(runs)
assert a["excluded_seeds"] == [1005] and a["n_analyzed"] == 39; n += 1
assert a["tests"]["H1"]["mean_d"] < -1.5 and a["tests"]["H1"]["decision"] == "pierwszy lepszy, efekt ≥ SESOI"; n += 1
assert a["tests"]["D2"]["decision"] == "opis (bez decyzji)" and a["tests"]["H1"]["p_decision"] == a["tests"]["H1"]["p_perm"]; n += 1
assert a["tests"]["H2"]["p_decision"] >= a["tests"]["H2"]["p_perm"] and "sensitivity_excluded_as_worst" in a["tests"]["H1"]; n += 1
assert sum(v["n"] for v in a["tests"]["H1"]["strata"].values()) == 39 and a["conds"]["SHUF_STR"]["sim_errors"] == 1; n += 1
runs0 = [dict(r, final_abs_err=5.0, error=None) for r in runs]
assert analyze(runs0)["H1_verdict_text"] == "Hipoteza nie została potwierdzona."; n += 1
print(f"OK: analiza V5 v3 ({n} asercji)")
