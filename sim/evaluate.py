"""Ewaluacja zestawu parametrów na zakresie ziaren (równolegle) z listą porażek.
python evaluate.py '{"k_muscle":0.5,"q_open":1.0}' 100 120 [--noise-draws 3]
--noise-draws k: każde ziarno próby × k ziaren szumu sieci (jak w Etapie 4: seed + 100·d).
--base-leak τ: wygasanie celu serwa bazy [s]."""
import json
import sys
from multiprocessing import Pool

import numpy as np

import stage3
from circuit import FlyController
from stage3 import run_trial, summarize


def _one(a):
    P, seed, d, leak = a
    stage3.BASE_LEAK = leak               # macOS: spawn — zmienne modułu nie przechodzą do procesów
    P = dict(P)
    q = P.pop("q_open", None)
    rf = P.pop("real_friction", stage3.REAL_FRICTION)
    return seed, d, run_trial(seed, FlyController(seed=seed + 100 * d, params=P), q_open=q, real_friction=rf)


def evaluate(P, seeds, draws=1, verbose=True, leak=None):
    with Pool(8) as pool:
        res = pool.map(_one, [(P, s, d, leak) for d in range(draws) for s in seeds])
    rs = [r for _, _, r in res]
    s = summarize(rs, json.dumps(P))
    az = [abs(r["az_err_deg"]) for r in rs if r["az_err_deg"] is not None]
    print(f"  błąd celowania |e| = {np.mean(az):.2f}°, w ±3,2°: {sum(a < 3.2 for a in az)}/{len(az)}")
    if verbose:
        for seed, d, r in res:
            if not r["success"]:
                kind = "chybiona" if r["miss"] else "zgnieciona" if r["crushed"] else "bez chwytu"
                print(f"  porażka: ziarno {seed} szum {d}: {kind}, szczyt {r['peak_force']:.2f} N, "
                      f"uniesiona {r['lifted']}, start unoszenia {r['t_lift']}, celowanie {r['az_err_deg']:.1f}°")
    return s, rs


if __name__ == "__main__":
    P = json.loads(sys.argv[1])
    draws = int(sys.argv[sys.argv.index("--noise-draws") + 1]) if "--noise-draws" in sys.argv else 1
    leak = float(sys.argv[sys.argv.index("--base-leak") + 1]) if "--base-leak" in sys.argv else None
    evaluate(P, range(int(sys.argv[2]), int(sys.argv[3])), draws, leak=leak)
