"""Pilot (exploratory, no seeds, noise 0): LC9 (visual input only) -> mids -> DNp09 -> VNC relays (1-2 hops) -> T2 L leg circuit MNs."""
import sys
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np, pandas as pd, pyarrow.dataset as ds
from alif import ALIFParams
from alif_sparse import SparseALIF
from connectome import load_edges
from leg_circuit import select
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build
from visual_path import ANN, NTS, WEIGHTS

T = int(sys.argv[1]) if len(sys.argv) > 1 else 5
DN = [10783, 11177]
a = pd.read_feather(ANN, columns=["bodyId", "type", "somaSide", "superclass"])
W = ds.dataset(WEIGHTS, format="ipc")
q = lambda col, ids: W.to_table(filter=ds.field(col).isin(list(ids))).to_pandas()
lc = a[a.type == "LC9"]; L = sorted(lc.bodyId[lc.somaSide == "L"].astype(int)); R = sorted(lc.bodyId[lc.somaSide == "R"].astype(int))
o = q("body_pre", L + R).groupby("body_post").weight.sum(); i = q("body_post", DN).groupby("body_pre").weight.sum()
mid = sorted(set(o[o >= 5].index) & set(i[i >= 5].index) - set(L + R) - set(DN))
leg, groups, _ = select("T2", "L")
vnc = set(a.bodyId[a.superclass.isin(["vnc_intrinsic", "descending", "ascending"])].astype(int))
d1 = q("body_pre", DN).groupby("body_post").weight.sum(); hop1 = set(d1[d1 >= T].index) & vnc
e = q("body_pre", hop1); e = e[e.weight >= T]
into_leg = set(e.body_post) & set(leg)
hop2c = set(e.body_post) & vnc - set(leg)
e2 = q("body_pre", hop2c); e2 = e2[(e2.weight >= T) & e2.body_post.isin(set(leg))]
relay = sorted((hop1 | set(e2.body_pre)) - set(leg) - set(DN))
B = L + R + [int(x) for x in mid] + DN + [int(x) for x in relay] + leg
B = list(dict.fromkeys(B))
print(f"T={T}: LC9 {len(L)}+{len(R)}, mids {len(mid)}, DN-relays {len(relay)} (hop1 {len(hop1)}), leg {len(leg)}, total {len(B)}; hop1 targets inside leg circuit {len(into_leg)}")
edges, _ = load_edges(WEIGHTS, bodies=B)
nts = pd.read_feather(NTS); t = nts.set_index("body").reindex(B)[list(NT_COLS)]
ov = {b: ("unknown", "brak NT; znak 0") for b, r in t.iterrows() if not any(isinstance(x, str) and x != "unclear" for x in r)}
pos = {b: k for k, b in enumerate(B)}
POOLS = ("Ti flexor MN", "Ti extensor MN", "Tr flexor MN", "Tr extensor MN", "Fe reductor MN", "Sternal anterior rotator MN", "Sternal posterior rotator MN", "Pleural remotor/abductor MN", "Sternotrochanter MN", "Tergotr. MN")
for glu in (-1.0, 1.0):
    s = {**DEFAULT_SIGN, "glutamate": glu}; s.update({n: 0.0 for n in set(assign_nt(B, nts, ov).nt) - set(s)})
    spec = build(edges, B, nts, ModelParams(J0=0.2, sign_map=s), nt_overrides=ov)
    res = []
    for grp in (L, R, L + R):
        X = np.zeros(len(B)); X[[pos[b] for b in grp]] = 12.0      # encoder i_max
        r = SparseALIF(spec, ALIFParams(), None).run(X, 600)[100:].mean(0) * 1000
        res.append(r)
    print(f"Glu {glu:+.0f}: DNp09 L/R per stimulus", [f"{r[pos[DN[0]]]:.0f}/{r[pos[DN[1]]]:.0f}" for r in res],
          "| relays active", [int((r[[pos[b] for b in relay]] > 0).sum()) for r in res])
    for p in POOLS:
        ix = [pos[b] for b in groups["MN"].get(p, [])]
        if ix: print(f"   {p:28s} LC9-L {res[0][ix].mean():6.1f}  LC9-R {res[1][ix].mean():6.1f}  both {res[2][ix].mean():6.1f} Hz")
