"""Krok 3, etap 0e (eksploracja, bez robota): „przesłuch” — dotyk TYLKO szczecinek T2 L (pady → noga środkowa), 1 N, 2 s.
Ile wynosi napęd stawów ramienia z pul nogi T1 L (której nikt nie dotknął)? Dryf = k·(POS − NEG) [rad/s], k = 0,005.
Dane kontra tasowania eksploracyjne 21 100 001–010. Uruchom: explore_leak.py OUT.json GLU"""
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


def leak(W, idx, ticks=200):
    net = SparseALIF(JN.LB._W(W), ALIFParams(), None)
    X = np.zeros(W.shape[0])
    for ix in idx["padsT2"]:
        X[ix] = 40.0
    S = np.concatenate([net.run(X, 10) for _ in range(ticks)])[500:]
    out = {}
    for j, (p, n) in idx["pools"].items():
        a, b = float(S[:, p].mean() * 1000), float(S[:, n].mean() * 1000)
        out[f"j{j}"] = dict(pos=round(a, 1), neg=round(b, 1), drift_rad_s=round(0.005 * (a - b), 4))
    out["sum_abs_drift"] = round(sum(abs(out[f"j{j}"]["drift_rad_s"]) for j in (1, 2, 3, 4)), 4)
    return out


def main(out, glu):
    glu = float(glu)
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    spec, idx, rep, layer = nets.build_rule(glu, 0.2, "pre")
    res = {"N": leak(spec.W, idx)}
    print(glu, "N ", res["N"], flush=True)
    for i in range(1, 11):
        seed = 21_100_000 + i
        sh = JN.visual_path.shuffle(spec, seed, equal_weight=True) if i <= 5 else side_shuffle.shuffle_within_side(spec, np.array(layer, str), seed)
        k = f"S{i}" if i <= 5 else f"L{i - 5}"
        res[k] = leak(sh.W, idx)
        print(glu, k, res[k]["sum_abs_drift"], {j: v["drift_rad_s"] for j, v in res[k].items() if j != "sum_abs_drift"}, flush=True)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:3])
