"""Opcja 2 (flyvis, Lappalainen i in. 2024): ta sama bramka G2/G3 na gotowych modelach „flow/0000/000–049”.
Uruchamiać w envs/flyvis (FLYVIS_ROOT_DIR=data/flyvis). flyvis_gate.py N_MODELS OUT.json"""
import json
import os
import sys
import time

import numpy as np
from flyvis import NetworkView
from flyvis.analysis.moving_bar_responses import angular_distance_to_known, direction_selectivity_index, preferred_direction

T4 = [f"T4{s}" for s in "abcd"]; T5 = [f"T5{s}" for s in "abcd"]


def main(n, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    rows = []
    for k in range(int(n)):
        t0 = time.time()
        nv = NetworkView(f"flow/0000/{k:03d}")
        ds = nv.moving_edge_responses()
        dsi = direction_selectivity_index(ds)                     # średnia po prędkościach/szerokościach
        pd_ = preferred_direction(ds)
        dist = angular_distance_to_known(pd_)
        r = dict(model=k, s=round(time.time() - t0, 1))
        for t in T4 + T5:
            inten = 1 if t in T4 else 0
            i = int(np.where(dsi.cell_type.values == t)[0][0])
            r[f"DSI_{t}"] = float(dsi.isel(neuron=i).sel(intensity=inten).squeeze())
            j = int(np.where(dist.cell_type.values == t)[0][0])
            r[f"dist_{t}"] = float(np.degrees(dist.isel(neuron=j).squeeze()))   # flyvis już wybiera ON dla T4, OFF dla T5
        rows.append(r)
        print(r, flush=True)
    json.dump(rows, open(out, "x"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:3])
