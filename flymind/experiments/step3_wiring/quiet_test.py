"""Krok 3 — H-cisza (bez robota; reguły w LOOP_TARGET_arm3_r1.md, zapisane przed uruchomieniem).
Dotyk 1 N na oba pady, 1 s, szum 0. Miara: średnia częstość [Hz] wszystkich MN „fl” L (ostatnie 0,5 s) oraz liczba pul
z ośmiu o częstości > 5 Hz. Dane kontra 20 tasowań swobodnych i 20 zachowujących warstwy na każde Glu.
Uruchom: quiet_test.py OUT_DIR GLU KIND FIRST LAST   (pliki cząstkowe, by liczyć równolegle)"""
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
BASE = {"free": 21_230_000, "layer": 21_240_000}


def measure(W, idx, layer):
    net = SparseALIF(JN.LB._W(W), ALIFParams(), None)
    N = W.shape[0]
    X = np.zeros(N)
    for name in ("padsT2", "padsT1"):
        for ix in idx[name]:
            X[ix] = 40.0
    S = np.concatenate([net.run(X, 10) for _ in range(100)])[500:]
    mn = np.flatnonzero(layer == "M")
    pools = {nets.NAMES[j][k]: round(float(S[:, ix].mean() * 1000), 2) for j, pq in idx["pools"].items() for k, ix in enumerate(pq)}
    return dict(mn_rate_Hz=round(float(S[:, mn].mean() * 1000), 3), in_rate_Hz=round(float(S[:, np.flatnonzero(layer == "I")].mean() * 1000), 3),
                pools_gt5=int(sum(v > 5 for v in pools.values())), pools=pools)


def main(out_dir, glu, kind, first, last):
    glu, first, last = float(glu), int(first), int(last)
    out = os.path.join(out_dir, f"quiet_g{glu:+.0f}_{kind}_{first:02d}_{last:02d}.json")
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    spec, idx, rep, layer = nets.build_rule(glu, 0.2, "pre")
    res = dict(glu=glu, kind=kind, W_sha256=rep["W_sha256"], rows={})
    if kind == "data":
        res["rows"]["N"] = measure(spec.W, idx, layer)
    else:
        for i in range(first, last + 1):
            seed = BASE[kind] + i
            sh = JN.visual_path.shuffle(spec, seed, equal_weight=True) if kind == "free" else \
                side_shuffle.shuffle_within_side(spec, np.array(layer, str), seed)
            res["rows"][str(seed)] = measure(sh.W, idx, layer)
            print(glu, kind, seed, res["rows"][str(seed)]["mn_rate_Hz"], flush=True)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:6])
