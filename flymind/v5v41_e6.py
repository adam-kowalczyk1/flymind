"""flymind/v5v41_e6.py — V5 v4.1 amendment A1, experiment E6 (symmetric operating point ± small asymmetry). EXPLORATORY.
Protocol: program_v5v41/V5v41_PROTOCOL.md + V5v41_PROTOCOL_AMENDMENT_A1.md. Uses v5v41.simulate/make_net unchanged; instance
hashes are checked against results/v5v41/instances.json. Writes only under --out.
Run: .venv/bin/python -I -B flymind/v5v41_e6.py --out flymind/results/v5v41/E6 --amendment-sha256 <sha>
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
from alif import ALIFParams  # noqa: E402

AMEND = os.path.join(HERE, "program_v5v41", "V5v41_PROTOCOL_AMENDMENT_A1.md")
I0S = (4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0)
DELTAS = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)


def run_network(job):
    t0 = time.perf_counter()
    spec, idx, _, _ = V.make_net(job["family"], job["k"], job.get("J0", 0.2))
    if V.w_sha(spec) != job["sha"]:
        raise RuntimeError(job["name"])
    P = ALIFParams(**{**ALIFParams(noise=2.0).__dict__, **job.get("alif", {})})
    R = job["reps"]
    counts = np.zeros((len(I0S), len(DELTAS), R, 100, 6), np.int16)
    angle = np.zeros((len(I0S), len(DELTAS), R, 100), np.float32)
    for i, I0 in enumerate(I0S):
        for j, dl in enumerate(DELTAS):
            IL, IR = I0 + dl / 2, I0 - dl / 2
            cfg = dict(I=IL, step_ms=1000, contra_frac=IR / IL)
            for r in range(R):
                x = V.simulate(spec, idx, "L", cfg, V.NOISE_SEEDS[r], P)
                counts[i, j, r], angle[i, j, r] = x["counts"], x["angle"]
    path = os.path.join(job["out"], f"{job['name']}.npz")
    with open(path, "xb") as f:
        np.savez_compressed(f, counts=counts, angle=angle, I0=np.array(I0S), deltas=np.array(DELTAS),
                            n_pop=np.array([len(idx["in_L"]), len(idx["in_R"]), len(idx["mid_L"]), len(idx["mid_R"]), 1, 1]))
    return dict(name=job["name"], wall_s=round(time.perf_counter() - t0, 1))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    ap.add_argument("--amendment-sha256")
    ap.add_argument("--instances", default=os.path.join(HERE, "results", "v5v41", "instances.json"))
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    import integrity_v5v41 as IG
    if IG.stage1()["ok"] != 28:
        sys.exit("STOP: Stage 1")
    sha = hashlib.sha256(open(AMEND, "rb").read()).hexdigest()
    if sha != a.amendment_sha256:
        sys.exit("refused: amendment sha256 mismatch")
    inst = json.load(open(a.instances))
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    jobs = [dict(family="DATA", k=None, sha=inst["summary"]["data_sha"], name="DATA")] + \
           [dict(family="SWS", k=r["seed"], sha=r["sha"], name=f"SWS_{r['seed']}") for r in inst["rows"]]
    for j in jobs:
        j.update(out=raw, reps=8)
    with open(os.path.join(a.out, "config.json"), "x") as f:
        json.dump(dict(amendment_sha256=sha, I0=I0S, deltas=DELTAS, reps=8, noise_seeds=V.NOISE_SEEDS, started=time.strftime("%Y-%m-%dT%H:%M:%S"),
                       code_sha256={f: IG.sha(os.path.join(HERE, f)) for f in ("v5v41_e6.py", "v5v41.py")}), f, indent=1)
    with mp.get_context("spawn").Pool(a.workers) as pool:
        for r in pool.imap_unordered(run_network, jobs):
            print(r, flush=True)
    with open(os.path.join(a.out, "run_done.json"), "x") as f:
        json.dump(dict(stage1_post=IG.stage1(), finished=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1)


if __name__ == "__main__":
    main()
