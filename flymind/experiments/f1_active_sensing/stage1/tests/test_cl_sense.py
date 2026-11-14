"""Stage 1 checks (smoke seeds 9 118 0xx only). F1: motion 'none', no noise, 300 ticks == loop.run_trial bit for bit (snn, p)."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import cl_sense as CS  # noqa: E402

L = CS.L
fails = []


def check(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name, info)
    if not ok:
        fails.append(name)


base = L.network(L.J0)[:2]
calib = dict(slope_snn=495.56388207807265, slope_p=L.calibrate_p((96, 128)))
for seed in (9118001, 9118002):
    tr = dict(seed=seed, az0_deg=12.0 if seed % 2 else -20.0, rho=0.2)
    for cond, ctrl in (("snn", "snn"), ("classical_p", "p")):
        a = L.run_trial(cond, seed, base, calib, tr=tr)
        b = CS.run(ctrl, base, seed, calib, tr)
        check(f"F1 {cond} seed {seed}: e_deg and omega identical to loop.run_trial",
              a["e_deg"] == b["e_deg"] and a["omega"] == b["omega"], f"max|Δe| {np.max(np.abs(np.subtract(a['e_deg'], b['e_deg']))):.2e}")

env = CS.envelope(600)
check("envelope: 0 at t=0, 1 in 0.25–4.75 s, 0 from 5.5 s, monotone ramps", env[0] == 0 and env[25:475].min() == 1 and env[550:].max() == 0
      and np.all(np.diff(env[:26]) >= 0)
      and np.all(np.diff(env[470:560]) <= 0))
x, n = CS.jvel(600, 1.0, np.random.default_rng([9118003, 3]))
w = slice(75, 475)
check("jvel: window RMS = 1/√2, velocity within ±20 %", abs(np.sqrt((x[w] ** 2).mean()) - 1 / math.sqrt(2)) < 1e-12
      and abs(np.sqrt((np.gradient(x, 0.01)[w] ** 2).mean()) / (2 * math.pi / math.sqrt(2)) - 1) <= 0.2)
check("calibrate_th: positive finite slope", CS.calibrate_th((96, 128)) > 0)

if fails:
    sys.exit(f"{len(fails)} FAILED: {fails}")
print("all passed")
