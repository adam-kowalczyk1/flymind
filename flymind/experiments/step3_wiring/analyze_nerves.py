"""Analiza testu „nerwy” (reguły: LOOP_TARGET_nerves_r1.md). Pary jak analyze_touch.py (wd, cs); chwyt = sukces próby C (trial5).
Pliki: {poziom}_{N|Nboth}_g{±1}_s{scena}.json. Uruchom: analyze_nerves.py KATALOG OUT.json"""
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_touch as A  # noqa: E402


def load(d, level, net, g):
    R = {"W": {}, "C": {}}
    files = sorted(glob.glob(os.path.join(d, f"{level}_{net}_g{g}_s*.json")))
    for p in files:
        for r in json.load(open(p))["runs"]:
            R[r["kind"]][(r["item"].split("/")[1], r["seed"])] = r
    # klucz pary: materiał + (ziarno W) — ziarno C = ziarno W + 100
    R["C"] = {(m, s - 100): r for (m, s), r in R["C"].items()}
    return R if files else None


def grip(R):
    C = [r for r in R["C"].values() if r.get("valid")]
    return sum(bool(r["success"]) for r in C), len(C)


def main():
    d, out = sys.argv[1], sys.argv[2]
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for g in ("1", "-1"):
        ideal = load(d, "ideal", "N", g)
        gi = grip(ideal) if ideal else None
        rg = {"ideal": dict(A.summary(ideal), grip=gi)} if ideal else {}
        for lv in ("typ", "pess"):
            N, L = load(d, lv, "N", g), load(d, lv, "Nboth", g)
            if N is None:
                continue
            _, wd, cs = A.pairs(N)
            gn = grip(N)
            r = dict(N=dict(A.summary(N), grip=gn))
            r["NV_A_withdraw_80"] = bool(wd.mean() >= 0.8)
            r["NV_C_still_95"] = bool(cs.mean() >= 0.95)
            if L is not None:
                _, wd2, _ = A.pairs(L)
                r["lesion_both"] = A.summary(L)
                r["NV_B_lesion_le20"] = bool(len(wd2) and wd2.mean() <= 0.2)
            if gi:
                r["NV_D_grip_not_10pp_worse"] = bool(gn[0] / gn[1] >= gi[0] / gi[1] - 0.10)
            r["ALL"] = all(r.get(k) for k in ("NV_A_withdraw_80", "NV_B_lesion_le20", "NV_C_still_95", "NV_D_grip_not_10pp_worse"))
            rg[lv] = r
        res[f"glu{g}"] = rg
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
