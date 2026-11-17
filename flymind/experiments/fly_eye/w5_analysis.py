"""W5 — ocena (LOOP_TARGET_W5.md). .venv lub envs/flyvis: w5_analysis.py MAP.npz W5_DIR OUT.json
Czyta W5_DIR/discs_rot30_*.npz, discs_rot210_*.npz (opisowo), cam_*.npz. Reguły: 0 = LIN (B1 wariant 0), 1 = AND."""
import glob
import json
import os
import re
import sys

import numpy as np

SEL_R, MIN_CELLS = 4.0, 3                                   # jak bridge_analysis.py
CENTERS = [(0.0, 0.0)] + [(5 * np.cos(np.radians(k)), 5 * np.sin(np.radians(k))) for k in range(30, 360, 60)]
CAM = ["S1_spokoj", "S2_bok", "S2r_bok_wstecz", "S3_zblizanie", "S4_ramie"]
RULES = {0: "LIN", 1: "AND"}


def flyxy(u, v):
    return np.c_[1.5 * v, -np.sqrt(3) * (u + v / 2)] / np.sqrt(3)


def merge(pat):
    d = {}
    for f in sorted(glob.glob(pat)):
        d.update(np.load(f))
    return d


def rf_of(M):
    ok = M["in_inside"]; P = flyxy(M["in_u"][ok], M["in_v"][ok]); w = M["in_w"][ok]; post = M["in_post"][ok]; n = len(M["post"])
    W = np.bincount(post, w, n)
    return np.c_[np.bincount(post, w * P[:, 0], n), np.bincount(post, w * P[:, 1], n)] / np.maximum(W, 1e-9)[:, None], P, w, post, W


def discs(D, M, rule, pol):
    rf = rf_of(M)[0]; is_t = M["post_type"] == "LPLC2"
    models = sorted({int(re.match(r"m(\d+)_", k).group(1)) for k in D if k.startswith("m")})
    LI, win, mod, Z, O, Pm = [], [], [], [], [], []
    for m in models:
        for ci, c in enumerate(CENTERS):
            sel = is_t & (np.hypot(rf[:, 0] - c[0], rf[:, 1] - c[1]) <= SEL_R)
            if sel.sum() < MIN_CELLS:
                continue
            L = D[f"m{m}_p{pol}_loom_{ci}"][rule][:, sel].mean(1); Rc = D[f"m{m}_p{pol}_recede_{ci}"][rule][:, sel].mean(1)
            Tr = np.mean([D[f"m{m}_p{pol}_trans{a}_{ci}"][rule][:, sel].mean(1) for a in (0, 90, 180, 270)], 0)
            ref = np.maximum(Rc, Tr)
            LI.append((L - ref) / (L + ref + 1e-12)); win.append(bool(L[0] > Rc[0] and L[0] > Tr[0])); mod.append(m)
            Z.append(L[0]); O.append(Rc[0]); Pm.append(Tr[0])
    LI = np.array(LI); med = np.median(LI, 0); mod = np.array(mod)
    return dict(n_cases=len(LI), n_models=len(models), median_LI=float(med[0]), frac_loom_wins=float(np.mean(win)),
                beats_all_perms=bool((med[0] > med[1:]).all()), rank_among_24=int(1 + (med[1:] >= med[0]).sum()),
                best_perm_LI=float(med[1:].max()), mean_loom=float(np.mean(Z)), mean_recede=float(np.mean(O)), mean_trans=float(np.mean(Pm)),
                models_with_median_LI_pos=int(sum(np.median(LI[mod == m, 0]) > 0 for m in models)),
                ok=bool(med[0] > 0 and np.mean(win) >= 0.8 and (med[0] > med[1:]).all()))


def main(mp, wd, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    M = np.load(mp)
    D = merge(os.path.join(wd, "discs_rot30_*.npz"))
    res = {"discs": {f"{RULES[r]}_pol{p}": discs(D, M, r, p) for r in (1, 0) for p in (0, 1)}}
    D2 = merge(os.path.join(wd, "discs_rot210_*.npz"))
    if D2:
        M2 = np.load(mp.replace("rot30", "rot210"))
        res["rot210"] = {f"{RULES[r]}_pol{p}": {k: v for k, v in discs(D2, M2, r, p).items() if k in ("median_LI", "frac_loom_wins", "rank_among_24", "n_models")}
                         for r in (1, 0) for p in (0, 1)}
    C = merge(os.path.join(wd, "cam_*.npz"))
    if C:
        rf, P, w, post, W = rf_of(M); n = len(M["post"])
        col = {(a, b): i for i, (a, b) in enumerate(np.round(np.asarray(C["xy_deg"]) / 5.1 * 1000).astype(int).tolist())}
        ci = np.array([col[(a, b)] for a, b in np.round(P * 1000).astype(int).tolist()])
        sel = (M["post_type"] == "LPLC2") & (np.bincount(post, w * C["inside"][ci], n) / np.maximum(W, 1e-9) >= 0.5)
        models = sorted({int(re.match(r"m(\d+)_", k).group(1)) for k in C if k.startswith("m")})
        cam = {"n_cells": int(sel.sum())}
        for r in (1, 0):
            pk = {m: {s: float(C[f"m{m}_{s}"][r, 0, sel].mean()) for s in CAM} for m in models}
            okm = {m: bool(all(pk[m]["S3_zblizanie"] > pk[m][s] for s in CAM if s != "S3_zblizanie")) for m in models}
            cam[RULES[r]] = dict(n_ok=int(sum(okm.values())), n_models=len(models), ok=bool(sum(okm.values()) >= 0.8 * len(models)),
                                 S3_over_S4_median=float(np.median([pk[m]["S3_zblizanie"] / (pk[m]["S4_ramie"] + 1e-12) for m in models])),
                                 peaks=pk)
        res["cam"] = cam
    a0 = res["discs"]["AND_pol0"]
    res["W5_pass"] = a0["ok"]
    res["W5_bright"] = res["discs"]["AND_pol1"]["ok"]
    res["W5_cam"] = res.get("cam", {}).get("AND", {}).get("ok")
    json.dump(res, open(out, "x"), indent=1)
    show = json.loads(json.dumps(res))
    for k in ("LIN", "AND"):
        show.get("cam", {}).get(k, {}).pop("peaks", None)
    print(json.dumps(show, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
