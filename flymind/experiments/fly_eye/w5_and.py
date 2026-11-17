"""W5 — LPLC2 z oka flyvis przez połączenia MaleCNS, odczyt „AND ramion” (cel: LOOP_TARGET_W5.md).
Ramię g ∈ {a, b, c, d} komórki LPLC2 = jej synapsy od T4g i T5g (warstwa g płata lobula plate; mapa i obrót 30° z B1, bridge_prep.py).
  pobudzenie ramienia d_g(t) = Σ_syn w × max(0, aktywność − stan przed ruchem)       (jak B1, wariant 0 — bez LPi)
  odczyt LIN = Σ_g d_g(t)        (= B1 wariant 0; kontrola zgodności kodu)
  odczyt AND = (Π_g d_g(t))^(1/4)  (średnia geometryczna ramion; żadnego dopasowanego parametru)
Odpowiedź = szczyt w fazie ruchu. Kontrola: 23 permutacje podtypów a–d jak w B1 (ta sama dla T4 i T5).
envs/flyvis (FLYVIS_ROOT_DIR=data/flyvis):
  w5_and.py discs MAP.npz MODELS OUT.npz
  w5_and.py cam   MAP.npz MODELS W0_DIR OUT.npz"""
import itertools
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))
torch.set_num_threads(3)
from flyvis import NetworkView  # noqa: E402

SUB = [f"T4{s}" for s in "abcd"] + [f"T5{s}" for s in "abcd"]
PERMS = list(itertools.permutations(range(4)))          # [0] = tożsamość, jak bridge_loom.PERMS


def readout(A, M, ci, ok):
    """A [klatki × 8 × 721] (wyprostowane) → szczyty [2 reguły × 24 permutacje × komórki] i przebieg AND/LIN układu prawdziwego."""
    n, T = len(M["post"]), A.shape[0]
    post, s0, w = M["in_post"][ok], M["in_sub"][ok], M["in_w"][ok]
    arm = s0 % 4                                         # ramię = warstwa MaleCNS (podtyp synapsy w danych)
    key = post * 4 + arm
    pk = np.zeros((2, len(PERMS), n), np.float32); tc = None
    for pi, P in enumerate(PERMS):
        sub = np.array([P[s % 4] + 4 * (s // 4) for s in range(8)])[s0]      # podtyp flyvis podany na tę synapsę
        d = np.zeros((n * 4, T))
        np.add.at(d, key, (A[:, sub, ci[ok]] * w[None]).T)
        d = d.reshape(n, 4, T)
        lin = d.sum(1); andr = np.prod(np.clip(d, 0, None), 1) ** 0.25
        pk[0, pi], pk[1, pi] = lin.max(1), andr.max(1)
        if pi == 0:
            tc = np.stack([lin, andr]).astype(np.float32)
    return pk, tc


def load(k):
    net = NetworkView(f"flow/0000/{k:03d}").init_network()
    nd = net.connectome.nodes
    t = np.array(nd.type[:]).astype(str); u = np.array(nd.u[:]); v = np.array(nd.v[:])
    r1 = t == "R1"
    idx = np.stack([np.where(t == s)[0] for s in SUB])
    for j in range(8):
        assert (u[idx[j]] == u[r1]).all() and (v[idx[j]] == v[r1]).all()
    return net, u[r1], v[r1], idx


def sim(net, mv, dt, n0, idx):
    with torch.no_grad():
        a = net.simulate(torch.tensor(mv, dtype=torch.float32)[None, :, None, :], dt).numpy()[0]
    A = a[:, idx]
    return np.clip(A[n0:] - A[n0 - 1][None], 0, None)


def main(mode, mp, models, *rest):
    out = rest[-1]
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    lo, hi = map(int, models.split("-"))
    M = np.load(mp); res = {}
    for k in range(lo, hi + 1):
        net, u, v, idx = load(k)
        col = {(a, b): i for i, (a, b) in enumerate(zip(u, v))}
        ci = np.array([col.get((a, b), -1) for a, b in zip(M["in_u"], M["in_v"])])
        ok = M["in_inside"] & (ci >= 0)
        if mode == "discs":
            from bridge_loom import DT, PRE, flyxy, movies
            for pol in (0, 1):
                for name, m in movies(flyxy(u, v), pol).items():
                    pk, tc = readout(sim(net, m, DT, int(PRE / DT), idx), M, ci, ok)
                    res[f"m{k}_p{pol}_{name}"] = pk
                    if name.endswith("_0"):
                        res[f"tc_m{k}_p{pol}_{name}"] = tc
        else:
            from w1_atlas import DEG_COL, SCENES, flyxy, hex_movie
            xy = flyxy(u, v) * DEG_COL
            for sc in SCENES:
                W0 = np.load(os.path.join(rest[0], f"{sc}.npz"))
                mv, inside = hex_movie(W0["lum"], float(W0["fovy_deg"]), xy)
                pk, tc = readout(sim(net, mv, 0.02, int(W0["n_pre"]), idx), M, ci, ok)
                res[f"m{k}_{sc}"] = pk; res[f"tc_m{k}_{sc}"] = tc
            res["inside"] = inside; res["xy_deg"] = xy
        print("model", k, "ok", flush=True)
    np.savez_compressed(out, **res)


if __name__ == "__main__":
    main(*sys.argv[1:])
