"""flymind/test_cl_runner.py — checks of cl_runner parameter injection (runs MuJoCo; smoke seeds 8 490 0xx only).
Run: .venv/bin/python -I -B flymind/test_cl_runner.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cl_runner as C  # noqa: E402

job = dict(name="t", family="DATA", k=None, J0=0.2, cond="snn", seed=8_490_020, az0_deg=18.0, rho=0.2, slope=492.11874242900916)
# T1 default injection == untouched frozen path
import loop as L  # noqa: E402
P0, E0 = L.P, L.ENC
r_direct = L.run_trial("snn", job["seed"], C.get_net("DATA", None), dict(slope_snn=job["slope"], slope_p=L.calibrate_p((96, 128))),
                       tr=dict(seed=job["seed"], az0_deg=18.0, rho=0.2), slope=job["slope"])
r1 = C.trial_job(job)
assert L.P == P0 and L.ENC == E0, "T1 default params differ from frozen loop.P/ENC"
assert np.allclose(r1["e_deg_ds"], np.array(r_direct["e_deg"])[::10].round(2)), "T1 default path differs"
# T2 encoder injection takes effect and does not leak
r2 = C.trial_job(dict(job, enc=dict(i_max=9.0)))
assert L.ENC.i_max == 9.0 and r2["e_deg_ds"] != r1["e_deg_ds"], "T2 i_max injection"
r3 = C.trial_job(job)
assert r3["e_deg_ds"] == r1["e_deg_ds"] and L.ENC.i_max == 12.0, "T3 leak after reset"
# T4 ALIF injection takes effect
r4 = C.trial_job(dict(job, alif=dict(b_a=0.0)))
assert L.P.b_a == 0.0 and r4["e_deg_ds"] != r1["e_deg_ds"], "T4 b_a injection"
C.configure()
# T5 calibration procedure under default params, registered seeds
c = C.calibrate_job(dict(name="cal", family="DATA", k=None))
print("default DATA calibration slope (seeds 8 601 001–003):", round(c["slope"], 2), "offset", c["offset"], "| frozen V5 v4: 492.12")
assert c["slope"] > 0 and not c["refused"]
# T6 SWS adjacency identical across J0 (equality classes of weights preserved by linear J0)
import v5v41 as V  # noqa: E402
a, b = V.make_net("SWS", 8_490_021, 0.2)[0], V.make_net("SWS", 8_490_021, 0.15)[0]
assert np.array_equal(a.W_data != 0, b.W_data != 0) and np.allclose(a.W_data * 0.75, b.W_data), "T6"
print("test_cl_runner: 6 tests OK | trial wall", r1["wall_s"], "s; final err default", round(r1["final_abs_err"], 3), "i_max 9", round(r2["final_abs_err"], 3), "b_a 0", round(r4["final_abs_err"], 3))
