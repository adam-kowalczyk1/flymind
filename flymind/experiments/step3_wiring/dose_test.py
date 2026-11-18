"""Sprawa 2 — test „dawka dotyku → siła zacisku” (reguły: LOOP_TARGET_dose_r1.md, zapisane przed uruchomieniem). Bez robota.
Bodziec: oba pady → szczecinki T2 L, LEVELS mV (40 mV = 1 N), 1 s, szum 0; odpowiedź z ostatnich 0,5 s:
  press = Ti extensor MN T2 L [Hz], release = Ti flexor + Acc. ti flexor MN T2 L [Hz], tau = 0,005·(press − release) N·m.
Uruchom: dose_test.py OUT_DIR GLU FAMILY FIRST LAST     FAMILY: data | F | L | G"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reflex import TwoNet  # noqa: E402

LEVELS = (0, 2.5, 5, 7.5, 10, 15, 20, 30, 40)
BASE = {"F": 21_910_000, "L": 21_920_000, "G": 21_930_000}
EXPLORE = set(range(21_100_001, 21_100_011))


def curve(net):
    rows = []
    for mv in LEVELS:
        net.reset()
        X = np.zeros(net.N)
        for ix in net.pads:
            X[ix] = mv
        S = np.concatenate([net.net.run(X, 10) for _ in range(100)])[500:]
        p, r = float(S[:, net.press].mean() * 1000), float(S[:, net.release].mean() * 1000)
        rows.append(dict(mV=mv, press_Hz=round(p, 3), release_Hz=round(r, 3), tau=round(0.005 * (p - r), 4)))
    return rows


def main(out_dir, glu, fam, first, last):
    glu, first, last = float(glu), int(first), int(last)
    out = os.path.join(out_dir, f"dose_g{glu:+.0f}_{fam}_{first:02d}_{last:02d}.json")
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    if fam != "data" and not 1 <= first <= last <= 20:
        sys.exit("FIRST..LAST w 1…20")
    res = dict(glu=glu, family=fam, levels_mV=LEVELS, rows={})
    seeds = [None] if fam == "data" else [BASE[fam] + i for i in range(first, last + 1)]
    for s in seeds:
        assert s is None or s not in EXPLORE
        net = TwoNet(glu, "N" if fam == "data" else fam, s)
        key = "N" if s is None else str(s)
        res["rows"][key] = dict(curve=curve(net), W_sha256=net.rep.get("W_sha256_shuffled", net.rep["W_sha256"]))
        print(glu, fam, key, [c["tau"] for c in res["rows"][key]["curve"]], flush=True)
    with open(out, "x") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:6])
