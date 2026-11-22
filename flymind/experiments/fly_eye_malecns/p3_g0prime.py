"""P3 G0′ (PREREG_P3.md, zmiana 22 XI): spadek straty modelu 000 (MaleCNS) vs K0 (flyvis od zera) przy tym samym k,
plus (tylko raport) DSI T4/T5 modelu 000 z ostatniego punktu kontrolnego. envs/flyvis."""
import json
import os
import sys

import h5py
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.environ["FLYVIS_ROOT_DIR"]
L = {n: np.array(h5py.File(f"{ROOT}/results/{p}/loss.h5", "r")["data"]) for n, p in
     (("m000", "p3_malecns/9200/000"), ("K0", "p3_ctrl/9300/000"))}
k = min(len(L["K0"]), len(L["m000"]))
drop = {n: float(1 - l[k - 1000:k].mean() / l[:1000].mean()) for n, l in L.items()}
res = dict(k=k, drop=drop, start={n: float(l[:1000].mean()) for n, l in L.items()}, end={n: float(l[k - 1000:k].mean()) for n, l in L.items()},
           G0prime_PASS=bool(k >= 10000 and drop["m000"] >= 0.5 * drop["K0"]), k_ok=k >= 10000)
try:
    import t1_transplant as T1
    from flyvis import NetworkView
    from flyvis.analysis.moving_bar_responses import angular_distance_to_known, direction_selectivity_index, preferred_direction
    net = NetworkView(f"{ROOT}/results/p3_malecns/9200/000").init_network(chkpt="recent")
    ds = T1.responses(net)
    dsi, dist = direction_selectivity_index(ds), angular_distance_to_known(preferred_direction(ds))
    out = {}
    for t in T1.T4 + T1.T5:
        i = int(np.where(dsi.cell_type.values == t)[0][0])
        out[t] = round(float(dsi.isel(neuron=i).sel(intensity=1 if t in T1.T4 else 0).squeeze()), 3)
    res["DSI_m000_recent"] = out
    res["vmax"] = float(np.nanmax(np.abs(ds.responses.values)))
except Exception as e:  # noqa: BLE001 — raport, nie bramka
    res["DSI_error"] = repr(e)[:300]
json.dump(res, open(os.path.join(HERE, "../../results/fly_eye_malecns_20261120/p3_g0prime.json"), "w"), indent=1)
print(json.dumps(res))
