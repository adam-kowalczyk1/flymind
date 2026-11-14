"""Krok 2 (stawy c–e, całe ramię): analiza jak analyze_b.py (te same funkcje), z wyborem wyniku głównego.
  --outcome lift|placed     truth["lift"] albo success (= placed)
  --no-reflex               kryterium C2 (lepiej niż odruch R) nie dotyczy zadania (ustalone w LOOP_TARGET przed iteracją)
Kryteria: C1 niegorszość wobec K (dolna granica bootstrapu ≥ −0,10), C2 McNemar N > R (p < 0,05) i 95 % CI > 0,
C3 McNemar N > Sᵢ z Holmem, C4 siła ≤ 5 N we wszystkich próbach N i bezpiecznik ≤ 10 % taktów aktywnych.
  .venv/bin/python -I -B analyze_joint.py DIR GLU --outcome lift [--no-reflex] [--out PLIK]
"""
import argparse
import glob
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_b import FMAX, GUARD, MARGIN, boot, holm, mcnemar, share, wilson  # noqa: E402


def outcome(r, key):
    return r["truth"]["lift"] if key == "lift" else r["success"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("glu")
    ap.add_argument("--outcome", choices=("lift", "placed"), required=True)
    ap.add_argument("--no-reflex", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    arms = {}
    for f in sorted(glob.glob(os.path.join(a.dir, "*.json"))):
        d = json.load(open(f))
        if d.get("arm") is None or (d["arm"] != "K0" and float(d["glu"]) != float(a.glu)):
            continue
        arms[d["arm"] if d["arm"] != "S" else f"S{d['shuffle_seed'] % 1000}"] = d
    keys = sorted({(r["item"], r["seed"]) for r in arms["N"]["runs"]})
    pick = lambda d, k: next(r for r in d["runs"] if (r["item"], r["seed"]) == k)  # noqa: E731
    Y = {n: np.array([outcome(pick(d, k), a.outcome) for k in keys]) for n, d in arms.items()}
    L = {n: np.array([pick(d, k)["truth"]["lift"] for k in keys]) for n, d in arms.items()}
    P = {n: np.array([pick(d, k)["success"] for k in keys]) for n, d in arms.items()}
    n = len(keys)
    res = dict(glu=float(a.glu), outcome=a.outcome, n=n, files={k: v["tag"] for k, v in arms.items()},
               main={k: dict(k=int(v.sum()), n=n, wilson95=wilson(int(v.sum()), n)) for k, v in Y.items()},
               lift={k: int(v.sum()) for k, v in L.items()}, placed={k: int(v.sum()) for k, v in P.items()})
    N = Y["N"]
    res["N_vs_K"] = dict(**boot(N, Y["K"]), **mcnemar(N, Y["K"])) if "K" in Y else None
    res["N_vs_R"] = dict(**boot(N, Y["R"]), **mcnemar(N, Y["R"])) if "R" in Y else None
    res["N_vs_K0"] = dict(**boot(N, Y["K0"]), **mcnemar(N, Y["K0"])) if "K0" in Y else None
    S = sorted((k for k in Y if re.fullmatch(r"S\d+", k)), key=lambda s: int(s[1:]))
    res["N_vs_S"] = {s: dict(**boot(N, Y[s]), **mcnemar(N, Y[s])) for s in S}
    hp = holm([res["N_vs_S"][s]["p"] for s in S]) if S else []
    rn = arms["N"]["runs"]
    fm = max(r["fmax"] for r in rn)
    act = sum(r.get("act_ticks", r.get("lift_ticks", 0)) for r in rn)
    gd = sum(r["guard"] for r in rn)
    res["force_max"] = {k: max(r["fmax"] for r in d["runs"]) for k, d in arms.items()}
    res["force_gt5N_trials"] = {k: sum(r["fmax"] > FMAX for r in d["runs"]) for k, d in arms.items()}
    res["guard"] = {k: dict(guard_ticks=sum(r["guard"] for r in d["runs"]),
                            active_ticks=sum(r.get("act_ticks", r.get("lift_ticks", 0)) for r in d["runs"]))
                    for k, d in arms.items() if k != "K0"}
    res["share"] = {k: share(d["runs"]) for k, d in arms.items()}
    res["snn_arm_ticks"] = {k: sum(v["ticks"] for r in d["runs"] for s, v in r["safety_stats"].items()
                                   if s.startswith("snn:legT1L")) for k, d in arms.items()}
    res["reasons"] = {k: {x: sum(x in r["reasons"] for r in d["runs"]) for x in sorted({y for r in d["runs"] for y in r["reasons"]})}
                      for k, d in arms.items()}
    res["roll_dev_max"] = {k: max(r.get("roll_dev", 0.0) for r in d["runs"]) for k, d in arms.items()}
    c1 = res["N_vs_K"] is not None and res["N_vs_K"]["ci95"][0] >= -MARGIN
    c2 = None if a.no_reflex else (res["N_vs_R"] is not None and res["N_vs_R"]["p"] < 0.05 and res["N_vs_R"]["ci95"][0] > 0)
    c3 = bool(S) and all(hp)
    c4 = fm <= FMAX and (gd / act if act else 0.0) <= GUARD
    res["criteria"] = dict(C1_noninferior_K=c1, C2_beats_reflex=c2, C3_beats_all_shuffles_holm=c3, holm=dict(zip(S, hp)),
                           C4_force_and_guard=c4, guard_frac=round(gd / act, 4) if act else None,
                           target_met=bool(c1 and (c2 is None or c2) and c3 and c4))
    print(json.dumps(res, indent=1))
    if a.out:
        with open(a.out, "x") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
