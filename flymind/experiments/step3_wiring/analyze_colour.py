"""Analiza benchmarku „kolor × położenie × czas pętli” (zapisana PRZED testem; reguły LOOP_TARGET_colour_r1.md).
Uruchom: analyze_colour.py KATALOG OUT.json"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_reflex import mcnemar  # noqa: E402

CHROM = ("czerwony", "niebieski", "zolty")
BOOT_SEED, B = 21_991_999, 10_000
LOOP_P99_MAX = 50.0          # ms: 10 ms okres kamery + p99 obliczeń < 60 ms
NI = -0.10                   # granica niegorszości


def load(d, arm, perc, col):
    p = os.path.join(d, f"{arm}_{perc}_{col}.json")
    if not os.path.exists(p):
        return None
    j = json.load(open(p))
    return dict(succ={r["seed"]: bool(r["objects"][0]["success"]) for r in j["runs"]},
                loop=j["summary"]["loop_ms"], n=len(j["runs"]))


def main(d, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res, R = {}, {}
    for arm in ("A_cam", "E_vis_touch"):
        for perc in ("chroma", "green"):
            for col in ("zielony", *CHROM, "bialy"):
                x = load(d, arm, perc, col)
                if x:
                    R[arm, perc, col] = x
                    res[f"{arm}|{perc}|{col}"] = dict(k=sum(x["succ"].values()), n=x["n"], loop_p99=x["loop"]["p99"],
                                                     loop_max=x["loop"]["max"], over_50=x["loop"]["over_50"])
    ver = {}
    for arm in ("A_cam", "E_vis_touch"):                                         # K1: odporność na kolor (percepcja chroma)
        g = R.get((arm, "chroma", "zielony"))
        rows = {}
        for col in CHROM:
            c = R.get((arm, "chroma", col))
            if not (g and c):
                continue
            keys = sorted(set(g["succ"]) & set(c["succ"]))
            a, b = np.array([g["succ"][k] for k in keys], int), np.array([c["succ"][k] for k in keys], int)
            n10, n01, p = mcnemar(a, b)                                          # n10: zielony OK, kolor NIE
            diff = (b.sum() - a.sum()) / len(keys)
            rows[col] = dict(n=len(keys), green=int(a.sum()), colour=int(b.sum()), diff_pp=round(100 * diff, 1), n10=n10, n01=n01,
                             p=p, ok=bool(diff >= NI and not (p < 0.05 and n10 > n01)))
        ver[f"K1_{arm}"] = dict(rows=rows, ok=bool(len(rows) == 3 and all(v["ok"] for v in rows.values())))
    pairs = []                                                                  # K2: sieć vs klasyczny, 4 kolory nasycone
    for col in ("zielony",) + CHROM:
        a, e = R.get(("A_cam", "chroma", col)), R.get(("E_vis_touch", "chroma", col))
        if a and e:
            pairs += [(a["succ"][k], e["succ"][k]) for k in sorted(set(a["succ"]) & set(e["succ"]))]
    if pairs:
        P = np.array(pairs, int)
        rng = np.random.default_rng(BOOT_SEED)
        bs = np.array([(lambda s: (s[:, 1] - s[:, 0]).mean())(P[rng.integers(0, len(P), len(P))]) for _ in range(B)])
        n10, n01, p = mcnemar(P[:, 0], P[:, 1])
        lo, hi = np.percentile(bs, [2.5, 97.5])
        ver["K2_E_vs_A"] = dict(n=len(P), A=int(P[:, 0].sum()), E=int(P[:, 1].sum()), diff_pp=round(100 * float((P[:, 1] - P[:, 0]).mean()), 1),
                                ci95_pp=[round(100 * lo, 1), round(100 * hi, 1)], A_only=n10, E_only=n01, p=p, ok=bool(lo >= NI))
    for arm in ("A_cam", "E_vis_touch"):                                         # K3: czas pętli
        L = {col: R[(arm, "chroma", col)]["loop"] for col in ("zielony",) + CHROM + ("bialy",) if (arm, "chroma", col) in R}
        ver[f"K3_{arm}"] = dict(p99=max(v["p99"] for v in L.values()) if L else None, max=max(v["max"] for v in L.values()) if L else None,
                                over_50=sum(v["over_50"] for v in L.values()), ticks=sum(v["n"] for v in L.values()),
                                ok=bool(L and all(v["p99"] < LOOP_P99_MAX for v in L.values())))
    k0 = {f"{arm}|{col}": sum(R[(arm, "green", col)]["succ"].values()) for arm in ("A_cam", "E_vis_touch") for col in CHROM if (arm, "green", col) in R}
    ver["K0_test_czuly"] = dict(rows=k0, ok=bool(len(k0) == 6 and all(v <= 2 for v in k0.values())))
    ver["WERDYKT"] = bool(ver["K0_test_czuly"]["ok"] and ver.get("K1_E_vis_touch", {}).get("ok") and ver.get("K2_E_vs_A", {}).get("ok")
                          and ver.get("K3_E_vis_touch", {}).get("ok"))
    out_d = dict(results=res, verdict=ver)
    for k, v in ver.items():
        print(k, v)
    with open(out, "x") as f:
        json.dump(out_d, f, indent=1, ensure_ascii=False, default=float)


if __name__ == "__main__":
    main(*sys.argv[1:3])
