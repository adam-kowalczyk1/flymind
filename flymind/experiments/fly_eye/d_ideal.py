"""D — idealne bodźce na kolumnach flyvis: zbliżanie dysku vs „własny ruch” (cała tekstura przesuwana / obracana) (LOOP_TARGET_D.md).
envs/flyvis (FLYVIS_ROOT_DIR=data/flyvis):
  d_ideal.py run  MAP.npz MODELS OUT.npz
  d_ideal.py eval MAP.npz D_DIR OUT.json"""
import glob
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))

SEEDS = (23506001, 23506002, 23506003)
MOVES = ["tr0", "tr90", "tr180", "tr270", "roll+", "roll-"]
SEL_R = 4.0


def texture(seed, X):
    """Funkcja p → {0, 1}: znak sumy 400 plam Gaussa (σ = 2 kolumny, losowy znak) w kwadracie ±40 kolumn."""
    g = np.random.default_rng(seed); c = g.uniform(-40, 40, (400, 2)); s = g.choice([-1.0, 1.0], 400)
    return lambda P: (np.exp(-((P[:, None, :] - c[None]) ** 2).sum(-1) / 8.0) @ s > 0).astype(float)


def self_motion(X, seed, n, npre, nhold):
    f = texture(seed, X); out = {}
    for mv in MOVES:
        fr = []
        for k in range(n):
            x = k / (n - 1)
            if mv.startswith("tr"):
                a = np.radians(int(mv[2:])); P = X - np.array([np.cos(a), np.sin(a)]) * (-8 + 16 * x)
            else:
                th = (1 if mv == "roll+" else -1) * 2.0 * x; cs, sn = np.cos(-th), np.sin(-th)
                P = X @ np.array([[cs, sn], [-sn, cs]])
            fr.append(f(P))
        out[f"{mv}_s{seed}"] = np.array([fr[0]] * npre + fr + [fr[-1]] * nhold)
    return out


def run(mp, models, out):
    import e2_lpi
    import w5_and as W
    import w7_run
    from bridge_loom import DT, HOLD, PRE, flyxy, loom_radius, movies
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    lo, hi = map(int, models.split("-")); M = np.load(mp); edges = e2_lpi.inhibition_edges(M); res = {}
    n, npre, nhold = len(loom_radius()), int(PRE / DT), int(HOLD / DT)
    for k in range(lo, hi + 1):
        net, u, v, idx = W.load(k); X = flyxy(u, v)
        p4, p5 = w7_run.align(net, X, idx); idx_al = idx[np.r_[p4, 4 + p5]]
        col = {(a, b): i for i, (a, b) in enumerate(zip(u, v))}
        ci = np.array([col.get((a, b), -1) for a, b in zip(M["in_u"], M["in_v"])]); ok = M["in_inside"] & (ci >= 0)
        stim = {f"loom_p{p}": movies(X, p)["loom_0"] for p in (0, 1)}
        for s in SEEDS:
            stim.update(self_motion(X, s, n, npre, nhold))
        for name, m in stim.items():
            A = W.sim(net, m, DT, npre, idx_al)
            res[f"m{k}_{name}"] = W.readout(A, M, ci, ok)[0][:, 0]                 # [LIN, AND] × komórki, układ prawdziwy
            res[f"lpi_m{k}_{name}"] = e2_lpi.readout_lpi(A, M, ci, ok, edges)[:, 0]
        res[f"align_m{k}"] = np.r_[p4, p5]
        print("model", k, "π_T4", p4.tolist(), "π_T5", p5.tolist(), flush=True)
    np.savez_compressed(out, **res)


def evaluate(mp, dd, out):
    from w5_analysis import rf_of
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    M = np.load(mp); D = {}
    for f in sorted(glob.glob(os.path.join(dd, "d_*.npz"))):
        D.update(np.load(f))
    rf = rf_of(M)[0]; sel = (M["post_type"] == "LPLC2") & (np.hypot(*rf.T) <= SEL_R)
    models = sorted({int(re.match(r"m(\d+)_", k).group(1)) for k in D if k.startswith("m")})
    sm = [f"{mv}_s{s}" for s in SEEDS for mv in MOVES]
    res = {"n_cells": int(sel.sum()), "n_models": len(models)}
    for var, pre in (("main", ""), ("lpi", "lpi_")):
        for ri, rule in ((1, "AND"), (0, "LIN")):
            for p in (0, 1):
                pk = lambda m, s: float(D[f"{pre}m{m}_{s}"][ri, sel].mean())        # noqa: E731
                L = np.array([pk(m, f"loom_p{p}") for m in models]); S = np.array([[pk(m, s) for s in sm] for m in models])
                okm = L > S.max(1)
                worst = [sm[i].split("_s")[0] for i in S.argmax(1)]
                res[f"{var}_{rule}_p{p}"] = dict(n_ok=int(okm.sum()), ok=bool(okm.sum() >= 0.8 * len(models)),
                                                 median_loom_over_worst=float(np.median(L / (S.max(1) + 1e-12))),
                                                 loom_beats_each_move={mv: int(sum(L[i] > max(S[i, j] for j, s in enumerate(sm) if s.startswith(mv + "_"))
                                                                                   for i in range(len(models)))) for mv in MOVES},
                                                 worst_move_counts={mv: worst.count(mv) for mv in MOVES})
    res["D_pass"] = bool(res["main_AND_p0"]["ok"] or res["main_AND_p1"]["ok"])
    json.dump(res, open(out, "x"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"run": run, "eval": evaluate}[sys.argv[1]](*sys.argv[2:5])
