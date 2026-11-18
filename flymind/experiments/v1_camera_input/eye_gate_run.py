"""Uruchomienie bramki: eye_gate_run.py data GLU OUT.npz | shuffle SEED OUT.npz. Zapis tylko w trybie „x”.
Zapisuje dla wybranych typów: R [komórki × warunek(S0, 60, 120, 240) × 12 bodźców × 2 połowy jednostek]."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eye_gate as G  # noqa: E402
import optic_slice as OS  # noqa: E402

KEEP = ["L1", "L2", "Mi1", "Tm3", "Tm1"] + [f"T4{s}" for s in "abcd"] + [f"T5{s}" for s in "abcd"]


def main():
    mode, out = sys.argv[1], sys.argv[-1]
    if "--lit" in sys.argv:                                   # r2: dynamika z literatury (eye_gate_lit.py)
        import eye_gate_lit
        eye_gate_lit.install()
        sys.argv.remove("--lit")
    units_data = [int(x) for x in os.environ.get("GATE_UNITS", "15502001-15502010").split("-")]
    units_data = list(range(units_data[0], units_data[1] + 1))
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    S = OS.build()
    if mode == "data":
        glu, units, shuf = float(sys.argv[2]), units_data, None
        G.check_pool(units, "data")
    else:
        shuf = int(sys.argv[2])
        G.check_pool([shuf], "shuffle")
        units = units_data[:4]
        S, done = G.shuffle_typed(S, shuf)
        glu = -1.0                                               # te same ziarna szumu co pierwsze 4 jednostki danych (pary)
    g, W = G.pick_g(S, units[:2])
    W = G.weights(S, S["n"], glu=glu, g=g)
    res = G.run_network(S, W, units)
    sel = np.where(np.isin(S["type"], KEEP))[0]
    h = len(units) // 2
    R = np.stack([np.stack([res[k][sel][:, :, :h].mean(2), res[k][sel][:, :, h:].mean(2)], -1) for k in ("S0",) + G.SPEEDS], 1)
    np.savez_compressed(open(out, "xb"), R=R.astype(np.float32), types=S["type"][sel], bodies=S["bodies"][sel], g=g, glu=glu,
                        units=np.array(units), shuffle_seed=-1 if shuf is None else shuf, swaps=0 if shuf is None else done)
    print("zapisano", out, R.shape, "g", g)


if __name__ == "__main__":
    main()
