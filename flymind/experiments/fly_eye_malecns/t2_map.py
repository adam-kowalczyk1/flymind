"""T2 — mapa wejść komórek zbliżania (LPLC2, LC4; prawa strona MaleCNS) do modelu bez tłumacza. Tylko odczyt.
.venv: t2_map.py → results/fly_eye_malecns_20261120/t2_map.npz
Krawędzie: (post, pre_typ flyvis, u, v kolumny pre, liczba synaps, znak NT) — wejścia od komórek typów flyvis z kolumną;
LPi: komórki LPi i ich wejścia z T4/T5 (kolumny) + krawędzie LPi → cel; rekurencja cel → cel."""
import os

import numpy as np
import pandas as pd

import t0_counts as T

SIGN = {"acetylcholine": 1.0, "gaba": -1.0, "glutamate": -1.0, "histamine": -1.0}


def main():
    K, w0, ncol, ncore, U, V = T.load()
    a = pd.read_feather(os.path.join(T.D, "body-annotations-male-cns-v1.0-minconf-0.5.feather"), columns=["bodyId", "type", "somaSide"])
    ty = dict(zip(a.bodyId, a.type))
    nts = pd.read_feather(os.path.join(T.D, "body-neurotransmitters-male-cns-v1.0.feather"),
                          columns=["body", "celltype_predicted_nt"]).set_index("body").celltype_predicted_nt
    sg = lambda b: SIGN.get(nts.get(b, None), 0.0)  # noqa: E731
    w = pd.read_feather(os.path.join(T.D, "connectome-weights-male-cns-v1.0-minconf-0.5.feather"))
    out = {}
    for tgt in ("LPLC2", "LC4"):
        cells = np.array(sorted(a.bodyId[(a.type == tgt) & (a.somaSide == "R")]), np.int64)
        ci = {b: i for i, b in enumerate(cells)}
        e = w[w.body_post.isin(ci)]
        f = e[e.body_pre.isin(U.keys())]                                   # wejścia od typów flyvis z kolumną
        ftype = f.body_pre.map(lambda b: T.ALIAS.get(ty[b], ty[b]))
        out[f"{tgt}_cells"] = cells
        out[f"{tgt}_in"] = np.c_[f.body_post.map(ci), f.body_pre.map(U), f.body_pre.map(V), f.weight, f.body_pre.map(sg)].astype(float)
        out[f"{tgt}_in_type"] = np.array(ftype.tolist(), dtype=str)
        lpi = e[e.body_pre.map(lambda b: str(ty.get(b, ""))).str.startswith("LPi")]
        out[f"{tgt}_lpi"] = np.c_[lpi.body_post.map(ci), lpi.body_pre, lpi.weight, lpi.body_pre.map(sg)].astype(float)
        rec = e[e.body_pre.isin(ci)]
        out[f"{tgt}_rec"] = np.c_[rec.body_post.map(ci), rec.body_pre.map(ci), rec.weight, rec.body_pre.map(sg)].astype(float)
        out[f"{tgt}_total_in"] = e.groupby("body_post").weight.sum().reindex(cells).fillna(0).values
        print(tgt, len(cells), "komórek; udział wejścia: flyvis z kolumną", round(f.weight.sum() / e.weight.sum(), 3),
              "LPi", round(lpi.weight.sum() / e.weight.sum(), 3), "rekurencja", round(rec.weight.sum() / e.weight.sum(), 3))
    lpis = np.unique(np.r_[out["LPLC2_lpi"][:, 1], out["LC4_lpi"][:, 1]]).astype(np.int64)
    li = {b: i for i, b in enumerate(lpis)}
    g = w[w.body_post.isin(li) & w.body_pre.isin(U.keys())]
    out["lpi_cells"], out["lpi_type"] = lpis, np.array([ty[b] for b in lpis]).astype(str)
    out["lpi_in"] = np.c_[g.body_post.map(li), g.body_pre.map(U), g.body_pre.map(V), g.weight, g.body_pre.map(sg)].astype(float)
    out["lpi_in_type"] = np.array(g.body_pre.map(lambda b: T.ALIAS.get(ty[b], ty[b])).tolist(), dtype=str)
    for k in ("LPLC2", "LC4"):
        out[f"{k}_lpi"][:, 1] = [li[int(b)] for b in out[f"{k}_lpi"][:, 1]]
    tot = w[w.body_post.isin(li)].groupby("body_post").weight.sum()
    print("LPi", len(lpis), "komórek; udział wejścia od typów flyvis z kolumną", round(g.weight.sum() / tot.sum(), 3))
    np.savez_compressed(os.path.join(T.RES, "t2_map.npz"), **out)


if __name__ == "__main__":
    main()
