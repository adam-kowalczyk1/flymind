"""Zamrożona nowa podstawa i bark: ta sama scena 45 s na wskazanych ziarnach (plan: PLAN_10_ZIAREN.md). base_shoulder.py bez zmian.
  seeds10.py --freeze PLIK.json          sumy wszystkich plików projektu wczytanych przez próbę, pule, znaki, wzmocnienie, suma macierzy sieci
  seeds10.py DIR_OUT ziarno,ziarno,...   przebiegi `nowa`; przed pracą sprawdza zamrożenie"""
import hashlib
import json
import os
import sys
import time

import numpy as np

sys.dont_write_bytecode = True
import base_shoulder as B  # noqa: E402

O, T = B.O, B.T
FLY = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PULE = os.path.join(FLY, "results", "six_readout_20261124", "pule.json")
FROZEN = os.path.join(FLY, "results", "seeds10_20261124", "zamrozenie.json")


def build():
    T.A_MV = B.S0.O.MV
    net, feco = O.build()
    U = json.load(open(PULE))
    G = {f"{ax}|{k}": list(map(int, v)) for ax, d in U.items() for k, v in d.items()}
    ix = lambda *ks: [net.pos[b] for k in ks for b in G[k]]             # noqa: E731
    net.pools = {0: (ix("1 podstawa|+ promotor"), ix("1 podstawa|- remotor")),
                 1: (ix("2 bark|Tr flexor", "2 bark|Acc. tr flexor"), ix("2 bark|Tr extensor", "2 bark|Sternotroch.", "2 bark|Tergotr.")), 2: net.pools[2], 3: net.pools[3]}
    inv = {i: b for b, i in net.pos.items()}
    ids = [b for v in G.values() for b in v] + [int(inv[i]) for i in list(net.press) + list(net.release)]   # te same 76 masek co w próbie (kolejność kolumn)
    for b in ids:
        m = np.zeros(net.N, bool)
        m[net.pos[b]] = True
        net._grp[f"id{b}"] = m
    return net, feco


def state(net):
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()    # noqa: E731
    files = sorted({os.path.abspath(m.__file__) for m in list(sys.modules.values()) if getattr(m, "__file__", None) and os.path.abspath(m.__file__).startswith(os.path.dirname(FLY) + os.sep) and "/.venv/" not in m.__file__})
    files = [f for f in files if not f.endswith("seeds10.py")] + [PULE]
    W = net._Wc.tocsc()
    inv = {i: b for b, i in net.pos.items()}
    return dict(pliki={os.path.relpath(f, FLY): sha(f) for f in files}, znaki={str(k): v for k, v in T.JN.SIGN.items()}, wzmocnienie=0.005, tau_r=0.05, J0=0.2, szum=T.SIGMA, glu=-1.0,
                pule={str(j): [[int(inv[i]) for i in s] for s in pn] for j, pn in net.pools.items()}, siec_sha256=hashlib.sha256(W.indptr.tobytes() + W.indices.tobytes() + W.data.tobytes()).hexdigest(), N=net.N,
                limity=dict(v_max=1.5, max_lead=[.02, .3, .3, .3, .3], z_min=0.005, margin=.05))


if __name__ == "__main__":
    net, feco = build()
    st = state(net)
    if sys.argv[1] == "--freeze":
        json.dump(st, open(sys.argv[2], "x"), indent=1, ensure_ascii=False)
        print(len(st["pliki"]), "plików; sieć", st["siec_sha256"][:12], "znaki", st["znaki"])
        sys.exit()
    fz = json.load(open(FROZEN))
    assert st == fz, "coś się zmieniło od zamrożenia: " + str([k for k in fz if fz[k] != st[k]])
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    cam = O.Cam()
    for s in map(int, sys.argv[2].split(",")):
        path = os.path.join(out, f"{s}.npz")
        if os.path.exists(path):
            sys.exit(f"istnieje {path}")
        O.SEED, t0 = s, time.time()
        g = B.trial(net, feco, cam)
        np.savez_compressed(path, **g)
        print(s, f"{time.time() - t0:.0f} s", "kąty °", np.degrees(g["q_all"][-1] - g["q0"])[:4].round(2).tolist(), "flagi", (g["flag"] > 0).sum(0).tolist(), "strażnik", int(g["guard"].sum()), "kontakty", int(g["ncon"].max()), flush=True)
