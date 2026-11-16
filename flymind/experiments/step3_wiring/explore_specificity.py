"""Krok 3, etap 0d (eksploracja, bez robota, szum 0): wybiórczość „która noga dotknięta → która noga odpowiada”.
Sieć „pre”. Bodziec A: dotyk tylko szczecinek T2 L (1 N, 1 s); bodziec B: tylko szczecinek T1 L.
Odpowiedź: średnia częstość MN nogi T2 L i MN nogi T1 L („fl” L) w ostatnich 0,5 s.
Wskaźnik wybiórczości dla bodźca: (własna − cudza) / (własna + cudza); W = średnia z obu bodźców (−1…+1; 0 = brak).
Dane kontra tasowania eksploracyjne (swobodne 21 100 001–005, zachowujące warstwy 21 100 006–010).
Uruchom: explore_specificity.py OUT.json GLU"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402
import side_shuffle  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402

JN = nets.JN


def mn_sets(bodies, m):
    pos = {b: i for i, b in enumerate(bodies)}
    t2 = sorted({pos[int(b)] for v in m["g2"]["MN"].values() for b in v})
    t1 = sorted({pos[int(b)] for b in m["flb"]} - set(t2))
    return np.array(t2), np.array(t1)


def specificity(W, idx, t2, t1, mV=40.0):
    out = {}
    for name, own, other in (("A_dotyk_T2", t2, t1), ("B_dotyk_T1", t1, t2)):
        net = SparseALIF(JN.LB._W(W), ALIFParams(), None)
        X = np.zeros(W.shape[0])
        for ix in idx["padsT2" if name.startswith("A") else "padsT1"]:
            X[ix] = mV
        S = np.concatenate([net.run(X, 10) for _ in range(100)])[500:]
        a, b = float(S[:, own].mean() * 1000), float(S[:, other].mean() * 1000)
        out[name] = dict(own_Hz=round(a, 2), other_Hz=round(b, 2), index=round((a - b) / (a + b), 3) if a + b > 0 else 0.0)
    out["W"] = round((out["A_dotyk_T2"]["index"] + out["B_dotyk_T1"]["index"]) / 2, 3)
    return out


def main(out, glu):
    glu = float(glu)
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    bodies, m = nets.bodies_for("pre")
    spec, idx, rep, layer = nets.build_rule(glu, 0.2, "pre")
    t2, t1 = mn_sets(bodies, m)
    res = dict(glu=glu, n_mn=dict(T2=len(t2), T1=len(t1)), rows={})
    res["rows"]["N"] = specificity(spec.W, idx, t2, t1)
    print(glu, "N ", res["rows"]["N"], flush=True)
    for i in range(1, 11):
        seed = 21_100_000 + i
        sh = JN.visual_path.shuffle(spec, seed, equal_weight=True) if i <= 5 else side_shuffle.shuffle_within_side(spec, np.array(layer, str), seed)
        k = f"S{i}" if i <= 5 else f"L{i - 5}"
        res["rows"][k] = specificity(sh.W, idx, t2, t1)
        print(glu, k, res["rows"][k], flush=True)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:3])
