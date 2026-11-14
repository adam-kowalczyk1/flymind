"""Opóźnienie samej sieci (czas MODELU, krok 1 ms, bez pętli robota): ile ms po pojawieniu się dotyku / obrazu zmienia się
aktywność wyjściowa. To górna granica tego, co dałaby pętla 1 kHz; obecna pętla czyta czujniki co 10 ms.
    .venv/bin/python -I -B flymind/results/vision_manipulation/net_latency.py > net_latency_v1.txt"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import sensory_manipulation as sm  # noqa: E402
import vision_manipulation as vm  # noqa: E402

fc = sm.FlyCfg(trigger="search")
d = vm.VisJaw(fc, noise=0.0)
c = d.c
print("sieć wspólna N =", d.N, "| krok 1 ms | filtr częstości wyjścia τ =", c.rate_tau, "s | k =", c.k, "N·m/Hz")
print("\nDotyk (oba pady) → MN zamykające (Ti extensor) → moment szczęki:")
print("| Siła [N] | pierwszy impuls MN zamykającego [ms] | moment > 0,05 N·m [ms] | moment > 0,10 N·m (próg zaciskania) [ms] |\n|---|---|---|---|")
for F in (0.1, 0.25, 0.5, 1.0, 2.0):
    d.reset()
    X = np.zeros(d.N)
    for ix in d.pad_in:
        X[ix] = min(c.max_mV, c.gain_mV_per_N * F)
    r, first, t05, t10 = 0.0, None, None, None
    for t in range(1, 301):
        s = d.net.run(X, 1)
        r += (0.001 / c.rate_tau) * ((s[:, d.press].mean() - s[:, d.release].mean()) * 1000 - r)
        first = first or (t if s[:, d.press].any() else None)
        t05 = t05 or (t if c.k * r > 0.05 else None)
        t10 = t10 or (t if c.k * r > 0.10 else None)
    print(f"| {F} | {first} | {t05} | {t10} |")
print("\nObraz (plamka po lewej, g = (0,9; 0,3)) → DNa02 L:")
for g in ((0.9, 0.3), (0.6, 0.5)):
    d.reset()
    X = np.zeros(d.N)
    X[d.vis["in_L"]], X[d.vis["in_R"]] = vm.ENC.i_max * g[0], vm.ENC.i_max * g[1]
    first = next((t for t in range(1, 301) if d.net.run(X, 1)[:, d.vis["DNa02_L"]].any()), None)
    print(f"  g = {g}: pierwszy impuls DNa02 L po {first} ms")
