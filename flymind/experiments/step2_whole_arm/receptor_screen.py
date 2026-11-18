"""Krok 2: które receptory T1 L / T2 L docierają (połączeniami z danych) do pul stawów 1–4? Sieć jak lift_b.union (T2 L + T1 L
+ MN „fl” L), szum 0, dt 1 ms. Każdy typ receptora osobno 40 mV przez 0,5 s (bez robota); wynik: średnia częstość pul [Hz].
Cel: uzasadnić wybór wejść propriocepcji PRZED iteracjami (nie strojenie na zadaniu). Wynik → results/.../receptor_screen_v1.json
  .venv/bin/python -B receptor_screen.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lift_b as L  # noqa: E402
import visual_path  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from leg_circuit import select  # noqa: E402

POOLS = {"j1+ wymach": L.SWING, "j1- podpor": L.STANCE,
         "j2+ Ti flex": ("Ti flexor MN", "Acc. ti flexor MN"), "j2- Ti ext": ("Ti extensor MN",),
         "j3+ Ta lev": ("Ta levator MN",), "j3- Ta dep": ("Ta depressor MN",),
         "j4+ Tr flex": ("Tr flexor MN",), "j4- Tr ext": ("Tr extensor MN", "Sternotrochanter MN", "Tergotr. MN")}


def main():
    a = pd.read_feather(visual_path.ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide"])
    ty = a.set_index("bodyId").type
    t2, g2, _ = select("T2", "L")
    t1, g1, _ = select("T1", "L")
    fl = a[(a.superclass == "vnc_motor") & (a.subclass == "fl") & (a.somaSide == "L")]
    bodies = list(dict.fromkeys([int(b) for b in list(t2) + list(t1) + sorted(fl.bodyId.astype(int))]))
    pos = {b: i for i, b in enumerate(bodies)}
    pidx = {k: [pos[int(b)] for b in fl.bodyId if ty[b] in v] for k, v in POOLS.items()}
    stim = {}
    for leg, g in (("T1L", g1), ("T2L", g2)):
        for cls, v in g["sensory"].items():
            for t in sorted({str(ty[b]) for b in v}):
                ids = [pos[b] for b in v if str(ty[b]) == t]
                if t not in ("SNxxxx", "SNppxx", "nan"):
                    stim[f"{leg}|{cls}|{t}"] = ids
    stim["T2L|pads (lift_b touch)"] = [i for p in L.union(-1.0, 0.2)[1]["pad_in"] for i in p]
    out = dict(pools={k: len(v) for k, v in pidx.items()}, stim_n={k: len(v) for k, v in stim.items()}, rates={})
    for glu in (-1.0, 1.0):
        spec, _, rep = L.union(glu, 0.2)
        assert [len(x) for x in pidx.values()] and spec.W.shape[0] == len(bodies)
        res = {}
        for k, ids in stim.items():
            net = SparseALIF(L._W(spec.W), ALIFParams(), None)
            X = np.zeros(len(bodies))
            X[ids] = 40.0
            S = np.concatenate([net.run(X, 10) for _ in range(50)])
            r = {p: round(float(S[:, ix].mean() * 1000), 1) for p, ix in pidx.items()}
            if any(r.values()):
                res[k] = r
        out["rates"][str(glu)] = res
        print("Glu", glu, "W", rep["W_sha256"][:12], "aktywne bodźce:", len(res), "/", len(stim))
        for k, r in res.items():
            print(f"  {k:45s}", " ".join(f"{p.split()[0]}{v:6.1f}" for p, v in r.items()))
    p = os.path.join(os.path.dirname(os.path.dirname(HERE)), "results", "step2_whole_arm_20261113", "receptor_screen_v1.json")
    with open(p, "x") as f:
        json.dump(out, f, indent=1)
    print("zapisano", p)


if __name__ == "__main__":
    main()
