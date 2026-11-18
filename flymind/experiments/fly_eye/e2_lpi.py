"""E2 — odczyt W7/W8 (przypisanie kierunków z pomiaru w każdym modelu) + hamowanie LPi z danych MaleCNS (LOOP_TARGET_E2_LPi.md).
  aktywność LPi j(t)   = Σ_syn w × T4/T5(t) / Σ wszystkich synaps T4/T5 → j          (średnia ważona; poza polem = 0, jak pobudzenie)
  hamowanie ramienia   I_g(t) = Σ_j w(j→LPLC2) × aktywność j(t), ramię g = warstwa WYJŚCIOWA z nazwy typu LPi (OUT_LAYERS)
  ramię                e_g = max(0, d_g − I_g);  LIN = Σ_g e_g;  AND = (Π_g e_g)^(1/4)
Bez stałych do dopasowania. Jeden etap (LPi → LPi pominięte). Zapisuje równolegle wariant bez LPi (= W8 „al”).
envs/flyvis (FLYVIS_ROOT_DIR=data/flyvis):  e2_lpi.py MAP.npz MODELS OUT_DIR etykieta=KATALOG_SCEN [...]"""
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))
import w5_and as W  # noqa: E402


def out_layers(t):
    """Warstwy wyjściowe z nazwy: LPi43 → [3]; LPi3412 → [1, 2]; LPi2c → [2] (typ jednowarstwowy)."""
    d = re.match(r"LPi(\d+)", t).group(1)
    return [int(x) for x in (d if len(d) == 1 else d[len(d) // 2:])]


def inhibition_edges(M):
    pt = M["post_type"]; pre, post, w, s = M["vv_pre"], M["vv_post"], M["vv_w"], M["vv_sign"]
    keep = np.array([pt[a].startswith("LPi") and not pt[b].startswith("LPi") for a, b in zip(pre, post)]) & (s < 0)
    E = [(a, b * 4 + L - 1, x / len(out_layers(pt[a]))) for a, b, x in zip(pre[keep], post[keep], w[keep]) for L in out_layers(pt[a])]
    a, k, x = map(np.array, zip(*E))
    return a.astype(int), k.astype(int), x.astype(float)


def readout_lpi(A, M, ci, ok, edges):
    """Jak w5_and.readout, ale ramiona po odjęciu hamowania LPi. Zwraca szczyty [2 reguły × 24 permutacje × komórki]."""
    n, T = len(M["post"]), A.shape[0]
    post, s0, w = M["in_post"][ok], M["in_sub"][ok], M["in_w"][ok]
    key = post * 4 + s0 % 4
    wtot = np.maximum(np.bincount(M["in_post"], M["in_w"], n), 1e-9)
    ea, ek, ew = edges
    pk = np.zeros((2, len(W.PERMS), n), np.float32)
    for pi, P in enumerate(W.PERMS):
        sub = np.array([P[s % 4] + 4 * (s // 4) for s in range(8)])[s0]
        d = np.zeros((n * 4, T)); np.add.at(d, key, (A[:, sub, ci[ok]] * w[None]).T)
        act = d.reshape(n, 4, T).sum(1) / wtot[:, None]
        inh = np.zeros((n * 4, T)); np.add.at(inh, ek, act[ea] * ew[:, None])
        e = np.clip(d - inh, 0, None).reshape(n, 4, T)
        pk[0, pi], pk[1, pi] = e.sum(1).max(1), (np.prod(e, 1) ** 0.25).max(1)
    return pk


def main(mp, models, od, *scenes):
    import w7_run
    from bridge_loom import flyxy
    from w1_atlas import DEG_COL, SCENES, hex_movie
    lo, hi = map(int, models.split("-"))
    outs = {(v, lab): os.path.join(od, f"{v}_{lab}_{lo:03d}-{hi:03d}.npz") for v in ("lpi", "nolpi") for lab, _ in (s.split("=") for s in scenes)}
    for f in outs.values():
        if os.path.exists(f):
            sys.exit(f"istnieje {f}")
    M = np.load(mp); edges = inhibition_edges(M); res = {k: {} for k in outs}
    for k in range(lo, hi + 1):
        net, u, v, idx = W.load(k); X = flyxy(u, v)
        p4, p5 = w7_run.align(net, X, idx); idx_al = idx[np.r_[p4, 4 + p5]]
        col = {(a, b): i for i, (a, b) in enumerate(zip(u, v))}
        ci = np.array([col.get((a, b), -1) for a, b in zip(M["in_u"], M["in_v"])]); ok = M["in_inside"] & (ci >= 0)
        for lab, sd in (s.split("=") for s in scenes):
            for sc in SCENES:
                S = np.load(os.path.join(sd, f"{sc}.npz"))
                mv, inside = hex_movie(S["lum"], float(S["fovy_deg"]), X * DEG_COL)
                A = W.sim(net, mv, 0.02, int(S["n_pre"]), idx_al)
                res[("lpi", lab)][f"m{k}_{sc}"] = readout_lpi(A, M, ci, ok, edges)
                res[("nolpi", lab)][f"m{k}_{sc}"] = W.readout(A, M, ci, ok)[0]
            for v_ in ("lpi", "nolpi"):
                res[(v_, lab)].update(inside=inside, xy_deg=X * DEG_COL, **{f"align_m{k}": np.r_[p4, p5]})
        print("model", k, "π_T4", p4.tolist(), "π_T5", p5.tolist(), flush=True)
    for key, f in outs.items():
        np.savez_compressed(f, **res[key])


if __name__ == "__main__":
    main(*sys.argv[1:])
