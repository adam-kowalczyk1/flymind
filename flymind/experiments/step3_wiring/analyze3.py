"""Krok 3 — analiza testu (zapisana i zahaszowana PRZED testem; reguły w LOOP_TARGET_arm3_r1.md).
Uruchom: .venv/bin/python -I -B analyze3.py KATALOG PREFIKS OUT.json     (np. .../test arm3_test analysis.json)
Wynik główny: truth.placed. Dla każdego Glu:
  C1  niegorszość N wobec K: dolna granica 95 % bootstrapu par (10 000 losowań, ziarno 21 299 999) różnicy odsetków ≥ −0,10
  C2  N > R: McNemar dokładny dwustronny p < 0,05 i różnica > 0
  C3S N > każde S_i (tasowania swobodne): McNemar + Holm (5 porównań), wszystkie p_Holm < 0,05 i różnice > 0
  C3L N > każde L_i (tasowania zachowujące warstwy): jw.
  C4  w każdej próbie N: siła ramię↔blat ≤ 5 N oraz bezpiecznik ≤ 10 % taktów aktywnych
Opisowo (bez progu): lift, liczba prób z bezpiecznikiem > 10 % w każdym ramieniu, odchylenie obrotu nadgarstka, częstości pul."""
import json
import math
import os
import sys

import numpy as np


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def mcnemar(a, b):
    """a, b: wektory 0/1 na tych samych próbach. Zwraca (n10, n01, p dwustronne dokładne)."""
    n10 = int(((a == 1) & (b == 0)).sum())
    n01 = int(((a == 0) & (b == 1)).sum())
    n = n10 + n01
    if n == 0:
        return n10, n01, 1.0
    k = min(n10, n01)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n * 2
    return n10, n01, min(1.0, p)


def holm(ps):
    order = np.argsort(ps)
    out, run = [0.0] * len(ps), 0.0
    for r, i in enumerate(order):
        run = max(run, (len(ps) - r) * ps[i])
        out[i] = min(1.0, run)
    return out


def load(d, pre, arm, g):
    p = os.path.join(d, f"{pre}_{arm}_g{g}.json")
    if not os.path.exists(p):
        return None
    runs = json.load(open(p))["runs"]
    return dict(seed=[r["seed"] for r in runs], placed=np.array([int(bool(r["truth"]["placed"])) for r in runs]),
                lift=np.array([int(bool(r["truth"]["lift"])) for r in runs]),
                fmax=np.array([r["fmax"] for r in runs]), arm_table=sum(r["unwanted"]["arm_table"] for r in runs),
                guard_frac=np.array([r["guard"] / max(r.get("act_ticks", 0), 1) for r in runs]),
                roll=np.array([r.get("roll_dev", 0.0) for r in runs]),
                rates=(np.array([r["mean_rates_active"] for r in runs if r.get("mean_rates_active")]).mean(0).round(1).tolist()
                       if any(r.get("mean_rates_active") for r in runs) else None))


def main(d, pre, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for g in ("-1", "1"):
        A = {a: load(d, pre, a, g) for a in ["N", "K", "R"] + [f"S{i}" for i in range(1, 6)] + [f"L{i}" for i in range(1, 6)]}
        N = A["N"]
        if N is None:
            continue
        n = len(N["placed"])
        rep = dict(n=n, arms={})
        for a, x in A.items():
            if x is None:
                continue
            assert x["seed"] == N["seed"], f"inne sceny w {a}"
            rep["arms"][a] = dict(placed=int(x["placed"].sum()), wilson95=wilson(int(x["placed"].sum()), n), lift=int(x["lift"].sum()),
                                  fmax_N=float(x["fmax"].max()), arm_table=x["arm_table"], guard_gt10pct_trials=int((x["guard_frac"] > 0.10).sum()),
                                  guard_mean=round(float(x["guard_frac"].mean()), 4), roll_dev_median=round(float(np.median(x["roll"])), 3),
                                  pool_rates_Hz=x["rates"])
        rng = np.random.default_rng(21_299_999 if g == "1" else 21_299_998)
        if A["K"] is not None:
            diff = N["placed"] - A["K"]["placed"]
            bs = np.array([diff[rng.integers(n, size=n)].mean() for _ in range(10_000)])
            lo, hi = np.percentile(bs, [2.5, 97.5])
            rep["C1"] = dict(diff=round(float(diff.mean()), 4), ci95=[round(float(lo), 4), round(float(hi), 4)], ok=bool(lo >= -0.10))
        if A["R"] is not None:
            n10, n01, p = mcnemar(N["placed"], A["R"]["placed"])
            rep["C2"] = dict(n10=n10, n01=n01, p=p, diff=round(float((N["placed"] - A["R"]["placed"]).mean()), 4), ok=bool(p < 0.05 and n10 > n01))
        for fam in ("S", "L"):
            names = [f"{fam}{i}" for i in range(1, 6) if A[f"{fam}{i}"] is not None]
            if not names:
                continue
            raw = [mcnemar(N["placed"], A[a]["placed"]) for a in names]
            ph = holm([r[2] for r in raw])
            rows = {a: dict(n10=r[0], n01=r[1], p=r[2], p_holm=h, diff=round(float((N["placed"] - A[a]["placed"]).mean()), 4),
                            N_better=bool(h < 0.05 and r[0] > r[1]), N_worse=bool(h < 0.05 and r[0] < r[1])) for a, r, h in zip(names, raw, ph)}
            rep[f"C3{fam}"] = dict(rows=rows, n_compared=len(names), ok=bool(len(names) == 5 and all(v["N_better"] for v in rows.values())))
        hs = [a for a in [f"S{i}" for i in range(1, 6)] + [f"L{i}" for i in range(1, 6)] if A[a] is not None]
        if hs:
            raw = []
            for a in hs:
                dlt = N["roll"] - A[a]["roll"]
                lo_n, hi_n = int((dlt < 0).sum()), int((dlt > 0).sum())
                m = lo_n + hi_n
                pv = min(1.0, 2 * sum(math.comb(m, i) for i in range(min(lo_n, hi_n) + 1)) / 2 ** m) if m else 1.0
                raw.append((lo_n, hi_n, pv))
            ph = holm([r[2] for r in raw])
            rows = {a: dict(N_smaller=r[0], N_larger=r[1], p=r[2], p_holm=h, N_calmer=bool(h < 0.05 and r[0] > r[1])) for a, r, h in zip(hs, raw, ph)}
            rep["H_spokoj"] = dict(rows=rows, n_compared=len(hs), ok=bool(len(hs) == 10 and all(v["N_calmer"] for v in rows.values())))
        rep["C4"] = dict(fmax_N=float(N["fmax"].max()), guard_max=round(float(N["guard_frac"].max()), 4),
                         ok=bool(N["fmax"].max() <= 5.0 and N["guard_frac"].max() <= 0.10))
        res[f"glu{g}"] = rep
        print(f"Glu {g}: placed", {a: v["placed"] for a, v in rep["arms"].items()})
        for c in ("C1", "C2", "C3S", "C3L", "C4", "H_spokoj"):
            if c in rep:
                print("  ", c, "OK" if rep[c]["ok"] else "nie", {k: v for k, v in rep[c].items() if k not in ("rows", "ok")})
    k0 = os.path.join(d, f"{pre}_K0.json")
    if os.path.exists(k0):
        r = json.load(open(k0))["runs"]
        res["K0"] = dict(placed=sum(bool(x["truth"]["placed"]) for x in r), n=len(r))
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:4])
