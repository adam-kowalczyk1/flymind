"""Krok 6 (punkt 3, tylko dane, bez symulacji): które zstępujące neurony z mózgu łączą się z pulami nogi T1 L
i dostają wejście z RECEPTORÓW (czucie: szczecinki, czujniki, wzrok), a nie tylko z innych neuronów mózgu.
Wejście czuciowe = udział synaps od superclass czuciowych (sensory_*, cb_sensory, visual) do neuronu zstępującego,
policzony w dwóch krokach (receptor → interneuron → DN) i bezpośrednio.
Wynik: ranking DN według synaps na pule nogi T1 L (fl, L), z ich udziałem wejścia czuciowego.
Uruchom: brain_leg_search.py OUT.json"""
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402

SENS = {"vnc_sensory", "vnc_sensory_tbc", "sensory_ascending", "sensory_ascending_tbc", "sensory_descending",
        "cb_sensory", "visual_projection", "visual_neuron", "optic_lobe_sensory", "sensory"}


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    vp = nets.visual_path
    a = pd.read_feather(vp.ANN, columns=["bodyId", "type", "superclass", "somaSide"]).set_index("bodyId")
    nt = pd.read_feather(vp.NTS)[["body", "consensus_nt"]].set_index("body").consensus_nt
    _, m = nets.bodies_for("pre")
    W = ds.dataset(vp.WEIGHTS, format="ipc")
    pools_mn = [int(b) for b in m["flb"]]
    d_mn = W.to_table(filter=ds.field("body_post").isin(pools_mn)).to_pandas()
    dn_ids = sorted({int(b) for b in d_mn.body_pre if a.superclass.get(b) == "descending_neuron"})
    to_pool = d_mn[d_mn.body_pre.isin(dn_ids)].groupby("body_pre").weight.sum()
    d_in = W.to_table(filter=ds.field("body_post").isin(dn_ids)).to_pandas()
    d_in["pre_sc"] = d_in.body_pre.map(a.superclass).fillna("brak")
    tot_in = d_in.groupby("body_post").weight.sum()
    sens_direct = d_in[d_in.pre_sc.isin(SENS)].groupby("body_post").weight.sum()
    rows = []
    for dn in dn_ids:
        t = int(tot_in.get(dn, 0))
        s = int(sens_direct.get(dn, 0))
        rows.append(dict(body=dn, type=str(a.type.get(dn)), side=str(a.somaSide.get(dn)), nt=str(nt.get(dn)),
                         syn_to_leg_pools=int(to_pool.get(dn, 0)), syn_input=t, sens_direct_syn=s,
                         sens_direct_frac=round(s / t, 3) if t else 0.0))
    df = pd.DataFrame(rows).sort_values("syn_to_leg_pools", ascending=False)
    df_sens = df[df.sens_direct_syn >= 5].sort_values("syn_to_leg_pools", ascending=False)
    res = dict(n_dn_to_pools=len(dn_ids), n_dn_with_direct_sensory_ge5=int(len(df_sens)),
               top_all=df.head(20).to_dict("records"), top_sensory=df_sens.head(20).to_dict("records"))
    print("zstępujące neurony łączące się z pulami nogi T1 L:", len(dn_ids))
    print("z bezpośrednim wejściem czuciowym (≥5 syn):", len(df_sens))
    print(df_sens.head(12).to_string(index=False))
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main(sys.argv[1])
