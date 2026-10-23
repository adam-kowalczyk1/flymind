"""Klasyfikacja prób bez chwytu: wytoczenie (kulka odjechała od paszczy) vs przepychanie (ruchoma szczęka
długo naciska, stała nie) vs inne.  python classify.py '{parametry}' od do [ziarna szumu]"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import stage3
from circuit import FlyController


def one(a):
    P, seed, d = a
    P = dict(P)
    q = P.pop("q_open", None)
    ax = P.pop("aim_x", None)
    cs = P.pop("contact_stop", stage3.CONTACT_STOP)
    fc = FlyController(seed=seed + 100 * d, params=P)
    r = stage3.run_trial(seed, fc, record=True, q_open=q, aim_x=ax, contact_stop=cs)
    if r["success"] or r["crushed"]:
        return seed, d, r["success"], r["crushed"], None, {}
    L = r["log"]
    k0 = int(r["contact"] * 100) if r["contact"] else 0
    F = L["force"][k0:]
    mov_only = float(((F[:, 1] > 0.3) & (F[:, 0] < 0.05)).mean() * (len(F) / 100))   # s
    both = float(((F > 0.3).all(1)).mean() * (len(F) / 100))
    # odległość kulki od punktu celowania na końcu (z logu pozycji kulki i kąta bazy pominięta: x od bazy)
    rb = np.hypot(L["ball"][:, 0], L["ball"][:, 1])
    escaped = rb[-1] - rb[k0] if r["contact"] else np.nan
    kind = "wytoczenie" if escaped > 0.03 else "przepychanie" if mov_only > 0.5 else "inne"
    return seed, d, False, False, kind, dict(mov_only_s=round(mov_only, 2), both_s=round(both, 2),
                                             escape_m=round(float(escaped), 3), q_end=round(float(L["q_grip"][-1]), 2),
                                             lift=r["t_lift"], az=round(r["az_err_deg"], 1))


if __name__ == "__main__":
    P = json.loads(sys.argv[1])
    draws = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    with Pool(8) as pool:
        res = pool.map(one, [(P, s, d) for d in range(draws) for s in range(int(sys.argv[2]), int(sys.argv[3]))])
    kinds = [k for *_, k, _ in res if k]
    print(f"sukces {sum(r[2] for r in res)}/{len(res)}, zgniecione {sum(r[3] for r in res)}, bez chwytu {len(kinds)}:",
          {k: kinds.count(k) for k in set(kinds)})
    for seed, d, _, _, k, info in res:
        if k:
            print(f"  {seed} szum {d}: {k} {info}")
