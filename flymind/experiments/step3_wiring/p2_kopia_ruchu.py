"""P2 (21 XI): kopia ruchu — oko dostaje przewidziany ruch obrazu z polecenia ruchu ramienia (PREREG_P2_KOPIA.md).
Sceny syntetyczne oko_mucha.scene (ruch kamery znany). Kopia może być błędna: wzmocnienie g i opóźnienie d.
  .venv/bin/python p2_kopia_ruchu.py --test    → flymind/results/p2_kopia_20261121/
  .venv/bin/python p2_kopia_ruchu.py --check   (znak przesunięcia na ziarnie spoza testu)"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import oko_mucha as O  # noqa: E402

RES = os.path.join(HERE, "../../results/p2_kopia_20261121")
SEEDS = range(24105001, 24105011)
PANS = ("pan_h", "pan_v", "pan_d")
COND = {"nominal": (1.0, 0.0), "g0.8_d25": (0.8, 0.025), "g1.2_d25": (1.2, 0.025)}
# ruch obrazu w scenach oko_mucha.scene [°/s] od t = 0,5 s: (x w prawo, y w dół); obraz jedzie przeciwnie do „kamery”
VEL = {"pan_h": (-50.0, 0.0), "pan_v": (0.0, -50.0), "pan_d": (-50 / np.sqrt(2), -50 / np.sqrt(2)), "loom_pan": (0.0, -20.0)}


def surface(seed, T=3.0, ttc=1.5):
    """Kamera jedzie prosto na fakturę: obraz skalowany wokół środka 1 / (1 − u / ttc), u = t − 0,5 (do 90 % drogi)."""
    from scipy import ndimage
    rng = np.random.default_rng(seed)
    tex = ndimage.gaussian_filter(rng.standard_normal((3 * O.H_PX, 3 * O.W_PX)), 3)
    tex = 140 + 25 * tex / tex.std()
    yy, xx = np.mgrid[:O.H_PX, :O.W_PX].astype(float)
    out = []
    for k in range(int(T * O.FPS)):
        t = k / O.FPS
        z = 1 / (1 - min(max(0.0, t - 0.5), 0.9 * ttc) / ttc)
        img = ndimage.map_coordinates(tex, [(yy - O.H_PX / 2) / z + 1.5 * O.H_PX, (xx - O.W_PX / 2) / z + 1.5 * O.W_PX], order=1)
        out.append((t, np.clip(np.round(img + O.SIGMA * rng.standard_normal(img.shape)), 0, 255).astype(np.uint8)))
    return out


def run(kind, seed, eye, g=1.0, d=0.0, ec=True):
    vx, vy = VEL.get(kind, (0.0, 0.0))
    px = O.W_PX / O.FOV_H                                         # px oka na stopień
    out = []
    for t, f in (surface(seed) if kind == "surface" else O.scene(kind, seed)):
        on = (t - d) > 0.5                                        # kopia przychodzi z opóźnieniem d
        if ec and on:
            eye.ec = (g * vx * px / O.FPS, g * vy * px / O.FPS)
        eye.see(f.astype(float), 1 / O.FPS, t)
        out.append(max(eye.out))
    return np.array(out)


def evaluate(make, ec=True, g=1.0, d=0.0):
    rows = []
    for s in SEEDS:
        lo = run("loom", s, make(), ec=False).max()
        r = {k: float(run(k, s, make(), g, d, ec).max() / lo) for k in (*PANS, "loom_pan", "surface")}
        r["E1"] = all(r[k] <= 0.25 for k in PANS)
        r["E2"] = r["loom_pan"] >= 0.5
        rows.append(r)
    return rows


def test():
    os.makedirs(RES, exist_ok=True)
    eyes = {"v3": lambda: O.FlyEye3(), "v2": lambda: O.FlyEye(out_full=O.OUT_FULL2, vshs=True, g0=O.G0)}
    res = {}
    for en, mk in eyes.items():
        res[en] = {"bez_kopii": evaluate(mk, ec=False)}
        for cn, (g, d) in COND.items():
            res[en][cn] = evaluate(mk, True, g, d)
        for cn, rows in res[en].items():
            n1, n2 = sum(r["E1"] for r in rows), sum(r["E2"] for r in rows)
            med = {k: round(float(np.median([r[k] for r in rows])), 3) for k in (*PANS, "loom_pan", "surface")}
            print(en, cn, f"E1 {n1}/10 E2 {n2}/10", med, flush=True)
    v3 = res["v3"]
    md = lambda c, k: float(np.median([r[k] for r in v3[c]]))   # noqa: E731
    better = any(md("bez_kopii", k) - md(c, k) >= 0.05 for c in COND for k in PANS) or \
        any(md(c, "loom_pan") - md("bez_kopii", "loom_pan") >= 0.05 for c in COND)
    verdict = better and all(sum(r["E1"] for r in v3[c]) >= 9 and sum(r["E2"] for r in v3[c]) >= 9 for c in COND)
    json.dump(dict(PASS=verdict, ec_improves=better, res=res), open(os.path.join(RES, "p2_test.json"), "w"), indent=1)
    print("P2:", "PASS" if verdict else "FAILED")


def _check():
    s = 24105900                                                   # poza ziarnami testu
    for k in ("pan_h", "pan_v"):
        a, b = run(k, s, O.FlyEye3(), ec=False).max(), run(k, s, O.FlyEye3()).max()
        c = run(k, s, O.FlyEye3(), g=-1.0).max()                  # zły znak musi pogorszyć
        print(k, "bez", round(a, 4), "z kopią", round(b, 4), "zły znak", round(c, 4))
        assert b < a and b < c, "kopia ruchu nie zmniejsza odpowiedzi na ruch kamery"
    print("p2 _check OK")


if __name__ == "__main__":
    _check() if "--check" in sys.argv else test()
