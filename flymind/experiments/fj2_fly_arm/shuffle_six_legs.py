"""Kontrola z przetasowanymi połączeniami dla wyniku „dotyk T2 L → wymach T2 R” (eksploracja, ziarna: SEED_REGISTRY.md).

Kryterium spisane przed uruchomieniem (eksploracyjne, nie potwierdzające):
- Miara: przewaga wymachu w T2 R, M = wymach − podpór [Hz].
- Wynik sieci z danych jest „specyficzny”, gdy przy danym znaku Glu M(dane) > M każdej z 10 przetasowanych instancji.
- Jest „niespecyficzny”, gdy średnie M(tasowane) ≥ M(dane) − 5 Hz.
- Pomiędzy wynik jest nierozstrzygnięty.
Raportowane jest też M dla wszystkich nóg.

Uruchom:  .venv/bin/python -I -B flymind/experiments/fj2_fly_arm/shuffle_six_legs.py [--smoke]
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from six_legs import network  # noqa: E402
from visual_path import shuffle  # noqa: E402

SEEDS = {-1.0: range(9_211_001, 9_211_011), 1.0: range(9_211_011, 9_211_021)}


def measure(spec, info):
    X = np.zeros(spec.W.shape[0])
    X[info["bristle"]] = 40.0
    r = SparseALIF(spec, ALIFParams(), None).run(X, 600)[100:].mean(0) * 1000
    return {leg: [round(float(r[sw].mean()), 2), round(float(r[st].mean()), 2)] for leg, (sw, st) in info["pools"].items()}


def main(argv):
    smoke = "--smoke" in argv
    out = os.path.join(HERE, "results", "shuffle_six_legs_smoke.jsonl" if smoke else "shuffle_six_legs.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        sys.exit(f"{out} istnieje — nie nadpisuję")
    with open(out, "w") as f:
        for glu in (-1.0, 1.0):
            spec, info = network(0.275, glu)
            f.write(json.dumps(dict(glu=glu, seed=None, kind="data", res=measure(spec, info))) + "\n")
            for sd in ([9_218_001] if smoke else SEEDS[glu]):
                t0 = time.time()
                sh = shuffle(spec, sd, equal_weight=True)
                ts = time.time() - t0
                r = measure(sh, info)
                f.write(json.dumps(dict(glu=glu, seed=sd, kind="shuffle", res=r, shuffle_s=round(ts))) + "\n")
                f.flush()
                print(f"Glu {glu:+.0f} seed {sd}: T2R wymach/podpór {r['T2R']}, T2L {r['T2L']} (tasowanie {ts:.0f} s)", flush=True)
                if smoke:
                    break
    rows = [json.loads(x) for x in open(out)]
    for glu in (-1.0, 1.0):
        M = lambda r: r["res"]["T2R"][0] - r["res"]["T2R"][1]  # noqa: E731
        d = [M(r) for r in rows if r["glu"] == glu and r["kind"] == "data"][0]
        s = [M(r) for r in rows if r["glu"] == glu and r["kind"] == "shuffle"]
        verdict = ("SPECYFICZNY" if s and all(d > x for x in s) else
                   "NIESPECYFICZNY" if s and np.mean(s) >= d - 5 else "NIEROZSTRZYGNIĘTY")
        print(f"Glu {glu:+.0f}: M(dane) {d:.1f} Hz, M(tasowane) {np.round(s, 1).tolist()} → {verdict}")


if __name__ == "__main__":
    main(sys.argv[1:])
