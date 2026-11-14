"""Krok 2(a): dane MaleCNS do wyboru drugiej nogi i przypisania pul MN do stawów. Tylko odczyt danych, bez symulacji.

Dla nóg T1 L, T2 L, T2 R, T3 L: pule MN (podklasa fl/ml/hl, jak six_legs.py — w T1 MN biodra wychodzą innymi nerwami),
rozmiary obwodów (leg_circuit.select), wspólne interneurony z T2 L, synapsy między obwodami (oba kierunki), wejście
DNa02 L/R i DNp09 L/R do obwodu, oraz wejście z receptorów dotyku (szczecinki) każdej nogi do jej pul MN.
  .venv/bin/python -I -B flymind/experiments/step2_whole_arm/leg_data.py OUT.json
"""
import json
import os
import sys

import pandas as pd
import pyarrow.dataset as ds

FLY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, FLY)
from leg_circuit import select  # noqa: E402
from visual_path import ANN, WEIGHTS  # noqa: E402

LEGS = (("T1", "L"), ("T2", "L"), ("T2", "R"), ("T3", "L"))
SUB = {"T1": "fl", "T2": "ml", "T3": "hl"}


def main(out):
    a = pd.read_feather(ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide"])
    W = ds.dataset(WEIGHTS, format="ipc")
    dn = {f"{t}_{s}": sorted(a.bodyId[(a.type == t) & (a.somaSide == s)].astype(int)) for t in ("DNa02", "DNp09")
          for s in ("L", "R")}
    rep, circ = dict(dn_bodies=dn), {}
    for seg, side in LEGS:
        b, g, r = select(seg, side)
        m = a[(a.superclass == "vnc_motor") & (a.subclass == SUB[seg]) & (a.somaSide == side)]
        mn = {k: sorted(v.bodyId.astype(int)) for k, v in m.groupby(m.type.fillna("NA"))}
        allb = set(b) | {x for v in mn.values() for x in v}
        circ[seg + side] = dict(bodies=allb, IN=set(g["IN"]), bristle=g["sensory"].get("mechanosensory bristle", []), mn=mn)
        e_in = W.to_table(filter=ds.field("body_post").isin(sorted(allb))).to_pandas()
        br = set(g["sensory"].get("mechanosensory bristle", []))
        rep[seg + side] = dict(
            circuit_sizes=r["sizes"], mn_by_subclass={k: len(v) for k, v in mn.items()},
            mn_leg_nerve_only=int(sum(len(v) for v in g["MN"].values())),
            dn_in={k: int(e_in[e_in.body_pre.isin(v)].weight.sum()) for k, v in dn.items()},
            bristle_to_mn_direct={k: int(e_in[e_in.body_pre.isin(br) & e_in.body_post.isin(v)].weight.sum())
                                  for k, v in mn.items()})
    base = circ["T2L"]
    for k, c in circ.items():
        if k == "T2L":
            continue
        e = W.to_table(filter=ds.field("body_pre").isin(sorted(base["bodies"]))).to_pandas()
        e2 = W.to_table(filter=ds.field("body_pre").isin(sorted(c["bodies"]))).to_pandas()
        rep[k]["vs_T2L"] = dict(shared_bodies=len(base["bodies"] & c["bodies"]), shared_IN=len(base["IN"] & c["IN"]),
                                syn_T2L_to_this=int(e[e.body_post.isin(c["bodies"] - base["bodies"])].weight.sum()),
                                syn_this_to_T2L=int(e2[e2.body_post.isin(base["bodies"] - c["bodies"])].weight.sum()),
                                syn_T2L_bristle_to_this_MN=int(e[e.body_pre.isin(base["bristle"]) & e.body_post.isin(
                                    {x for v in c["mn"].values() for x in v})].weight.sum()))
    with open(out, "x") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
