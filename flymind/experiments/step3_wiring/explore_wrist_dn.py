"""Krok 5, eksploracja bez robota (szum 0): dwie naturalne drogi do puli Ta levator (nadgarstek) znalezione w danych:
  V  wzrok:  LPLC4 (neurony wzrokowe projekcyjne) → DNp07 → Ta levator MN
  H  dotyk głowy:  BM (szczecinki mechanosensoryczne głowy, cb_sensory) → DNge078 → Ta levator MN
Sieć = „pre” + neurony drogi. Bodziec: prąd stały na neurony czuciowe/wzrokowe (jak enkoder V5: do 12 mV; dotyk: 40 mV), 1 s.
Uruchom: explore_wrist_dn.py OUT.json"""
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
    pick = lambda t: [int(b) for b in a.bodyId[a.type == t]]  # noqa: E731
    side = a.set_index("bodyId").somaSide
    groups = dict(LPLC4=pick("LPLC4"), DNp07=pick("DNp07"), BM=[int(b) for b in a.bodyId[(a.type == "BM") & (a.superclass == "cb_sensory")]],
                  DNge078=pick("DNge078"))
    extra = [b for v in groups.values() for b in v]
    res = dict(sizes={k: len(v) for k, v in groups.items()},
               sides={k: pd.Series([str(side.get(b)) for b in v]).value_counts().to_dict() for k, v in groups.items()})
    print(res["sizes"], res["sides"], flush=True)
    for glu in (1.0, -1.0):
        spec, idx, rep, layer, pos, m = nets2.build_ext(glu, extra)
        gi = {k: np.array([pos[b] for b in v]) for k, v in groups.items()}
        rows = {}
        for name, src, dn, levels in (("V wzrok LPLC4", "LPLC4", "DNp07", (8.0, 10.0, 12.0, 20.0)), ("H dotyk głowy BM", "BM", "DNge078", (10.0, 20.0, 40.0))):
            for mv in levels:
                for sel in ("obie", "L"):
                    ids = gi[src] if sel == "obie" else np.array([pos[b] for b in groups[src] if str(side.get(b)) == "L"])
                    if len(ids) == 0:
                        continue
                    net = SparseALIF(JN.LB._W(spec.W), ALIFParams(), None)
                    X = np.zeros(spec.W.shape[0])
                    X[ids] = mv
                    S = np.concatenate([net.run(X, 10) for _ in range(100)])[500:]
                    r = {nets.NAMES[j][q]: round(float(S[:, ix].mean() * 1000), 1) for j, pq in idx["pools"].items() for q, ix in enumerate(pq)}
                    row = dict(src_Hz=round(float(S[:, ids].mean() * 1000), 1), dn_Hz=round(float(S[:, gi[dn]].mean() * 1000), 1), pools=r)
                    rows[f"{name} {mv:.0f} mV strona {sel}"] = row
                    print(f"Glu {glu:+.0f} {name:18s} {mv:4.0f} mV {sel:4s} | źródło {row['src_Hz']:6.1f} Hz → {dn} {row['dn_Hz']:6.1f} Hz → Ta lev {r['j3+ Ta lev']:6.1f}  Ta dep {r['j3- Ta dep']:5.1f} | bark {r['j1+ wymach']:.0f}/{r['j1- podpór']:.0f} łokieć {r['j2+ Ti flex']:.0f}/{r['j2- Ti ext']:.0f} obrót {r['j4+ Tr flex']:.0f}/{r['j4- Tr ext']:.0f}", flush=True)
        res[f"glu{glu:+.0f}"] = dict(rep=rep, rows=rows)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
