"""Wycina z MaleCNS v1.0 (Janelia FlyEM, CC-BY 4.0) obwód bio2 (~300 neuronów) → bio2/circuit_bio2.json.
Dane: data/malecns/ (te same pliki co sim/extract_connectome.py).

Moduły:
  cx      EPG 46, PEN_a 20, PEN_b 22, Delta7 42, PFL3 24 (kompleks centralny). EPG dostają numer klina 0–15
          z kolejności pierścienia WYZNACZONEJ Z DANYCH: EPG z glomerulusa L_i łączą się najsilniej z R_(9−i)
          i R_(10−i), co daje pierścień R1–L8–R2–L7–…–R8–L1 (macierz EPG→EPG, 2026-10-23).
  dn      DNa01, DNa02, MDN, DNp01 (Giant Fiber), DNp09 — wszystkie z obu stron.
  loom    po N_LOOM neuronów LC4 i LPLC2 o najsilniejszym wejściu do DNp01 (z każdej strony).
  hs      HSN, HSE, HSS (płytka lobuli, ruch poziomy — kopia eferentna w Etapie 3).
  grip    noga T1-L jak w v1–v3 (sim/extract_connectome.py): 20 aferentów proprioceptywnych, 20 IN, 11 MN
          + płytka włoskowa nerwu ProLN (jedyna opisana w v1.0 dla T1-L).
Uruchom:  .venv/bin/python -I bio2/extract_bio2.py
"""
import json
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "malecns")
OUT = os.path.join(ROOT, "bio2", "circuit_bio2.json")
N_LOOM, N_IN = 12, 20
RING = ["R1", "L8", "R2", "L7", "R3", "L6", "R4", "L5", "R5", "L4", "R6", "L3", "R7", "L2", "R8", "L1"]
NT_SHORT = {"acetylcholine": "ACh", "gaba": "GABA", "glutamate": "Glu", "octopamine": "OA", "dopamine": "DA",
            "serotonin": "5HT", "histamine": "HA"}


def main():
    ann = pd.read_feather(os.path.join(DATA, "body-annotations-male-cns-v1.0-minconf-0.5.feather")).set_index("bodyId")
    nt = pd.read_feather(os.path.join(DATA, "body-neurotransmitters-male-cns-v1.0.feather")).set_index("body")
    w = pd.read_feather(os.path.join(DATA, "connectome-weights-male-cns-v1.0-minconf-0.5.feather"))

    sel = {}
    for t in ["EPG", "PEN_a(PEN1)", "PEN_b(PEN2)", "Delta7", "PFL3"]:
        sel.update({b: "cx" for b in ann.index[ann.type == t]})
    for t in ["DNa01", "DNa02", "MDN", "DNp01", "DNp09"]:
        sel.update({b: "dn" for b in ann.index[ann.type == t]})
    gf = ann.index[ann.type == "DNp01"]
    for t in ["LC4", "LPLC2"]:
        for side in "LR":
            ids = ann.index[(ann.type == t) & (ann.somaSide == side)]
            top = w[w.body_pre.isin(ids) & w.body_post.isin(gf)].groupby("body_pre").weight.sum().nlargest(N_LOOM)
            sel.update({b: "loom" for b in top.index})
    for t in ["HSN", "HSE", "HSS"]:
        sel.update({b: "hs" for b in ann.index[ann.type == t]})
    # chwyt T1-L (ta sama reguła co sim/extract_connectome.py)
    mn = ann[ann.type.isin(["Ti flexor MN", "Ti extensor MN", "ltm MN"]) & (ann.somaNeuromere == "T1")
             & (ann.somaSide == "L")]
    leg = (ann.superclass == "vnc_sensory") & (ann.entryNerve == "ProLN") & ((ann.rootSide == "L") | (ann.somaSide == "L"))
    sens = ann[leg & (ann["class"] == "mechanosensory_proprioceptive") & ann.subclass.isin(["campaniform sensilla", "leg"])]
    hp = ann[leg & (ann.subclass == "hair plate")]
    ws = w[w.weight >= 3]
    from_s = ws[ws.body_pre.isin(sens.index)].groupby("body_post").weight.sum()
    to_m = ws[ws.body_post.isin(mn.index)].groupby("body_pre").weight.sum()
    cand = from_s.index.intersection(to_m.index).difference(sens.index).difference(mn.index)
    ins = np.minimum(from_s[cand], to_m[cand]).nlargest(N_IN).index
    for ids in (sens.index, ins, mn.index, hp.index):
        sel.update({b: "grip" for b in ids})

    neurons = []
    mn_in = w[w.body_post.isin(mn.index)].groupby("body_post").weight.sum()
    for bid, module in sel.items():
        r = ann.loc[bid]
        ntc = nt.consensus_nt.get(bid)
        if ntc not in NT_SHORT:
            c = nt.celltype_predicted_nt.get(bid)
            ntc = c if c in NT_SHORT else ("glutamate" if "MN" in str(r.type) else "acetylcholine")
        n = dict(bodyId=int(bid), type=str(r.type), instance=str(r.instance), side=str(r.somaSide), module=module,
                 subclass=str(r.subclass), nt=NT_SHORT[ntc])
        if r.type == "EPG":
            g = re.search(r"_([LR]\d)$", str(r.instance)).group(1)
            n["glomerulus"], n["wedge"] = g, RING.index(g)
        if bid in mn_in.index:
            n["input_synapses"] = int(mn_in[bid])
        neurons.append(n)
    ids = list(sel)
    sub = w[w.body_pre.isin(ids) & w.body_post.isin(ids)]
    json.dump(dict(source="MaleCNS v1.0 flat-connectome minconf-0.5 (Janelia FlyEM, CC-BY 4.0)", ring=RING,
                   neurons=neurons, edges=[[int(a), int(b), int(c)] for a, b, c in sub[["body_pre", "body_post", "weight"]].values]),
              open(OUT, "w"))
    cnt = pd.Series([n["module"] for n in neurons]).value_counts().to_dict()
    print(f"neuronów: {len(neurons)} {cnt}, krawędzi: {len(sub)}, synaps: {int(sub.weight.sum())} → {OUT}")


if __name__ == "__main__":
    main()
