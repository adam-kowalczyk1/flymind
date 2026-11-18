"""flymind/v61_toy.py — V6.1 protocol §2 reference: toy relay (loop_v2.toy_relay, unchanged; MODEL control with no intermediate
layer) under E1 (unilateral 4–12 mV) and E6 (symmetric I0 ± δ/2), default ALIF σ 2, 4 reps (seeds 8 411 001–004). No mujoco.
Run: .venv/bin/python -I -B flymind/v61_toy.py --out flymind/results/v61/toy
"""
import argparse
import json
import os
import sys

import numpy as np

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("run with python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import loop_v2 as L2  # noqa: E402
import v5v41 as V  # noqa: E402
import v5v41_e6 as E6  # noqa: E402
from alif import ALIFParams  # noqa: E402
from v6 import LV, REPS  # noqa: E402


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec, idx, _, _ = V.make_net("DATA", None)
    toy, tidx, rep = L2.toy_relay(spec, idx)
    tidx.update(mid_L=np.array([], int), mid_R=np.array([], int))
    P = ALIFParams(noise=2.0)
    e1 = np.zeros((len(LV), 2, REPS, 100, 6), np.int16)
    for i, x in enumerate(LV):
        for si, side in enumerate("LR"):
            for r in range(REPS):
                e1[i, si, r] = V.simulate(toy, tidx, side, dict(I=float(x), step_ms=1000), V.NOISE_SEEDS[r], P)["counts"]
    e6 = np.zeros((len(E6.I0S), len(E6.DELTAS), REPS, 100, 6), np.int16)
    for i, I0 in enumerate(E6.I0S):
        for j, dl in enumerate(E6.DELTAS):
            IL, IR = I0 + dl / 2, I0 - dl / 2
            for r in range(REPS):
                e6[i, j, r] = V.simulate(toy, tidx, "L", dict(I=IL, step_ms=1000, contra_frac=IR / IL), V.NOISE_SEEDS[r], P)["counts"]
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "toy.npz"), "xb") as f:
        np.savez_compressed(f, E1_counts=e1, E1_levels=np.array(LV), E6_counts=e6, I0=np.array(E6.I0S), deltas=np.array(E6.DELTAS),
                            n_pop=np.array([len(tidx["in_L"]), len(tidx["in_R"]), 1, 1, 1, 1]))
    with open(os.path.join(a.out, "toy_report.json"), "x") as f:
        json.dump(dict(rep, noise_seeds=V.NOISE_SEEDS[:REPS]), f, indent=1)
    print("toy relay done", rep)


if __name__ == "__main__":
    main()
