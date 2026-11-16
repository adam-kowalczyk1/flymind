"""Krok 5 — analiza K5-A (zapisana PRZED testem; reguły LOOP_TARGET_wrist_r1.md). K5-B liczy analyze_reflex.py.
Uruchom: analyze_wrist.py KATALOG PREFIKS OUT.json"""
import glob
import json
import os
import statistics as st
import sys


def main(d, pre, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    res = {}
    for p in sorted(glob.glob(os.path.join(d, pre + "_*_g*.json"))):
        tag = os.path.basename(p)[len(pre) + 1:-5]
        r = json.load(open(p))["runs"]
        W = [x for x in r if x["kind"] == "W" and x["valid"]]
        C = [x for x in r if x["kind"] == "C" and x["valid"]]
        res[tag] = dict(W_valid=len(W), wrist_moved=sum(x.get("dq3_lev", 0) >= 0.02 for x in W), C_valid=len(C),
                        wrist_still=sum(abs(x.get("dq3_lev", 0)) <= 0.01 for x in C), W_strict=sum(x["success"] for x in W),
                        C_strict=sum(x["success"] for x in C), dq3_median=round(st.median([x.get("dq3_lev", 0) for x in W]), 4) if W else None,
                        palm_max_median=st.median([x.get("palm_max", 0) for x in W]) if W else None,
                        palm_max_max=max([x.get("palm_max", 0) for x in W], default=None),
                        other_joint_max=round(max([max(abs(x.get("dq1", 0)), abs(x.get("dq2", 0))) for x in W], default=0), 4))
        print(tag.ljust(8), res[tag])
    ok = {}
    for g in ("1", "-1"):
        n = res.get(f"N_g{g}")
        if n:
            ok[g] = bool(n["wrist_moved"] >= 0.8 * n["W_valid"] and n["wrist_still"] >= 0.95 * n["C_valid"])
    res["K5_A"] = dict(per_glu=ok, ok=bool(len(ok) == 2 and all(ok.values())))
    print("K5-A:", res["K5_A"])
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:4])
