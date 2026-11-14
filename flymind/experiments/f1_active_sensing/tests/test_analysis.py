"""F1 analysis tests (code red team M3): pure numpy + the smoke-pool outputs in results/smoke (units 9 108 030–033, current runner).
Run: .venv/bin/python -I -B flymind/experiments/f1_active_sensing/tests/test_analysis.py"""
import os
import sys

import numpy as np

if not sys.flags.dont_write_bytecode:
    sys.exit("run with python -B")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import analysis as AN  # noqa: E402
import analysis_core as AC  # noqa: E402

ok = []


def check(name, cond, info=""):
    print(("PASS " if cond else "FAIL ") + name, info, flush=True)
    ok.append(bool(cond))


rng = np.random.default_rng(9108090)
# classify: order and float safety
bs = np.full(1000, 0.07) + rng.normal(0, 0.005, 1000)
check("classify: est exactly 0.57 − 0.5 (float 0.0699…) with CI > 0 → SUPPORTED", AN.classify(0.57 - 0.5, bs)["cls"] == "SUPPORTED")
check("classify: tiny precise effect → EQUIVALENT (not DETECTABLE) when gates pass",
      AN.classify(0.01, 0.01 + rng.normal(0, 0.005, 1000))["cls"] == "EQUIVALENT")
check("classify: tiny precise effect, arm unmeasurable → DETECTABLE-BELOW-SESOI",
      AN.classify(0.01, 0.01 + rng.normal(0, 0.002, 1000), measurable=False)["cls"] == "DETECTABLE-BELOW-SESOI")
check("classify: −0.1 with CI < 0 → HARMFUL and negative", (lambda r: r["cls"] == "HARMFUL" and r["negative"])(AN.classify(-0.1, -0.1 + rng.normal(0, 0.01, 1000))))
check("classify: point mass at 0 → p = 1", AN.classify(0.0, np.zeros(100))["p"] == 1.0)
check("classify: wide CI → INCONCLUSIVE", AN.classify(0.02, 0.02 + rng.normal(0, 0.2, 1000))["cls"] == "INCONCLUSIVE")
# criterion / bsc with 'none' = wrong
L = np.array([3, 0, 1, -2.0]); R = np.array([-1, 0, 2, -5.0]); N0 = np.zeros(4)
check("bsc: ties and wrong-sign count as wrong", AN.bsc((L, R, N0), np.arange(4)) == 0.5 * (2 / 4 + 2 / 4))
Nc = np.r_[np.zeros(95), np.arange(1, 6)]
check("criterion: FA ≤ 0.05 with 5 % non-zero no-target trials", AC.criterion(Nc) == 0.0 and (np.abs(Nc) > 0).mean() <= 0.05)
Nc2 = np.r_[np.zeros(94), np.arange(1, 7)]
c2 = AC.criterion(Nc2)
check("criterion: 6 % non-zero → c > 0 and FA ≤ 0.05", c2 > 0 and (np.abs(Nc2) > c2).mean() <= 0.05, f"c {c2}")
# SK validity: step psychometric inside the range valid; non-monotone invalid; range C direction
x = np.linspace(0.22, 0.36, 700)
step = lambda thr, inc=False: ((x > thr) if inc else (x < thr)).astype(float)
D3 = lambda h: (np.where(h > 0, 1.0, 0.0), np.where(h > 0, -1.0, 0.0), np.zeros_like(h))
check("SK: interior step valid", AN.sk_valid(D3(step(0.29)), x, 0.22, 0.36)["valid"])
check("SK: threshold at the far edge invalid (edges)", not AN.sk_valid(D3(step(0.355)), x, 0.22, 0.36)["valid"])
nm = step(0.29).copy(); nm[(x > 0.32) & (x < 0.34)] = 1
check("SK: non-monotone invalid", not AN.sk_valid(D3(nm), x, 0.22, 0.36)["monotone"])
check("SK: range C increasing direction", AN.sk_valid(D3(step(0.29, True)), x, 0.22, 0.36, increasing=True)["valid"])
check("SK threshold: BSC 0.5 ↔ midpoint", abs(AN.sk_threshold(0.5, 0.22, 0.36) - 0.29) < 1e-12
      and abs(AN.sk_threshold(np.mean(step(0.29)), 0.22, 0.36) - 0.29) < 1e-3)
# hierarchical bootstrap index: instances resampled, units drawn only within drawn instances, same length
inst = np.arange(40) % 10
idx = AN.hier_idx(np.random.default_rng(1), inst, 40)
check("hier_idx: length n and instance-consistent", len(idx) == 40 and all(np.unique(inst[idx[k * 4:(k + 1) * 4]]).size == 1 for k in range(10)))
# Holm with the dummy S6
adj, rej = AC.holm([0.001, 0.2, 0.3, 0.04, 0.5, 1.0])
check("Holm over 6 incl. dummy p = 1", abs(adj[0] - 0.006) < 1e-12 and rej[0] and not rej[3])
# Data pairing on smoke outputs: every system aligned on the same sorted unit list
X = AN.Data("smoke", th=6.0, th_lp=6.0)
X.snn = X.snn[X.snn.unit.between(9108030, 9108033)]
X.units = X.units[(X.units.index >= 9108030) & (X.units.index <= 9108033)]
X.u = X.units.index.to_numpy()
dd = X.D("DATA", "stat")
pp = X.D("P", "stat", "C")
check("Data: units 9108030–033 aligned for DATA and P", list(X.u) == [9108030, 9108031, 9108032, 9108033] and len(dd[0]) == len(pp[0]) == 4)
s1 = X.snn[(X.snn.system == "DATA") & (X.snn.cond == "stat") & (X.snn.side == "L")].set_index("unit").D
check("Data: DL equals the stored per-unit D in unit order", np.array_equal(dd[0], s1.reindex(X.u).to_numpy(float)))
check("P on no-target is tiny (|D| < 1e-3) — c for P is ≈ 0, not exactly 0", np.abs(pp[2]).max() < 1e-3, f"max {np.abs(pp[2]).max():.1e}")
print(f"{sum(ok)}/{len(ok)} passed")
sys.exit(0 if all(ok) else 1)
