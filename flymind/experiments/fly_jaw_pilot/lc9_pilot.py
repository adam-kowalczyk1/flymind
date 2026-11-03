"""Pilot (exploratory, no seeds, noise 0): LC9 -> intermediates (>=5 from LC9 and >=5 to DNp09) -> DNp09; drive LC9 L / R / both."""
import sys
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np, pandas as pd, pyarrow.dataset as ds
from alif import ALIFParams
from alif_sparse import SparseALIF
from connectome import load_edges
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build
from visual_path import ANN, NTS, WEIGHTS

DN = {"L": 10783, "R": 11177}
a = pd.read_feather(ANN, columns=["bodyId", "type", "somaSide"])
lc = a[a.type == "LC9"]; L, R = sorted(lc.bodyId[lc.somaSide == "L"].astype(int)), sorted(lc.bodyId[lc.somaSide == "R"].astype(int))
W = ds.dataset(WEIGHTS, format="ipc")
out = W.to_table(filter=ds.field("body_pre").isin(L + R)).to_pandas().groupby("body_post").weight.sum()
inn = W.to_table(filter=ds.field("body_post").isin(list(DN.values()))).to_pandas().groupby("body_pre").weight.sum()
mid = sorted(set(out[out >= 5].index) & set(inn[inn >= 5].index) - set(L + R) - set(DN.values()))
B = L + R + [int(b) for b in mid] + [DN["L"], DN["R"]]
print(f"LC9 L {len(L)} R {len(R)}, intermediates {len(mid)}, DNp09 input from LC9 direct {int(inn.reindex(L+R).fillna(0).sum())}, from mids {int(inn.reindex(mid).sum())}, total {int(inn.sum())}")
edges, _ = load_edges(WEIGHTS, bodies=B)
nts = pd.read_feather(NTS); t = nts.set_index("body").reindex(B)[list(NT_COLS)]
ov = {b: ("unknown", "brak NT; znak 0") for b, r in t.iterrows() if not any(isinstance(x, str) and x != "unclear" for x in r)}
pos = {b: i for i, b in enumerate(B)}
for glu in (-1.0, 1.0):
    s = {**DEFAULT_SIGN, "glutamate": glu}; s.update({n: 0.0 for n in set(assign_nt(B, nts, ov).nt) - set(s)})
    spec = build(edges, B, nts, ModelParams(J0=0.2, sign_map=s), nt_overrides=ov)
    print(f"Glu {glu:+.0f}  (DNp09 L / R Hz)")
    for name, grp in (("LC9 L", L), ("LC9 R", R), ("both", L + R)):
        for I in (10.0, 20.0):
            X = np.zeros(len(B)); X[[pos[b] for b in grp]] = I
            r = SparseALIF(spec, ALIFParams(), None).run(X, 500)[100:].mean(0) * 1000
            print(f"   {name:6s} I={I:4.0f}: {r[pos[DN['L']]]:6.1f} / {r[pos[DN['R']]]:6.1f}")
