"""W7 — W5 z przypisaniem podtypów flyvis do ramion LPLC2 według kierunków zmierzonych w danym modelu (LOOP_TARGET_W7.md).
envs/flyvis (FLYVIS_ROOT_DIR=data/flyvis):
  w7_run.py discs MAP.npz MODELS OUT.npz
  w7_run.py cam   MAP.npz MODELS W0_DIR OUT.npz
Zapisuje te same klucze co w5_and.py (więc ocenia je w5_analysis.py) oraz align_m{k} = [π_T4 (4), π_T5 (4)]."""
import itertools
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))
import w5_and as W  # noqa: E402
from bridge_loom import DT, PRE, flyxy, loom_radius  # noqa: E402
from w5_posthoc_dsi import edge_movies  # noqa: E402

ARM_DIR = [180, 0, 90, 270]                                   # ramiona MaleCNS a, b, c, d (kierunek „na zewnątrz”, flyxy)


def align(net, X, idx):
    """π[g] = indeks podtypu flyvis (0–3) podawanego na ramię g; osobno T4 (krawędź jasna) i T5 (krawędź ciemna)."""
    n = len(loom_radius()); near = np.hypot(*X.T) <= 6; out = []
    for pol, off in ((1, 0), (0, 4)):
        R = {a: W.sim(net, m, DT, int(PRE / DT), idx)[:, :, near].sum((0, 2)) for a, m in edge_movies(X, pol, n).items()}
        di = np.array([[(R[d][off + s] - R[(d + 180) % 360][off + s]) / (R[d][off + s] + R[(d + 180) % 360][off + s] + 1e-12)
                        for d in ARM_DIR] for s in range(4)])          # di[podtyp, ramię]
        out.append(max(itertools.permutations(range(4)), key=lambda p: sum(di[p[g], g] for g in range(4))))
    return np.array(out[0]), np.array(out[1])


def main(mode, mp, models, *rest):
    out = rest[-1]
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    lo, hi = map(int, models.split("-"))
    M = np.load(mp); res = {}
    for k in range(lo, hi + 1):
        net, u, v, idx = W.load(k); X = flyxy(u, v)
        p4, p5 = align(net, X, idx)
        idx_al = idx[np.r_[p4, 4 + p5]]                        # ramię g dostaje podtyp flyvis π(g); dalej jak W5
        res[f"align_m{k}"] = np.r_[p4, p5]
        col = {(a, b): i for i, (a, b) in enumerate(zip(u, v))}
        ci = np.array([col.get((a, b), -1) for a, b in zip(M["in_u"], M["in_v"])]); ok = M["in_inside"] & (ci >= 0)
        if mode == "discs":
            from bridge_loom import movies
            for pol in (0, 1):
                for name, m in movies(X, pol).items():
                    pk, tc = W.readout(W.sim(net, m, DT, int(PRE / DT), idx_al), M, ci, ok)
                    res[f"m{k}_p{pol}_{name}"] = pk
                    if name.endswith("_0"):
                        res[f"tc_m{k}_p{pol}_{name}"] = tc
        else:
            from w1_atlas import DEG_COL, SCENES, hex_movie
            for sc in SCENES:
                W0 = np.load(os.path.join(rest[0], f"{sc}.npz"))
                mv, inside = hex_movie(W0["lum"], float(W0["fovy_deg"]), X * DEG_COL)
                pk, tc = W.readout(W.sim(net, mv, 0.02, int(W0["n_pre"]), idx_al), M, ci, ok)
                res[f"m{k}_{sc}"] = pk; res[f"tc_m{k}_{sc}"] = tc
            res["inside"] = inside; res["xy_deg"] = X * DEG_COL
        print("model", k, "π_T4", p4.tolist(), "π_T5", p5.tolist(), flush=True)
    np.savez_compressed(out, **res)


if __name__ == "__main__":
    main(*sys.argv[1:])
