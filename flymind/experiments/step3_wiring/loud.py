"""Etap 2 — „głośność”: tasowania o TEJ SAMEJ aktywności co sieć z danych. Bez robota; o wzmocnieniu nie decyduje wynik zadania.
Aktywność sieci = średnia częstość [Hz] wszystkich neuronów poza receptorami pobudzanymi w danym warunku, z ostatnich 0,5 s
z 1 s bodźca, uśredniona po dwóch warunkach dotyku: dłoń (receptory T1 L, 40 mV) i palce (pady → T2 L, 40 mV).
Wyrównanie: W tasowania mnożone przez jedno wzmocnienie g (wszystkie synapsy, ze znakiem), g szukane bisekcją, aż aktywność
tasowania = aktywność sieci z danych (±2 %). Sieć z danych bez zmian (g = 1).
Uruchom: loud.py measure GLU KIND SEED…   |   loud.py calib OUT.json GLU KIND SEED…   (KIND: N | F | L | G)"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reflex as R  # noqa: E402


def activity(net, conds=("palm", "pads")):
    out = {}
    for c in ("none",) + tuple(conds):
        net.reset()
        X, rec = np.zeros(net.N), []
        if c == "palm":
            rec = list(net.palm)
        elif c == "pads":
            rec = [i for ix in net.pads for i in ix]
        X[rec] = 40.0
        S = np.concatenate([net.net.run(X, 10) for _ in range(100)])[500:]
        keep = np.ones(net.N, bool)
        keep[rec] = False
        out[c] = float(S[:, keep].mean() * 1000)
    out["touch_mean"] = float(np.mean([out[c] for c in conds]))
    return out


class GainNet(R.TwoNet):
    """TwoNet bez zmian + W · g (g = 1 → identyczna sieć)."""

    def __init__(self, glu, kind="N", shuffle_seed=None, rule="pre", gain=1.0):
        super().__init__(glu, kind, shuffle_seed, rule)
        if gain != 1.0:
            self.W = self.W * gain
            self.rep["gain"] = gain
            self.reset()


def calibrate(glu, kind, seed, target, tol=0.02):
    base = R.TwoNet(glu, kind, seed)
    W0 = base.W.copy()

    def act(g):
        base.W = W0 * g
        base.reset()
        return activity(base)["touch_mean"]

    lo, hi = 0.0, 1.0
    while act(hi) < target and hi < 64:
        lo, hi = hi, hi * 2
    g, a = hi, act(hi)
    for _ in range(30):
        if abs(a - target) <= tol * target:
            break
        g = (lo + hi) / 2
        a = act(g)
        lo, hi = (g, hi) if a < target else (lo, g)
    return dict(gain=round(g, 6), activity=a, target=target, ok=bool(abs(a - target) <= tol * target), act_g1=None)


def main():
    mode, args = sys.argv[1], sys.argv[2:]
    if mode == "measure":
        glu, kind, seeds = float(args[0]), args[1], [int(s) for s in args[2:]] or [None]
        for s in seeds:
            print(glu, kind, s, {k: round(v, 2) for k, v in activity(R.TwoNet(glu, kind, s)).items()}, flush=True)
    elif mode == "calib":
        out, glu, kind, seeds = args[0], float(args[1]), args[2], [int(s) for s in args[3:]]
        if os.path.exists(out):
            sys.exit(f"istnieje {out}")
        target = activity(R.TwoNet(glu, "N"))["touch_mean"]
        res = dict(glu=glu, kind=kind, target_N=target, nets={})
        for s in seeds:
            c = calibrate(glu, kind, s, target)
            c["act_g1"] = activity(R.TwoNet(glu, kind, s))["touch_mean"]
            res["nets"][str(s)] = c
            print(glu, kind, s, c, flush=True)
        with open(out, "x") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
