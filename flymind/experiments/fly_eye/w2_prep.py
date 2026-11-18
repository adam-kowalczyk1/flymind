"""W2 — mapa wejść „typy obecne we flyvis → LC4” (MaleCNS, prawa strona) w kolumnach flyvis. Tylko odczyt danych.
.venv: w2_prep.py OUT.npz        (cel: LOOP_TARGET_W2.md; obrót 30° i to_flyvis z v1_camera_input/bridge_prep.py, VERIFIED tamże)
Położenie komórki wejściowej: własna kolumna (assignedOlHex), a gdy jej brak — środek ważony synapsami jej wejść
od komórek z przypisaną kolumną. Jedna reguła dla wszystkich typów."""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))
from bridge_prep import D, RFLY, to_flyvis  # noqa: E402

TARGET, ROT = "LC4", 30.0
# typy flyvis z pełnym zestawem 721 kolumn (odczyt z sieci flow/0000/040; bez Lawf1/Lawf2 po 123)
FV = ("Am C2 C3 CT1(Lo1) CT1(M10) L1 L2 L3 L4 L5 Mi1 Mi10 Mi11 Mi12 Mi13 Mi14 Mi15 Mi2 Mi3 Mi4 Mi9 R1 R2 R3 R4 R5 R6 R7 R8 "
      "T1 T2 T2a T3 T4a T4b T4c T4d T5a T5b T5c T5d Tm1 Tm16 Tm2 Tm20 Tm28 Tm3 Tm30 Tm4 Tm5Y Tm5a Tm5b Tm5c Tm9 "
      "TmY10 TmY13 TmY14 TmY15 TmY18 TmY3 TmY4 TmY5a TmY9").split()
SIGN = {"acetylcholine": 1.0, "glutamate": -1.0, "gaba": -1.0}      # jak bridge_prep.py; inne/nieznane = 0


def main(out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    a = pd.read_feather(os.path.join(D, "body-annotations-male-cns-v1.0-minconf-0.5.feather"),
                        columns=["bodyId", "type", "somaSide", "assignedOlHex1", "assignedOlHex2"])
    a = a[a.type.notna()]
    R = a[a.somaSide == "R"]
    hx = R[R.assignedOlHex1.notna()]
    c = (np.median(hx.assignedOlHex1[hx.type == "Mi1"]), np.median(hx.assignedOlHex2[hx.type == "Mi1"]))
    q = hx.assignedOlHex1.values - c[0]; r = hx.assignedOlHex2.values - c[1]
    hxy = pd.DataFrame(dict(x=q - 0.5 * r, y=r * np.sqrt(3) / 2), index=hx.bodyId.values)
    ty = dict(zip(a.bodyId, a.type))
    nts = pd.read_feather(os.path.join(D, "body-neurotransmitters-male-cns-v1.0.feather"),
                          columns=["body", "celltype_predicted_nt"]).set_index("body").celltype_predicted_nt
    w = pd.read_feather(os.path.join(D, "connectome-weights-male-cns-v1.0-minconf-0.5.feather"))
    post = np.array(sorted(R.bodyId[R.type == TARGET])); pidx = {b: i for i, b in enumerate(post)}
    allin = w[w.body_post.isin(set(post))]
    total = float(allin.weight.sum())
    pre = set(R.bodyId[R.type.isin(FV)])
    f = allin[allin.body_pre.isin(pre)]
    # położenia komórek wejściowych
    need = set(f.body_pre) - set(hxy.index)
    e = w[w.body_post.isin(need) & w.body_pre.isin(set(hxy.index))]
    ex = e.body_pre.map(hxy.x).values * e.weight.values; ey = e.body_pre.map(hxy.y).values * e.weight.values
    g = pd.DataFrame(dict(b=e.body_post.values, x=ex, y=ey, w=e.weight.values)).groupby("b").sum()
    px = {**hxy.x.to_dict(), **(g.x / g.w).to_dict()}; py = {**hxy.y.to_dict(), **(g.y / g.w).to_dict()}
    f = f[f.body_pre.isin(px.keys())]
    x = f.body_pre.map(px).values; y = f.body_pre.map(py).values
    u, v = to_flyvis(x, y, ROT)
    inside = (np.abs(u) <= RFLY) & (np.abs(v) <= RFLY) & (np.abs(u + v) <= RFLY)
    typ = np.array([ty[b] for b in f.body_pre], dtype="U")
    sign = np.array([SIGN.get(nts.get(b), 0.0) for b in f.body_pre])
    np.savez(out, post=post, in_post=f.body_post.map(pidx).values, in_type=typ, in_u=u, in_v=v, in_inside=inside,
             in_w=f.weight.values.astype(float), in_sign=sign, rot=ROT, center=np.array(c), total_in=total)
    by = pd.DataFrame(dict(t=typ, w=f.weight.values, i=inside)).groupby("t").apply(lambda d: pd.Series(dict(syn=d.w.sum(), inside=d.w[d.i].sum())))
    by = by.sort_values("syn", ascending=False)
    print(dict(target=TARGET, cells=len(post), total_in=int(total), mapped=int(f.weight.sum()), mapped_frac=round(f.weight.sum() / total, 3),
               inside_frac_of_total=round(float((f.weight * inside).sum()) / total, 3), types=len(by), sign0_syn=int(f.weight[sign == 0].sum())))
    print(by.head(12).astype(int).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
