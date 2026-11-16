"""Krok 4 r2 — analiza większego testu „dwa czucia, dwa odruchy” (zapisana PRZED testem; reguły LOOP_TARGET_reflex_r2.md).
Uruchom: analyze_reflex2.py KATALOG OUT.json
Jak analyze_reflex.py (McNemar dokładny + Holm, wynik OBA), ale sceny z trzech ziaren 21951/21952/21953 (pliki x{SEED}_{sieć}_g{Glu}.json);
klucz pary = ziarno sceny W (C ma to samo + 100), więc pary z różnych ziaren się nie zlewają."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_reflex import holm, mcnemar  # noqa: E402

SEEDS = (21951, 21952, 21953)


def load(d, tag, g):
    R = {"W": {}, "C": {}}
    for s in SEEDS:
        p = os.path.join(d, f"x{s}_{tag}_g{g}.json")
        if not os.path.exists(p):
            return None
        for r in json.load(open(p))["runs"]:
            key = r["seed"] - (100 if r["kind"] == "C" else 0)
            assert key not in R[r["kind"]], f"powtórzona scena {key} w {p}"
            R[r["kind"]][key] = (bool(r["valid"]), bool(r["success"]))
    return R


def main(d, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for g in ("1", "-1"):
        N = load(d, "N", g)
        if N is None:
            continue
        keys = sorted(k for k in N["W"] if N["W"][k][0] and N["C"].get(k, (False,))[0])
        vec = lambda R, kind: np.array([int(R[kind][k][1]) for k in keys])  # noqa: E731
        both = lambda R: vec(R, "W") * vec(R, "C")  # noqa: E731
        rep = dict(n_pairs=len(keys), nets={"N": dict(W=int(vec(N, "W").sum()), C=int(vec(N, "C").sum()), both=int(both(N).sum()))})
        for fam in "FLG":
            names = [f"{fam}{i}" for i in range(1, 6)]
            A = {a: load(d, a, g) for a in names}
            names = [a for a in names if A[a] is not None]
            if not names:
                continue
            for a in names:
                assert all(A[a]["W"][k][0] and A[a]["C"][k][0] for k in keys), f"ważność zależy od sieci w {a}"
                rep["nets"][a] = dict(W=int(vec(A[a], "W").sum()), C=int(vec(A[a], "C").sum()), both=int(both(A[a]).sum()))
            raw = [mcnemar(both(N), both(A[a])) for a in names]
            ph = holm([r[2] for r in raw])
            rows = {a: dict(n10=r[0], n01=r[1], p=r[2], p_holm=h, N_better=bool(h < 0.05 and r[0] > r[1])) for a, r, h in zip(names, raw, ph)}
            rep[f"H_R_{fam}"] = dict(rows=rows, n_beaten=sum(v["N_better"] for v in rows.values()),
                                     ok=bool(len(names) == 5 and all(v["N_better"] for v in rows.values())))
        rep["claim"] = bool(rep.get("H_R_F", {}).get("ok") and rep.get("H_R_L", {}).get("ok"))
        res[f"glu{g}"] = rep
        print(f"Glu {g}: par {len(keys)} |", {a: (v["W"], v["C"], v["both"]) for a, v in rep["nets"].items()})
        for fam in "FLG":
            if f"H_R_{fam}" in rep:
                h = rep[f"H_R_{fam}"]
                print(f"   H-R({fam})", "POTWIERDZONA" if h["ok"] else f"nie ({h['n_beaten']}/5)",
                      {a: (v["n10"], v["n01"], round(v["p_holm"], 4)) for a, v in h["rows"].items()})
        print(f"   schemat ma znaczenie (F i L): {rep['claim']}")
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:3])
