"""Sprawdzenie dt 0,1 ms (log T.4): N przy dt 0,1 vs N przy dt 1 na tych samych scenach testowych pozy 0 (seed % 10 == 0).
To sprawdzenie, nie kryterium celu → McNemar dokładny DWUSTRONNY + sparowany bootstrap (funkcje z analyze_b).
  .venv/bin/python -I -B compare_dt01.py TEST_DIR DT01_DIR GLU [--out PLIK]
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
from scipy.stats import binomtest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_b import boot, wilson  # noqa: E402


def load(pattern):
    paths = sorted(glob.glob(pattern))
    runs = [r for p in paths for r in json.load(open(p))["runs"] if r["seed"] % 10 == 0]
    out = {(r["item"], r["seed"]): r for r in runs}
    assert paths and len(out) == len(runs), f"brak plików lub zdublowane sceny: {pattern}"
    return out


def dz(r):
    v = [x["dz_mm"] for x in r.get("lift_log", []) if "dz_mm" in x]
    return max(v) if v else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("test_dir"), ap.add_argument("dt01_dir"), ap.add_argument("glu", type=float), ap.add_argument("--out")
    a = ap.parse_args()
    g = f"{a.glu:+.0f}".replace("+", "")
    one = load(os.path.join(a.test_dir, f"test_N_g{g}.json"))
    tenth = load(os.path.join(a.dt01_dir, f"test_dt01_N_g{g}_*.json"))  # 9 kawałków po kształcie (log T.8)
    keys = sorted(tenth)
    assert keys == sorted(one), "różne zestawy scen"
    A = np.array([bool(tenth[k]["truth"]["lift"]) for k in keys])
    B = np.array([bool(one[k]["truth"]["lift"]) for k in keys])
    n10, n01 = int((A & ~B).sum()), int((~A & B).sum())
    p = float(binomtest(n10, n10 + n01, 0.5).pvalue) if n10 + n01 else 1.0
    dza = [x for x in (dz(tenth[k]) for k in keys) if x is not None]
    dzb = [x for x in (dz(one[k]) for k in keys) if x is not None]
    res = dict(glu=a.glu, n=len(keys),
               dt01=dict(lift=int(A.sum()), wilson=wilson(int(A.sum()), len(keys)), dz_mm_median=float(np.median(dza)) if dza else None,
                         fmax=max(r["fmax"] for r in tenth.values())),
               dt1=dict(lift=int(B.sum()), wilson=wilson(int(B.sum()), len(keys)), dz_mm_median=float(np.median(dzb)) if dzb else None,
                        fmax=max(r["fmax"] for r in one.values())),
               mcnemar_two_sided=dict(dt01_only=n10, dt1_only=n01, p=round(p, 5)), boot_dt01_minus_dt1=boot(A, B))
    print(json.dumps(res, indent=1))
    if a.out:
        with open(a.out, "x") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
