"""Krok 5 (tylko dane, bez symulacji): skąd pule stępu nogi T1 L (Ta levator / Ta depressor = „nadgarstek”) dostają wejście
i jakie NATURALNE czucie do nich prowadzi w całym MaleCNS.
A) najwięksi bezpośredni partnerzy presynaptyczni (typ, klasa, przekaźnik, czy są w sieci „pre”);
B) dla każdej grupy neuronów czuciowych w całym zbiorze (nerw wejścia × podklasa × typ): siła drogi 2-krokowej
   czucie → interneuron → MN stępu, ze znakiem interneuronu (ACh +, GABA −, Glu ± wg wariantu), oraz synapsy bezpośrednie;
C) neurony zstępujące (z mózgu) z bezpośrednim wejściem na pule stępu.
Uruchom: wrist_screen.py OUT.json"""
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402

JN = nets.JN
SENS = ("vnc_sensory", "vnc_sensory_tbc", "sensory_ascending", "sensory_ascending_tbc", "sensory_descending")


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    vp = nets.visual_path
    a = pd.read_feather(vp.ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide", "rootSide", "entryNerve"]).set_index("bodyId")
    nt = pd.read_feather(vp.NTS)[["body", "consensus_nt"]].set_index("body").consensus_nt
    bodies, m = nets.bodies_for("pre")
    inb = set(bodies)
    W = ds.dataset(vp.WEIGHTS, format="ipc")
    ty = a.type
    res = {}
    for name, types in (("Ta levator", ("Ta levator MN",)), ("Ta depressor", ("Ta depressor MN",))):
        mn = [b for b in m["flb"] if ty[b] in types]
        d1 = W.to_table(filter=ds.field("body_post").isin(mn)).to_pandas()
        pre = d1.groupby("body_pre").weight.sum().sort_values(ascending=False)
        tot = int(pre.sum())
        top = [dict(body=int(b), syn=int(w), frac=round(w / tot, 3), type=str(ty.get(b)), superclass=str(a.superclass.get(b)),
                    nt=str(nt.get(b)), side=str(a.somaSide.get(b)), in_pre_net=bool(int(b) in inb)) for b, w in pre.head(25).items()]
        # C: zstępujące bezpośrednio
        dn = pre[[b for b in pre.index if a.superclass.get(b) == "descending_neuron"]]
        dn_types = dn.groupby([ty.get(b) for b in dn.index]).sum().sort_values(ascending=False).head(12)
        # B: drogi 2-krokowe od wszystkich neuronów czuciowych
        p1 = [int(b) for b, w in pre.items() if w >= 5]
        d2 = W.to_table(filter=ds.field("body_post").isin(p1) & (ds.field("weight") >= 3)).to_pandas()
        d2 = d2[d2.body_pre.map(a.superclass).isin(SENS)]
        wmn = pre / tot                                            # udział interneuronu w wejściu puli
        rows = {}
        for glu in (-1.0, 1.0):
            sg = {"acetylcholine": 1.0, "gaba": -1.0, "glutamate": glu}
            s_i = pd.Series({b: sg.get(str(nt.get(b)), 0.0) for b in p1})
            d2["eff"] = d2.weight * d2.body_post.map(s_i) * d2.body_post.map(wmn)
            key = d2.body_pre.map(lambda b: f"{a.entryNerve.get(b)}|{a.rootSide.get(b)}|{a.subclass.get(b)}|{ty.get(b)}")
            g = d2.groupby(key).agg(eff=("eff", "sum"), syn=("weight", "sum"), n=("body_pre", "nunique")).sort_values("eff", ascending=False)
            rows[f"glu{glu:+.0f}"] = dict(top_exc=[dict(group=k, eff=round(float(r.eff), 2), syn=int(r.syn), n_sens=int(r.n)) for k, r in g.head(12).iterrows()],
                                         top_inh=[dict(group=k, eff=round(float(r.eff), 2), syn=int(r.syn), n_sens=int(r.n)) for k, r in g.tail(6).iterrows()])
        direct = d1[d1.body_pre.map(a.superclass).isin(SENS)]
        dkey = direct.body_pre.map(lambda b: f"{a.entryNerve.get(b)}|{a.rootSide.get(b)}|{a.subclass.get(b)}|{ty.get(b)}")
        res[name] = dict(n_mn=len(mn), mn_bodies=[int(b) for b in mn], syn_total=tot, n_partners_ge5=len(p1), top_partners=top,
                         descending_direct=dict(syn=int(dn.sum()), frac=round(float(dn.sum()) / tot, 3), top_types={str(k): int(v) for k, v in dn_types.items()}),
                         sensory_direct={str(k): int(v) for k, v in direct.groupby(dkey).weight.sum().sort_values(ascending=False).head(8).items()},
                         sensory_2hop=rows)
        print(f"== {name}: {len(mn)} MN, {tot} synaps wejściowych, partnerów ≥5 syn: {len(p1)}")
        print("  najwięksi partnerzy:", [(t["type"], t["superclass"][:10], t["nt"][:5], t["syn"], "w sieci" if t["in_pre_net"] else "POZA") for t in top[:10]])
        print("  zstępujące bezpośrednio:", res[name]["descending_direct"])
        print("  czucie bezpośrednio:", res[name]["sensory_direct"])
        for g_ in ("glu+1", "glu-1"):
            print(f"  czucie 2-krokowo ({g_}) pobudzające:", [(r["group"], r["eff"], r["n_sens"]) for r in rows[g_]["top_exc"][:8]])
            print(f"  czucie 2-krokowo ({g_}) hamujące:", [(r["group"], r["eff"]) for r in rows[g_]["top_inh"][-4:]])
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
