"""Krok 6, eksploracja bez robota (szum 0): szlak BM (szczecinki głowy) → DNg15 → pule łokcia / obrotu nadgarstka,
oraz BM → DNge078 → dźwigacz stępu (znany z kroku 5). Sieć: „pre” + BM + DNge078 + DNg15.
Bodziec: BM 10/20/40 mV, 1 s, osobno dla każdej drogi i razem. Uruchom: explore_dng15.py OUT.json"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402
import nets2  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402

JN = nets.JN


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    a = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type", "superclass", "somaSide"])
    bm = [int(b) for b in a.bodyId[(a.type == "BM") & (a.superclass == "cb_sensory")]]
    dn078 = [int(b) for b in a.bodyId[a.type == "DNge078"]]
    dn15 = [int(b) for b in a.bodyId[a.type == "DNg15"]]
    res = {}
    for glu in (1.0, -1.0):
        rows = {}
        for route, extra in (("cała sieć (BM+DNge078+DNg15)", bm + dn078 + dn15), ("bez DNg15 (tylko BM→DNge078)", bm + dn078),
                             ("bez DNge078 (tylko BM→DNg15)", bm + dn15)):
            spec, idx, rep, layer, pos, m = nets2.build_ext(glu, extra)
            B = [pos[b] for b in bm]
            for mv in (10.0, 20.0, 40.0):
                net = SparseALIF(JN.LB._W(spec.W), ALIFParams(), None)
                X = np.zeros(spec.W.shape[0])
                X[B] = mv
                S = np.concatenate([net.run(X, 10) for _ in range(100)])[500:]
                r = {nets.NAMES[j][q]: round(float(S[:, ix].mean() * 1000), 1) for j, pq in idx["pools"].items() for q, ix in enumerate(pq)}
                row = dict(bm_Hz=round(float(S[:, B].mean() * 1000), 1), N=spec.W.shape[0], pools=r)
                rows[f"{mv:.0f}mV | {route}"] = row
                print(f"Glu {glu:+.0f} {mv:3.0f} mV | {route:30s} N={spec.W.shape[0]} | łokieć ext {r['j2- Ti ext']:5.1f} flex {r['j2+ Ti flex']:4.1f} | "
                      f"obrót ext {r['j4- Tr ext']:4.1f} flex {r['j4+ Tr flex']:4.1f} | dźwigacz {r['j3+ Ta lev']:5.1f} | bark {r['j1+ wymach']:.1f}/{r['j1- podpór']:.1f}", flush=True)
        res[f"glu{glu:+.0f}"] = rows
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
