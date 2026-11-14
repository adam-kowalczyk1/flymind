"""Diagnostyka (bez symulatora, szum 0): częstości pul wymach / podpór T1 L w sieci T1 L + T2 L przy stałym dotyku padów.
Sieć z danych i tasowania S1–S2 (ziarna treningowe), Glu ±1, dotyk 0,25 / 0,5 / 1 N na oba pady (= 10 / 20 / 40 mV).
  .venv/bin/python -I -B pool_diag.py OUT.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lift_b as lb  # noqa: E402
import visual_path  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402


def rates(W, idx, n, f_N, ms=1000):
    X = np.zeros(n)
    for ix in idx["pad_in"]:
        X[ix] = min(40.0, 40.0 * f_N)
    s = SparseALIF(lb._W(W), ALIFParams(), None).run(X, ms)[ms // 2:]
    t1 = sorted(i for v in idx["t1_sensory"].values() for i in v)
    return dict(swing=round(float(s[:, idx["swing"]].mean() * 1000), 1), stance=round(float(s[:, idx["stance"]].mean() * 1000), 1),
                all=round(float(s.mean() * 1000), 2), t1_sensory=round(float(s[:, t1].mean() * 1000), 2))


def main(out, net="it1"):
    res = {}
    for glu in (-1.0, 1.0):
        spec, idx, rep = lb.union(glu, 0.2, net)
        nets = {"N": spec.W, "S1": visual_path.shuffle(spec, 20110001, equal_weight=True).W,
                "S2": visual_path.shuffle(spec, 20110002, equal_weight=True).W}
        res[f"glu{glu:+.0f}"] = {k: {str(f): rates(W, idx, W.shape[0], f) for f in (0.25, 0.5, 1.0)} for k, W in nets.items()}
        res[f"glu{glu:+.0f}"]["rep"] = rep
    with open(out, "x") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], *sys.argv[2:3])
