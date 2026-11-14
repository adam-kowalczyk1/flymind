"""Krok 7: analiza wg CONFLICT_TARGET_r1.md. Pary = ta sama scena (item, seed) w „on” i „sham” tego samego ramienia i Glu.
  .venv/bin/python -I -B analyze_conflict.py DIR [--out PLIK]
"""
import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np
from scipy.stats import binomtest, wilcoxon

BOOT = 20_999_999


def boot_ci(d, nb=10_000):
    d = np.asarray(d, float)
    m = d[np.random.default_rng(BOOT).integers(len(d), size=(nb, len(d)))].mean(1)
    return [round(float(x), 5) for x in np.percentile(m, [2.5, 97.5])]


def mcnemar2(a, b):
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    p = float(binomtest(n10, n10 + n01, 0.5).pvalue) if n10 + n01 else 1.0
    return dict(on_only=n10, sham_only=n01, p=round(p, 5))


def effect(on, sham, keys=None):
    ks = sorted(set(on) & set(sham) if keys is None else keys)
    ks = [k for k in ks if on[k]["win_first"] and sham[k]["win_first"]]
    res = dict(n_pairs=len(ks))
    for name, f in (("tau", lambda w: w["tau_mean"]), ("dnaL", lambda w: w["dn_mean"][0]), ("dnaR", lambda w: w["dn_mean"][1]),
                    ("gL", lambda w: w["g_mean"][0]), ("gR", lambda w: w["g_mean"][1])):
        d = np.array([f(on[k]["win_first"]) - f(sham[k]["win_first"]) for k in ks])
        nz = d[d != 0]
        res[name] = dict(mean=round(float(d.mean()), 5) if len(d) else None, ci95=boot_ci(d) if len(d) else None,
                         wilcoxon_p=round(float(wilcoxon(nz).pvalue), 6) if len(nz) >= 6 else None, n_nonzero=int(len(nz)))
    allk = sorted(set(on) & set(sham) if keys is None else keys)
    for name, f in (("placed", lambda r: r["success"]), ("released", lambda r: "snn_released" in r["reasons"])):
        a = np.array([f(on[k]) for k in allk], bool)
        b = np.array([f(sham[k]) for k in allk], bool)
        res[name] = dict(on=int(a.sum()), sham=int(b.sum()), n=len(allk), **mcnemar2(a, b))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--out")
    a = ap.parse_args()
    D = defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(a.dir, "*.json"))):
        d = json.load(open(f))
        if "stim" not in d:
            continue
        arm = "N" if d["arm"] == "N" else f"S{d['shuffle_seed'] % 1000}"
        D[(arm, d["glu"])][d["stim"]] = {(r["item"], r["seed"]): r for r in d["runs"]}
    out = {}
    for glu in sorted({g for _, g in D}):
        N = D.get(("N", glu), {})
        if not {"on", "sham"} <= set(N):
            continue
        r = dict(N=effect(N["on"], N["sham"]))
        S = sorted(k for k, g in D if g == glu and k != "N")
        common = None
        for s in S:
            if {"on", "sham"} <= set(D[(s, glu)]):
                common = set(D[(s, glu)]["on"]) & set(D[(s, glu)]["sham"]) if common is None else common & set(D[(s, glu)]["on"])
        if S and common:
            r["N_common"] = effect(N["on"], N["sham"], sorted(common & set(N["on"])))
            r["S"] = {s: effect(D[(s, glu)]["on"], D[(s, glu)]["sham"], sorted(common)) for s in S if {"on", "sham"} <= set(D[(s, glu)])}
        t = r["N"]["tau"]
        manip = r["N"]["dnaL"]
        r["decision"] = dict(
            manipulation_ok=bool(manip["wilcoxon_p"] is not None and manip["wilcoxon_p"] < 0.05 and manip["mean"] > 0),
            vision_changes_grip=bool(t["wilcoxon_p"] is not None and t["wilcoxon_p"] < 0.05 and (t["ci95"][0] > 0 or t["ci95"][1] < 0)),
        )
        if "S" in r and r["S"]:
            eN = abs(r["N_common"]["tau"]["mean"] or 0)
            eS = max(abs(v["tau"]["mean"] or 0) for v in r["S"].values())
            r["decision"].update(N_common_abs=round(eN, 5), S_max_abs=round(eS, 5),
                                 data_specific=bool(r["decision"]["vision_changes_grip"] and eN > eS))
        out[str(glu)] = r
    print(json.dumps(out, indent=1))
    if a.out:
        with open(a.out, "x") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
