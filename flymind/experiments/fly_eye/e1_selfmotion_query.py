"""E1 — odczyt danych (bez symulacji): czy w MaleCNS sygnał o WŁASNYM ruchu (neurony wstępujące z brzusznego zwoju, czucie położenia
nogi, neurony odśrodkowe do płata wzrokowego) dochodzi do detektorów zbliżania LPLC2/LPLC4 albo do ich neuronów zstępujących (DN).
Odpowiada na decyzję Adama „1” (17 XI). .venv: e1_selfmotion_query.py OUT.json"""
import json
import os
import sys

import numpy as np
import pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "malecns")
VPN = ("LPLC2", "LPLC4")
ASC = {"ascending_neuron", "sensory_ascending", "efferent_ascending"}      # sygnał z ciała (brzuszny zwój) w górę
OL = {"ol_intrinsic", "visual_projection", "ol_sensory", "visual_projection_tbc"}


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    a = pd.read_feather(os.path.join(D, "body-annotations-male-cns-v1.0-minconf-0.5.feather"),
                        columns=["bodyId", "type", "superclass", "class", "somaSide", "somaNeuromere", "subclass"]).set_index("bodyId")
    w = pd.read_feather(os.path.join(D, "connectome-weights-male-cns-v1.0-minconf-0.5.feather"))
    nt = pd.read_feather(os.path.join(D, "body-neurotransmitters-male-cns-v1.0.feather"),
                         columns=["body", "celltype_predicted_nt"]).set_index("body").celltype_predicted_nt
    sc, ty = a.superclass, a.type
    w = w.assign(sc_pre=w.body_pre.map(sc), sc_post=w.body_post.map(sc), ty_pre=w.body_pre.map(ty), ty_post=w.body_post.map(ty))
    tin = w.groupby("body_post").weight.sum()                                  # wszystkie wejścia każdej komórki

    def top(df, by, n=12):
        g = df.groupby(by).weight.sum().sort_values(ascending=False)
        return {str(k): int(v) for k, v in g.head(n).items()}

    res = {}
    # czucie mechaniczne przedniej nogi: wchodzi nerwem nogi przedniej ProLN (somaNeuromere czuciowych jest puste w danych),
    # klasy mechanosensory + mechanosensory_proprioceptive (struny, czujki naprężeń, płytki włosowe), obie strony
    a["entryNerve"] = pd.read_feather(os.path.join(D, "body-annotations-male-cns-v1.0-minconf-0.5.feather"), columns=["entryNerve"]).entryNerve.values
    prop = set(a.index[(a.entryNerve == "ProLN") & a["class"].isin(["mechanosensory", "mechanosensory_proprioceptive"])])
    res["T1_proprio_n"] = len(prop)
    asc_ids = set(a.index[a.superclass.isin(ASC)])
    # ile wejścia każdego neuronu wstępującego pochodzi z proprioceptorów T1 (1 i 2 kroki)
    e = w[w.body_post.isin(asc_ids)]
    p1 = e[e.body_pre.isin(prop)].groupby("body_post").weight.sum()
    mid = w[w.body_pre.isin(prop)].groupby("body_post").weight.sum()
    mid = set(mid[mid >= 20].index) - asc_ids                                 # pośrednicy z ≥ 20 synapsami od proprioceptorów T1
    p2 = e[e.body_pre.isin(mid)].groupby("body_post").weight.sum()
    for V in VPN:
        cells = set(a.index[(a.type == V) & (a.somaSide == "R")])
        inn = w[w.body_post.isin(cells)]
        tot = float(inn.weight.sum())
        r = dict(cells=len(cells), in_total=int(tot),
                 in_by_superclass={k: round(v / tot, 4) for k, v in inn.groupby("sc_pre").weight.sum().sort_values(ascending=False).items()},
                 in_nonOL_types=top(inn[~inn.sc_pre.isin(OL)], "ty_pre"),
                 in_ascending=top(inn[inn.sc_pre.isin(ASC)], "ty_pre"))
        # 2 kroki: wstępujące → X → komórki V
        x = inn.groupby("body_pre").weight.sum()
        xin = w[w.body_post.isin(set(x.index)) & w.body_pre.isin(asc_ids)]
        # udział wejścia wstępującego w wejściu pośrednika × jego synapsy do V (przybliżenie siły drogi)
        frac = xin.groupby("body_post").weight.sum() / tin.reindex(xin.body_post.unique())
        r["in_2hop_via_asc_syn_weighted"] = round(float((frac * x.reindex(frac.index)).sum()) / tot, 5)
        r["in_2hop_top_mediators"] = {f"{ty.get(b)}:{b}": dict(frac_asc=round(float(frac[b]), 3), syn_to_V=int(x[b]))
                                      for b in (frac * x.reindex(frac.index)).sort_values(ascending=False).head(6).index}
        # neurony zstępujące z ≥ 100 synapsami od V (ta sama reguła jak w3_explore_dose.py)
        o = w[w.body_pre.isin(cells) & (w.sc_post == "descending_neuron")].groupby("body_post").weight.sum()
        dns = o[o >= 100]
        r["DN"] = {}
        for b, s in dns.sort_values(ascending=False).items():
            di = w[w.body_post == b]; dt = float(di.weight.sum())
            asc = di[di.sc_pre.isin(ASC)]
            # wstępujące niosące czucie nogi T1 (1 lub 2 kroki)
            prop_asc = asc[asc.body_pre.isin(set(p1.index) | set(p2.index))]
            r["DN"][f"{ty.get(b)}:{b}"] = dict(
                syn_from_V=int(s), frac_of_DN_input_from_V=round(s / dt, 4), DN_in_total=int(dt),
                frac_from_ascending=round(asc.weight.sum() / dt, 4), ascending_top=top(asc, "ty_pre", 6),
                ascending_nt={str(k): int(v) for k, v in asc.groupby(asc.body_pre.map(nt)).weight.sum().items()},
                frac_from_T1prop_ascending=round(prop_asc.weight.sum() / dt, 4),
                T1prop_ascending_top=top(prop_asc, "ty_pre", 6))
        res[V] = r
    json.dump(res, open(out, "x"), indent=1, default=str)
    print(json.dumps(res, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main(sys.argv[1])
