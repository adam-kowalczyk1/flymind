"""W2 — ocena (LOOP_TARGET_W2.md). envs/flyvis: w2_analysis.py MAP.npz W2_DIR
Czyta W2_DIR/discs_*.npz i cam_*.npz, pisze w2_result.json i w2_lc4_przebieg.png."""
import glob
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))
from bridge_loom import CENTERS, DT  # noqa: E402

SEL_R, MIN_CELLS = 4.0, 3            # jak B1 (bridge_analysis.py)
CAM = ["S1_spokoj", "S2_bok", "S2r_bok_wstecz", "S3_zblizanie", "S4_ramie"]


def flyxy(u, v):
    return np.c_[1.5 * v, -np.sqrt(3) * (u + v / 2)] / np.sqrt(3)


def merge(pat):
    d = {}
    for f in sorted(glob.glob(pat)):
        d.update(np.load(f))
    return d


def li(a, b):
    return (a - b) / (a + b + 1e-12)


def main(mp, wd):
    out = os.path.join(wd, "w2_result.json")
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    M = np.load(mp)
    ok = M["in_inside"]; P = flyxy(M["in_u"][ok], M["in_v"][ok]); w = M["in_w"][ok]; post = M["in_post"][ok]; n = len(M["post"])
    W = np.bincount(post, w, n)
    rf = np.c_[np.bincount(post, w * P[:, 0], n), np.bincount(post, w * P[:, 1], n)] / np.maximum(W, 1e-9)[:, None]
    Dn = merge(os.path.join(wd, "discs_*.npz"))
    models = sorted({int(re.match(r"m(\d+)_", k).group(1)) for k in Dn if k.startswith("m")})
    res = dict(models=models, n_cells_per_center=[int((np.hypot(rf[:, 0] - c[0], rf[:, 1] - c[1]) <= SEL_R).sum()) for c in CENTERS], discs={})
    for pol in (0, 1):
        LI, LIr, LIt, win, mod = [], [], [], [], []
        for m in models:
            for ci, c in enumerate(CENTERS):
                sel = np.hypot(rf[:, 0] - c[0], rf[:, 1] - c[1]) <= SEL_R
                if sel.sum() < MIN_CELLS:
                    continue
                L = Dn[f"m{m}_p{pol}_loom_{ci}"][:, sel].mean(1)
                Rc = Dn[f"m{m}_p{pol}_recede_{ci}"][:, sel].mean(1)
                Tr = np.mean([Dn[f"m{m}_p{pol}_trans{a}_{ci}"][:, sel].mean(1) for a in (0, 90, 180, 270)], 0)
                LI.append(li(L, np.maximum(Rc, Tr))); LIr.append(li(L, Rc)[0]); LIt.append(li(L, Tr)[0])
                win.append(bool(L[0] > Rc[0] and L[0] > Tr[0])); mod.append(m)
        LI = np.array(LI); med = np.median(LI, 0); mod = np.array(mod)
        res["discs"][f"pol{pol}"] = dict(
            n_cases=len(LI), median_LI=float(med[0]), frac_loom_wins=float(np.mean(win)),
            median_LI_perms=[float(x) for x in med[1:]], beats_all_perms=bool((med[0] > med[1:]).all()),
            rank_among_24=int(1 + (med[1:] >= med[0]).sum()),
            median_LI_vs_recede=float(np.median(LIr)), median_LI_vs_trans=float(np.median(LIt)),
            per_model_median_LI={int(m): float(np.median(LI[mod == m, 0])) for m in models},
            per_model_wins={int(m): int(np.sum(np.array(win)[mod == m])) for m in models})
    d0 = res["discs"]["pol0"]
    res["KA"] = bool(d0["median_LI"] > 0); res["KB"] = bool(d0["frac_loom_wins"] >= 0.8); res["KC"] = d0["beats_all_perms"]
    res["W2_pass"] = bool(res["KA"] and res["KB"])
    # sceny z kamery
    Cn = merge(os.path.join(wd, "cam_*.npz"))
    cam = {}
    if Cn:
        ins = Cn["inside"]
        col = {(a, b): i for i, (a, b) in enumerate(np.round(np.asarray(Cn["xy_deg"]) / 5.1 * 1000).astype(int).tolist())}
        ci = np.array([col[(a, b)] for a, b in np.round(P * 1000).astype(int).tolist()])
        frac = np.bincount(post, w * ins[ci], n) / np.maximum(W, 1e-9)
        sel = frac >= 0.5
        peaks = {m: {s: float(Cn[f"m{m}_{s}"][0, sel].mean()) for s in CAM} for m in models}
        okm = {m: bool(all(peaks[m]["S3_zblizanie"] > peaks[m][s] for s in CAM if s != "S3_zblizanie")) for m in models}
        okobj = {m: bool(all(peaks[m]["S3_zblizanie"] > peaks[m][s] for s in CAM[:3])) for m in models}
        cam = dict(n_cells=int(sel.sum()), peaks=peaks, model_ok=okm, n_ok=int(sum(okm.values())),
                   n_ok_object_only=int(sum(okobj.values())), KD=bool(sum(okm.values()) >= 8))
    res["cam"] = cam
    json.dump(res, open(out, "x"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "cam"} | {"cam": {k: v for k, v in cam.items() if k != "peaks"}},
                     indent=1, default=str).replace('"median_LI_perms"', '"perms"'))
    # obraz opisowy: przebiegi LC4 (model 000)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    m0 = models[0]; s0 = np.hypot(rf[:, 0], rf[:, 1]) <= SEL_R
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
    for name, lab in [("loom_0", "zbliżanie"), ("recede_0", "oddalanie"), ("trans0_0", "przesuwanie →"), ("trans90_0", "przesuwanie ↑")]:
        tc = Dn[f"tc_m{m0}_p0_{name}"][s0].mean(0)
        ax[0].plot(np.arange(len(tc)) * DT, tc, label=lab)
    ax[0].set(title=f"LC4 (model {m0:03d}): ciemny dysk w środku oka", xlabel="czas ruchu [s]", ylabel="odpowiedź LC4 [j.u.]"); ax[0].legend()
    if Cn:
        for s in CAM:
            tc = Cn[f"tc_m{m0}_{s}"][sel].mean(0)
            ax[1].plot(np.arange(len(tc)) * 0.02, tc, label=s)
        ax[1].axvline(1.0, color="0.7", lw=0.8)
        ax[1].set(title=f"LC4 (model {m0:03d}): sceny z kamery robota", xlabel="czas od początku ruchu [s]"); ax[1].legend(fontsize=7)
    fig.suptitle("Przewidywanie modelu (flyvis → synapsy MaleCNS → LC4), nie pomiar muchy", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(wd, "w2_lc4_przebieg.png"), dpi=130)


if __name__ == "__main__":
    main(*sys.argv[1:3])
