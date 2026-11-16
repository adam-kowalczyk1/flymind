"""Krok 3 (tylko dane, bez symulacji): skąd pule MN stawów 1–4 dostają synapsy — podział wg superclass neuronu presynaptycznego
i udział neuronów obecnych w sieci „pre”. Uruchom: who_drives.py OUT.json"""
import json
import os
import sys

import pandas as pd
import pyarrow.dataset as ds

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402

JN = nets.JN


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    bodies, m = nets.bodies_for("pre")
    inb = set(bodies)
    a = m["a"].set_index("bodyId")
    ty = a.type
    W = ds.dataset(nets.visual_path.WEIGHTS, format="ipc")
    res = {}
    for j, (p, n) in JN.POOLS.items():
        for k, names in enumerate((p, n)):
            mn = [b for b in m["flb"] if ty[b] in names]
            d = W.to_table(filter=ds.field("body_post").isin(mn)).to_pandas()
            d["sc"] = d.body_pre.map(a.superclass).fillna("brak adnotacji")
            tot = int(d.weight.sum())
            by = (d.groupby("sc").weight.sum() / tot).sort_values(ascending=False).round(3)
            res[nets.NAMES[j][k]] = dict(n_mn=len(mn), syn_total=tot, frac_in_pre_net=round(float(d.weight[d.body_pre.isin(inb)].sum()) / tot, 3),
                                         by_superclass=by.head(6).to_dict())
            print(nets.NAMES[j][k].ljust(13), tot, "w sieci pre:", res[nets.NAMES[j][k]]["frac_in_pre_net"], by.head(5).to_dict(), flush=True)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
