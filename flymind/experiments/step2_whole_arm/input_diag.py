"""Diagnostyka (bez symulatora, szum 0, sieć z danych T1 L + T2 L): które receptory T1 L (wg podklasy) i przy jakim prądze
pobudzają pule wymachu / podporu T1 L. Służy WYŁĄCZNIE do wyboru hipotezy wejścia (r2 §8: nowe wejścia przez receptory).
  .venv/bin/python -I -B input_diag.py OUT.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lift_b as lb  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402


def main(out, net="it1"):
    res = {}
    for glu in (-1.0, 1.0):
        spec, idx, rep = lb.union(glu, 0.2, net)
        n, row = spec.W.shape[0], {}
        for sub, ix in idx["t1_sensory"].items():
            for mv in (20.0, 40.0):
                for half in ("all", "first_half"):
                    X = np.zeros(n)
                    X[ix if half == "all" else ix[: len(ix) // 2]] = mv
                    s = SparseALIF(lb._W(spec.W), ALIFParams(), None).run(X, 1000)[500:]
                    row[f"{sub}|{int(mv)}|{half}"] = dict(n=len(ix), swing=round(float(s[:, idx["swing"]].mean() * 1000), 1),
                                                          stance=round(float(s[:, idx["stance"]].mean() * 1000), 1))
        res[f"glu{glu:+.0f}"] = row
    with open(out, "x") as f:
        json.dump(res, f, indent=1)
    for g, r in res.items():
        for k, v in r.items():
            print(g, k, v)


if __name__ == "__main__":
    main(sys.argv[1], *sys.argv[2:3])
