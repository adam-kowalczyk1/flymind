"""Wycinek S-core prawego płata wzrokowego z MaleCNS (DESIGN.md §1, reguła zamrożona; ma dać 5120 neuronów).
build() → dict(bodies, type, hexq, hexr, core_cols, edges(pre_idx, post_idx, n), nt)."""
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
D = os.path.join(ROOT, "data", "malecns")
ANN = os.path.join(D, "body-annotations-male-cns-v1.0-minconf-0.5.feather")
NTS = os.path.join(D, "body-neurotransmitters-male-cns-v1.0.feather")
WTS = os.path.join(D, "connectome-weights-male-cns-v1.0-minconf-0.5.feather")
HEX_TYPES = ["L1", "L2", "L3", "L5", "Mi1", "Mi4", "Mi9", "Tm1", "Tm2", "Tm4", "Tm9", "C3"]
NOHEX = ["Tm3", "L4"] + [f"T4{s}" for s in "abcd"] + [f"T5{s}" for s in "abcd"] + ["LPLC2", "LC4"]
RADIUS = 8


def hexdist(dq, dr):
    return (np.abs(dq) + np.abs(dr) + np.abs(dq - dr)) / 2


def xy(q, r):
    """Osadzenie w płaszczyźnie (jednostka = 1 kolumna): x = q + r·cos120°, y = r·sin120°."""
    return np.c_[np.asarray(q, float) - 0.5 * np.asarray(r, float), np.asarray(r, float) * np.sqrt(3) / 2]


def build(hex_pool="12types"):
    a = pd.read_feather(ANN, columns=["bodyId", "type", "somaSide", "assignedOlHex1", "assignedOlHex2"])
    a = a[a.type.notna()]
    hx = a[a.type.isin(HEX_TYPES) & (a.somaSide == "R") & a.assignedOlHex1.notna()].copy()
    l1 = hx[hx.type == "L1"]
    c = (np.median(l1.assignedOlHex1), np.median(l1.assignedOlHex2))
    hx["d"] = hexdist(hx.assignedOlHex1 - c[0], hx.assignedOlHex2 - c[1])
    core = hx[hx.d <= RADIUS]
    core_ids = set(core.bodyId.astype(int))
    pool = set(hx.bodyId.astype(int)) if hex_pool == "12types" else set(a.bodyId[a.assignedOlHex1.notna()].astype(int))
    cand = a[(a.type.isin(NOHEX) & (a.somaSide == "R")) | (a.type == "R1-R6")]
    cand_ids = set(cand.bodyId.astype(int))
    w = pd.read_feather(WTS)
    pre, post, n = w.body_pre.values, w.body_post.values, w.weight.values
    pool_arr, core_arr, cand_arr = (np.fromiter(s, np.int64) for s in (pool, core_ids, cand_ids))
    # wejścia kandydatów (bez R1-R6) od komórek z puli hex: udział z rdzenia
    m = np.isin(post, cand_arr) & np.isin(pre, pool_arr)
    e = pd.DataFrame(dict(pre=pre[m], post=post[m], n=n[m]))
    e["in_core"] = e.pre.isin(core_ids)
    fin = e.groupby("post").apply(lambda g: g.n[g.in_core].sum() / g.n.sum(), include_groups=False)
    # wyjścia R1-R6 do puli hex: udział do rdzenia
    rr = set(cand.bodyId[cand.type == "R1-R6"].astype(int))
    m = np.isin(pre, np.fromiter(rr, np.int64)) & np.isin(post, pool_arr)
    e2 = pd.DataFrame(dict(pre=pre[m], post=post[m], n=n[m]))
    e2["in_core"] = e2.post.isin(core_ids)
    fout = e2.groupby("pre").apply(lambda g: g.n[g.in_core].sum() / g.n.sum(), include_groups=False)
    keep = core_ids | {b for b, f in fin.items() if f >= 0.5 and b not in rr} | {b for b, f in fout.items() if f >= 0.5}
    bodies = np.array(sorted(keep), np.int64)
    idx = {b: i for i, b in enumerate(bodies)}
    m = np.isin(pre, bodies) & np.isin(post, bodies)
    E = pd.DataFrame(dict(pre=pre[m], post=post[m], n=n[m]))
    E = E[E.pre != E.post]
    ty = dict(zip(a.bodyId, a.type))
    nts = pd.read_feather(NTS, columns=["body", "celltype_predicted_nt"]).set_index("body").celltype_predicted_nt
    hq = dict(zip(hx.bodyId, hx.assignedOlHex1)); hr = dict(zip(hx.bodyId, hx.assignedOlHex2))
    return dict(bodies=bodies, type=np.array([ty[b] for b in bodies]), nt=np.array([nts.get(b, None) for b in bodies], object),
                hexq=np.array([hq.get(b, np.nan) for b in bodies]) - c[0], hexr=np.array([hr.get(b, np.nan) for b in bodies]) - c[1],
                center=c, pre=E.pre.map(idx).values, post=E.post.map(idx).values, n=E.n.values.astype(float),
                n_core_cells=len(core_ids), n_core_cols=int((core.type == "L1").sum()))


if __name__ == "__main__":
    import collections
    for hp in ("12types", "allhex"):
        S = build(hp)
        cnt = collections.Counter(S["type"])
        print(hp, "neurony", len(S["bodies"]), "rdzeń", S["n_core_cells"], "kolumn L1", S["n_core_cols"], "krawędzie", len(S["n"]), "synapsy", int(S["n"].sum()),
              {k: cnt[k] for k in ("LPLC2", "LC4", "R1-R6", "Tm3", "L4", "T4a", "T5a")})
