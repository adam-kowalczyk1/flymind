"""Krok 3, etap 0 (eksploracja, bez robota, szum 0 → bez ziaren): czy pule barku / stępu milczą dlatego, że sieć kroku 2
jest za małym wycinkiem danych? Dla każdej reguły wyboru neuronów: dotyk 1 N na oba pady (T2 L + T1 L), 1 s → częstości pul.
Uruchom: .venv/bin/python -I -B flymind/experiments/step3_wiring/explore_rules.py OUT.json"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402

JN = nets.JN
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402


def respond(W, idx, touch_N=1.0, ticks=100, tau_r=0.05, dt=0.01):
    net = SparseALIF(JN.LB._W(W), ALIFParams(), None)
    N = W.shape[0]
    r = np.zeros((5, 2))
    tot = 0
    for _ in range(ticks):
        X = np.zeros(N)
        for name in ("padsT2", "padsT1"):
            for ix in idx[name]:
                X[ix] = min(40.0, 40.0 * touch_N)
        s = net.run(X, 10)
        tot += int(s.sum())
        for j, (p, n) in idx["pools"].items():
            now = np.array([s[:, p].mean(), s[:, n].mean()]) * 1000.0
            r[j] += dt / tau_r * (now - r[j])
    return {nets.NAMES[j][k]: round(float(r[j, k]), 2) for j in nets.NAMES for k in (0, 1)}, tot


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for rule in ("base", "pre", "pre2", "full2"):
        for glu in (-1.0, 1.0):
            t0 = time.time()
            spec, idx, rep, layer = nets.build_rule(glu, 0.2, rule)
            if rule == "base":
                ref = JN.build_net(glu, 0.2, "fl")[2]["W_sha256"]
                assert ref == rep["W_sha256"], "reguła base ≠ sieć kroku 2"
            rates, tot = respond(spec.W, idx)
            res[f"{rule}|glu{glu:+.0f}"] = dict(rep=rep, rates_Hz=rates, total_spikes=tot, build_sim_s=round(time.time() - t0, 1))
            print(rule, glu, rep["N"], rep["layers"], rates, flush=True)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
