"""F1 Stage 1 runner (STAGE1_DESIGN.md d3). Job = one unit (41 trials, §4). Atomic per-unit output, resumable, python -I -B only.
  prepare  → stage1_params.json (decoder calibration of every network with seeds 9 114 001–003, slope_P, slope_TH, f from R5)
  run      → results/<stage>/u<unit>.json + .npz; manifest_<stage>.json written first (mode x) with sha256 of every input
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
import zlib
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
F1 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, F1)
import cl_sense as CS  # noqa: E402

if not (sys.flags.isolated and sys.flags.dont_write_bytecode):
    sys.exit("run with python -I -B")
L = CS.L
FLY = CS.FLY
PARAMS = os.path.join(HERE, "stage1_params.json")
CONF = os.path.join(HERE, "stage1_confirm_params.json")       # written by analysis1.py pilot-rules (mode x)
POOLS = dict(pilot=dict(units=range(9111001, 9111061), b1=range(9113201, 9113206), sws=range(9113301, 9113306)),
             confirm=dict(units=range(9112001, 9112401), b1=range(9113001, 9113011), sws=range(9113101, 9113111)),
             smoke=dict(units=range(9118040, 9118042), b1=range(9118090, 9118091), sws=range(9118091, 9118092)))
CAL_SEEDS = (9114001, 9114002, 9114003)
DEPS = ["loop.py", "safety.py", "decoder.py", "encoder.py", "so101.py", "sensory.py", "alif.py", "visual_path.py", "latency.py",
        "block_shuffle.py", "side_shuffle.py", "v5v4.py", "v4_open_loop.py", "snn_interface.py", "connectome.py"]
OWN = ["cl_sense.py", "runner1.py", "analysis1.py", "STAGE1_DESIGN.md", "stage1_params.json", "stage1_confirm_params.json"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def hashes():
    h = {f"stage1/{f}": sha(os.path.join(HERE, f)) for f in OWN if os.path.exists(os.path.join(HERE, f))}
    h.update({f"flymind/{f}": sha(os.path.join(FLY, f)) for f in DEPS})
    h["f1/systems.py"] = sha(os.path.join(F1, "systems.py"))
    return h


def networks(stage):
    import systems as SY
    p = POOLS[stage]
    return SY.Networks(list(p["b1"]), list(p["sws"]), p["units"][0])


def conditions():
    """(controller family, motion, range) for one unit — the §4 matrix, 41 trials."""
    c = [("DATA", m, g) for m in ("none", "sin", "jvel", "gated", "virtual", "mt") for g in ("W", "S", "N")]
    c += [(n, m, g) for n in ("B1", "SWS") for m in ("none", "sin") for g in ("W", "N")]
    c += [("TH", m, g) for m in ("none", "sin", "jvel") for g in ("W", "S", "N")]
    c += [("P", m, g) for m in ("none", "sin") for g in ("W", "S", "N")]
    return c


def prepare(f_hz):
    """Calibrations for pilot + confirm networks (deterministic); refuses to overwrite."""
    import v5v4
    if os.path.exists(PARAMS):
        sys.exit(f"exists: {PARAMS}")
    out = dict(f_hz=f_hz, omega_on=0.10, ranges=CS.RANGES, cal_seeds=CAL_SEEDS,
               slope_p=L.calibrate_p((96, 128)), slope_th=CS.calibrate_th((96, 128)), slopes={})
    for stage in ("pilot", "confirm"):
        N = networks(stage)
        for fam, nets in N.nets.items():
            for i, spec in enumerate(nets):
                c = v5v4.calibrate(spec, N.idx, seeds=CAL_SEEDS)
                if c["refused"]:
                    sys.exit(f"calibration refused: {stage} {fam} {i}")
                out["slopes"][f"{stage}|{fam}|{i}"] = c["slope"]
                print(stage, fam, i, round(c["slope"], 2), flush=True)
    v4 = 495.56388207807265
    d = out["slopes"]["pilot|DATA|0"] / v4 - 1
    out["data_slope_vs_v4"] = d
    if abs(d) > 0.10:
        sys.exit(f"DATA slope differs from V4 by {d:+.1%} > 10 % → STOP (§13)")
    with open(PARAMS, "x") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", PARAMS)


def unit_job(args):
    stage, u, man_sha = args
    P = json.load(open(PARAMS))
    C = json.load(open(CONF)) if stage == "confirm" else dict(ranges=P["ranges"], omega_on=P["omega_on"])
    rng_ = C["ranges"]
    st = CS.draw(u, rng_)
    N = networks(stage)
    inst = (u - POOLS[stage]["units"][0])
    noise = CS.pixel_noise(u)
    f = P["f_hz"]
    om_on = C["omega_on"]
    jit = CS.jvel(600, f, np.random.default_rng([u, 3, zlib.crc32(b"jvel")]))[0]
    base_cal = dict(slope_p=P["slope_p"], slope_th=P["slope_th"])
    rows, tr_ = [], {}
    pstage = "pilot" if stage in ("pilot", "smoke") else "confirm"
    for fam, motion, g in conditions():
        s = st[g]
        tr = dict(az0_deg=s["side"] * s["az"], rho=s["rho"]) if g != "N" else dict(az0_deg=None)
        if fam in ("DATA", "B1", "SWS"):
            k = 0 if fam == "DATA" else inst % len(N.nets[fam])
            spec = N.nets[fam][k]
            slope = P["slopes"][f"{pstage}|{fam}|{k}"] if stage != "smoke" else P["slopes"][f"pilot|{fam}|0"]
            ctrl, base = "snn", (spec, N.idx)
        else:
            k, slope, ctrl, base = 0, None, {"TH": "th", "P": "p"}[fam], (N.spec, N.idx)
        g_b = CS.gain_for(tr)
        t0 = time.perf_counter()
        r = CS.run(ctrl, base, u, dict(base_cal, slope_snn=slope or 1.0), tr, motion=motion, f=f, phase=s["phi"], noise=noise,
                   ticks=600, slope=slope, jit=jit, omega_on=om_on, g_b=g_b)
        key = f"{fam}|{motion}|{g}"
        m = L.metrics(r) if g != "N" else dict(success=None, final_abs_err=None, t_first_within=None, overshoot_deg=None)
        pan = np.asarray(r["pan_t"])
        rows.append(dict(stage=stage, unit=u, fam=fam, inst=k, motion=motion, rng=g, rho=s.get("rho"), az=s.get("az"),
                         side=s.get("side"), phi=s["phi"], f=f, slope=slope, g_b=g_b, a_pan=r["a_pan"], **m,
                         track_cost=float(np.mean(np.abs(r["e_deg"][300:475]))) if g != "N" else None,
                         s10_deg=math.degrees(CS.lockin(pan, f, s["phi"])),
                         false_turn=bool(abs(math.degrees(pan[-1])) > 5 or math.degrees(np.abs(np.diff(pan)).sum()) > 10)
                         if g == "N" else None,
                         latency_s=next((i * CS.DT for i, w in enumerate(r["omega"]) if abs(w) > 0.05 and g != "N"
                                         and math.copysign(1, w) == math.copysign(1, tr["az0_deg"])), None),
                         invalid_ticks=r["invalid_ticks"], flags=r["safety_flags"], ball_dev_mm=1000 * r["ball_dev_m"],
                         lc_ipsi=int(r["counts"][:, 0 if (tr.get("az0_deg") or 1) > 0 else 1].sum()),
                         dn_L=int(r["counts"][:, 2].sum()), dn_R=int(r["counts"][:, 3].sum()),
                         wall_s=time.perf_counter() - t0, manifest_sha256=man_sha))
        tr_[key + "|e"] = np.asarray(r["e_deg"], np.float32)
        tr_[key + "|pan"] = pan.astype(np.float32)
        tr_[key + "|th"] = r["theta_s"].astype(np.float32)
        tr_[key + "|om"] = np.asarray(r["omega"], np.float32)
        tr_[key + "|cnt"] = r["counts"]
    d = os.path.join(HERE, "results", stage)
    for ext, write in (("npz", lambda fh: np.savez_compressed(fh, **tr_)), ("json", lambda fh: fh.write(json.dumps(rows).encode()))):
        p = os.path.join(d, f"u{u}.{ext}")
        with open(p + ".part", "wb") as fh:
            write(fh)
        os.replace(p + ".part", p)
    return u, sum(x["invalid_ticks"] > 0 for x in rows), round(sum(x["wall_s"] for x in rows), 1)


def run(stage, workers):
    import subprocess
    d = os.path.join(HERE, "results", stage)
    os.makedirs(d, exist_ok=True)
    if stage == "confirm" and not os.path.exists(CONF):
        sys.exit("confirm requires stage1_confirm_params.json (pilot rules)")
    mp = os.path.join(HERE, f"manifest_{stage}.json")
    man = dict(stage=stage, hashes=hashes(), git=subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                                                                cwd=FLY).stdout.strip(), time=time.strftime("%Y-%m-%dT%H:%M:%S"))
    if os.path.exists(mp):
        old = json.load(open(mp))
        if old["hashes"] != man["hashes"]:
            sys.exit(f"inputs changed since {mp} was written: refusing to resume")
    else:
        with open(mp, "x") as fh:
            json.dump(man, fh, indent=1)
    man_sha = sha(mp)
    units = POOLS[stage]["units"]
    if stage == "confirm":
        units = units[:json.load(open(CONF))["n_units"]]
    todo = [u for u in units if not (os.path.exists(os.path.join(d, f"u{u}.json")) and os.path.exists(os.path.join(d, f"u{u}.npz")))]
    print(f"{len(todo)} units to run ({stage})", flush=True)
    bad = 0
    with Pool(workers) as p:
        for u, inv, w in p.imap_unordered(unit_job, [(stage, u, man_sha) for u in todo]):
            bad += inv > 0
            print(f"u{u} invalid_trials {inv} wall {w}", flush=True)
            if bad > max(1, 0.01 * len(units)):
                p.terminate()
                sys.exit(f"STOP: {bad} units with invalid trials (> 1 %)")
    print(f"done; units with invalid trials {bad}; hashes unchanged: {hashes() == man['hashes']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "run"])
    ap.add_argument("--stage", choices=list(POOLS))
    ap.add_argument("--f", type=float)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    prepare(a.f) if a.cmd == "prepare" else run(a.stage, a.workers)
