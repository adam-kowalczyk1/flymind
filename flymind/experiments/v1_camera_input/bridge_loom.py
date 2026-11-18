"""Most oko flyvis → LPLC2/LPLC4 MaleCNS: odpowiedzi na dysk zbliżający się / oddalający / przesuwany.
envs/flyvis: bridge_loom.py MAP.npz MODELS(np. 0-9) OUT.npz   (plan: PREREG_BRIDGE.md)"""
import itertools
import os
import sys

import numpy as np
import torch
from flyvis import NetworkView

SUB = [f"T4{s}" for s in "abcd"] + [f"T5{s}" for s in "abcd"]
DT = 0.01
LV = 0.04                                  # l/v [s]
DEG_COL = 5.1                              # stopnie na kolumnę (jak w eye_gate)
R0, R1 = 0.5, 8.0                          # promień dysku [kolumny], start/koniec
PRE, HOLD = 1.0, 0.2                       # pierwsza klatka nieruchomo przed ruchem (adaptacja), przytrzymanie po [s]
TR_R, TR_PATH = 4.0, 16.0                  # przesuwany dysk: promień, droga [kolumny]
CENTERS = [(0.0, 0.0)] + [(5 * np.cos(np.radians(k)), 5 * np.sin(np.radians(k))) for k in range(30, 360, 60)]
DIRS = [0, 90, 180, 270]
PERMS = list(itertools.permutations(range(4)))          # [0] = tożsamość; ta sama permutacja dla T4 i T5


def flyxy(u, v):
    return np.c_[1.5 * v, -np.sqrt(3) * (u + v / 2)] / np.sqrt(3)


def loom_radius():
    a0, a1 = np.radians(R0 * DEG_COL), np.radians(R1 * DEG_COL)
    t0, t1 = LV / np.tan(a0), LV / np.tan(a1)           # czas do zderzenia na początku/końcu
    tc = np.arange(t0, t1, -DT)
    return np.degrees(np.arctan(LV / tc)) / DEG_COL      # promień [kolumny] w każdej klatce


def movies(X, polarity):
    """Zwraca dict nazwa → (klatki × 721). polarity 0 = ciemny dysk, 1 = jasny."""
    rad = loom_radius(); n = len(rad); npre, nhold = int(PRE / DT), int(HOLD / DT)
    out = {}
    for ci, c in enumerate(CENTERS):
        d = np.hypot(X[:, 0] - c[0], X[:, 1] - c[1])
        fr = [np.where(d <= rr, polarity, 0.5) for rr in rad]
        out[f"loom_{ci}"] = np.array([fr[0]] * npre + fr + [fr[-1]] * nhold)
        out[f"recede_{ci}"] = np.array([fr[-1]] * npre + fr[::-1] + [fr[0]] * nhold)
        for a in DIRS:
            e = np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
            tr = []
            for k in range(n):
                p = c + e * (-TR_PATH / 2 + TR_PATH * k / (n - 1))
                tr.append(np.where(np.hypot(X[:, 0] - p[0], X[:, 1] - p[1]) <= TR_R, polarity, 0.5))
            out[f"trans{a}_{ci}"] = np.array([tr[0]] * npre + tr + [tr[-1]] * nhold)
    return out


def main(mp, models, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    lo, hi = map(int, models.split("-"))
    M = np.load(mp)
    res = {}
    for k in range(lo, hi + 1):
        net = NetworkView(f"flow/0000/{k:03d}").init_network()
        nd = net.connectome.nodes
        t = np.array(nd.type[:]).astype(str); u = np.array(nd.u[:]); v = np.array(nd.v[:])
        r1 = t == "R1"; X = flyxy(u[r1], v[r1])
        col = {(a, b): i for i, (a, b) in enumerate(zip(u[r1], v[r1]))}
        idx = np.stack([np.where(t == s)[0] for s in SUB])               # 8 × 721, kolejność kolumn jak R1?
        for j, s in enumerate(SUB):
            assert (u[idx[j]] == u[r1]).all() and (v[idx[j]] == v[r1]).all()
        ci = np.array([col.get((a, b), -1) for a, b in zip(M["in_u"], M["in_v"])])
        ok = M["in_inside"] & (ci >= 0)
        Win = np.maximum(np.bincount(M["in_post"][ok], M["in_w"][ok], len(M["post"])), 1.0)
        vvm = ~np.char.startswith(M["post_type"][M["vv_post"]].astype(str), "LPi")      # LPi → LPLC2/LPLC4 (bez LPi → LPi)
        for pol in (0, 1):
            mv = movies(X, pol)
            for name, m in mv.items():
                with torch.no_grad():
                    a = net.simulate(torch.tensor(m, dtype=torch.float32)[None, :, None, :], DT).numpy()[0]
                A = a[:, idx]                                            # klatki × 8 × 721
                n0 = int(PRE / DT)
                A = np.clip(A[n0:] - A[n0 - 1][None], 0, None)           # tylko faza ruchu, ponad stan po adaptacji (prostowane)
                pk = np.zeros((2, len(PERMS), len(M["post"])), np.float32)   # [0] tylko T4/T5, [1] + hamowanie LPi
                for pi, P in enumerate(PERMS):                           # P[s]: podtyp flyvis podany na podtyp s MaleCNS
                    sub = np.array([P[s % 4] + 4 * (s // 4) for s in M["in_sub"][ok]])
                    drive = np.zeros((len(M["post"]), A.shape[0]))
                    np.add.at(drive, M["in_post"][ok], (A[:, sub, ci[ok]] * M["in_w"][ok][None]).T)
                    act = drive / Win[:, None]                           # LPi: średnie pobudzenie na synapsę wejściową
                    opp = drive.copy()
                    np.add.at(opp, M["vv_post"][vvm], (act[M["vv_pre"][vvm]] * (M["vv_w"] * M["vv_sign"])[vvm][:, None]))
                    pk[0, pi] = drive.max(1); pk[1, pi] = np.clip(opp, 0, None).max(1)
                res[f"m{k}_p{pol}_{name}"] = pk
        print("model", k, "ok", flush=True)
    np.savez_compressed(out, **res)


if __name__ == "__main__":
    main(*sys.argv[1:4])
