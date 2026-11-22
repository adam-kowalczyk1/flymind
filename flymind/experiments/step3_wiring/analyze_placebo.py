"""Test „placebo” — analiza (zapisana PRZED liczeniem; reguły PREREG_PLACEBO.md).
Uruchom: analyze_placebo.py select KATALOG_TRAIN OUT.json   |   analyze_placebo.py test KATALOG_TEST SELECT.json OUT.json"""
import itertools
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_reflex import holm, mcnemar  # noqa: E402

SCENES = (27111, 27112, 27113)
MULTS = (0.6, 0.8, 1.0, 1.25, 1.6)
NF = NL = 10          # tasowań w P1
NP2 = 6               # tasowań na rodzinę w P2
MARGIN = 5            # par


def load(path, off=0):
    """{klucz pary: (W_ważne, W_ok, C_ważne, C_ok)} → wynik OBA i ważność"""
    if not os.path.exists(path):
        return None
    R = {"W": {}, "C": {}}
    for r in json.load(open(path))["runs"]:
        R[r["kind"]][r["seed"] - (100 if r["kind"] == "C" else 0)] = (bool(r["valid"]), bool(r["success"]))
    return R


def merge(paths):
    """kilka scen → {klucz: (ważna, OBA)}"""
    out = {}
    for p in paths:
        R = load(p)
        if R is None:
            return None
        for k in R["W"]:
            c = R["C"].get(k, (False, False))
            assert k not in out
            out[k] = (R["W"][k][0] and c[0], int(R["W"][k][1] and c[1]))
    return out


def best_m(tr):
    """tr: {m: wynik} → wybrane m: najwięcej par OBA; remis → najbliżej 1 (w log), potem mniejsze"""
    return sorted(tr, key=lambda m: (-tr[m], abs(math.log(m)), m))[0]


def select(d, out):
    nets = ["N"] + [f"F{i:02d}" for i in range(1, NP2 + 1)] + [f"L{i:02d}" for i in range(1, NP2 + 1)]
    sel = {}
    for n in nets:
        tr = {}
        for m in MULTS:
            R = merge([os.path.join(d, f"tr_{n}_m{m}.json")])
            tr[m] = sum(v[1] for v in R.values() if v[0])
        sel[n] = dict(train=tr, m=best_m(tr))
        print(n, tr, "->", sel[n]["m"])
    with open(out, "x") as f:
        json.dump(sel, f, indent=1)


def vecs(d, names_m):
    """{nazwa: słownik par} dla zadanych (nazwa, m); ważne pary = wspólne dla wszystkich sieci"""
    M = {n: merge([os.path.join(d, f"{s}_{n}_m{m}.json") for s in SCENES]) for n, m in names_m.items()}
    missing = [n for n in M if M[n] is None]
    if missing:
        sys.exit(f"brak plików: {missing}")
    keys = sorted(k for k in M["N"] if all(M[n][k][0] for n in M))
    return keys, {n: np.array([M[n][k][1] for k in keys]) for n in M}


def beats_all(v, a, others):
    raw = [mcnemar(v[a], v[b]) for b in others]
    ph = holm([r[2] for r in raw])
    return all(h < 0.05 and r[0] > r[1] for r, h in zip(raw, ph)), [(r[0], r[1], round(h, 4)) for r, h in zip(raw, ph)]


def p1(d):
    F, L = [f"F{i:02d}" for i in range(1, NF + 1)], [f"L{i:02d}" for i in range(1, NL + 1)]
    keys, v = vecs(d, {n: 1.0 for n in ["N"] + F + L})
    sc = {n: int(x.sum()) for n, x in v.items()}
    res = dict(n_pairs=len(keys), scores=sc)
    for fam, names in (("F", F), ("L", L)):
        ok, rows = beats_all(v, "N", names)
        pl = {a: beats_all(v, a, [b for b in names if b != a])[0] for a in names}
        sig_ss = sum(1 for a, b in itertools.combinations(names, 2) if mcnemar(v[a], v[b])[2] < 0.05)
        sig_ns = sum(1 for b in names if mcnemar(v["N"], v[b])[2] < 0.05 and sc["N"] > sc[b])
        res[fam] = dict(C1_N_beats_all=ok, rows=rows, placebo_pass=pl, placebo_FPR=sum(pl.values()) / len(names),
                        shuffle_pairs_significant_of_45=sig_ss, N_vs_shuffles_significant_of_10=sig_ns,
                        spread=max(sc[a] for a in names) - min(sc[a] for a in names))
    sh = sorted((sc[n] for n in F + L), reverse=True)
    res["rank_p"] = (1 + sum(s >= sc["N"] for s in sh)) / (len(sh) + 1)
    res["N_margin"], res["placebo_margin"] = sc["N"] - sh[0], sh[0] - sh[1]
    res["C1"] = bool(res["F"]["C1_N_beats_all"] and res["L"]["C1_N_beats_all"])
    res["C2"] = bool(res["F"]["placebo_FPR"] <= 0.1 and res["L"]["placebo_FPR"] <= 0.1 and res["rank_p"] <= 0.05
                     and res["N_margin"] >= res["placebo_margin"] + MARGIN)
    return res


def p2(d, sel):
    names_m = {n: sel[n]["m"] for n in sel}
    F, L = [n for n in sel if n[0] == "F"], [n for n in sel if n[0] == "L"]
    keys, v = vecs(d, names_m)
    sc = {n: int(x.sum()) for n, x in v.items()}
    res = dict(n_pairs=len(keys), chosen_m=names_m, scores=sc)
    for fam, names in (("F", F), ("L", L)):
        ok, rows = beats_all(v, "N", names)
        res[fam] = dict(N_beats_all=ok, rows=rows)
    res["C3"] = bool(res["F"]["N_beats_all"] and res["L"]["N_beats_all"] and sc["N"] > max(sc[n] for n in F + L))
    return res


if __name__ == "__main__":
    if sys.argv[1] == "select":
        select(sys.argv[2], sys.argv[3])
    else:
        d, sel, out = sys.argv[2:5]
        res = dict(P1=p1(d), P2=p2(d, json.load(open(sel))))
        res["verdict"] = "REAL" if (res["P1"]["C1"] and res["P1"]["C2"] and res["P2"]["C3"]) else \
            "PARTIAL" if (res["P1"]["C1"] and res["P1"]["C2"]) else "INFLATED"
        with open(out, "x") as f:
            json.dump(res, f, indent=1, default=float)
        print(json.dumps(res, indent=1, default=float))
