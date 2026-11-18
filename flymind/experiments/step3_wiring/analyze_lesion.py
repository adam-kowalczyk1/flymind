"""Krok 6 r3 — analiza testu wycięcia szlaku (zapisana PRZED testem; reguły LOOP_TARGET_brainleg_r3.md).
Uruchom: analyze_lesion.py KATALOG PREFIKS OUT.json"""
import json
import os
import sys

import numpy as np

import analyze_brainleg as A


def main(d, pre, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for g in ("1", "-1"):
        N = A.load(d, pre, "N", g)
        kN, e, w, b, cs = A.outcomes(N)
        rep = dict(N=dict(pairs=len(kN), elbow=int(e.sum()), wrist=int(w.sum()), both=int(b.sum()), C_still=int(cs.sum())),
                   LZ_3_intact=bool(e.mean() >= 0.8 and w.mean() >= 0.8 and cs.mean() >= 0.95))
        ps = {}
        for les, keep, gone in (("d15", 1, 2), ("d78", 2, 1)):     # 1 = nadgarstek (dq3), 2 = łokieć (dq2)
            L = A.load(d, pre, les, g)
            kL, le, lw, _, lcs = A.outcomes(L)
            o = {1: lw, 2: le}
            oN = {1: w, 2: e}
            common = [k for k in kN if k in kL]
            nn = np.array([int(oN[gone][kN.index(k)]) for k in common]); ll = np.array([int(o[gone][kL.index(k)]) for k in common])
            n10, n01, p = A.mcnemar(nn, ll)
            ps[les] = p
            rep[les] = dict(pairs=len(kL), elbow=int(le.sum()), wrist=int(lw.sum()), C_still=int(lcs.sum()), mcnemar_lost=(n10, n01),
                            ok=bool(o[gone].mean() <= 0.10 and o[keep].mean() >= 0.8 and lcs.mean() >= 0.95))
        for les, h in zip(ps, A.holm(list(ps.values()))):
            rep[les]["p_holm"] = h
            rep[les]["ok"] = bool(rep[les]["ok"] and h < 0.05)
        rep["LZ_1_bez_DNg15"], rep["LZ_2_bez_DNge078"] = rep["d15"]["ok"], rep["d78"]["ok"]
        res[f"glu{g}"] = rep
        print(f"Glu {g}:", json.dumps(rep, ensure_ascii=False))
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:4])
