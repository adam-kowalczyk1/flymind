"""Pilot (exploratory, no seeds, noise 0): DNp09 drive into T2 L leg circuit (+ DNp09 relay INs) -> MN pools, with/without touch."""
import sys
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np, pandas as pd, pyarrow.dataset as ds
from alif import ALIFParams
from alif_sparse import SparseALIF
from connectome import load_edges
from leg_circuit import select
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build
from visual_path import ANN, NTS, WEIGHTS

DN = [10783, 11177]
bodies, groups, rep = select("T2", "L")
a = pd.read_feather(ANN, columns=["bodyId", "superclass"])
intr = set(a.bodyId[a.superclass == "vnc_intrinsic"].astype(int))
W = ds.dataset(WEIGHTS, format="ipc")
o = W.to_table(filter=ds.field("body_pre").isin(DN)).to_pandas().groupby("body_post").weight.sum()
mn = [b for v in groups["MN"].values() for b in v]
inn = W.to_table(filter=ds.field("body_post").isin(mn + groups["IN"])).to_pandas().groupby("body_pre").weight.sum()
relay = sorted(set(o[o >= 5].index) & set(inn[inn >= 5].index) & intr - set(bodies))
B = bodies + relay + DN
print("relay INs", len(relay), "DNp09 -> circuit IN direct syn", int(o.reindex(groups["IN"]).fillna(0).sum()), "-> relay", int(o.reindex(relay).sum()))
edges, _ = load_edges(WEIGHTS, bodies=B)
nts = pd.read_feather(NTS)
t = nts.set_index("body").reindex(B)[list(NT_COLS)]
ov = {b: ("unknown", "brak NT; znak 0") for b, r in t.iterrows() if not any(isinstance(x, str) and x != "unclear" for x in r)}
pos = {b: i for i, b in enumerate(B)}
br = [pos[b] for b in groups["sensory"]["mechanosensory bristle"]]
POOLS = ("Ti flexor MN", "Acc. ti flexor MN", "Ti extensor MN", "ltm MN", "ltm2-femur MN", "Tr flexor MN", "Tr extensor MN", "Fe reductor MN")
for glu in (-1.0, 1.0):
    signs = {**DEFAULT_SIGN, "glutamate": glu}
    signs.update({n: 0.0 for n in set(assign_nt(B, nts, ov).nt) - set(signs)})
    spec = build(edges, B, nts, ModelParams(J0=0.2, sign_map=signs), nt_overrides=ov)
    print(f"\nGlu = {glu:+.0f}   columns: DNp09 drive 0/20/40 mV, touch 0 | DNp09 40 + touch 20")
    res = []
    for dn_I, touch in ((0, 0), (20, 0), (40, 0), (40, 20)):
        X = np.zeros(len(B)); X[[pos[d] for d in DN]] = dn_I; X[br] = touch
        r = SparseALIF(spec, ALIFParams(), None).run(X, 500)[100:].mean(0) * 1000
        res.append(r)
    for p in POOLS:
        ix = [pos[b] for b in groups["MN"].get(p, [])]
        print(f"  {p:22s}", "  ".join(f"{r[ix].mean():6.1f}" for r in res), "Hz")
    print(f"  {'DNp09':22s}", "  ".join(f"{r[[pos[d] for d in DN]].mean():6.1f}" for r in res), "Hz")
