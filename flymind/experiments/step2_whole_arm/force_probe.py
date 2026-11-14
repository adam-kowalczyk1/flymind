"""Sprawdzenie, że pomiar siły ramię↔blat w lift_b.ForceWorld działa: ramię celowo dociskane do blatu (bez sieci, bez
bezpiecznika, tylko świat). Oczekiwane: siła > 0 i rośnie z głębokością celu. Wynik → force_probe_v1.json."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lift_b as L  # noqa: E402
import object_handling as oh  # noqa: E402

w = L.ForceWorld([oh.SETS["base"][0]], 1)
w.phase = "probe"
q = np.array(oh.OHCfg.home, float)
out = []
for dq in np.arange(0.0, 1.21, 0.1):
    w.fmax = {}
    for _ in range(100):
        w.step(np.r_[q[:1], q[1] + dq, q[2:5]], 0.0)
    out.append(dict(dq1=round(float(dq), 2), fmax_N=w.fmax.get("probe", 0.0), unwanted=dict(w.unwanted)))
    print(out[-1])
p = os.path.join(L.OUT, "..", "force_probe_v1.json")
with open(p, "x") as f:
    json.dump(out, f, indent=1)
