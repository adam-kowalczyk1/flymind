import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/admin/so101_fly_project/flymind/experiments/step3_wiring')
import nets
A = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide", "rootSide"])
ty = dict(zip(A.bodyId, A.type)); sc = dict(zip(A.bodyId, A.superclass)); side = dict(zip(A.bodyId, A.somaSide.fillna(A.rootSide))); sub = dict(zip(A.bodyId, A.subclass))
W = pd.read_feather(nets.visual_path.WEIGHTS)
pre_, post_, w = W.body_pre.values, W.body_post.values, W.weight.values
DNS = {"DNb05": None, "DNp07": None, "DNp11": None, "DNp01": None, "DNa02": None}
for t in DNS:
    ids = [int(b) for b in A.bodyId[A.type == t]]
    for b in ids:
        mi = post_ == b
        i = pd.DataFrame(dict(p=pre_[mi], w=w[mi])); i["t"] = i.p.map(ty); i["s"] = i.p.map(side); i["c"] = i.p.map(sc)
        vi = i[i.c == "visual_projection"].groupby(["t", "s"]).w.sum().sort_values(ascending=False).head(4)
        mo = pre_ == b
        o = pd.DataFrame(dict(q=post_[mo], w=w[mo])); o["c"] = o.q.map(sc); o["t"] = o.q.map(ty); o["sub"] = o.q.map(sub); o["s"] = o.q.map(side)
        mn = o[o.c == "vnc_motor"].groupby(["sub", "s", "t"]).w.sum().sort_values(ascending=False).head(6)
        print(f"== {t} {b} strona {side.get(b)} | wejście z oka (typ, strona oka): {dict(vi)}")
        print("   bezpośrednio do neuronów ruchowych (noga, strona, typ):", {k: int(v) for k, v in mn.items()})
