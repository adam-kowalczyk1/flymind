"""Krok 6 — analiza testu dwóch szlaków (zapisana PRZED testem; reguły LOOP_TARGET_brainleg_r1.md).
Uruchom: analyze_brainleg.py KATALOG PREFIKS OUT.json"""
import glob
import json
import math
import os
import sys

import numpy as np


def mcnemar(a, b):
    n10, n01 = int(((a == 1) & (b == 0)).sum()), int(((a == 0) & (b == 1)).sum())
    n = n10 + n01
    p = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(n10, n01) + 1)) / 2 ** n)
    return n10, n01, p


def holm(ps):
    order, out, run = np.argsort(ps), [0.0] * len(ps), 0.0
    for r, i in enumerate(order):
        run = max(run, (len(ps) - r) * ps[i])
        out[i] = min(1.0, run)
    return out


def load(d, pre, tag, g):
    p = os.path.join(d, f"{pre}_{tag}_g{g}.json")
    if not os.path.exists(p):
        return None
    R = {"W": {}, "C": {}}
    for r in json.load(open(p))["runs"]:
        key = (r["item"].split("/")[1], r["seed"] % 10)
        R[r["kind"]][key] = dict(valid=bool(r["valid"]), ok=r.get("valid") and r.get("dq2") is not None, dq2=r.get("dq2", 0.0),
                                 dq3=r.get("dq3_lev", 0.0), dq1=r.get("dq1", 0.0), palm=r.get("palm_max", 0.0),
                                 success=bool(r.get("success", False)), max_eng=r.get("max_eng", 0), guard=r.get("guard_frac", 0.0))
    return R


def outcomes(R):
    """Dla każdej pary ważnej: o1 = łokieć ruszył (|dq2|≥0,01), o2 = nadgarstek ruszył (dq3≥0,02), o12 = oba."""
    keys = [k for k in R["W"] if R["W"][k]["valid"] and k in R["C"] and R["C"][k]["valid"]]
    o1 = np.array([int(abs(R["W"][k]["dq2"]) >= 0.01) for k in keys])
    o2 = np.array([int(R["W"][k]["dq3"] >= 0.02) for k in keys])
    o12 = o1 * o2
    cs = np.array([int(abs(R["C"][k]["dq2"]) <= 0.01 and abs(R["C"][k]["dq3"]) <= 0.01) for k in keys])
    return keys, o1, o2, o12, cs


def specific(R):
    """Odpowiedź wybiórcza na parę: oba stawy ruszyły po dotyku (W) I chwyt bez dotyku głowy stał (C)."""
    keys, _, _, o12, cs = outcomes(R)
    return keys, o12 * cs


def main(d, pre, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for g in ("1", "-1"):
        N = load(d, pre, "N", g)
        if N is None:
            continue
        keys, o1, o2, o12, cs = outcomes(N)
        rep = dict(n_pairs=len(keys), N=dict(elbow=int(o1.sum()), wrist=int(o2.sum()), both=int(o12.sum()), C_still=int(cs.sum())))
        rep["BL_A_elbow"] = bool(o1.mean() >= 0.8)
        rep["BL_B_wrist"] = bool(o2.mean() >= 0.8)
        rep["BL_C_both_independent"] = bool(o12.mean() >= 0.7)
        rep["BL_D_chwyt_still"] = bool(cs.mean() >= 0.95)
        fams = {}
        for fam in "FL":
            names = [f"{fam}{i}" for i in range(1, 6)]
            arms = {a: load(d, pre, a, g) for a in names}
            arms = {a: v for a, v in arms.items() if v is not None}
            if not arms:
                continue
            raw, rows = [], {}
            for a, A in arms.items():
                k2, b12 = specific(A)  # główna miara H: odpowiedź wybiórcza (LOOP_TARGET_brainleg_r1.md)
                sN = o12 * cs
                common = [k for k in keys if k in k2]
                nn = np.array([int(sN[keys.index(k)]) for k in common]); aa = np.array([int(b12[k2.index(k)]) for k in common])
                n10, n01, p = mcnemar(nn, aa)
                raw.append((n10, n01, p))
            ph = holm([r[2] for r in raw])
            for (a, A), r, h in zip(arms.items(), raw, ph):
                rows[a] = dict(n10=r[0], n01=r[1], p_holm=h, N_better=bool(h < 0.05 and r[0] > r[1]))
            fams[fam] = dict(rows=rows, ok=bool(len(rows) == 5 and all(v["N_better"] for v in rows.values())))
        rep["H_fam"] = fams
        res[f"glu{g}"] = rep
        print(f"Glu {g}: pary {len(keys)} | N: łokieć {o1.sum()}, nadgarstek {o2.sum()}, oba {o12.sum()}, chwyt bez ruchu {cs.sum()} |",
              {k: rep[k] for k in ("BL_A_elbow", "BL_B_wrist", "BL_C_both_independent", "BL_D_chwyt_still")})
        for fam, v in fams.items():
            print("   H(", fam, ")", "POTWIERDZONA" if v["ok"] else "nie", {a: (x["n10"], x["n01"], round(x["p_holm"], 4)) for a, x in v["rows"].items()})
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:4])
