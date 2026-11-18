"""W8 — ocena powtórzenia W7-kamera (LOOP_TARGET_W8.md). .venv: w8_analysis.py MAP.npz W8_DIR OUT.json
Pliki W8_DIR/{wariant}_{obiekt}.npz z w7_run.py cam (wariant „al” = przypisanie z pomiaru, główny) lub w5_and.py cam („id”, opisowo)."""
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from w5_analysis import CAM, rf_of  # noqa: E402

OBJ = ("hard_slick", "mid")


def cam_eval(C, M, rule=1):
    rf, P, w, post, W = rf_of(M); n = len(M["post"])
    col = {(a, b): i for i, (a, b) in enumerate(np.round(np.asarray(C["xy_deg"]) / 5.1 * 1000).astype(int).tolist())}
    ci = np.array([col[(a, b)] for a, b in np.round(P * 1000).astype(int).tolist()])
    sel = (M["post_type"] == "LPLC2") & (np.bincount(post, w * C["inside"][ci], n) / np.maximum(W, 1e-9) >= 0.5)
    models = sorted({int(re.match(r"m(\d+)_", k).group(1)) for k in C if k.startswith("m")})
    pk = {m: {s: float(C[f"m{m}_{s}"][rule, 0, sel].mean()) for s in CAM} for m in models}
    okm = {m: bool(all(pk[m]["S3_zblizanie"] > pk[m][s] for s in CAM if s != "S3_zblizanie")) for m in models}
    beats = {s: int(sum(pk[m]["S3_zblizanie"] > pk[m][s] for m in models)) for s in CAM if s != "S3_zblizanie"}
    return dict(n_cells=int(sel.sum()), n_models=len(models), n_ok=int(sum(okm.values())), ok=bool(sum(okm.values()) >= 0.8 * len(models)),
                S3_beats=beats, S3_over_S4_median=float(np.median([pk[m]["S3_zblizanie"] / (pk[m]["S4_ramie"] + 1e-12) for m in models])),
                model_ok={str(m): okm[m] for m in models}, peaks={str(m): pk[m] for m in models})


def main(mp, wd, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    M = np.load(mp); res = {}
    for var in ("al", "id"):
        for obj in OBJ:
            f = os.path.join(wd, f"{var}_{obj}.npz")
            if os.path.exists(f):
                res[f"{var}_{obj}"] = {r: cam_eval(np.load(f), M, i) for i, r in ((1, "AND"), (0, "LIN"))}
    res["W8_pass"] = bool(all(res[f"al_{o}"]["AND"]["ok"] for o in OBJ))
    json.dump(res, open(out, "x"), indent=1)
    for k, v in res.items():
        if isinstance(v, dict):
            for r, x in v.items():
                print(k, r, {q: y for q, y in x.items() if q not in ("peaks", "model_ok")})
    print("W8_pass", res["W8_pass"])


if __name__ == "__main__":
    main(*sys.argv[1:4])
