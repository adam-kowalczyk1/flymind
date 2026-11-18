"""Biegunowość T2 (i innych wejść LC4) w modelach flyvis: plamka r = 2 kolumny w środku oka, skok szary → jasny (ON) lub szary → ciemny (OFF)
po 1 s adaptacji. Odpowiedź = szczyt max(0, aktywność − stan przed skokiem) w kolumnie środkowej w ciągu 0,5 s.
P = (ON − OFF) / (ON + OFF): +1 = tylko rozjaśnienie, −1 = tylko ściemnienie, 0 = oba jednakowo (literatura T2: oba, Keleş i in. 2020).
envs/flyvis: t2_flash.py MODELS(np. 0-9) OUT.json"""
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))
import w2_run as W  # noqa: E402
from bridge_loom import flyxy  # noqa: E402

TYPES = ["T2", "TmY3", "Tm4", "Tm2", "Tm3", "T2a", "T3"]
DT, PRE, POST, R_SPOT = 0.01, 1.0, 0.5, 2.0


def main(models, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    lo, hi = map(int, models.split("-")); res = {}
    for k in range(lo, hi + 1):
        net, t, u, v, r1, col = W.load(k)
        X = flyxy(u[r1], v[r1]); spot = np.hypot(*X.T) <= R_SPOT; c = int(np.argmin(np.hypot(*X.T)))
        idx = [np.where(t == s)[0][c] for s in TYPES]
        n0, n1 = int(PRE / DT), int(POST / DT); r = {}
        for name, val in (("on", 1.0), ("off", 0.0)):
            mv = np.full((n0 + n1, 721), 0.5, np.float32); mv[n0:, spot] = val
            with torch.no_grad():
                a = net.simulate(torch.tensor(mv)[None, :, None, :], DT).numpy()[0][:, idx]
            r[name] = np.clip(a[n0:] - a[n0 - 1], 0, None).max(0)
        res[k] = {s: dict(on=float(r["on"][i]), off=float(r["off"][i]), P=float((r["on"][i] - r["off"][i]) / (r["on"][i] + r["off"][i] + 1e-9)))
                  for i, s in enumerate(TYPES)}
        print(k, " ".join(f"{s}:{res[k][s]['P']:+.2f}" for s in TYPES), flush=True)
    json.dump(res, open(out, "x"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:3])
