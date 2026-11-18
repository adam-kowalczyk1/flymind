"""Ocena B1 (PREREG_BRIDGE.md): bridge_analysis.py MAP.npz RUN.npz OUT.json [TYPE=LPLC2] [VARIANT=1]"""
import json
import os
import re
import sys

import numpy as np

SEL_R = 4.0                     # LPLC2 z środkiem pola recepcyjnego ≤ 4 kolumny od środka bodźca
MIN_CELLS = 3


def flyxy(u, v):
    return np.c_[1.5 * v, -np.sqrt(3) * (u + v / 2)] / np.sqrt(3)


def main(mp, run, out, typ="LPLC2", variant="1"):
    variant = int(variant)                                 # 1 = z hamowaniem LPi (główny), 0 = tylko T4/T5
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    M = np.load(mp); Rn = np.load(run)
    sys.path.insert(0, os.path.dirname(__file__))
    from bridge_loom import CENTERS
    ok = M["in_inside"]
    P = flyxy(M["in_u"][ok], M["in_v"][ok]); w = M["in_w"][ok]; post = M["in_post"][ok]
    n = len(M["post"])
    W = np.bincount(post, w, n)
    rf = np.c_[np.bincount(post, w * P[:, 0], n), np.bincount(post, w * P[:, 1], n)] / np.maximum(W, 1e-9)[:, None]
    is_t = M["post_type"] == typ
    keys = list(Rn.keys())
    models = sorted({int(re.match(r"m(\d+)_", k).group(1)) for k in keys})
    res = dict(type=typ, variant=variant, models=models, cases={})
    for pol in (0, 1):
        LI = []                                            # [case][perm]
        win = []
        for m in models:
            for ci, c in enumerate(CENTERS):
                sel = is_t & (np.hypot(rf[:, 0] - c[0], rf[:, 1] - c[1]) <= SEL_R)
                if sel.sum() < MIN_CELLS:
                    continue
                L = Rn[f"m{m}_p{pol}_loom_{ci}"][variant][:, sel].mean(1)
                Rc = Rn[f"m{m}_p{pol}_recede_{ci}"][variant][:, sel].mean(1)
                Tr = np.mean([Rn[f"m{m}_p{pol}_trans{a}_{ci}"][variant][:, sel].mean(1) for a in (0, 90, 180, 270)], 0)
                ref = np.maximum(Rc, Tr)
                LI.append((L - ref) / (L + ref + 1e-12))
                win.append(bool(L[0] > Rc[0] and L[0] > Tr[0]))
        LI = np.array(LI)
        med = np.median(LI, 0)
        res["cases"][f"pol{pol}"] = dict(n_cases=len(LI), median_LI_identity=float(med[0]), frac_loom_wins=float(np.mean(win)),
                                         median_LI_perms=[float(x) for x in med[1:]], identity_beats_all_perms=bool((med[0] > med[1:]).all()),
                                         n_cells_per_center=[int((is_t & (np.hypot(rf[:, 0] - c[0], rf[:, 1] - c[1]) <= SEL_R)).sum()) for c in CENTERS])
    p0 = res["cases"]["pol0"]
    res["B1_pass"] = bool(p0["median_LI_identity"] > 0 and p0["frac_loom_wins"] >= 0.8 and p0["identity_beats_all_perms"])
    json.dump(res, open(out, "x"), indent=1)
    print(json.dumps({k: (v if k != "cases" else {p: {q: r for q, r in d.items() if q != "median_LI_perms"} for p, d in v.items()}) for k, v in res.items()}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:])
