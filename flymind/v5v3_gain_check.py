"""flymind/v5v3_gain_check.py — PO PRZEBIEGU V5 v3, EKSPLORACJA (nie część protokołu): weryfikacja zarzutu Red Team, że część H2
to skala sygnału. Ziarna dev 1501–1520 (instancje SHUF_STR + 200 000). Uruchom: .venv/bin/python -I -B flymind/v5v3_gain_check.py"""
import sys, json, numpy as np
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import loop as L, loop_v2 as L2
from visual_path import network, shuffle
from v5v3 import boot_ci, perm_test
spec, idx, _ = network(0.2)
cal = dict(slope_snn=495.56388207807265, slope_p=L.calibrate_p((96, 128)))
rows = []
for s in range(1501, 1521):
    tr = {k: v for k, v in L2.trial_spec_v2(s).items() if k in ("seed", "az0_deg", "rho")}
    sh = shuffle(spec, s + 200_000, equal_weight=True)
    own = L2.calibrate_v4v2(sh, idx)["slope"]
    e = {}
    for name, net, slope in (("DATA", spec, None), ("STR_shared", sh, None), ("STR_own", sh, own)):
        r = L.run_trial("snn", s, (net, idx), cal, tr=tr, slope=slope); r.update(L.metrics(r)); e[name] = r["final_abs_err"]
    rows.append(dict(seed=s, own_slope=own, **e)); print(rows[-1], flush=True)
E = {k: np.array([r[k] for r in rows]) for k in ("DATA", "STR_shared", "STR_own")}
for a, b in (("DATA", "STR_shared"), ("DATA", "STR_own"), ("STR_own", "STR_shared")):
    d = E[a] - E[b]; print(f"{a} − {b}: śr {d.mean():+.3f} CI95 {np.round(boot_ci(d, 0.95, seed=1701), 3)} p {perm_test(d, seed=1702):.4f}")
json.dump(rows, open("gain_rows.json", "w"))
