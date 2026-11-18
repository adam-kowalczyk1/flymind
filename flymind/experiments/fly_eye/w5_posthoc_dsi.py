"""W5 — analiza PO FAKCIE (opisowa): kierunkowość T4/T5 flyvis na bodźcach B1/W5 (dysk przesuwany w 4 strony, środek 0)
vs na pełnych krawędziach (ten sam ruch, ale krawędź przez całe pole). Pytanie: czy to mały przedmiot gubi kierunek.
DI podtypu = (R_pref − R_null)/(R_pref + R_null), R = Σ wyprostowanej odpowiedzi w kolumnach ≤ 6 od środka i w fazie ruchu.
Kierunki preferowane (flyxy, PREREG_BRIDGE.md, model 000): a 180°, b 0°, c 90°, d 270° (zaokrąglone do kierunków bodźca).
envs/flyvis: w5_posthoc_dsi.py MODELS OUT.json"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))
import w5_and as W  # noqa: E402
from bridge_loom import DIRS, DT, PRE, flyxy, movies  # noqa: E402

PREF = {"a": 180, "b": 0, "c": 90, "d": 270}


def edge_movies(X, pol, n):
    """Pełna krawędź (półpłaszczyzna) przesuwana o 16 kolumn w tym samym czasie co dysk; polarity = kolor nadchodzącej strony."""
    out = {}
    for a in DIRS:
        e = np.array([np.cos(np.radians(a)), np.sin(np.radians(a))]); p = X @ e
        fr = [np.where(p <= -8 + 16 * k / (n - 1), pol, 0.5) for k in range(n)]
        out[a] = np.array([fr[0]] * int(PRE / DT) + fr + [fr[-1]] * 20)
    return out


def main(models, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    lo, hi = map(int, models.split("-")); res = {}
    for k in range(lo, hi + 1):
        net, u, v, idx = W.load(k); X = flyxy(u, v); near = np.hypot(*X.T) <= 6; r = {}
        for pol in (0, 1):
            mv = movies(X, pol); n = len(mv["loom_0"]) - int(PRE / DT) - 20
            for kind, mvs in (("dysk", {a: mv[f"trans{a}_0"] for a in DIRS}), ("krawedz", edge_movies(X, pol, n))):
                R = {a: W.sim(net, m, DT, int(PRE / DT), idx)[:, :, near].sum((0, 2)) for a, m in mvs.items()}   # 8 podtypów
                for j, s in enumerate(W.SUB):
                    pa = PREF[s[-1]]; na = (pa + 180) % 360
                    r[f"p{pol}_{kind}_{s}"] = float((R[pa][j] - R[na][j]) / (R[pa][j] + R[na][j] + 1e-12))
        res[k] = r; print(k, "ok", flush=True)
    json.dump(res, open(out, "x"), indent=1)
    import numpy as _np
    for pol in (0, 1):
        for kind in ("dysk", "krawedz"):
            m = {s: _np.median([res[k][f"p{pol}_{kind}_{s}"] for k in res]) for s in W.SUB}
            print(f"{'ciemny' if pol == 0 else 'jasny'} {kind:8s} mediana DI:", " ".join(f"{s}:{m[s]:+.2f}" for s in W.SUB),
                  f"| T4 śr. {_np.mean([m[s] for s in W.SUB[:4]]):+.2f}  T5 śr. {_np.mean([m[s] for s in W.SUB[4:]]):+.2f}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
