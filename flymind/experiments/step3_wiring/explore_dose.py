"""Sprawa 2, kierunek „liczby” (EKSPLORACJA, bez robota, szum 0): krzywa dawka → odpowiedź szczęki.
Bodziec: oba pady → szczecinki T2 L, poziomy 0…40 mV (= 0…1 N przy 40 mV/N), 1 s; odpowiedź: moment szczęki
0,005 N·m/Hz · (Ti ext − Ti flex/Acc. ti flex), średnia z ostatnich 0,5 s (jak w reflex.py).
Sieci: N; tasowania eksploracyjne F 21 100 001–003, L 21 100 006–008, G 21 100 006–008 (już używane w eksploracji).
Uruchom: explore_dose.py OUT.json GLU"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reflex import TwoNet  # noqa: E402

LEVELS = (0, 2.5, 5, 7.5, 10, 15, 20, 30, 40)


def curve(net):
    out = []
    for mv in LEVELS:
        net.reset()
        X = np.zeros(net.N)
        for ix in net.pads:
            X[ix] = mv
        S = np.concatenate([net.net.run(X, 10) for _ in range(100)])[500:]
        out.append(round(0.005 * float(S[:, net.press].mean() - S[:, net.release].mean()) * 1000, 4))
    return out


def main(out, glu):
    glu = float(glu)
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = dict(glu=glu, levels_mV=LEVELS, rows={})
    for kind, seeds in (("N", [None]), ("F", [21_100_001, 21_100_002, 21_100_003]),
                        ("L", [21_100_006, 21_100_007, 21_100_008]), ("G", [21_100_006, 21_100_007, 21_100_008])):
        for s in seeds:
            k = kind if s is None else f"{kind}{s % 100}"
            res["rows"][k] = curve(TwoNet(glu, kind, s))
            print(glu, k, res["rows"][k], flush=True)
    with open(out, "x") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:3])
