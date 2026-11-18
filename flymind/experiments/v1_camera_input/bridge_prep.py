"""Most oko flyvis → MaleCNS: mapa wejść T4/T5 → LPLC2/LPLC4 (prawa strona) w kolumnach flyvis.
Uruchamiać w .venv: bridge_prep.py ROT_DEG OUT.npz  (ROT_DEG: obrót układu MaleCNS → flyvis, zapisany w PREREG_BRIDGE.md)."""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
D = os.path.join(ROOT, "data", "malecns")
SUB = [f"T4{s}" for s in "abcd"] + [f"T5{s}" for s in "abcd"]
POS_IN = {"T4": ["Mi1"], "T5": ["Tm1", "Tm2", "Tm4", "Tm9"]}        # położenie T4/T5 = środek wejść z typów z kolumną
RFLY = 15


def to_flyvis(x, y, rot):
    """xy MaleCNS (sąsiedzi (1,1)) → obrót → osiowe (u,v) flyvis (x=1.5v/√3, y=−(u+v/2)), zaokrąglenie sześcienne."""
    c, s = np.cos(np.radians(rot)), np.sin(np.radians(rot))
    X, Y = c * x - s * y, s * x + c * y
    v = 2 * X / np.sqrt(3); u = -Y - v / 2
    w = -u - v
    ru, rv, rw = np.round(u), np.round(v), np.round(w)
    du, dv, dw = abs(ru - u), abs(rv - v), abs(rw - w)
    fu = (du > dv) & (du > dw); fv = ~fu & (dv > dw)
    ru = np.where(fu, -rv - rw, ru); rv = np.where(fv, -ru - rw, rv)
    return ru.astype(int), rv.astype(int)


def main(rot, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    rot = float(rot)
    a = pd.read_feather(os.path.join(D, "body-annotations-male-cns-v1.0-minconf-0.5.feather"),
                        columns=["bodyId", "type", "somaSide", "assignedOlHex1", "assignedOlHex2"])
    a = a[a.type.notna()]
    R = a[a.somaSide == "R"]
    hx = R[R.assignedOlHex1.notna()]
    c = (np.median(hx.assignedOlHex1[hx.type == "Mi1"]), np.median(hx.assignedOlHex2[hx.type == "Mi1"]))
    q = dict(zip(hx.bodyId, hx.assignedOlHex1 - c[0])); r = dict(zip(hx.bodyId, hx.assignedOlHex2 - c[1]))
    ty = dict(zip(a.bodyId, a.type))
    tt = R[R.type.isin(SUB)]; vp = R[R.type.isin(["LPLC2", "LPLC4"]) | R.type.astype(str).str.startswith("LPi")]
    nts = pd.read_feather(os.path.join(D, "body-neurotransmitters-male-cns-v1.0.feather"), columns=["body", "celltype_predicted_nt"]).set_index("body").celltype_predicted_nt
    SIGN = {"acetylcholine": 1.0, "glutamate": -1.0, "gaba": -1.0}
    dn = a[a.type == "DNp07"]
    w = pd.read_feather(os.path.join(D, "connectome-weights-male-cns-v1.0-minconf-0.5.feather"))
    tid = set(tt.bodyId)
    # położenie każdego T4/T5
    e = w[w.body_post.isin(tid) & w.body_pre.isin(set(hx.bodyId))].copy()
    e["pt"] = e.body_pre.map(ty); e["qt"] = e.body_post.map(ty).str[:2]
    e = e[[p in POS_IN[k] for p, k in zip(e.pt, e.qt)]]
    Q = e.body_pre.map(q).values; Rr = e.body_pre.map(r).values
    e["x"] = (Q - 0.5 * Rr) * e.weight; e["y"] = Rr * np.sqrt(3) / 2 * e.weight
    g = e.groupby("body_post")[["x", "y", "weight"]].sum()
    px, py = (g.x / g.weight).to_dict(), (g.y / g.weight).to_dict()
    # wejścia T4/T5 → LPLC2/LPLC4
    vid = set(vp.bodyId)
    f = w[w.body_pre.isin(tid) & w.body_post.isin(vid) & w.body_pre.isin(px.keys())]
    x = f.body_pre.map(px).values; y = f.body_pre.map(py).values
    u, v = to_flyvis(x, y, rot)
    inside = (np.abs(u) <= RFLY) & (np.abs(v) <= RFLY) & (np.abs(u + v) <= RFLY)
    post = np.array(sorted(vid)); pidx = {b: i for i, b in enumerate(post)}
    vv = w[w.body_pre.isin(vid) & w.body_post.isin(set(vid) | set(dn.bodyId))]
    vv = vv[vv.body_pre.map(ty).str.startswith("LPi") & vv.body_post.isin(vid)]          # LPi → LPLC2/LPLC4/LPi
    vsign = np.array([SIGN.get(nts.get(b), 0.0) for b in vv.body_pre])
    np.savez(out, post=post, post_type=np.array([ty[b] for b in post]),
             in_post=f.body_post.map(pidx).values, in_sub=np.array([SUB.index(ty[b]) for b in f.body_pre]),
             in_u=u, in_v=v, in_inside=inside, in_w=f.weight.values.astype(float), in_x=x, in_y=y,
             vv_pre=vv.body_pre.map(pidx).values, vv_post=vv.body_post.map(pidx).values, vv_w=vv.weight.values.astype(float), vv_sign=vsign,
             rot=rot, center=np.array(c),
             n_t45_no_pos=int(len(tid - set(px))))
    print(dict(post=len(post), edges=len(f), syn=int(f.weight.sum()), inside_frac=round(float((f.weight * inside).sum() / f.weight.sum()), 3),
               t45_no_pos=len(tid - set(px)), vv_edges=len(vv), lpi_cells=int(sum(str(ty[b]).startswith("LPi") for b in post)),
               lpi_to_lplc2=int(vv.weight[vv.body_post.map(ty) == "LPLC2"].sum()), lpi_sign_counts={k: int((vsign == k).sum()) for k in (-1.0, 0.0, 1.0)}))


if __name__ == "__main__":
    main(*sys.argv[1:3])
