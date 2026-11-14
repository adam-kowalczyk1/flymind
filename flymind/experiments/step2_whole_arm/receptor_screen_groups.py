"""Uzupełnienie receptor_screen.py: bodźce GRUPOWE (cała klasa receptorów T1 L / wszystkie receptory T1 L / T1 L + pady T2 L)
przy 10, 20, 40 mV; te same pule i sieć. Wynik → receptor_screen_groups_v1.json. Bez robota, szum 0."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lift_b as L  # noqa: E402
import receptor_screen as RS  # noqa: E402
import visual_path  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from leg_circuit import select  # noqa: E402


def main():
    a = pd.read_feather(visual_path.ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide"])
    ty = a.set_index("bodyId").type
    t2, g2, _ = select("T2", "L")
    t1, g1, _ = select("T1", "L")
    fl = a[(a.superclass == "vnc_motor") & (a.subclass == "fl") & (a.somaSide == "L")]
    bodies = list(dict.fromkeys([int(b) for b in list(t2) + list(t1) + sorted(fl.bodyId.astype(int))]))
    pos = {b: i for i, b in enumerate(bodies)}
    pidx = {k: [pos[int(b)] for b in fl.bodyId if ty[b] in v] for k, v in RS.POOLS.items()}
    stim = {f"T1L|{c}": [pos[b] for b in v] for c, v in g1["sensory"].items()}
    stim["T1L|ALL sensory"] = [pos[b] for v in g1["sensory"].values() for b in v]
    pads = [i for p in L.union(-1.0, 0.2)[1]["pad_in"] for i in p]
    stim["T1L ALL + T2L pads"] = stim["T1L|ALL sensory"] + pads
    stim["T2L|ALL sensory"] = [pos[b] for v in g2["sensory"].values() for b in v]
    out = dict(pools={k: len(v) for k, v in pidx.items()}, stim_n={k: len(v) for k, v in stim.items()}, rates={})
    for glu in (-1.0, 1.0):
        spec, _, rep = L.union(glu, 0.2)
        for mv in (10.0, 20.0, 40.0):
            for k, ids in stim.items():
                net = SparseALIF(L._W(spec.W), ALIFParams(), None)
                X = np.zeros(len(bodies))
                X[ids] = mv
                S = np.concatenate([net.run(X, 10) for _ in range(50)])
                r = {p: round(float(S[:, ix].mean() * 1000), 1) for p, ix in pidx.items()}
                out["rates"][f"{glu}|{mv}|{k}"] = r
                print(f"Glu{glu:+.0f} {mv:4.0f} mV {k:28s}", " ".join(f"{p.split()[0]}{v:6.1f}" for p, v in r.items()))
    p = os.path.join(os.path.dirname(os.path.dirname(HERE)), "results", "step2_whole_arm_20261113", "receptor_screen_groups_v1.json")
    with open(p, "x") as f:
        json.dump(out, f, indent=1)
    print("zapisano", p)


if __name__ == "__main__":
    main()
