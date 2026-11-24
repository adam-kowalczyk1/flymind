"""Pierwszy nacisk = A1 zamiast A0 (plan: PLAN_A0_A1.md). a0_a1.py DIR_OUT ziarno,ziarno,..."""
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
import seeds10 as F  # noqa: E402

O, B = F.O, F.B
net, feco = F.build()
fz = json.load(open(F.FROZEN))
st = F.state(net)
st["pliki"] = {k: v for k, v in st["pliki"].items() if not k.endswith("a0_a1.py")}
assert st == fz, "coś się zmieniło od zamrożenia"
assert O.PRESS[0] == (20.0, 22.0, 0)
O.PRESS = [(20.0, 22.0, 1)] + O.PRESS[1:]                               # jedyna zmiana bodźca
O.N = 2200                                                              # koniec w 22,00 s
out, cam = sys.argv[1], O.Cam()
os.makedirs(out, exist_ok=True)
for s in map(int, sys.argv[2].split(",")):
    path = os.path.join(out, f"{s}.npz")
    if os.path.exists(path):
        sys.exit(f"istnieje {path}")
    O.SEED = s
    g = B.trial(net, feco, cam)
    np.savez_compressed(path, **g)
    print(s, np.degrees(g["q_all"][-1] - g["q0"])[:4].round(2).tolist(), "flagi", (g["flag"] > 0).sum(0).astype(int).tolist(), "strażnik", int(g["guard"].sum()), "kontakty", int(g["ncon"].max()), flush=True)
