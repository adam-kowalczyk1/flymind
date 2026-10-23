"""Losowe przeszukiwanie stałych modułu chwytu na ZIARNACH STROJENIA 100–119 (rozłącznych z testowymi
0–9 z Etapu 3).  python tune.py [liczba konfiguracji] [plik wynikowy .json]"""
import json
import sys
from multiprocessing import Pool

import numpy as np

from circuit import FlyController
from stage3 import run_trial

TUNE_SEEDS = range(100, 120)
SPACE = dict(k_muscle=(0.4, 0.7), sens_gain=(15, 28), vel_gain=(120, 260), syn_resist_slow=[10, 30, 100],
             hold_offset=(10, 25), state_bias=(3.8, 4.4))


def sample(rng):
    return {k: (float(rng.uniform(*v)) if isinstance(v, tuple) else v[rng.integers(len(v))]) for k, v in SPACE.items()}


def evaluate(P):
    rs = [run_trial(s, FlyController(seed=s, params=P)) for s in TUNE_SEEDS]
    rt = [r["reaction_ms"] for r in rs if r["success"]]
    return dict(params=P, success=sum(r["success"] for r in rs), crushed=sum(r["crushed"] for r in rs),
                reaction=float(np.mean(rt)) if rt else 1e9,
                lifted=sum(r["lifted"] for r in rs), peak=float(np.mean([r["peak_force"] for r in rs])))


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    out = sys.argv[2] if len(sys.argv) > 2 else "../results/tune.json"
    rng = np.random.default_rng(1)
    configs = [{}] + [sample(rng) for _ in range(n - 1)]
    with Pool(8) as pool:
        res = pool.map(evaluate, configs)
    res.sort(key=lambda r: (-r["success"], r["crushed"], r["reaction"]))
    json.dump(res, open(out, "w"), indent=1)
    for r in res[:8]:
        print(r["success"], r["crushed"], r["lifted"], round(r["peak"], 2), round(r["reaction"]), {k: round(v, 2) for k, v in r["params"].items()})
