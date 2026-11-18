"""Etap 1 — analiza „sieć sama kończy zwykły dotyk dłoni” (reguły: LOOP_TARGET_touch_r1.md).
Para = ten sam materiał i poza: próba W (dotyk dłoni) + próba C (chwyt bez dotyku dłoni).
  wd  = w próbie W dłoń puszczona na końcu (palm_end < 0,05 N)
  cs  = w próbie C łokieć i nadgarstek stoją (|dq2|, |dq3| ≤ 0,01 rad)
  sel = wd · cs (odpowiedź wybiórcza: wycofanie po dotyku i spokój bez dotyku)
Uruchom: analyze_touch.py KATALOG OUT.json [--shuffles F1,..,L5] [--lesion-tag Nboth]"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_brainleg import holm, mcnemar  # noqa: E402

P_OFF, STILL = 0.05, 0.01


def load(d, tag, g):
    p = os.path.join(d, f"{tag}_g{g}.json")
    if not os.path.exists(p):
        return None
    R = {"W": {}, "C": {}}
    for r in json.load(open(p))["runs"]:
        R[r["kind"]][(r["item"].split("/")[1], r["seed"] % 10)] = r
    return R


def pairs(R):
    keys = sorted(k for k in R["W"] if R["W"][k].get("valid") and R["W"][k].get("palm_end") is not None
                  and k in R["C"] and R["C"][k].get("valid") and R["C"][k].get("dq2") is not None)
    wd = np.array([int(R["W"][k]["palm_end"] < P_OFF) for k in keys])
    cs = np.array([int(abs(R["C"][k]["dq2"]) <= STILL and abs(R["C"][k]["dq3_lev"]) <= STILL) for k in keys])
    return keys, wd, cs


def summary(R):
    keys, wd, cs = pairs(R)
    W = [R["W"][k] for k in keys]
    toff = [w["t_off"] for w in W if w.get("t_off") is not None]
    return dict(n_pairs=len(keys), withdraw=int(wd.sum()), C_still=int(cs.sum()), selective=int((wd * cs).sum()),
                t_off_median=None if not toff else float(np.median(toff)), recontact_trials=int(sum(w["recontact"] > 0 for w in W)),
                elbow_moved=int(sum(abs(w["dq2"]) >= 0.01 for w in W)), wrist_moved=int(sum(w["dq3_lev"] >= 0.02 for w in W)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("out")
    ap.add_argument("--shuffles", default="F1,F2,F3,F4,F5,L1,L2,L3,L4,L5")
    ap.add_argument("--lesion-tag", default="Nboth")
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"istnieje {a.out}")
    res = {}
    for g in ("1", "-1"):
        N = load(a.dir, "N", g)
        if N is None:
            continue
        keys, wd, cs = pairs(N)
        rep = dict(N=summary(N))
        rep["T1_A_withdraw_80"] = bool(wd.mean() >= 0.8)
        rep["T1_C_still_95"] = bool(cs.mean() >= 0.95)
        Lz = load(a.dir, a.lesion_tag, g)
        if Lz is not None:
            k2, wd2, _ = pairs(Lz)
            rep["lesion_both"] = summary(Lz)
            rep["T1_B_lesion_withdraw_le20"] = bool(len(k2) and wd2.mean() <= 0.2)
        for fam in "FL":
            names = [s for s in a.shuffles.split(",") if s.startswith(fam)]
            rows = {}
            for s in names:
                S = load(a.dir, s, g)
                if S is None:
                    continue
                ks, wds, css = pairs(S)
                common = [k for k in keys if k in ks]
                iN, iS = [keys.index(k) for k in common], [ks.index(k) for k in common]
                n10, n01, p = mcnemar((wd * cs)[iN], (wds * css)[iS])
                rows[s] = dict(summary(S), n_common=len(common), N_only=n10, S_only=n01, p=p)
            if rows:
                ph = holm([r["p"] for r in rows.values()])
                for r, q in zip(rows.values(), ph):
                    r["p_holm"] = q
                rep[f"H_{fam}"] = dict(pass_=bool(all(r["p_holm"] < 0.05 and r["N_only"] > r["S_only"] for r in rows.values())),
                                       arms=rows)
        res[f"glu{g}"] = rep
    with open(a.out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
