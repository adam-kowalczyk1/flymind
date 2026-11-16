"""Krok 4 — analiza testu „dwa czucia, dwa odruchy” (zapisana PRZED testem; reguły: LOOP_TARGET_reflex_r1.md).
Uruchom: analyze_reflex.py KATALOG PREFIKS OUT.json
Para scen = (materiał, numer pozy): próba W (wycofanie) i próba C (chwyt). Para ważna, gdy obie próby są ważne w sieci N
(ważność nie zależy od sieci: podjazd jest klasyczny). Wynik główny pary: OBA = W udane ORAZ C udane.
H-R(rodzina): sieć z danych lepsza na wyniku OBA od każdego z 5 tasowań rodziny (McNemar dokładny + Holm, p < 0,05, różnica > 0)."""
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
        R[r["kind"]][key] = (bool(r["valid"]), bool(r["success"]))
    return R


def main(d, pre, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for g in ("1", "-1"):
        N = load(d, pre, "N", g)
        if N is None:
            continue
        keys = sorted(k for k in N["W"] if N["W"][k][0] and N["C"].get(k, (False,))[0])
        vec = lambda R, kind: np.array([int(R[kind][k][1]) for k in keys])  # noqa: E731
        both = lambda R: vec(R, "W") * vec(R, "C")  # noqa: E731
        rep = dict(n_pairs=len(keys), nets={"N": dict(W=int(vec(N, "W").sum()), C=int(vec(N, "C").sum()), both=int(both(N).sum()))})
        for fam in "FLG":
            names = [f"{fam}{i}" for i in range(1, 6)]
            A = {a: load(d, pre, a, g) for a in names}
            names = [a for a in names if A[a] is not None]
            if not names:
                continue
            for a in names:
                assert all(A[a]["W"][k][0] and A[a]["C"][k][0] for k in keys), f"ważność zależy od sieci w {a}"
                rep["nets"][a] = dict(W=int(vec(A[a], "W").sum()), C=int(vec(A[a], "C").sum()), both=int(both(A[a]).sum()))
            raw = [mcnemar(both(N), both(A[a])) for a in names]
            ph = holm([r[2] for r in raw])
            rows = {a: dict(n10=r[0], n01=r[1], p=r[2], p_holm=h, N_better=bool(h < 0.05 and r[0] > r[1])) for a, r, h in zip(names, raw, ph)}
            rawW = [mcnemar(vec(N, "W"), vec(A[a], "W")) for a in names]
            phW = holm([r[2] for r in rawW])
            rep[f"H_R_{fam}"] = dict(rows=rows, ok=bool(len(names) == 5 and all(v["N_better"] for v in rows.values())),
                                     W_only={a: dict(n10=r[0], n01=r[1], p_holm=h) for a, r, h in zip(names, rawW, phW)})
        res[f"glu{g}"] = rep
        print(f"Glu {g}: par {len(keys)} |", {a: (v["W"], v["C"], v["both"]) for a, v in rep["nets"].items()})
        for fam in "FLG":
            if f"H_R_{fam}" in rep:
                print(f"   H-R({fam})", "POTWIERDZONA" if rep[f"H_R_{fam}"]["ok"] else "nie",
                      {a: (v["n10"], v["n01"], round(v["p_holm"], 4)) for a, v in rep[f"H_R_{fam}"]["rows"].items()})
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:4])
