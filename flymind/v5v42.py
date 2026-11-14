"""flymind/v5v42.py — V5 v4.2 single-block connectivity controls (EXPLORATORY). Protocol: program_v5v41/V5v42_PROTOCOL.md.
Families (CONTROL, block_shuffle.py): B1 LC×LC, B2 LC→mid, B3 mid→LC, B4 mid×mid, B5 ALL (= SWS v2 rule, fresh seeds).
Reference families from V5 v4.1 (same seeds, same networks): DATA, SWS (8 410 001–050).
Step 1 (--structure): per-instance checks + graph metrics → structure.json. Step 2 (run): open-loop schedules on every instance.
No mujoco, no bio2. Writes only under --out.
Run: .venv/bin/python -I -B flymind/v5v42.py --structure --out flymind/results/v5v42
     .venv/bin/python -I -B flymind/v5v42.py --out flymind/results/v5v42 --protocol-sha256 <sha>
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
from block_shuffle import block_masks, block_shuffle, graph_metrics, strongest_preserved  # noqa: E402
from side_shuffle import KEYS, layer_side_labels, properties  # noqa: E402
from visual_path import network  # noqa: E402

PROTOCOL = os.path.join(HERE, "program_v5v41", "V5v42_PROTOCOL.md")
FAMILIES = {"B1": ("LCxLC", range(8_421_001, 8_421_051)), "B2": ("LC2MID", range(8_422_001, 8_422_051)),
            "B3": ("MID2LC", range(8_423_001, 8_423_051)), "B4": ("MIDxMID", range(8_424_001, 8_424_051)),
            "B5": ("ALL", range(8_425_001, 8_425_051))}
STEP_EXPS = ("E1", "E1n0")          # from v5v41.schedules (unchanged); plus E6 from v5v41_e6


def make_block_net(block, seed, J0=0.2):
    spec, idx, _ = network(J0)
    gr, _ = layer_side_labels(spec, idx)
    idx = dict(idx, mid_L=np.flatnonzero(gr == "mid_L"), mid_R=np.flatnonzero(gr == "mid_R"))
    sh = block_shuffle(spec, gr, seed, block, max_attempt_factor=3 if block == "ALL" else 10)
    return sh, idx, gr, spec


def net_for_job(job):
    if job["family"] in ("DATA", "SWS"):
        spec, idx, _, _ = V.make_net(job["family"], job["k"], job.get("J0", 0.2))
    else:
        spec, idx, _, _ = make_block_net(FAMILIES[job["family"]][0], job["k"], job.get("J0", 0.2))
    if V.w_sha(spec) != job["sha"]:
        raise RuntimeError(f"{job['name']}: rebuilt network differs from the checked instance")
    return spec, idx


def run_network(job):
    t0 = time.perf_counter()
    spec, idx = net_for_job(job)
    P = ALIFParams(**{**ALIFParams(noise=2.0).__dict__, **job.get("alif", {})})
    E = V.schedules(False)
    R = job["reps"]
    out = {}
    for ename in job.get("exps", STEP_EXPS):
        Rr = 1 if ename == "E1n0" else R
        Pe = ALIFParams(**{**P.__dict__, "noise": 0.0}) if ename == "E1n0" else P
        res = [[[V.simulate(spec, idx, side, c, V.NOISE_SEEDS[r], Pe, V.INITV_SEEDS[r]) for r in range(Rr)]
                for side in ("L", "R")] for c in E[ename]]
        for key in ("counts", "adapt", "angle", "first_dn"):
            out[f"{ename}_{key}"] = np.array([[[x[key] for x in s] for s in lv] for lv in res])
        out[f"{ename}_ss"] = np.array([[np.sum([x["ss"] for x in s], 0) for s in lv] for lv in res])
        out[f"{ename}_levels"] = np.array([c["I"] for c in E[ename]])
    if job.get("e6", True):
        c6 = np.zeros((len(E6.I0S), len(E6.DELTAS), R, 100, 6), np.int16)
        for i, I0 in enumerate(E6.I0S):
            for j, dl in enumerate(E6.DELTAS):
                cfg = dict(I=I0 + dl / 2, step_ms=1000, contra_frac=(I0 - dl / 2) / (I0 + dl / 2))
                for r in range(R):
                    c6[i, j, r] = V.simulate(spec, idx, "L", cfg, V.NOISE_SEEDS[r], P)["counts"]
        out["E6_counts"], out["E6_I0"], out["E6_deltas"] = c6, np.array(E6.I0S), np.array(E6.DELTAS)
    out["n_pop"] = np.array([len(idx["in_L"]), len(idx["in_R"]), len(idx["mid_L"]), len(idx["mid_R"]), 1, 1])
    path = os.path.join(job["out"], f"{job['name']}.npz")
    with open(path, "xb") as f:
        np.savez_compressed(f, **out)
    return dict(name=job["name"], wall_s=round(time.perf_counter() - t0, 1))


def structure_job(args):
    fam, k = args
    spec, idx, _ = network(0.2)
    gr, _ = layer_side_labels(spec, idx)
    if fam == "DATA":
        sh = spec
        rep = {}
    elif fam == "SWS":
        sh, _, _, rep = V.make_net("SWS", k)
    else:
        block = FAMILIES[fam][0]
        sh = block_shuffle(spec, gr, k, block, max_attempt_factor=3 if block == "ALL" else 10)
        rep = sh.report["block_shuffle"]
    row = dict(family=fam, seed=k, sha=V.w_sha(sh), graph=graph_metrics(sh.W_data, gr),
               strongest=strongest_preserved(spec.W_data, sh.W_data), report={x: y for x, y in rep.items() if x != "report"})
    if fam != "DATA":
        p = properties(spec, sh, gr)
        row["properties_ok"] = bool(all(p[x] for x in KEYS))
        row["failed"] = [x for x in KEYS if not p[x]]
        row["changed_frac_total"] = p["changed_frac"]
        A0, A1 = spec.W_data != 0, sh.W_data != 0
        row["changed_frac_by_block"] = {b: round(float((A1 & ~A0)[m].sum() / max(A0[m].sum(), 1)), 4) for b, m in block_masks(gr).items()}
        if fam in FAMILIES and FAMILIES[fam][0] != "ALL":
            m = block_masks(gr)[FAMILIES[fam][0]]
            row["outside_block_unchanged"] = bool(np.array_equal(sh.W_data[~m], spec.W_data[~m]))
            row["complete"] = bool(rep["complete"])
        elif fam == "B5":
            row["complete"] = bool(rep["complete"])
    return row


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    ap.add_argument("--structure", action="store_true")
    ap.add_argument("--protocol-sha256")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    import integrity_v5v41 as IG
    if IG.stage1()["ok"] != 28:
        sys.exit("STOP: Stage 1")
    os.makedirs(a.out, exist_ok=True)
    spath = os.path.join(a.out, "structure.json")
    if a.structure:
        jobs = [("DATA", None)] + [("SWS", k) for k in V.SWS_SEEDS] + [(f, k) for f, (_, ks) in FAMILIES.items() for k in ks]
        with mp.get_context("spawn").Pool(a.workers) as pool:
            rows = pool.map(structure_job, jobs)
        shas = [r["sha"] for r in rows]
        summ = dict(n=len(rows), distinct=len(set(shas)) == len(shas),
                    all_ok=all(r.get("properties_ok", True) and r.get("outside_block_unchanged", True) and r.get("complete", True) for r in rows))
        with open(spath, "x") as f:
            json.dump(dict(rows=rows, summary=summ), f, indent=1, default=float)
        print(summ)
        return
    psha = hashlib.sha256(open(PROTOCOL, "rb").read()).hexdigest()
    if psha != a.protocol_sha256:
        sys.exit("refused: protocol sha256 mismatch")
    st = json.load(open(spath))
    if not (st["summary"]["distinct"] and st["summary"]["all_ok"]):
        sys.exit("STOP: structure checks failed")
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    jobs = [dict(family=r["family"], k=r["seed"], sha=r["sha"], name=r["family"] if r["family"] == "DATA" else f"{r['family']}_{r['seed']}")
            for r in st["rows"] if r["family"] not in ("SWS",)]       # SWS + DATA open-loop E1/E1n0/E6 already in v5v41 (same seeds)
    jobs = [j for j in jobs if j["family"] != "DATA"]
    for j in jobs:
        j.update(out=raw, reps=8)
    with open(os.path.join(a.out, "config.json"), "x") as f:
        json.dump(dict(protocol_sha256=psha, families={k: (v[0], [v[1][0], v[1][-1]]) for k, v in FAMILIES.items()}, exps=STEP_EXPS + ("E6",),
                       reps=8, noise_seeds=V.NOISE_SEEDS, started=time.strftime("%Y-%m-%dT%H:%M:%S"),
                       code_sha256={f: IG.sha(os.path.join(HERE, f)) for f in ("v5v42.py", "block_shuffle.py", "v5v41.py", "v5v41_e6.py")}),
                  f, indent=1, default=str)
    with mp.get_context("spawn").Pool(a.workers) as pool:
        for r in pool.imap_unordered(run_network, jobs):
            print(r, flush=True)
    with open(os.path.join(a.out, "run_done.json"), "x") as f:
        json.dump(dict(stage1_post=IG.stage1(), finished=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1)


if __name__ == "__main__":
    main()
