"""Krok 2(b): analiza wg LOOP_TARGET_b_r2.md, sekcja 4 (i 8.6 dla treningu).

Pary = te same (przedmiot, ziarno sceny) we wszystkich ramionach. Wynik główny: truth["lift"].
  N vs K:  niegorszość — dolna granica 95 % bootstrapu (sparowanego, 10 000, ziarno 20 299 999) różnicy ≥ −0,10
  N vs R:  McNEMAR dokładny jednostronny p < 0,05 ORAZ 95 % przedział różnicy > 0
  N vs Si: McNemar jednostronny, korekta Holma (rodzina α 0,05)
  siła:    max siła ramię↔blat ≤ 5 N w każdej próbie N;  bezpiecznik ≤ 10 % taktów fazy podniesienia N
  .venv/bin/python -I -B analyze_b.py DIR GLU [--out PLIK]   (DIR: pliki *_N_*, *_S?_*, *_R_*, *_K_*, *_K0* z jednej wersji)
"""
import argparse
import glob
import json
import math
import os
import re

import numpy as np
from scipy.stats import binomtest

BOOT_SEED, NB, MARGIN, FMAX, GUARD = 20_299_999, 10_000, 0.10, 5.0, 0.10


def wilson(k, n, z=1.96):
    if n == 0:
        return [float("nan")] * 2
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, c - h), 3), round(min(1.0, c + h), 3)]


def mcnemar(a, b):
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    p = float(binomtest(n10, n10 + n01, 0.5, "greater").pvalue) if n10 + n01 else 1.0
    return dict(a_only=n10, b_only=n01, p=round(p, 5))


def boot(a, b):
    d = a.astype(float) - b.astype(float)
    m = d[np.random.default_rng(BOOT_SEED).integers(len(d), size=(NB, len(d)))].mean(1)
    return dict(diff=round(float(d.mean()), 4), ci95=[round(float(x), 4) for x in np.percentile(m, [2.5, 97.5])])


def holm(ps, alpha=0.05):
    order, out, m = np.argsort(ps), [False] * len(ps), len(ps)
    for r, i in enumerate(order):
        if ps[i] <= alpha / (m - r):
            out[i] = True
        else:
            break
    return out


def share(runs):
    tot = snn = 0
    for r in runs:
        for s, v in r["safety_stats"].items():
            tot += v["ticks"]
            snn += v["ticks"] if s.startswith("snn") else 0
    j1 = sum(v["ticks"] for r in runs for s, v in r["safety_stats"].items() if s in ("snn:legT1L", "snn:legT1L_shuffled"))
    return dict(snn_all_channels=round(snn / tot, 4) if tot else None, joint1_snn_ticks=j1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("glu")
    ap.add_argument("--out")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.dir, "*.json")))
    arms = {}
    for f in files:
        d = json.load(open(f))
        if d.get("arm") is None or (d["arm"] != "K0" and float(d["glu"]) != float(a.glu)):
            continue
        name = d["arm"] if d["arm"] != "S" else f"S{d['shuffle_seed'] % 1000}"
        arms[name] = d
    keys = sorted({(r["item"], r["seed"]) for r in arms["N"]["runs"]})
    L = {n: np.array([next(r for r in d["runs"] if (r["item"], r["seed"]) == k)["truth"]["lift"] for k in keys])
         for n, d in arms.items()}
    P = {n: np.array([next(r for r in d["runs"] if (r["item"], r["seed"]) == k)["success"] for k in keys]) for n, d in arms.items()}
    n = len(keys)
    res = dict(glu=float(a.glu), n=n, files={k: os.path.basename(v["tag"]) for k, v in arms.items()},
               lift={k: dict(k=int(v.sum()), n=n, wilson95=wilson(int(v.sum()), n)) for k, v in L.items()},
               placed={k: int(v.sum()) for k, v in P.items()})
    N = L["N"]
    res["N_vs_K"] = dict(**boot(N, L["K"]), **mcnemar(N, L["K"])) if "K" in L else None
    res["N_vs_R"] = dict(**boot(N, L["R"]), **mcnemar(N, L["R"])) if "R" in L else None
    S = sorted(k for k in L if re.fullmatch(r"S\d+", k))
    res["N_vs_S"] = {s: dict(**boot(N, L[s]), **mcnemar(N, L[s])) for s in S}
    hp = holm([res["N_vs_S"][s]["p"] for s in S]) if S else []
    rn = arms["N"]["runs"]
    fm = max(r["fmax"] for r in rn)
    lt, gd = sum(r["lift_ticks"] for r in rn), sum(r["guard"] for r in rn)
    res["force_N_max"] = fm
    res["force_max"] = {k: max(r["fmax"] for r in d["runs"]) for k, d in arms.items()}
    res["guard"] = {k: dict(guard_ticks=sum(r["guard"] for r in d["runs"]), lift_ticks=sum(r["lift_ticks"] for r in d["runs"]))
                    for k, d in arms.items() if k != "K0"}
    res["share"] = {k: share(d["runs"]) for k, d in arms.items()}
    res["no_lift_reasons"] = {k: sum("no_lift" in r["reasons"] for r in d["runs"]) for k, d in arms.items()}
    c1 = res["N_vs_K"] is not None and res["N_vs_K"]["ci95"][0] >= -MARGIN
    c2 = res["N_vs_R"] is not None and res["N_vs_R"]["p"] < 0.05 and res["N_vs_R"]["ci95"][0] > 0
    c3 = bool(S) and all(hp)
    c4 = fm <= FMAX and (gd / lt if lt else 0.0) <= GUARD
    res["criteria"] = dict(C1_noninferior_K=c1, C2_beats_reflex=c2, C3_beats_all_shuffles_holm=c3, holm=dict(zip(S, hp)),
                           C4_force_and_guard=c4, guard_frac=round(gd / lt, 4) if lt else None, target_met=c1 and c2 and c3 and c4)
    print(json.dumps(res, indent=1))
    if a.out:
        with open(a.out, "x") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
