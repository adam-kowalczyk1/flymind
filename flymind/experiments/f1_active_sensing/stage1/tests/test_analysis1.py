"""Stage 1 analysis self-checks on synthetic data (no simulation)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analysis1 as A  # noqa: E402

fails = []


def check(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name, info)
    if not ok:
        fails.append(name)


r = np.random.default_rng(9118050)
big = r.normal(0.2, 0.3, 300)
check("classify: clear effect ≥ SESOI → SUPPORTED", A.classify(big.mean(), A.stat_boot(lambda i: big[i].mean(), 300, 9118051))["cls"] == "SUPPORTED")
zero = r.normal(0.0, 0.1, 300)
check("classify: tight null → EQUIVALENT", A.classify(zero.mean(), A.stat_boot(lambda i: zero[i].mean(), 300, 9118052))["cls"] == "EQUIVALENT")
check("classify: unmeasurable arms block EQUIVALENT",
      A.classify(zero.mean(), A.stat_boot(lambda i: zero[i].mean(), 300, 9118052), measurable=False)["cls"] == "UNMEASURABLE")
adj = A.holm(np.array([0.001, 0.2, 0.3, 0.04, 0.5, 1.0, 0.01]))
check("Holm over 7: smallest ×7, monotone", abs(adj[0] - 0.007) < 1e-12 and adj[6] == 0.06 and adj[3] == 0.2)
z = np.zeros(200, bool)
s = A.s6(z, z)
check("S6: zero events → NOT-HARMFUL with exact upper bound < 0.05", s["cls"] == "NOT-HARMFUL" and 0 < s["ci95"][1] < 0.05, s["ci95"])
b = z.copy()
b[:40] = True
check("S6: 20 % sin-only false turns → HARMFUL", A.s6(b, z)["cls"] == "HARMFUL")
g = np.repeat(np.arange(10), 20)
idx = A.boot_idx(np.random.default_rng(9118053), 200, g)
check("hierarchical boot: whole instances resampled", len(idx) == 200 and len(np.unique(g[idx])) <= 10)
if fails:
    sys.exit(f"{len(fails)} FAILED: {fails}")
print("all passed")
