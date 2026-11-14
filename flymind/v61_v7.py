"""flymind/v61_v7.py — closed-loop runs of V6.1 (drive manipulation, I_max) and V7 (generalization blocks). EXPLORATORY.
Protocols: program_v5v41/V61_PROTOCOL.md, V7_PROTOCOL.md. Trials via cl_runner (frozen loop.run_trial). Writes only under --out.
  --drive-index : initial-frame encoder output g (L, R) per scene (one static render per scene; ENGINEERING) → drive_index.json
  --v61 / --v7  : trials → v61.jsonl / v7.jsonl (resumable)
Run: .venv/bin/python -I -B flymind/v61_v7.py --out <dir> --protocol-sha256 <sha of the stage protocol> --v61|--v7|--drive-index
"""
import argparse
import hashlib
import json
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("run with python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cl_runner as C  # noqa: E402
import v5v41 as V  # noqa: E402

P61 = os.path.join(HERE, "program_v5v41", "V61_PROTOCOL.md")
P7 = os.path.join(HERE, "program_v5v41", "V7_PROTOCOL.md")
IMAX = (8.0, 10.0, 14.0, 16.0)                  # 12 = V6 D0 (re-used)
V6_SCENES = range(8_600_001, 8_600_121)
V7_BLOCKS = {"G1": (range(8_700_001, 8_700_121), (0.28, 0.40), "uniform30", {}),
             "G2": (range(8_700_201, 8_700_321), (0.16, 0.28), "wide", {}),
             "G3": (range(8_700_401, 8_700_521), (0.16, 0.28), "uniform30", dict(noise=6.0)),
             "G4": (range(8_700_601, 8_700_721), (0.12, 0.16), "uniform30", {})}


def v7_scene(seed, rho, az):
    rng = np.random.default_rng(seed)
    if az == "wide":
        a = float(rng.uniform(30, 40) * rng.choice([-1, 1]))
        return dict(az0_deg=a, rho=float(rng.uniform(*rho)))
    return dict(az0_deg=float(rng.uniform(-30, 30)), rho=float(rng.uniform(*rho)))


def drive_job(sc):
    """Initial camera frame → encoder g (no network, no motion)."""
    import loop as L
    from encoder import EncoderParams, TargetEncoder
    from so101 import SO101Sim
    sim = SO101Sim()
    try:
        sim.reset(L.Q_POSE, ball_pos=L.place_ball(sim, math.radians(sc["az0_deg"]), sc["rho"]))
        img = sim.observe().frame.image
        e = TargetEncoder(img.shape[:2], EncoderParams(blur_px=3)).encode(img)
        return dict(sc, gL=float(e["g"][0]), gR=float(e["g"][1]), n_px=e["n_px"])
    finally:
        sim.close()


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    ap.add_argument("--protocol-sha256", required=True)
    ap.add_argument("--v6-run", default=os.path.join(HERE, "results", "v6"))
    ap.add_argument("--family-x", default=None)
    ap.add_argument("--v61", action="store_true")
    ap.add_argument("--v7", action="store_true")
    ap.add_argument("--drive-index", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    import integrity_v5v41 as IG
    import v6
    if IG.stage1()["ok"] != 28:
        sys.exit("STOP: Stage 1")
    proto = P7 if a.v7 else P61
    if hashlib.sha256(open(proto, "rb").read()).hexdigest() != a.protocol_sha256:
        sys.exit("refused: protocol sha256 mismatch")
    os.makedirs(a.out, exist_ok=True)
    cal = json.load(open(os.path.join(a.v6_run, "calibration.json")))
    ctx = mp.get_context("spawn")
    if a.drive_index:
        scs = [v6.scene_of(s) for s in V6_SCENES] + [dict(seed=s, block=b, **v7_scene(s, rho, az)) for b, (ss, rho, az, _) in V7_BLOCKS.items() for s in ss]
        with ctx.Pool(a.workers) as pool:
            rows = pool.map(drive_job, scs)
        with open(os.path.join(a.out, "drive_index.json"), "x") as f:
            json.dump(rows, f, indent=1)
        print("drive index rows", len(rows))
    jobs, raw = [], None
    if a.v61:
        raw = os.path.join(a.out, "v61.jsonl")
        for im in IMAX:
            for i, s in enumerate(V6_SCENES):
                sc = v6.scene_of(s)
                pairs = [("DATA", None), ("SWS", V.SWS_SEEDS[i % 50])]
                if a.family_x:
                    import v5v42 as V2
                    pairs.append((a.family_x, list(V2.FAMILIES[a.family_x][1])[i % 25]))
                for fam, k in pairs:
                    jobs.append(dict(name=f"I{im:g}|{fam}|{s}", config=f"I{im:g}", i_max=im, family=fam, k=k, J0=0.2, alif={}, enc=dict(i_max=im),
                                     cond="snn", slope=cal["D0"]["slope"], **sc))
    if a.v7:
        raw = os.path.join(a.out, "v7.jsonl")
        for b, (ss, rho, az, al) in V7_BLOCKS.items():
            slope = cal["SG6"]["slope"] if al.get("noise") == 6.0 else cal["D0"]["slope"]
            for i, s in enumerate(ss):
                sc = dict(seed=s, block=b, **v7_scene(s, rho, az))
                for fam, k, cond in (("DATA", None, "snn"), ("SWS", V.SWS_SEEDS[i % 50], "snn"), ("DATA", None, "classical_p")):
                    jobs.append(dict(name=f"{b}|{'P' if cond == 'classical_p' else fam}|{s}", config=b, family=fam, k=k, J0=0.2, alif=al,
                                     cond=cond, slope=slope, **sc))
    if raw:
        done = C.done_names(raw)
        jobs = [j for j in jobs if j["name"] not in done]
        print("trials to run:", len(jobs), flush=True)
        with ctx.Pool(a.workers) as pool:
            for r in pool.imap_unordered(C.trial_job, jobs, chunksize=2):
                C.append(raw, r)
    with open(os.path.join(a.out, f"stage1_post_{time.strftime('%Y%m%dT%H%M%S')}.json"), "x") as f:
        json.dump(IG.stage1(), f)
    print("done")


if __name__ == "__main__":
    main()
