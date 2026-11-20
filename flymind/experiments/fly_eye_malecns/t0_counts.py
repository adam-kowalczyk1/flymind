"""T0 (PREREG_T0_T1.md): filtry średnie (typ pre, typ post, du, dv) z MaleCNS, prawa strona, w układzie kolumn flyvis.
.venv: t0_counts.py → results/fly_eye_malecns_20261120/{malecns_keys.csv, t0_gate.json}
du, dv = kolumna POST − kolumna PRE (tak liczy flyvis: sprawdzone na tabeli krawędzi, 100 % zgodności)."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../v1_camera_input"))
from bridge_prep import D, to_flyvis  # noqa: E402

RES = os.path.join(HERE, "../../results/fly_eye_malecns_20261120")
ROT, RCORE, NMIN = 30.0, 12, 50
ALIAS = {"Am1": "Am", "TmY9a": "TmY9", "TmY9b": "TmY9"}           # nazwa MaleCNS → nazwa flyvis
POS_IN = {"T4": ["Mi1"], "T5": ["Tm1", "Tm2", "Tm4", "Tm9"]}


def hexdist(u, v):
    return (np.abs(u) + np.abs(v) + np.abs(u + v)) / 2


def main():
    K = pd.read_csv(f"{RES}/flyvis_keys.csv")
    fv_types = set(K.source_type) | set(K.target_type)
    a = pd.read_feather(os.path.join(D, "body-annotations-male-cns-v1.0-minconf-0.5.feather"),
                        columns=["bodyId", "type", "somaSide", "assignedOlHex1", "assignedOlHex2"])
    a = a[(a.somaSide == "R") & a.type.notna()].copy()
    a["ft"] = a.type.map(lambda t: ALIAS.get(t, t))
    a = a[a.ft.isin(fv_types) & ~a.ft.str.startswith("R") & (a.ft != "CT1")]
    hx = a[a.assignedOlHex1.notna()]
    c = (np.median(hx.assignedOlHex1[hx.type == "Mi1"]), np.median(hx.assignedOlHex2[hx.type == "Mi1"]))
    q, r = hx.assignedOlHex1 - c[0], hx.assignedOlHex2 - c[1]
    X = dict(zip(hx.bodyId, q - 0.5 * r)); Y = dict(zip(hx.bodyId, r * np.sqrt(3) / 2))
    ft = dict(zip(a.bodyId, a.ft))
    w = pd.read_feather(os.path.join(D, "connectome-weights-male-cns-v1.0-minconf-0.5.feather"))
    ids = set(a.bodyId)
    w = w[w.body_pre.isin(ids) & w.body_post.isin(ids)].copy()
    w["pt"], w["qt"] = w.body_pre.map(ft), w.body_post.map(ft)
    # kolumny komórek bez assignedOlHex: środek wejść (T4: Mi1; T5: Tm1/2/4/9; reszta: wszystkie wejścia z kolumną)
    nohex = set(a.bodyId) - set(hx.bodyId)
    e = w[w.body_post.isin(nohex) & w.body_pre.isin(X.keys())].copy()
    fam = e.qt.str[:2]
    ok = np.array([(f not in POS_IN) or (p in POS_IN[f]) for f, p in zip(fam, e.pt)])
    e = e[ok]
    e["x"], e["y"] = e.body_pre.map(X) * e.weight, e.body_pre.map(Y) * e.weight
    g = e.groupby("body_post")[["x", "y", "weight"]].sum()
    X.update((g.x / g.weight).to_dict()); Y.update((g.y / g.weight).to_dict())
    pos = pd.DataFrame(dict(b=list(X), x=list(X.values()), y=[Y[b] for b in X]))
    pos["u"], pos["v"] = to_flyvis(pos.x.values, pos.y.values, ROT)
    U, V = dict(zip(pos.b, pos.u)), dict(zip(pos.b, pos.v))
    ncol = pd.Series({t: sum(1 for b, tt in ft.items() if tt == t and b in U) for t in set(ft.values())})
    w = w[w.body_pre.isin(U.keys()) & w.body_post.isin(U.keys())].copy()
    w["du"] = w.body_post.map(U) - w.body_pre.map(U)
    w["dv"] = w.body_post.map(V) - w.body_pre.map(V)
    w["core"] = hexdist(w.body_post.map(U), w.body_post.map(V)) <= RCORE
    s = w[w.core].groupby(["pt", "qt", "du", "dv", "body_post"]).weight.sum().reset_index()
    M = s.groupby(["pt", "qt", "du", "dv"]).weight.mean().reset_index()
    M.columns = ["source_type", "target_type", "du", "dv", "n_syn"]
    M.to_csv(f"{RES}/malecns_keys.csv", index=False)
    # bramka
    good = set(ncol[ncol >= NMIN].index)
    Kp = K[~K.source_type.str.match(r"^R\d") & ~K.source_type.str.startswith("CT1") & ~K.target_type.str.startswith("CT1")]
    pairs = Kp.groupby(["source_type", "target_type"]).n_syn.sum()
    mp = M.groupby(["source_type", "target_type"]).n_syn.sum()
    J = K.merge(M, on=["source_type", "target_type", "du", "dv"], how="left", suffixes=("_fv", "_m"))
    rep = [(p, q) for p, q in pairs.index if p in good and q in good]
    have = [k for k in rep if k in mp.index]
    rho = spearmanr([pairs[k] for k in have], [mp[k] for k in have]).statistic
    m_in = M.merge(K[["source_type", "target_type", "du", "dv"]], how="inner").n_syn.sum()
    mass_pairs = M[[(p, q) in set(pairs.index) for p, q in zip(M.source_type, M.target_type)]].n_syn.sum()
    out = dict(n_pairs_flyvis_noR=len(pairs), n_pairs_replaceable=len(rep), n_pairs_with_malecns=len(have),
               frac_pairs_with_malecns=len(have) / len(pairs), spearman_pair_totals=float(rho),
               frac_malecns_mass_in_flyvis_keys=float(m_in / mass_pairs),
               keys_with_malecns=int(J.n_syn_m.notna().sum()), keys_total=len(K),
               types_lt_50=sorted(set(ncol.index) - good), n_cells=int(len(U)),
               PASS=bool(len(have) / len(pairs) >= 0.6 and rho >= 0.5))
    worst = sorted(((np.log((mp.get(k, 0) + 1) / (pairs[k] + 1)), k) for k in have), key=lambda z: z[0])
    out["most_lower_in_malecns"] = [(f"{k[0]}→{k[1]}", round(pairs[k], 1), round(float(mp[k]), 1)) for _, k in worst[:8]]
    out["most_higher_in_malecns"] = [(f"{k[0]}→{k[1]}", round(pairs[k], 1), round(float(mp[k]), 1)) for _, k in worst[-8:]]
    json.dump(out, open(f"{RES}/t0_gate.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
