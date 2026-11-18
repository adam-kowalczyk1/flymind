"""flymind/cl_runner.py — generic closed-loop MuJoCo runner for V6 / V6.1 / V7 (EXPLORATORY). No bio2; frozen code unchanged.

Every trial calls the frozen `loop.run_trial` + `loop.metrics` (V5 v4 code path). Parameter variants are injected by assigning the
module attributes `loop.P` (ALIFParams) and `loop.ENC` (EncoderParams) inside the worker process before the trial, and
`v4_open_loop.P` before decoder calibration (`v5v4.calibrate`, same procedure as V5 v4, with registered seeds). Files are not
modified. Defaults reproduce V5 v4 exactly (test_cl_runner.py checks the injection and the default path).

Job = dict(name, family, k, J0, alif{}, enc{}, cond ('snn'|'classical_p'), seed (scene + ALIF noise), az0_deg, rho, slope, pan0?).
Results: one JSON line per trial (append + fsync), resumable by name.
"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CAL_SEEDS = (8_601_001, 8_601_002, 8_601_003)       # registered in program_v5v41/SEED_REGISTRY.md (decoder calibration, V6+)
_NET = {}


def configure(alif=None, enc=None):
    """Set loop.P / loop.ENC / v4_open_loop.P for this process. Returns the effective params."""
    import loop as L
    import v4_open_loop as V4
    from alif import ALIFParams
    from encoder import EncoderParams
    P = ALIFParams(**{**ALIFParams(noise=2.0).__dict__, **(alif or {})})
    E = EncoderParams(**{**EncoderParams(blur_px=3).__dict__, **(enc or {})})
    L.P, L.ENC, V4.P = P, E, P
    return P, E


def get_net(family, k, J0=0.2):
    key = (family, k, J0)
    if key not in _NET:
        if family in ("DATA", "SWS"):
            import v5v41 as V
            spec, idx, _, _ = V.make_net(family, k, J0)
        else:
            import v5v42 as V2
            spec, idx, _, _ = V2.make_block_net(V2.FAMILIES[family][0], k, J0)
        _NET.clear() if len(_NET) > 64 else None
        _NET[key] = (spec, idx)
    return _NET[key]


def calibrate_job(job):
    """Decoder calibration (CONTROL) of a network under the job's params: v5v4.calibrate with CAL_SEEDS."""
    configure(job.get("alif"), job.get("enc"))
    import v5v4
    spec, idx = get_net(job["family"], job.get("k"), job.get("J0", 0.2))
    c = v5v4.calibrate(spec, idx, seeds=CAL_SEEDS)
    return dict(name=job["name"], **c)


def trial_job(job):
    configure(job.get("alif"), job.get("enc"))
    import loop as L
    spec, idx = get_net(job["family"], job.get("k"), job.get("J0", 0.2))
    tr = dict(seed=job["seed"], az0_deg=job["az0_deg"], rho=job["rho"])
    base_cal = dict(slope_snn=job["slope"], slope_p=L.calibrate_p((96, 128)))
    t0 = time.perf_counter()
    try:
        r = L.run_trial(job["cond"], job["seed"], (spec, idx), base_cal, tr=tr, slope=job["slope"])
        r.update(L.metrics(r))
        if not math.isfinite(r["final_abs_err"]):
            raise ValueError("non-finite error")
        e = np.array(r["e_deg"])
        om = np.array(r["omega"])
        out = dict(name=job["name"], success=r["success"], final_abs_err=r["final_abs_err"], t_first_within=r["t_first_within"],
                   overshoot_deg=r["overshoot_deg"], safety_ticks_flagged=r["safety_ticks_flagged"],
                   final_signed_err=float(e[-50:].mean()), moved=bool(np.abs(om).max() > 0), e_sd_last1s=float(e[-100:].std()),
                   omega_abs_mean=float(np.abs(om).mean()), e_deg_ds=e[::10].round(2).tolist(), error=None)
    except Exception as ex:                                  # noqa: BLE001 — reported as simulator error
        out = dict(name=job["name"], success=False, final_abs_err=float("nan"), error=f"{type(ex).__name__}: {ex}")
    out["wall_s"] = round(time.perf_counter() - t0, 2)
    return {**{k: v for k, v in job.items() if k not in ("out",)}, **out}


def append(path, rec):
    with open(path, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=float) + "\n")
        f.flush()
        os.fsync(f.fileno())


def done_names(path):
    s = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                s.add(json.loads(line)["name"])
            except (json.JSONDecodeError, KeyError):
                pass
    return s


def scene(seed, rho_range, az_range=(-30.0, 30.0)):
    """Scene generator (ENGINEERING): az0 ~ U(az_range), ρ ~ U(rho_range), from its own registered seed."""
    rng = np.random.default_rng(seed)
    return dict(az0_deg=float(rng.uniform(*az_range)), rho=float(rng.uniform(*rho_range)))
