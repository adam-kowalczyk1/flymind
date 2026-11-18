"""Analiza testu „widzenie jak oko złożone muchy” (zapisana PRZED testem; reguły LOOP_TARGET_eye_r1.md).
Uruchom: analyze_eye.py KATALOG OUT.json"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_reflex import mcnemar  # noqa: E402

BRIGHT = ("zielony", "niebieski", "zolty")     # jasne dla Rh1 (≈ jak stół) — model przewiduje „niewidoczne”
NI, MAX_BLIND = -0.10, 5


def load(d, arm, perc, col):
    p = os.path.join(d, f"{arm}_{perc}_{col}.json")
    return {r["seed"]: bool(r["objects"][0]["success"]) for r in json.load(open(p))["runs"]} if os.path.exists(p) else None


def main(d, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for arm in ("E_vis_touch", "A_cam"):
        e, c = load(d, arm, "eye", "czerwony"), load(d, arm, "chroma", "czerwony")
        h1 = None
        if e and c:
            keys = sorted(set(e) & set(c))
            a, b = np.array([c[k] for k in keys], int), np.array([e[k] for k in keys], int)
            n10, n01, p = mcnemar(a, b)                       # n10: chroma OK, oko NIE
            diff = float((b.sum() - a.sum()) / len(keys))
            h1 = dict(n=len(keys), chroma=int(a.sum()), eye=int(b.sum()), diff_pp=round(100 * diff, 1), n10=n10, n01=n01, p=p,
                      ok=bool(diff >= NI and not (p < 0.05 and n10 > n01)))
        blind = {col: sum(x.values()) for col in BRIGHT if (x := load(d, arm, "eye", col)) is not None}
        h2 = dict(rows=blind, ok=bool(len(blind) == 3 and all(v <= MAX_BLIND for v in blind.values())))
        res[arm] = dict(H1_czerwony=h1, H2_jasne_niewidoczne=h2, verdict=bool(h1 and h1["ok"] and h2["ok"]))
        print(arm, res[arm])
    res["WERDYKT_siec"] = res["E_vis_touch"]["verdict"]
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False, default=float)


if __name__ == "__main__":
    main(*sys.argv[1:3])
