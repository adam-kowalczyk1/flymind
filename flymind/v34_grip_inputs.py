"""V3.4 — wejścia MN „chwytu” (bio2 grip: Ti flexor/extensor MN, ltm MN, T1 L) w CAŁYM connectomie MaleCNS.
Tylko analiza danych; circuit_bio2.json czytany jako tekst JSON (bez importu bio2). Znak: ACh +, GABA/Glu −, nieznany 0.
Uruchom: .venv/bin/python -I -B flymind/v34_grip_inputs.py"""
import json, os
import numpy as np, pandas as pd, pyarrow.dataset as ds
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "malecns") + os.sep
G = [n for n in json.load(open(os.path.join(ROOT, "bio2", "circuit_bio2.json")))["neurons"] if n["module"] == "grip"]
mn = {k: [n["bodyId"] for n in G if n["type"] == t] for k, t in (("flex", "Ti flexor MN"), ("ext", "Ti extensor MN"), ("ltm", "ltm MN"))}
a = pd.read_feather(D + "body-annotations-male-cns-v1.0-minconf-0.5.feather")[["bodyId", "type", "superclass", "subclass"]]
nt = pd.read_feather(D + "body-neurotransmitters-male-cns-v1.0.feather").set_index("body")
def sign(b):
    r = nt.reindex(b); x = r.ground_truth.where(r.ground_truth.notna() & (r.ground_truth != "unclear"), r.consensus_nt)
    x = x.where(x.notna() & (x != "unclear"), r.celltype_predicted_nt)
    return x.map({"acetylcholine": 1, "gaba": -1, "glutamate": -1}).fillna(0).values
W = ds.dataset(D + "connectome-weights-male-cns-v1.0-minconf-0.5.feather", format="ipc")
gids = {n["bodyId"] for n in G}
w = W.to_table(filter=ds.field("body_post").isin(sum(mn.values(), []))).to_pandas().merge(a.rename(columns={"bodyId": "body_pre"}), on="body_pre", how="left")
w["s"] = sign(w.body_pre.values) * w.weight
for k, ids in mn.items():
    d = w[w.body_post.isin(ids)]
    print(f"{k}: wejście {d.weight.sum()} syn; z podgrafu grip {100 * d[d.body_pre.isin(gids)].weight.sum() / d.weight.sum():.1f}%; "
          f"netto ze znakiem {d.s.sum():+.0f}; bez NT {d[d.s == 0].weight.sum()}; nadklasy {d.groupby('superclass').weight.sum().sort_values(ascending=False).head(4).to_dict()}")
sens = a[a.superclass == "vnc_sensory"].bodyId.astype(int).tolist()
pre = w.groupby(["body_pre", "body_post"]).s.sum().unstack(fill_value=0)
w2 = W.to_table(filter=ds.field("body_post").isin(pre.index.tolist()) & ds.field("body_pre").isin(sens)).to_pandas()
w2["s"] = sign(w2.body_pre.values) * w2.weight
M = w2.pivot_table(index="body_pre", columns="body_post", values="s", aggfunc="sum", fill_value=0)
T = pd.DataFrame(M.values @ pre.reindex(M.columns).values, index=M.index, columns=pre.columns)
st = a.set_index("bodyId").reindex(T.index).subclass
for k, v in mn.items():
    x = T[[b for b in v if b in T.columns]].sum(axis=1)
    print(f"2 skoki czucie→{k} (syn², znak): suma {x.sum():+.0f}; wg podklasy {x.groupby(st).sum().sort_values(key=abs, ascending=False).head(5).round(0).to_dict()}")
