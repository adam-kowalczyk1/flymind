"""Wycina z MaleCNS v1.0 (Janelia FlyEM, CC-BY 4.0) dwa obwody i zapisuje je do
sim/circuit_malecns.json (neurony + liczby synaps). Dane wejściowe: publiczny bucket
https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/
(pliki body-annotations…minconf-0.5, body-neurotransmitters…, connectome-weights…minconf-0.5)
pobrane do data/malecns/.

1. Pościg wzrokowy: wszystkie LC10a, AOTU019, AOTU025, DNa02 (obie strony).
2. Chwyt — przednia lewa noga (T1, L):
   - MN: Ti flexor MN, Ti extensor MN, ltm MN z neuromeru T1 po lewej;
   - czucie: neurony proprioceptywne nerwu ProLN po lewej o podklasie „campaniform sensilla”
     albo „leg” (w v1.0 tylko 2 opisano jako CS; „leg” to proprioceptory nogi bez podtypu);
   - interneurony premotoryczne: N_IN najsilniejszych ścieżek czucie→IN→MN
     (siła ścieżki = min(synapsy z czucia, synapsy do MN), połączenia ≥ 3 synapsy).
Uruchom:  .venv/bin/python -I sim/extract_connectome.py
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "malecns")
OUT = os.path.join(ROOT, "sim", "circuit_malecns.json")
N_IN = 20
NT_SHORT = {"acetylcholine": "ACh", "gaba": "GABA", "glutamate": "Glu"}


def main():
    ann = pd.read_feather(os.path.join(DATA, "body-annotations-male-cns-v1.0-minconf-0.5.feather")).set_index("bodyId")
    nt = pd.read_feather(os.path.join(DATA, "body-neurotransmitters-male-cns-v1.0.feather")).set_index("body")
    w = pd.read_feather(os.path.join(DATA, "connectome-weights-male-cns-v1.0-minconf-0.5.feather"))

    track = ann[ann.type.isin(["LC10a", "AOTU019", "AOTU025", "DNa02"])]
    mn = ann[ann.type.isin(["Ti flexor MN", "Ti extensor MN", "ltm MN"])
             & (ann.somaNeuromere == "T1") & (ann.somaSide == "L")]
    sens = ann[(ann.superclass == "vnc_sensory") & (ann.entryNerve == "ProLN")
               & ((ann.rootSide == "L") | (ann.somaSide == "L"))
               & (ann["class"] == "mechanosensory_proprioceptive")
               & ann.subclass.isin(["campaniform sensilla", "leg"])]

    ws = w[w.weight >= 3]
    from_s = ws[ws.body_pre.isin(sens.index)].groupby("body_post").weight.sum()
    to_m = ws[ws.body_post.isin(mn.index)].groupby("body_pre").weight.sum()
    cand = from_s.index.intersection(to_m.index).difference(sens.index).difference(mn.index)
    path = np.minimum(from_s[cand], to_m[cand]).sort_values(ascending=False)
    ins = ann.reindex(path.index[:N_IN])

    neurons = []
    for df, circuit in ((track, "track"), (sens, "grip"), (ins, "grip"), (mn, "grip")):
        for bid, r in df.iterrows():
            ntc = nt.consensus_nt.get(bid)
            if ntc not in NT_SHORT:            # MN „unclear”/brak → Glu (konsensus typu MN = glutaminian)
                ntc = nt.celltype_predicted_nt.get(bid) if nt.celltype_predicted_nt.get(bid) in NT_SHORT else "glutamate"
            neurons.append(dict(bodyId=int(bid), type=str(r.type), side=str(r.somaSide), circuit=circuit,
                                subclass=str(r.subclass), nt=NT_SHORT[ntc]))
    ids = [n["bodyId"] for n in neurons]
    sub = w[w.body_pre.isin(ids) & w.body_post.isin(ids)]
    # rozmiar MN ~ liczba synaps wejściowych (Lesser i in. 2024: r = 0,94 z powierzchnią MN)
    mn_in = w[w.body_post.isin(mn.index)].groupby("body_post").weight.sum()
    for n in neurons:
        if n["bodyId"] in mn_in.index:
            n["input_synapses"] = int(mn_in[n["bodyId"]])
    out = dict(source="MaleCNS v1.0 flat-connectome minconf-0.5 (Janelia FlyEM, CC-BY 4.0)",
               neurons=neurons,
               edges=[[int(a), int(b), int(c)] for a, b, c in sub[["body_pre", "body_post", "weight"]].values],
               in_path_strength={str(k): int(v) for k, v in path[:N_IN].items()})
    with open(OUT, "w") as f:
        json.dump(out, f)
    print(f"neuronów: {len(neurons)} (track {len(track)}, czucie {len(sens)}, IN {len(ins)}, MN {len(mn)}), "
          f"krawędzi: {len(sub)}, synaps: {sub.weight.sum()} → {OUT}")


if __name__ == "__main__":
    main()
