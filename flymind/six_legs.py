"""flymind/six_legs.py — sieć sześciu nóg z MaleCNS (tylko dane) do pytania: co dotyk jednej nogi robi z pozostałymi.

Skład (jak w experiments/fj2_fly_arm/pilot_touch_other_legs.py):
  obwody 6 nóg (leg_circuit.select)
  + MN nóg według podklasy fl/ml/hl, bo T1 ma biodro na ProAN/VProN/DProN
  + przekaźniki vnc_intrinsic: ≥ t synaps od obwodu nogi dotykanej i ≥ t synaps do obwodów pozostałych nóg.
Znaki przez snn_interface.build; glutaminian jest parametrem; ciała bez NT i NT spoza mapy dostają znak 0.
"""
import pandas as pd
import pyarrow.dataset as ds

from connectome import load_edges
from leg_circuit import select
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build
from visual_path import ANN, NTS, WEIGHTS

SUB = {"T1": "fl", "T2": "ml", "T3": "hl"}
SWING = ("Sternal anterior rotator MN", "Tr flexor MN", "Tergopleural/Pleural promotor MN")
STANCE = ("Pleural remotor/abductor MN", "Sternal posterior rotator MN", "Tr extensor MN", "Sternotrochanter MN", "Tergotr. MN")


def select_all(touched="T2L", t=5):
    a = pd.read_feather(ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide"])
    A = a.set_index("bodyId")
    W = ds.dataset(WEIGHTS, format="ipc")

    def q(col, ids):
        return W.to_table(filter=ds.field(col).isin([int(x) for x in ids])).to_pandas()

    legs, mns = {}, {}
    for seg in ("T1", "T2", "T3"):
        for side in ("L", "R"):
            b, g, _ = select(seg, side, t)
            m = a[(a.superclass == "vnc_motor") & (a.subclass == SUB[seg]) & (a.somaSide == side)]
            legs[seg + side] = (set(b), g)
            mns[seg + side] = {k: sorted(v.bodyId.astype(int)) for k, v in m.groupby(m.type.fillna("NA"))}
    src = legs[touched][0]
    others = (set().union(*[v[0] for k, v in legs.items() if k != touched])
              | {b for d in mns.values() for v in d.values() for b in v})
    e = q("body_pre", src)
    e = e[(e.weight >= t) & (A.superclass.reindex(e.body_post).values == "vnc_intrinsic")]
    e2 = q("body_pre", set(e.body_post) - src - others)
    relay = sorted(set(e2[(e2.weight >= t) & e2.body_post.isin(others)].body_pre))
    bodies = list(dict.fromkeys([int(x) for x in sorted(src)] + [int(x) for x in sorted(others)] + [int(x) for x in relay]))
    return bodies, legs, mns, relay


def network(J0=0.275, glu_sign=-1.0, touched="T2L", t=5):
    bodies, legs, mns, relay = select_all(touched, t)
    edges, _ = load_edges(WEIGHTS, bodies=bodies)
    nts = pd.read_feather(NTS)
    tab = nts.set_index("body").reindex(bodies)[list(NT_COLS)]
    ov = {b: ("unknown", "brak NT; znak 0") for b, r in tab.iterrows()
          if not any(isinstance(x, str) and x != "unclear" for x in r)}
    signs = {**DEFAULT_SIGN, "glutamate": glu_sign}
    signs.update({n: 0.0 for n in set(assign_nt(bodies, nts, ov).nt) - set(signs)})
    spec = build(edges, bodies, nts, ModelParams(J0=J0, sign_map=signs), nt_overrides=ov)
    pos = {b: k for k, b in enumerate(bodies)}
    pools = {leg: ([pos[b] for n in SWING for b in d.get(n, [])], [pos[b] for n in STANCE for b in d.get(n, [])])
             for leg, d in mns.items()}
    bristle = [pos[b] for b in legs[touched][1]["sensory"]["mechanosensory bristle"]]
    return spec, dict(pos=pos, pools=pools, bristle=bristle, source=[pos[b] for b in legs[touched][0]],
                      sizes=dict(total=len(bodies), relay=len(relay)))
