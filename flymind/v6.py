"""flymind/v6.py — V6 network structure × ALIF dynamics (EXPLORATORY). Protocol: program_v5v41/V6_PROTOCOL.md.
Open loop: --openloop (engine v5v41.simulate, unchanged). Closed loop: --calibrate then --closedloop (cl_runner → frozen loop.run_trial).
Writes only under --out. Run with .venv/bin/python -I -B.
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("run with python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v5v41 as V  # noqa: E402
import v5v41_e6 as E6  # noqa: E402
from alif import ALIFParams  # noqa: E402

PROTOCOL = os.path.join(HERE, "program_v5v41", "V6_PROTOCOL.md")
CONFIGS = {"D0": {}, "BA0": dict(b_a=0.0), "BA025": dict(b_a=0.25), "BA1": dict(b_a=1.0), "TH6": dict(v_th=-46.0), "TH8": dict(v_th=-44.0),
           "J015": dict(J0=0.15), "J025": dict(J0=0.25), "SG0": dict(noise=0.0), "SG6": dict(noise=6.0), "TA100": dict(tau_a=100.0),
           "TA1000": dict(tau_a=1000.0), "BA0xTH6": dict(b_a=0.0, v_th=-46.0), "BA0xTH8": dict(b_a=0.0, v_th=-44.0),
           "BA0xJ015": dict(b_a=0.0, J0=0.15), "BA0xJ025": dict(b_a=0.0, J0=0.25)}
CL_CONFIGS = ("D0", "BA0", "BA1", "TH6", "TH8", "J015", "J025", "SG6")
LV = np.round(np.arange(4.0, 12.0001, 0.25), 4)
REPS = 4
SCENES = range(8_600_001, 8_600_121)


def split(cfg):
    c = dict(cfg)
    J0 = c.pop("J0", 0.2)
    return J0, c


def openloop_job(job):
    import v5v42 as V2
    t0 = time.perf_counter()
    J0, al = split(CONFIGS[job["config"]])
    spec, idx = V2.net_for_job(dict(job, J0=J0, sha=job["sha"][J0]))
    P = ALIFParams(**{**ALIFParams(noise=2.0).__dict__, **al})
    c1 = np.zeros((len(LV), 2, REPS, 100, 6), np.int16)
    for i, x in enumerate(LV):
        for s, side in enumerate("LR"):
            for r in range(REPS):
                c1[i, s, r] = V.simulate(spec, idx, side, dict(I=float(x), step_ms=1000), V.NOISE_SEEDS[r], P)["counts"]
    c6 = np.zeros((len(E6.I0S), len(E6.DELTAS), REPS, 100, 6), np.int16)
    for i, I0 in enumerate(E6.I0S):
        for j, dl in enumerate(E6.DELTAS):
            cfg = dict(I=I0 + dl / 2, step_ms=1000, contra_frac=(I0 - dl / 2) / (I0 + dl / 2))
            for r in range(REPS):
                c6[i, j, r] = V.simulate(spec, idx, "L", cfg, V.NOISE_SEEDS[r], P)["counts"]
    sp = V.simulate(spec, idx, "L", dict(I=0.0, step_ms=300), V.NOISE_SEEDS[0], P)["counts"].sum()
    d = os.path.join(job["out"], job["config"])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{job['name']}.npz"), "xb") as f:
        np.savez_compressed(f, E1_counts=c1, E1_levels=LV, E6_counts=c6, E6_I0=np.array(E6.I0S), E6_deltas=np.array(E6.DELTAS),
                            spont_spikes_300ms=np.array(sp), n_pop=np.array([len(idx["in_L"]), len(idx["in_R"]), len(idx["mid_L"]), len(idx["mid_R"]), 1, 1]))
    return dict(config=job["config"], name=job["name"], wall_s=round(time.perf_counter() - t0, 1))


def sha_at(family, k, J0):
    import v5v42 as V2
    if family in ("DATA", "SWS"):
        return V.w_sha(V.make_net(family, k, J0)[0])
    return V.w_sha(V2.make_block_net(V2.FAMILIES[family][0], k, J0)[0])


def sha_job(a):
    fam, k = a
    return (fam, k), {J0: sha_at(fam, k, J0) for J0 in (0.15, 0.2, 0.25)}


def scene_of(seed):
    import cl_runner as C
    rho = (0.16, 0.22) if seed <= 8_600_040 else (0.22, 0.28)
    return dict(seed=seed, stratum="S1" if seed <= 8_600_040 else "S2", **C.scene(seed, rho))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    ap.add_argument("--protocol-sha256", required=True)
    ap.add_argument("--openloop", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--closedloop", action="store_true")
    ap.add_argument("--family-x", default=None, help="V5 v4.2 family selected by the §2 rule (e.g. B1), or none")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    import integrity_v5v41 as IG
    import cl_runner as C
    if IG.stage1()["ok"] != 28:
        sys.exit("STOP: Stage 1")
    psha = hashlib.sha256(open(PROTOCOL, "rb").read()).hexdigest()
    if psha != a.protocol_sha256:
        sys.exit("refused: protocol sha256 mismatch")
    os.makedirs(a.out, exist_ok=True)
    ctx = mp.get_context("spawn")
    nets = [("DATA", None)] + [("SWS", k) for k in V.SWS_SEEDS]
    if a.family_x:
        import v5v42 as V2
        nets += [(a.family_x, k) for k in list(V2.FAMILIES[a.family_x][1])[:25]]
    if a.openloop:
        with ctx.Pool(a.workers) as pool:
            shas = dict(pool.map(sha_job, nets))
        jobs = [dict(config=c, family=f, k=k, sha=shas[(f, k)], name="DATA" if f == "DATA" else f"{f}_{k}", out=os.path.join(a.out, "openloop"))
                for c in CONFIGS if c != "D0" for f, k in nets]
        with open(os.path.join(a.out, "openloop_config.json"), "x") as f:
            json.dump(dict(protocol_sha256=psha, configs=CONFIGS, levels=LV.tolist(), reps=REPS, nets=nets, family_x=a.family_x,
                           started=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1, default=str)
        with ctx.Pool(a.workers) as pool:
            for r in pool.imap_unordered(openloop_job, jobs, chunksize=1):
                print(r, flush=True)
    if a.calibrate:
        jobs = [dict(name=c, family="DATA", k=None, J0=split(CONFIGS[c])[0], alif=split(CONFIGS[c])[1]) for c in CL_CONFIGS]
        with ctx.Pool(a.workers) as pool:
            cal = {r["name"]: r for r in pool.map(C.calibrate_job, jobs)}
        with open(os.path.join(a.out, "calibration.json"), "x") as f:
            json.dump(cal, f, indent=1)
        print(cal)
    if a.closedloop:
        cal = json.load(open(os.path.join(a.out, "calibration.json")))
        raw = os.path.join(a.out, "closedloop.jsonl")
        done = C.done_names(raw)
        jobs = []
        for c in CL_CONFIGS:
            J0, al = split(CONFIGS[c])
            for i, s in enumerate(SCENES):
                sc = scene_of(s)
                pairs = [("DATA", None), ("SWS", V.SWS_SEEDS[i % 50])]
                if a.family_x:
                    import v5v42 as V2
                    pairs.append((a.family_x, list(V2.FAMILIES[a.family_x][1])[i % 25]))
                for fam, k in pairs:
                    jobs.append(dict(name=f"{c}|{fam}|{s}", config=c, family=fam, k=k, J0=J0, alif=al, cond="snn", slope=cal[c]["slope"], **sc))
                if c == "D0":
                    jobs.append(dict(name=f"P|{s}", config="P", family="DATA", k=None, J0=0.2, alif={}, cond="classical_p", slope=cal[c]["slope"], **sc))
        jobs = [j for j in jobs if j["name"] not in done]
        print("closed-loop trials to run:", len(jobs), flush=True)
        with ctx.Pool(a.workers) as pool:
            for r in pool.imap_unordered(C.trial_job, jobs, chunksize=2):
                C.append(raw, r)
        print("closed loop done", flush=True)
    with open(os.path.join(a.out, f"stage1_post_{time.strftime('%Y%m%dT%H%M%S')}.json"), "x") as f:
        json.dump(IG.stage1(), f)


if __name__ == "__main__":
    main()
