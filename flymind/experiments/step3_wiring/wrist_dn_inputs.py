"""Krok 5 (tylko dane): co pobudza neurony zstępujące (DN), które bezpośrednio łączą się z pulami stępu nogi T1 L.
Dla każdego typu DN: liczba neuronów, synapsy na pule stępu, przekaźnik, skład wejścia wg superclass i 8 największych typów
wejściowych (z superclass). Uruchom: wrist_dn_inputs.py OUT.json"""
import json
import os
import sys

import pandas as pd
import pyarrow.dataset as ds

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nets  # noqa: E402

DNS = ["DNge078", "DNp07", "DNge012", "DNb06", "DNge020", "DNg37", "DNge077", "DNge028", "DNge003", "DNge063", "DNg69"]


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    vp = nets.visual_path
    a = pd.read_feather(vp.ANN, columns=["bodyId", "type", "superclass", "class", "somaSide"]).set_index("bodyId")
    nt = pd.read_feather(vp.NTS)[["body", "consensus_nt"]].set_index("body").consensus_nt
    _, m = nets.bodies_for("pre")
    ty = a.type
    ta = {"lev": [b for b in m["flb"] if ty[b] == "Ta levator MN"], "dep": [b for b in m["flb"] if ty[b] == "Ta depressor MN"]}
    W = ds.dataset(vp.WEIGHTS, format="ipc")
    res = {}
    for dn in DNS:
        ids = [int(b) for b in a.index[a.type == dn]]
        to_ta = {k: int(W.to_table(filter=ds.field("body_pre").isin(ids) & ds.field("body_post").isin(v)).to_pandas().weight.sum()) for k, v in ta.items()}
        d = W.to_table(filter=ds.field("body_post").isin(ids)).to_pandas()
        tot = int(d.weight.sum())
        d["sc"] = d.body_pre.map(a.superclass).fillna("brak")
        d["ty"] = d.body_pre.map(a.type).fillna("brak")
        by_sc = (d.groupby("sc").weight.sum() / tot).sort_values(ascending=False).round(3).head(6).to_dict()
        g = d.groupby(["ty", "sc"]).weight.sum().sort_values(ascending=False).head(8)
        res[dn] = dict(n=len(ids), sides=[str(a.somaSide.get(b)) for b in ids], nt=sorted({str(nt.get(b)) for b in ids}), syn_to_Ta=to_ta,
                       input_syn=tot, input_by_superclass=by_sc, top_input_types=[dict(type=k[0], superclass=k[1], syn=int(v), frac=round(v / tot, 3)) for k, v in g.items()])
        print(f"{dn:8s} n={len(ids)} {res[dn]['nt']} → Ta lev {to_ta['lev']}, dep {to_ta['dep']} | wejście {tot}: {by_sc}")
        print("         ", [(t["type"], t["superclass"][:12], t["frac"]) for t in res[dn]["top_input_types"][:7]])
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
