"""E2 — ocena (LOOP_TARGET_E2_LPi.md). .venv: e2_analysis.py MAP.npz E2_DIR OUT.json
Łączy pliki {lpi|nolpi}_{etykieta}_{zakres}.npz z e2_lpi.py i ocenia je regułą W8 (w8_analysis.cam_eval)."""
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from w8_analysis import cam_eval  # noqa: E402


def main(mp, ed, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    M = np.load(mp); res = {}
    for var in ("lpi", "nolpi"):
        for lab in ("w0d", "hard_slick", "mid"):
            C = {}
            for f in sorted(glob.glob(os.path.join(ed, f"{var}_{lab}_*.npz"))):
                C.update(dict(np.load(f)))
            if C:
                res[f"{var}_{lab}"] = {r: cam_eval(C, M, i) for i, r in ((1, "AND"), (0, "LIN"))}
    res["E2_pass"] = bool(res["lpi_w0d"]["AND"]["ok"])
    json.dump(res, open(out, "x"), indent=1)
    for k, v in res.items():
        if isinstance(v, dict):
            for r, x in v.items():
                print(k, r, {q: y for q, y in x.items() if q not in ("peaks", "model_ok")})
    print("E2_pass", res["E2_pass"])


if __name__ == "__main__":
    main(*sys.argv[1:4])
