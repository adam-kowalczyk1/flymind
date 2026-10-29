import json, sys, time
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import pandas as pd
from connectome import load_edges, map_populations, direction
D = "/Users/admin/so101_fly_project/data/malecns/"
W = D + "connectome-weights-male-cns-v1.0-minconf-0.5.feather"
c = json.load(open("/Users/admin/so101_fly_project/bio2/circuit_bio2.json"))
ids = [n["bodyId"] for n in c["neurons"]]
t0 = time.perf_counter()
df, rep = load_edges(W, bodies=ids)
print("load s", round(time.perf_counter() - t0, 1)); print(json.dumps({k: v for k, v in rep.items() if k != "provenance"}, default=str))
src = {(a, b): w for a, b, w in df.itertuples(index=False)}
js = {(a, b): w for a, b, w in c["edges"]}
print("circuit_bio2.json vs source: same keys", src.keys() == js.keys(), "weights equal", all(src[k] == js[k] for k in js if k in src), len(src), len(js))
ann = pd.read_feather(D + "body-annotations-male-cns-v1.0-minconf-0.5.feather", columns=["bodyId", "type", "somaSide"])
spec = {f"{t}_{s}": dict(type=t, somaSide=s) for t in ("DNa01", "DNa02", "PFL3") for s in "LR"}
pops, prep = map_populations(ann, spec)
print("pops", prep["sizes"])
allp = [b for v in pops.values() for b in v]
e2, _ = load_edges(W, bodies=allp)
for s, o in (("L", "R"), ("R", "L"), ("L", "L"), ("R", "R")):
    print(f"PFL3_{s}->DNa02_{o}", direction(e2, pops[f"PFL3_{s}"], pops[f"DNa02_{o}"]), f"PFL3_{s}->DNa01_{o}", direction(e2, pops[f"PFL3_{s}"], pops[f"DNa01_{o}"]))
# all inputs to DNa01 in the full connectome (top types)
import pyarrow.dataset as ds, pyarrow.compute as pc, pyarrow as pa
dn1 = pa.array([int(b) for k in ("DNa01_L", "DNa01_R") for b in pops[k]], pa.int64())
inp = ds.dataset(W, format="ipc").to_table(filter=pc.field("body_post").isin(dn1)).to_pandas()
inp = inp.merge(ann.rename(columns={"bodyId": "body_pre"}), on="body_pre", how="left")
print("DNa01 total input synapses", int(inp.weight.sum()), "top pre types:", inp.groupby("type").weight.sum().nlargest(8).to_dict())
