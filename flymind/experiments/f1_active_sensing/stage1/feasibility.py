"""Stage 1-F feasibility (STAGE1_DESIGN.md d3 §7 F2–F5, rule R5). Smoke seeds 9 118 010–029 only; never analysed inferentially.
Writes results/feasibility.json (mode x)."""
import json
import math
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cl_sense as CS  # noqa: E402

UNITS = range(9118010, 9118030)
SLOPE = 501.32934029670935            # DATA, v5v4.calibrate with seeds 9 114 001–003 (+1.2 % vs V4)


def trial(job):
    u, rng_name, ctrl, motion, f = job
    st = CS.draw(u)[rng_name]
    tr = dict(az0_deg=st["side"] * st["az"], rho=st["rho"])
    base = CS.L.network(CS.L.J0)[:2]
    calib = dict(slope_snn=SLOPE, slope_p=CS.L.calibrate_p((96, 128)), slope_th=CS.calibrate_th((96, 128)))
    jit = CS.jvel(600, f, np.random.default_rng([u, 3, 1])) [0] if motion == "jvel" else None
    t0 = time.perf_counter()
    r = CS.run(ctrl, base, u, calib, tr, motion=motion, f=f, phase=st["phi"], noise=CS.pixel_noise(u), ticks=600,
               jit=jit, g_b=CS.gain_for(tr))
    r["wall_s"] = time.perf_counter() - t0
    r.update(CS.L.metrics(r))
    m = slice(int(0.75 / CS.DT), int(CS.T_MOVE / CS.DT))
    sens = np.array(r["e_deg"]) - r["e_motor_deg"]              # bearing modulation caused by the sensing motion
    return dict(unit=u, rng=rng_name, ctrl=ctrl, motion=motion, f=f, success=r["success"], final=r["final_abs_err"],
                s10=CS.lockin(r["pan_t"], f, st["phi"]), s10_deg=math.degrees(CS.lockin(r["pan_t"], f, st["phi"])),
                cmd_amp_deg=math.degrees(r["a_pan"]), sens_bearing_amp_deg=float(np.sqrt(2) * sens[m].std()),
                track_err_deg=float(math.degrees(np.max(np.abs(r["q0"][m] - (r["pan_t"][m] + r["theta_s"][m]))))) if motion != "none" else 0.0,
                flags=r["safety_flags"], invalid=r["invalid_ticks"], ball_dev_mm=1000 * r["ball_dev_m"], wall_s=r["wall_s"],
                omega_spec_peak_hz=float(np.fft.rfftfreq(400, 0.01)[np.argmax(np.abs(np.fft.rfft(np.array(r["omega"][75:475])
                                                                                     - np.mean(r["omega"][75:475]))))]))


def main():
    jobs = [(u, g, "snn", m, f) for u in UNITS for g in ("W", "S") for m, f in (("none", 1.0), ("sin", 0.5), ("sin", 1.0))]
    jobs += [(u, "S", "zero", "sin", f) for u in UNITS[:5] for f in (0.5, 1.0)]
    jobs += [(u, "W", "snn", m, 1.0) for u in UNITS[:3] for m in ("mt", "virtual", "jvel", "gated")]
    jobs += [(u, "W", c, m, 1.0) for u in UNITS[:3] for c in ("th", "p") for m in ("none", "sin")]
    out = os.path.join(HERE, "results", sys.argv[1] if len(sys.argv) > 1 else "feasibility.json")
    if os.path.exists(out):
        sys.exit(f"exists: {out}")
    t0 = time.perf_counter()
    with Pool(4) as p:
        res = p.map(trial, jobs, chunksize=1)
    with open(out, "x") as fh:
        json.dump(dict(jobs=len(jobs), wall_s=time.perf_counter() - t0, slope_snn=SLOPE, results=res), fh, default=str)
    print("wrote", out, "wall", round(time.perf_counter() - t0), "s")


if __name__ == "__main__":
    main()
