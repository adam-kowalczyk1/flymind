"""Krok 3, etap 0c (eksploracja, bez robota, szum 0): sieć „pre” — który typ receptora nogi T1 L / T2 L (każdy osobno, 40 mV,
0,5 s) pobudza które pule? Pytanie: czy nadgarstek (pule stępu) da się poruszyć naturalnym wejściem.
Uruchom: explore_receptors.py OUT.json"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402

JN = nets.JN


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for glu in (-1.0, 1.0):
        bodies, m = nets.bodies_for("pre")
        spec, idx, rep, layer = nets.build_rule(glu, 0.2, "pre")
        pos = {b: i for i, b in enumerate(bodies)}
        ty = m["a"].set_index("bodyId").type
        stim = {}
        for leg, g in (("T1L", m["g1"]), ("T2L", m["g2"])):
            for cls, v in g["sensory"].items():
                for t in sorted({str(ty[b]) for b in v}):
                    stim[f"{leg}|{cls}|{t}"] = [pos[b] for b in v if str(ty[b]) == t]
        rows = {}
        for k, ids in stim.items():
            net = SparseALIF(JN.LB._W(spec.W), ALIFParams(), None)
            X = np.zeros(len(bodies))
            X[ids] = 40.0
            S = np.concatenate([net.run(X, 10) for _ in range(50)])
            r = {nets.NAMES[j][q]: round(float(S[:, ix].mean() * 1000), 1) for j, pq in idx["pools"].items() for q, ix in enumerate(pq)}
            rows[k] = dict(n=len(ids), rates=r)
            if r["j3+ Ta lev"] > 1 or r["j3- Ta dep"] > 1 or r["j1+ wymach"] > 5:
                print(glu, k.ljust(44), len(ids), " ".join(f"{v:6.1f}" for v in r.values()), flush=True)
        res[f"glu{glu:+.0f}"] = rows
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    print("pule:", " | ".join(n for j in nets.NAMES for n in nets.NAMES[j]))
    main(sys.argv[1])
