"""Losowe przeszukiwanie stałych chwytu na ZIARNACH STROJENIA 100–119 × 3 ziarna szumu (60 prób),
rozłącznych z walidacją 120–139 i testem 0–9.  python tune.py [liczba konfiguracji] [plik .json]
Wynik = sukcesy − 2·zgniecenia, potem krótszy czas reakcji."""
import json
import sys
from multiprocessing import Pool

import numpy as np

from evaluate import _one

TUNE_SEEDS = range(100, 120)
DRAWS = 3
SPACE = dict(q_open=(0.9, 1.15), vel_gain=(150, 350), vel_gain_far=(10, 80), q_near=(0.8, 1.0),
             hold_offset=(18, 23), k_muscle=(0.4, 0.7), syn_jaw_resist=[3, 10, 30, 100, 300, 1000])
FIXED = dict(real_friction=True)


def sample(rng):
    return {k: (float(rng.uniform(*v)) if isinstance(v, tuple) else v[rng.integers(len(v))]) for k, v in SPACE.items()}


def score(P, rs):
    ok = [r for r in rs if r["success"]]
    crushed = sum(r["crushed"] for r in rs)
    return dict(params=P, success=len(ok), crushed=crushed, nogrip=len(rs) - len(ok) - crushed,
                reaction=float(np.mean([r["reaction_ms"] for r in ok])) if ok else 1e9,
                score=len(ok) - 2 * crushed)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    out = sys.argv[2] if len(sys.argv) > 2 else "../results/tune.json"
    rng = np.random.default_rng(2)
    configs = [dict(FIXED)] + [dict(FIXED, **sample(rng)) for _ in range(n - 1)]
    tasks = [(i, (P, s, d, None)) for i, P in enumerate(configs) for d in range(DRAWS) for s in TUNE_SEEDS]
    with Pool(8) as pool:
        res = pool.map(_one, [t for _, t in tasks], chunksize=4)
    by = {}
    for (i, _), (_, _, r) in zip(tasks, res):
        by.setdefault(i, []).append(r)
    table = sorted((score(configs[i], rs) for i, rs in by.items()), key=lambda r: (-r["score"], r["reaction"]))
    json.dump(table, open(out, "w"), indent=1)
    for r in table[:8]:
        print(r["success"], r["crushed"], r["nogrip"], round(r["reaction"]),
              {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r["params"].items()})
