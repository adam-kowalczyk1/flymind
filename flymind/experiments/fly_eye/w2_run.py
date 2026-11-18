"""W2 — oko flyvis → LC4 przez liczby synaps MaleCNS. Cel: LOOP_TARGET_W2.md.
envs/flyvis (FLYVIS_ROOT_DIR=data/flyvis):
  w2_run.py discs MAP.npz MODELS(np. 0-4) OUT.npz          dyski zbliżanie/oddalanie/przesuwanie (bodźce B1: bridge_loom.movies)
  w2_run.py cam   MAP.npz MODELS W0_DIR OUT.npz            sceny z kamery robota (W0, optyka w1_atlas.hex_movie)
Odczyt (ta sama reguła co B1): wydzielanie = max(0, aktywność − stan w ostatniej klatce przed ruchem);
LC4 = max(0, Σ znak × synapsy × wydzielanie). Kontrola: 23 losowe permutacje etykiet typów (ziarna 23 505 001–023)."""
import os
import sys

import numpy as np
import torch
from scipy import sparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))
torch.set_num_threads(3)
from flyvis import NetworkView  # noqa: E402

NCOL, NPERM, SEED0 = 721, 23, 23505001


def perms(k):
    out = [np.arange(k)]
    for i in range(NPERM):
        out.append(np.random.default_rng(SEED0 + i).permutation(k))      # 27 typów: tożsamość praktycznie niemożliwa
    return out


def readout_mats(M, col):
    """Lista macierzy rzadkich [komórki LC4 × (typy·721)]: [0] układ prawdziwy, [1:] permutacje etykiet typów.
    Znak synapsy idzie za typem, którego aktywność jest podawana (neuron wydzielający)."""
    types = sorted(set(M["in_type"].astype(str)))
    tix = np.array([types.index(t) for t in M["in_type"].astype(str)])
    ci = np.array([col.get((a, b), -1) for a, b in zip(M["in_u"], M["in_v"])])
    ok = M["in_inside"] & (ci >= 0)
    sgn = np.array([M["in_sign"][tix == k][0] for k in range(len(types))])       # znak typu (ten sam dla wszystkich komórek typu)
    n = len(M["post"])
    mats = [sparse.csr_matrix((M["in_w"][ok] * sgn[p[tix[ok]]], (M["in_post"][ok], p[tix[ok]] * NCOL + ci[ok])),
                              shape=(n, len(types) * NCOL)) for p in perms(len(types))]
    return types, mats


def load(k):
    net = NetworkView(f"flow/0000/{k:03d}").init_network()
    nd = net.connectome.nodes
    t = np.array(nd.type[:]).astype(str); u = np.array(nd.u[:]); v = np.array(nd.v[:])
    r1 = t == "R1"
    return net, t, u, v, r1, {(a, b): i for i, (a, b) in enumerate(zip(u[r1], v[r1]))}


def lc4(net, mv, dt, n0, idx, mats):
    """mv [klatki × 721] → (szczyty [permutacje × komórki], przebieg układu prawdziwego [komórki × klatki ruchu])."""
    with torch.no_grad():
        a = net.simulate(torch.tensor(mv, dtype=torch.float32)[None, :, None, :], dt).numpy()[0]
    A = a[:, idx]                                                   # klatki × typy × 721
    rel = np.clip(A[n0:] - A[n0 - 1][None], 0, None).reshape(len(a) - n0, -1).T     # (typy·721) × klatki ruchu
    drive = [np.clip(m @ rel, 0, None) for m in mats]
    return np.stack([d.max(1) for d in drive]).astype(np.float32), drive[0].astype(np.float32)


def type_idx(t, u, v, r1, types):
    idx = np.stack([np.where(t == s)[0] for s in types])
    for j in range(len(types)):
        assert (u[idx[j]] == u[r1]).all() and (v[idx[j]] == v[r1]).all(), types[j]
    return idx


def main(mode, mp, models, *rest):
    out = rest[-1]
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    lo, hi = map(int, models.split("-"))
    M = np.load(mp)
    res = {}
    for k in range(lo, hi + 1):
        net, t, u, v, r1, col = load(k)
        types, mats = readout_mats(M, col)
        idx = type_idx(t, u, v, r1, types)
        if mode == "discs":
            from bridge_loom import DT, PRE, flyxy, movies
            X = flyxy(u[r1], v[r1])
            for pol in (0, 1):
                for name, m in movies(X, pol).items():
                    pk, tc = lc4(net, m, DT, int(PRE / DT), idx, mats)
                    res[f"m{k}_p{pol}_{name}"] = pk
                    if name.endswith("_0"):
                        res[f"tc_m{k}_p{pol}_{name}"] = tc
        else:
            from w1_atlas import DEG_COL, SCENES, flyxy, hex_movie
            xy = flyxy(u[r1], v[r1]) * DEG_COL
            for sc in SCENES:
                W0 = np.load(os.path.join(rest[0], f"{sc}.npz"))
                mv, inside = hex_movie(W0["lum"], float(W0["fovy_deg"]), xy)
                pk, tc = lc4(net, mv, 0.02, int(W0["n_pre"]), idx, mats)
                res[f"m{k}_{sc}"] = pk; res[f"tc_m{k}_{sc}"] = tc
            res["inside"] = inside; res["xy_deg"] = xy
        print("model", k, "ok", flush=True)
    res["types"] = np.array(types)
    np.savez_compressed(out, **res)


if __name__ == "__main__":
    main(*sys.argv[1:])
