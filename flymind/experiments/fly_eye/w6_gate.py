"""W6 — bramka kierunkowości T4/T5 na pełnych krawędziach (cel: LOOP_TARGET_W6.md). Niezależna od LPLC2 i od wyników W5.
Krawędź (półpłaszczyzna) przesuwana o 16 kolumn w 4 strony, środek oka, kontrast jak bodźce B1 (szary 0,5 → 0 lub 1).
DI podtypu = (R_pref − R_null)/(R_pref + R_null); R = Σ wyprostowanej odpowiedzi w kolumnach ≤ 6 od środka, faza ruchu.
ON = jasna krawędź nadchodzi (dla T4), OFF = ciemna nadchodzi (dla T5). Kierunki preferowane jak w5_posthoc_dsi.PREF.
Model przechodzi bramkę, gdy: średnie DI T4 (ON) ≥ 0,3 i średnie DI T5 (OFF) ≥ 0,3 i każdy z 8 podtypów ma DI > 0 na swojej krawędzi.
envs/flyvis: w6_gate.py MODELS OUT.json"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))
import w5_and as W  # noqa: E402
from bridge_loom import DIRS, DT, PRE, flyxy, loom_radius  # noqa: E402
from w5_posthoc_dsi import PREF, edge_movies  # noqa: E402

THR = 0.3


def main(models, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    lo, hi = map(int, models.split("-")); res = {}
    n = len(loom_radius())                                   # tyle klatek ruchu co w bodźcach B1
    for k in range(lo, hi + 1):
        net, u, v, idx = W.load(k); X = flyxy(u, v); near = np.hypot(*X.T) <= 6; di = {}
        for pol, grp in ((1, W.SUB[:4]), (0, W.SUB[4:])):
            R = {a: W.sim(net, m, DT, int(PRE / DT), idx)[:, :, near].sum((0, 2)) for a, m in edge_movies(X, pol, n).items()}
            for s in grp:
                j = W.SUB.index(s); pa = PREF[s[-1]]; na = (pa + 180) % 360
                di[s] = float((R[pa][j] - R[na][j]) / (R[pa][j] + R[na][j] + 1e-12))
        t4, t5 = np.mean([di[s] for s in W.SUB[:4]]), np.mean([di[s] for s in W.SUB[4:]])
        res[k] = dict(DI=di, T4_ON=float(t4), T5_OFF=float(t5), passed=bool(t4 >= THR and t5 >= THR and min(di.values()) > 0))
        print(k, f"T4(ON) {t4:+.2f}  T5(OFF) {t5:+.2f}", "PASS" if res[k]["passed"] else "-", flush=True)
    json.dump(res, open(out, "x"), indent=1)
    print("przechodzą:", [k for k in res if res[k]["passed"]])


if __name__ == "__main__":
    main(*sys.argv[1:3])
