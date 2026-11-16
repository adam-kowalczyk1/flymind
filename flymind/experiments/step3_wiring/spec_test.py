"""Krok 3b — test wybiórczości (reguły: LOOP_TARGET_spec_r1.md, zapisane przed uruchomieniem). Bez robota.
Uruchom: spec_test.py OUT_DIR GLU FAMILY FIRST LAST     FAMILY: data | F | L | G"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import explore_specificity as ES  # noqa: E402
import nets  # noqa: E402
import side_shuffle  # noqa: E402

JN = nets.JN
BASE = {"F": 21_250_000, "L": 21_260_000, "G": 21_270_000}


def main(out_dir, glu, fam, first, last):
    glu, first, last = float(glu), int(first), int(last)
    out = os.path.join(out_dir, f"spec_g{glu:+.0f}_{fam}_{first:02d}_{last:02d}.json")
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    bodies, m = nets.bodies_for("pre")
    spec, idx, rep, layer = nets.build_rule(glu, 0.2, "pre")
    t2, t1 = ES.mn_sets(bodies, m)
    res = dict(glu=glu, family=fam, W_sha256=rep["W_sha256"], rows={})
    if fam == "data":
        res["rows"]["N"] = ES.specificity(spec.W, idx, t2, t1)
    else:
        g = np.array(layer, object)
        if fam == "G":
            pos = {b: i for i, b in enumerate(bodies)}
            for b in m["sens2"]:
                g[pos[b]] = "S_T2"
            for b in m["sens1"]:
                g[pos[b]] = "S_T1"
            g[t2] = "M_T2"
            g[t1] = "M_T1"
            res["groups"] = {k: int((g == k).sum()) for k in sorted(set(g))}
        for i in range(first, last + 1):
            seed = BASE[fam] + i
            sh = JN.visual_path.shuffle(spec, seed, equal_weight=True) if fam == "F" else \
                side_shuffle.shuffle_within_side(spec, np.array(g, str), seed)
            res["rows"][str(seed)] = ES.specificity(sh.W, idx, t2, t1)
            print(glu, fam, seed, res["rows"][str(seed)]["W"], flush=True)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:6])
