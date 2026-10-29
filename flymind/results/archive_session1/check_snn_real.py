import json, sys
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np, pandas as pd
from connectome import load_edges, ConnectomeError
from snn_interface import build, ModelEdge, ModelParams, assign_nt
D = "/Users/admin/so101_fly_project/data/malecns/"
c = json.load(open("/Users/admin/so101_fly_project/bio2/circuit_bio2.json"))
nt = pd.read_feather(D + "body-neurotransmitters-male-cns-v1.0.feather")
allids = [n["bodyId"] for n in c["neurons"]]
try:
    assign_nt(allids, nt)
except ConnectomeError as e:
    print("pełny podzbiór bio2 (272):", e)
unclear = [n for n in c["neurons"] if nt.set_index("body").loc[n["bodyId"], ["ground_truth", "consensus_nt", "celltype_predicted_nt"]].isin(["unclear"]).sum() + nt.set_index("body").loc[n["bodyId"], ["ground_truth"]].isna().sum() == 3]
print("neurony bez przekaźnika w danych:", [(n["bodyId"], n["module"], n["type"], "bio2 przypisało:", n["nt"]) for n in unclear])
# podzbiór mózgu jak w brain.py (moduły cx, dn, loom, hs)
N = [n for n in c["neurons"] if n["module"] in ("cx", "dn", "loom", "hs")]
ids = [n["bodyId"] for n in N]
e, rep = load_edges(D + "connectome-weights-male-cns-v1.0-minconf-0.5.feather", bodies=ids)
ty = {n["bodyId"]: (n["type"], n["side"]) for n in N}
pick = lambda t, s: [b for b, v in ty.items() if v == (t, s)]
# krawędzie modelowe = to, co robi brain.py:111 (kopia PFL3→DNa02 krzyżowo na DNa01)
me = []
for sp, so in (("L", "R"), ("R", "L")):
    dna02, dna01 = pick("DNa02", so)[0], pick("DNa01", so)[0]
    for p in pick("PFL3", sp):
        w = e.weight[(e.body_pre == p) & (e.body_post == dna02)].sum()
        if w:
            me.append(ModelEdge(p, dna01, float(w), "bio2 brain.py:111 — kopia PFL3→DNa02 na DNa01; w danych 0 synaps PFL3→DNa01"))
full = build(e, ids, nt, ModelParams(J0=0.3), model_edges=me)
data_only = build(e, ids, nt, ModelParams(J0=0.3), model_edges=me, include_model=False)
print(json.dumps(full.report, ensure_ascii=False, indent=1))
nt_b2 = {n["bodyId"]: n["nt"] for n in N}
short = {"acetylcholine": "ACh", "gaba": "GABA", "glutamate": "Glu"}
diff = [(b, nt_b2[b], short.get(x, x), s) for b, x, s in full.nt.itertuples(index=False) if short.get(x, x) != nt_b2[b]]
print("różnice przekaźnika vs circuit_bio2.json:", diff)
k = full.bodies.tolist()
for side in "LR":
    j = k.index(pick("DNa01", side)[0])
    print(f"DNa01_{side}: wejście |W| dane {np.abs(full.W_data[j]).sum():.1f} mV, model {np.abs(full.W_model[j]).sum():.1f} mV "
          f"→ udział modelu {np.abs(full.W_model[j]).sum() / np.abs(full.W[j]).sum():.0%}")
print("W_sha256 dane+model", full.report["W_sha256"][:12], "tylko dane", data_only.report["W_sha256"][:12])
