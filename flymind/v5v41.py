"""flymind/v5v41.py — V5 v4.1 open-loop response characterization (EXPLORATORY). Protocol: program_v5v41/V5v41_PROTOCOL.md.
No mujoco, no bio2, frozen modules imported unchanged (alif, visual_path, side_shuffle, decoder). Writes only under --out.

Also the shared engine for the later open-loop stages (v4.2 block controls, V6 parameter study): networks come from a "family"
(DATA, SWS, block shuffles), dynamics from alif.ALIF with optional ALIFParams overrides, schedules from SCHEDULES.

Run:   .venv/bin/python -I -B flymind/v5v41.py --out flymind/results/v5v41 --protocol-sha256 <sha>
Smoke: .venv/bin/python -I -B flymind/v5v41.py --smoke --out <scratchpad dir>
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
from alif import ALIF, ALIFParams  # noqa: E402
from decoder import SteerDecoder, SteerParams  # noqa: E402
from side_shuffle import KEYS, layer_side_labels, properties, shuffle_within_side  # noqa: E402
from visual_path import network  # noqa: E402

PROTOCOL = os.path.join(HERE, "program_v5v41", "V5v41_PROTOCOL.md")
SWS_SEEDS = tuple(range(8_410_001, 8_410_051))
NOISE_SEEDS = tuple(range(8_411_001, 8_411_009))
INITV_SEEDS = tuple(range(8_412_001, 8_412_009))
SMOKE_SEEDS = (8_490_001, 8_490_002)
DEC_OFFSET, DEC_SLOPE = 0.0, 492.11874242900916            # frozen V5 v4 DATA decoder (results/v5v4/run_meta_A_*.json)
STEER = SteerParams(tau_s=(0.10,), gain=2.5, w_max=1.0)     # as loop.STEER
BIN = 10                                                    # ms
POPS = ("in_ipsi", "in_contra", "mid_L", "mid_R", "dn_L", "dn_R")
LV_E1 = np.round(np.union1d(np.arange(4.0, 12.0001, 0.25), np.arange(6.0, 10.0001, 0.125)), 4)
LV_610 = np.round(np.arange(6.0, 10.0001, 0.25), 4)
LV_E5 = np.round(np.arange(6.0, 10.0001, 0.5), 4)


def schedules(smoke=False):
    """Experiment name → list of (level, pre_ms, pre_side, pre_mV, step_ms, contra_frac, ramp, init_v, noise_override)."""
    lv1 = LV_E1[::8] if smoke else LV_E1
    lv2 = LV_610[::4] if smoke else LV_610
    E = {"E1": [dict(I=float(x), step_ms=1000) for x in lv1],
         "E1n0": [dict(I=float(x), step_ms=1000, noise=0.0) for x in lv1],
         "E2": [dict(I=float(x), step_ms=1000, contra_frac=0.5) for x in lv2],
         "E3": [dict(I=float(x), step_ms=1000, pre_ms=500, pre_side="ipsi", pre_mV=10.0) for x in lv2],
         "E3c": [dict(I=float(x), step_ms=1000, pre_ms=500, pre_side="contra", pre_mV=10.0) for x in lv2],
         "E4": [dict(I=None, ramp=(4.0, 12.0, 4000))],
         "E5": [dict(I=float(x), step_ms=1000, init_v=True) for x in (LV_E5[::4] if smoke else LV_E5)]}
    return E


def make_net(family, k, J0=0.2):
    """(spec, idx, groups, report). family: 'DATA' or 'SWS' (k = seed). Later stages add block families in their own modules."""
    spec, idx, _ = network(J0)
    gr, _ = layer_side_labels(spec, idx)
    idx = dict(idx, mid_L=np.flatnonzero(gr == "mid_L"), mid_R=np.flatnonzero(gr == "mid_R"))
    if len(idx["mid_L"]) + len(idx["mid_R"]) != len(idx["mid"]):
        raise ValueError("mid neurons without L/R side")
    if family == "DATA":
        return spec, idx, gr, dict(family="DATA")
    if family == "SWS":
        sh = shuffle_within_side(spec, gr, k)
        return sh, idx, gr, dict(family="SWS", **sh.report["shuffle_within_side"])
    raise ValueError(family)


def w_sha(spec):
    return hashlib.sha256(np.ascontiguousarray(spec.W_data).tobytes()).hexdigest()


def simulate(spec, idx, side, cfg, seed, P, initv_seed=None):
    """One run. Returns dict of compact arrays. Step onset at t = pre_ms. Currents only on LC10a."""
    o = "R" if side == "L" else "L"
    net = ALIF(spec, P, seed)
    if cfg.get("init_v"):
        net.v = np.random.default_rng(initv_seed).uniform(P.v_rest, P.v_th, net.N)
    N = net.N
    iI, iC = idx[f"in_{side}"], idx[f"in_{o}"]
    if "ramp" in cfg and cfg["ramp"]:
        lo, hi, half = cfg["ramp"]
        prof = np.r_[np.linspace(lo, hi, half, endpoint=False), np.linspace(hi, lo, half, endpoint=False)]
        pre, T = 0, 2 * half
        ipsi_t, contra_t = prof, np.zeros(T)
    else:
        pre = cfg.get("pre_ms", 0)
        T = pre + cfg["step_ms"]
        ipsi_t = np.full(T, cfg["I"])
        contra_t = np.full(T, cfg["I"] * cfg.get("contra_frac", 0.0))
        if pre:
            ipsi_t[:pre] = cfg["pre_mV"] if cfg["pre_side"] == "ipsi" else 0.0
            contra_t[:pre] = cfg["pre_mV"] if cfg["pre_side"] == "contra" else 0.0
    dec = SteerDecoder({"DNa02_L": idx["DNa02_L"], "DNa02_R": idx["DNa02_R"]}, ("DNa02",), [DEC_OFFSET], [DEC_SLOPE], STEER)
    nb = T // BIN
    counts = np.zeros((nb, 6), np.int16)
    adapt = np.zeros((nb, 3), np.float32)
    angle = np.zeros(nb, np.float32)
    ss = np.zeros(N, np.int32)                          # per-neuron spikes in steady window (pre+500 … pre+1000)
    first_dn = -1
    dn_i = idx[f"DNa02_{side}"][0]
    mL, mR = idx["mid_L"], idx["mid_R"]
    I = np.zeros(N)
    chunk = np.zeros((BIN, N), bool)
    for b in range(nb):
        for j in range(BIN):
            t = b * BIN + j
            I[iI] = ipsi_t[t]
            I[iC] = contra_t[t]
            s = net.step(I)
            chunk[j] = s
            if first_dn < 0 and t >= pre and s[dn_i]:
                first_dn = t - pre
        counts[b] = (chunk[:, iI].sum(), chunk[:, iC].sum(), chunk[:, mL].sum(), chunk[:, mR].sum(),
                     chunk[:, idx["DNa02_L"]].sum(), chunk[:, idx["DNa02_R"]].sum())
        if pre + 500 <= b * BIN < pre + 1000 and "ramp" not in cfg:
            ss += chunk.sum(0)
        adapt[b] = (net.a[iI].mean(), net.a[np.r_[mL, mR]].mean(), net.a[dn_i])
        angle[b] = dec.step(chunk, 1.0)["angle"][0]
    if not (np.isfinite(net.v).all() and np.isfinite(net.g).all() and np.isfinite(net.a).all()):
        raise FloatingPointError("non-finite ALIF state")
    return dict(counts=counts, adapt=adapt, angle=angle, ss=ss, first_dn=first_dn, pre=pre)


def run_network(job):
    """Worker: all experiments for one network. job = dict(family, k, sha, out, smoke, alif, J0, name)."""
    t0 = time.perf_counter()
    spec, idx, gr, rep = make_net(job["family"], job["k"], job.get("J0", 0.2))
    if w_sha(spec) != job["sha"]:
        raise RuntimeError(f"{job['name']}: rebuilt network differs from the checked instance")
    base = ALIFParams(noise=2.0)
    P = ALIFParams(**{**base.__dict__, **job.get("alif", {})})
    E = schedules(job["smoke"])
    reps = job["reps"]
    out = {}
    for ename, cfgs in E.items():
        R = 1 if ename == "E1n0" else reps
        Pe = ALIFParams(**{**P.__dict__, "noise": 0.0}) if ename == "E1n0" else P
        res = [[[simulate(spec, idx, side, c, NOISE_SEEDS[r], Pe, INITV_SEEDS[r]) for r in range(R)]
                for side in ("L", "R")] for c in cfgs]
        out[f"{ename}_counts"] = np.array([[[x["counts"] for x in s] for s in lv] for lv in res])
        out[f"{ename}_adapt"] = np.array([[[x["adapt"] for x in s] for s in lv] for lv in res])
        out[f"{ename}_angle"] = np.array([[[x["angle"] for x in s] for s in lv] for lv in res])
        out[f"{ename}_first_dn"] = np.array([[[x["first_dn"] for x in s] for s in lv] for lv in res])
        out[f"{ename}_ss"] = np.array([[np.sum([x["ss"] for x in s], 0) for s in lv] for lv in res])
        out[f"{ename}_levels"] = np.array([c["I"] if c["I"] is not None else np.nan for c in cfgs])
    out["n_pop"] = np.array([len(idx["in_L"]), len(idx["in_R"]), len(idx["mid_L"]), len(idx["mid_R"]), 1, 1])
    path = os.path.join(job["out"], f"{job['name']}.npz")
    with open(path, "xb") as f:
        np.savez_compressed(f, **out)
    return dict(name=job["name"], wall_s=round(time.perf_counter() - t0, 1), path=path)


def graph_stats(W, groups):
    """LC×LC block statistics (MODEL-free graph measures on data edges). Directed adjacency A[post, pre]."""
    A = (W != 0)
    inn = np.array([g.startswith("in_") for g in groups])
    B = A[np.ix_(inn, inn)]
    recip = int((B & B.T).sum() // 2)
    U = (B | B.T).astype(float)
    tri = int(np.trace(U @ U @ U) // 6)
    return dict(lc_edges=int(B.sum()), lc_reciprocal_pairs=recip, lc_triangles_undirected=tri)


def check_instances(seeds, smoke):
    spec, idx, _ = network(0.2)
    gr, _ = layer_side_labels(spec, idx)
    A0 = spec.W_data != 0
    rows, changed = [], []
    for k in seeds:
        sh = shuffle_within_side(spec, gr, k)
        p = properties(spec, sh, gr)
        ok = all(p[x] for x in KEYS) and sh.report["shuffle_within_side"]["complete"]
        A = sh.W_data != 0
        changed.append(A & ~A0)
        rows.append(dict(seed=k, sha=w_sha(sh), properties_ok=bool(ok), failed=[x for x in KEYS if not p[x]],
                         changed_edges=p["changed_edges"], changed_frac=p["changed_frac"], jaccard_vs_data=p["jaccard_edges"],
                         **graph_stats(sh.W_data, gr), swaps=sh.report["shuffle_within_side"]["swaps"]))
    jac = []
    for i in range(len(changed)):
        for j in range(i + 1, len(changed)):
            u = (changed[i] | changed[j]).sum()
            jac.append(float((changed[i] & changed[j]).sum() / u) if u else 1.0)
    shas = [r["sha"] for r in rows]
    summ = dict(n=len(rows), all_properties_ok=all(r["properties_ok"] for r in rows), distinct_W=len(set(shas)) == len(shas),
                data_sha=w_sha(spec), any_equal_data=w_sha(spec) in shas, data_graph=graph_stats(spec.W_data, gr),
                pairwise_changed_jaccard=dict(min=min(jac), median=float(np.median(jac)), max=max(jac)) if jac else None)
    return rows, summ


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    ap.add_argument("--protocol-sha256")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    import integrity_v5v41 as IG
    s1 = IG.stage1()
    if s1["ok"] != 28:
        sys.exit(f"STOP: Stage 1 {s1}")
    psha = hashlib.sha256(open(PROTOCOL, "rb").read()).hexdigest()
    if not a.smoke and psha != a.protocol_sha256:
        sys.exit("refused: protocol sha256 mismatch")
    seeds = SMOKE_SEEDS if a.smoke else SWS_SEEDS
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    rows, summ = check_instances(seeds, a.smoke)
    if not (summ["all_properties_ok"] and summ["distinct_W"] and not summ["any_equal_data"]):
        sys.exit(f"STOP: instance checks failed {summ}")
    with open(os.path.join(a.out, "instances.json"), "x") as f:
        json.dump(dict(rows=rows, summary=summ), f, indent=1)
    reps = 2 if a.smoke else 8
    jobs = [dict(family="DATA", k=None, sha=summ["data_sha"], name="DATA")] + \
           [dict(family="SWS", k=r["seed"], sha=r["sha"], name=f"SWS_{r['seed']}") for r in rows]
    for j in jobs:
        j.update(out=raw, smoke=a.smoke, reps=reps)
    cfg = dict(protocol_sha256=psha, smoke=a.smoke, reps=reps, noise_seeds=NOISE_SEEDS[:reps], initv_seeds=INITV_SEEDS[:reps],
               sws_seeds=list(seeds), decoder=dict(offset=DEC_OFFSET, slope=DEC_SLOPE, steer=STEER.__dict__),
               alif=ALIFParams(noise=2.0).__dict__, J0=0.2, bin_ms=BIN, pops=POPS,
               schedules={k: v for k, v in schedules(a.smoke).items()}, stage1_pre=s1, started=time.strftime("%Y-%m-%dT%H:%M:%S"),
               code_sha256={f: IG.sha(os.path.join(HERE, f)) for f in ("v5v41.py", "alif.py", "side_shuffle.py", "visual_path.py",
                                                                     "decoder.py", "snn_interface.py", "connectome.py")})
    with open(os.path.join(a.out, "config.json"), "x") as f:
        json.dump(cfg, f, indent=1, default=str)
    t0 = time.perf_counter()
    with mp.get_context("spawn").Pool(a.workers) as pool:
        for r in pool.imap_unordered(run_network, jobs):
            print(r, flush=True)
    s1b = IG.stage1()
    with open(os.path.join(a.out, "run_done.json"), "x") as f:
        json.dump(dict(wall_s=round(time.perf_counter() - t0, 1), stage1_post=s1b, finished=time.strftime("%Y-%m-%dT%H:%M:%S"),
                       VALID=s1b["ok"] == 28), f, indent=1)
    print("done", s1b["ok"], "/ 28")


if __name__ == "__main__":
    main()
