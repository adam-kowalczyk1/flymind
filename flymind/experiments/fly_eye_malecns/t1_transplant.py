"""T1 (PREREG_T0_T1.md): modele flyvis z liczbami synaps MaleCNS → czy T4/T5 liczą kierunek.
envs/flyvis (FLYVIS_ROOT_DIR=data/flyvis): t1_transplant.py MODE FIRST LAST OUT.json   MODE = orig | malecns | shuffle | shape | shape_shuffle
orig = liczby flyvis (ta sama droga liczenia — sprawdzian metody), malecns = zamiana wg T0, shuffle = kontrola: liczby MaleCNS
potasowane między przesunięciami w obrębie pary typów (suma pary ta sama; ziarno 24 103 000 + model)."""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import xarray as xr
from flyvis import NetworkView
from flyvis.analysis.moving_bar_responses import angular_distance_to_known, direction_selectivity_index, preferred_direction
from flyvis.datasets.moving_bar import MovingEdge

torch.set_num_threads(2)
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../results/fly_eye_malecns_20261120")
T4, T5 = [f"T4{s}" for s in "abcd"], [f"T5{s}" for s in "abcd"]
HYBRID = lambda t: t.startswith(("R", "CT1", "Am"))              # noqa: E731  bez danych MaleCNS → liczby flyvis zostają


def counts(mode, model):
    K = pd.read_csv(f"{RES}/flyvis_keys.csv")
    if mode == "orig":
        return K.n_syn.values, 0.0
    M = pd.read_csv(f"{RES}/malecns_keys.csv")
    J = K.merge(M, on=["source_type", "target_type", "du", "dv"], how="left", suffixes=("", "_m"))
    rep = ~(J.source_type.map(HYBRID) | J.target_type.map(HYBRID))
    n = np.where(rep, J.n_syn_m.fillna(0.0), J.n_syn).astype(float)
    if mode.startswith("shape"):
        for _, ix in J[rep].groupby(["source_type", "target_type"]).groups.items():
            ix = np.asarray(ix)
            sm = J.n_syn_m.fillna(0.0).values[ix].sum()
            n[ix] = J.n_syn.values[ix] if sm == 0 else J.n_syn_m.fillna(0.0).values[ix] * J.n_syn.values[ix].sum() / sm
    if mode.endswith("shuffle"):
        rng = np.random.default_rng(24103000 + model)
        for _, ix in J[rep].groupby(["source_type", "target_type"]).groups.items():
            ix = np.asarray(ix)
            n[ix] = n[rng.permutation(ix)]
    return n, float(rep.mean())


def responses(net, dt=1 / 200):
    ds = MovingEdge(offsets=(-10, 11), intensities=[0, 1], speeds=(2.4, 4.8, 9.7, 13, 19, 25), height=80,
                    post_pad_mode="continue", dt=dt, device="cpu", t_pre=1.0, t_post=1.0)
    ci = net.connectome.central_cells_index[:]
    resp = [np.take(r, ci, axis=-1) for _, r in net.stimulus_response(ds, dt, t_pre=1.0, t_fade_in=0.0, batch_size=4)]
    resp = np.concatenate(resp, axis=0)[None]
    types = [t.decode() if isinstance(t, bytes) else t for t in net.connectome.unique_cell_types[:]]
    return xr.Dataset({"responses": (["network_id", "sample", "frame", "neuron"], resp)}, attrs={"config": {"offsets": (-10, 11), "dt": dt}},
                      coords={"sample": np.arange(len(ds)), **{c: ("sample", ds.arg_df[c].values) for c in ds.arg_df.columns},
                              "cell_type": ("neuron", types), "time": ("frame", np.arange(resp.shape[2]) * dt - 1.0)})


def main(mode, first, last, out):
    rows = []
    for k in range(int(first), int(last) + 1):
        t0 = time.time()
        net = NetworkView(f"flow/0000/{k:03d}").init_network()
        n, frac = counts(mode, k)
        with torch.no_grad():
            net.edges_syn_count.data = torch.tensor(np.log(np.maximum(n, 1e-6)), dtype=net.edges_syn_count.dtype)
        ds = responses(net)
        vmax = float(np.nanmax(np.abs(ds.responses.values)))
        dsi, dist = direction_selectivity_index(ds), angular_distance_to_known(preferred_direction(ds))
        r = dict(model=k, mode=mode, frac_keys_replaced=frac, vmax=vmax, s=round(time.time() - t0, 1))
        for t in T4 + T5:
            i = int(np.where(dsi.cell_type.values == t)[0][0])
            r[f"DSI_{t}"] = float(dsi.isel(neuron=i).sel(intensity=1 if t in T4 else 0).squeeze())
            j = int(np.where(dist.cell_type.values == t)[0][0])
            r[f"dist_{t}"] = float(np.degrees(dist.isel(neuron=j).squeeze()))
        rows.append(r)
        print(json.dumps(r), flush=True)
        json.dump(rows, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:5])
