"""W2b — ocena (LOOP_TARGET_W2b.md). envs/flyvis: w2b_analysis.py MAP.npz DISCS_DIR FLASH.json OUT.json
Czy biegunowość T2 w modelu (t2_flash.py) przewiduje wybiórczość LC4, i czy w modelach z T2 „zrównoważonym” LC4 woli zbliżanie."""
import json
import os
import re
import sys

import numpy as np
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from w2_analysis import CENTERS, MIN_CELLS, SEL_R, flyxy, li, merge  # noqa: E402

P_MAX, MIN_MODELS = 1 / 3, 3


def main(mp, dd, flash, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    M = np.load(mp); F = json.load(open(flash))
    ok = M["in_inside"]; P = flyxy(M["in_u"][ok], M["in_v"][ok]); w = M["in_w"][ok]; post = M["in_post"][ok]; n = len(M["post"])
    W = np.bincount(post, w, n)
    rf = np.c_[np.bincount(post, w * P[:, 0], n), np.bincount(post, w * P[:, 1], n)] / np.maximum(W, 1e-9)[:, None]
    D = merge(os.path.join(dd, "discs_*.npz"))
    models = sorted({int(re.match(r"m(\d+)_", k).group(1)) for k in D if k.startswith("m")} & {int(k) for k in F})
    per = {}
    for m in models:
        per[m] = dict(P=F[str(m)]["T2"]["P"])
        for pol in (0, 1):
            LI, win = [], []
            for ci, c in enumerate(CENTERS):
                sel = np.hypot(rf[:, 0] - c[0], rf[:, 1] - c[1]) <= SEL_R
                if sel.sum() < MIN_CELLS:
                    continue
                L = D[f"m{m}_p{pol}_loom_{ci}"][:, sel].mean(1); Rc = D[f"m{m}_p{pol}_recede_{ci}"][:, sel].mean(1)
                Tr = np.mean([D[f"m{m}_p{pol}_trans{a}_{ci}"][:, sel].mean(1) for a in (0, 90, 180, 270)], 0)
                LI.append(li(L, np.maximum(Rc, Tr))); win.append(bool(L[0] > Rc[0] and L[0] > Tr[0]))
            LI = np.array(LI)
            per[m][f"LI{pol}"] = [float(x) for x in LI[:, 0]]; per[m][f"win{pol}"] = win
            per[m][f"medLI{pol}"] = float(np.median(LI[:, 0])); per[m][f"rank{pol}"] = int(1 + (np.median(LI[:, 1:], 0) >= np.median(LI[:, 0])).sum())
    Pv = np.array([per[m]["P"] for m in models])
    rho = {pol: float(spearmanr(Pv, [per[m][f"medLI{pol}"] for m in models])[0]) for pol in (0, 1)}
    rho_diff = float(spearmanr(Pv, [per[m]["medLI0"] - per[m]["medLI1"] for m in models])[0])
    bal = [m for m in models if abs(per[m]["P"]) <= P_MAX]
    res = dict(models=models, n_models=len(models), rho_dark=rho[0], rho_bright=rho[1], rho_diff=rho_diff, H_T2=bool(rho_diff <= -0.5),
               balanced=bal, per_model={m: {k: v for k, v in per[m].items() if not k.startswith(("LI", "win"))} for m in models})
    if len(bal) >= MIN_MODELS:
        for pol, nm in ((0, "dark"), (1, "bright")):
            LI = np.concatenate([per[m][f"LI{pol}"] for m in bal]); win = np.concatenate([per[m][f"win{pol}"] for m in bal])
            res[nm] = dict(n_cases=len(LI), median_LI=float(np.median(LI)), frac_wins=float(win.mean()),
                           ok=bool(np.median(LI) > 0 and win.mean() >= 0.8))
        res["W2b_pass"] = bool(res["dark"]["ok"] and res["bright"]["ok"])
    else:
        res["W2b_pass"] = None                       # NOT TESTABLE: za mało modeli zrównoważonych
    rest = [m for m in models if m not in bal]
    res["unbalanced_wins"] = {nm: float(np.mean(np.concatenate([per[m][f"win{pol}"] for m in rest]))) for pol, nm in ((0, "dark"), (1, "bright"))} if rest else {}
    json.dump(res, open(out, "x"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "per_model"}, indent=1))
    print("model   P_T2  LI_ciemny  LI_jasny  (miejsce wśród 24: ciemny/jasny)")
    for m in models:
        p = per[m]; print(f"{m:03d}  {p['P']:+.2f}   {p['medLI0']:+.2f}     {p['medLI1']:+.2f}    {p['rank0']}/{p['rank1']}" + ("   <- zrównoważony" if m in bal else ""))


if __name__ == "__main__":
    main(*sys.argv[1:5])
