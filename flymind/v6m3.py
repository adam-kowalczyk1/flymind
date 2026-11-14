"""flymind/v6m3.py — V6m3 intermediate-layer count-vs-timing dissection (EXPLORATORY, pre-registered: program_v5v41/V6m3_PROTOCOL.md).
Part A: LC10a clamped, intermediates free (REF / t_ref 0 / t_ref 0 + gain- or bias-matched) → intermediate count deficit.
Part B: LC10a + intermediates clamped (DNa02 only free), 2×2 count-swap of real intermediate trains (timing source × count source).
Engine: v6m2.step2 (= v6m.step / alif.ALIF.step with defaults) with per-neuron gain (alif `gain`) and per-neuron bias current.
Run: .venv/bin/python -I -B flymind/v6m3.py --out flymind/results/v6m3 --protocol-sha256 <sha> [--smoke]
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
import v5v42 as V2  # noqa: E402
import v5v43 as R  # noqa: E402
import v6m as M  # noqa: E402
import v6m2 as M2  # noqa: E402
from alif import ALIF, ALIFParams  # noqa: E402

PROTOCOL = os.path.join(HERE, "program_v5v41", "V6m3_PROTOCOL.md")
T, W0, W1, SS = M.T, M.W0, M.W1, M.SS
LEVELS = (8.0, 9.0)
SETS = {"MAIN": dict(b1=tuple(range(8_421_001, 8_421_011)), noise=tuple(range(8_445_001, 8_445_009))),
        "REP": dict(b1=tuple(range(8_421_011, 8_421_021)), noise=tuple(range(8_445_201, 8_445_209)))}
CAL_SEEDS = tuple(range(8_445_101, 8_445_105))
GAIN_GRID = np.round(np.arange(0.30, 1.0 + 1e-9, 0.025), 3)
BIAS_GRID = np.round(np.arange(-20.0, 0.0 + 1e-9, 0.5), 2)
A_CONDS = ("REF", "MT0", "MT0G", "MT0B", "LCIRC")
B_CELLS = ("DD", "DB", "BD", "BB")          # (timing source, count source)
B_DYN = ("REF", "T0", "T0G")
P = ALIFParams(noise=2.0)


def setup():
    data, idx, _, _ = V.make_net("DATA", None)
    N = len(data.bodies)
    lc, mid = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    dn = np.r_[idx["DNa02_L"], idx["DNa02_R"]]
    return data, idx, N, lc, mid, dn


def run3(data, sd, I, cidx, forced, tref, gain, bias):
    """One 1000-step replay. tref/gain per neuron; bias: per-neuron constant current added to I (or None)."""
    net = ALIF(data, P, sd, gain=gain)
    if bias is not None:
        I = I + bias[None, :]
    kl = np.ones(net.N)
    out = np.zeros((T, net.N), bool)
    for t in range(T):
        out[t] = M2.step2(net, I[t], forced[t], cidx, tref, kl)
    return out


def a_vectors(cond, N, mid, cal):
    tref, gain, bias = np.full(N, P.t_ref), np.ones(N), None
    if cond in ("MT0", "MT0G", "MT0B"):
        tref[mid] = 0.0
    if cond == "MT0G":
        gain[mid] = cal["mid_gain"]
    if cond == "MT0B":
        bias = np.zeros(N)
        bias[mid] = cal["mid_bias"]
    return tref, gain, bias


def b_vectors(dyn, N, dn, cal):
    tref, gain = np.full(N, P.t_ref), np.ones(N)
    if dyn in ("T0", "T0G"):
        tref[dn] = 0.0
    if dyn == "T0G":
        gain[dn] = cal["dn_gain"]
    return tref, gain


def count_swap(timing, counts, rng):
    """timing, counts: [T, n] bool. Returns (train with timing's spikes, per-neuron count of `counts` in [W0, W1)), n_added, n_fallback)."""
    out = timing.copy()
    seg = out[W0:W1]
    added = fallback = 0
    for j in range(seg.shape[1]):
        have = np.flatnonzero(seg[:, j])
        want = int(counts[W0:W1, j].sum())
        if len(have) > want:
            seg[:, j] = False
            seg[rng.choice(have, want, replace=False), j] = True
        elif len(have) < want:
            for _ in range(want - len(have)):
                occ = np.flatnonzero(seg[:, j])
                ok = np.ones(len(seg), bool)
                for d in range(-3, 4):
                    pos = occ + d
                    ok[pos[(pos >= 0) & (pos < len(seg))]] = False
                cand = np.flatnonzero(ok)
                if len(cand) == 0:                     # r2 fallback: any free 1-ms slot (ISI >= 1), counted
                    cand = np.flatnonzero(~seg[:, j])
                    fallback += 1
                seg[rng.choice(cand), j] = True
                added += 1
    return out, added, fallback


def cal_job(c):
    """One (level, side, seed) calibration cell on the DATA source: curves for mid gain, mid bias, DN gain."""
    data, idx, N, lc, mid, dn = setup()
    lv, side, sd = c
    I = R.current(idx, side, lv, N)
    mi, d = idx[f"mid_{side}"], idx[f"DNa02_{side}"][0]
    lc_tr = ALIF(data, P, sd).run(I, T)[:, lc]
    tref = np.full(N, P.t_ref)
    ref = run3(data, sd, I, lc, lc_tr, tref, np.ones(N), None)
    out = dict(ref_mid=ref[SS:W1][:, mi].sum() / (len(mi) * 0.5), ref_dn=ref[SS:W1, d].sum() / 0.5, mid_gain=[], mid_bias=[], dn_gain=[])
    t0m = tref.copy()
    t0m[mid] = 0.0
    for g in GAIN_GRID:
        gv = np.ones(N)
        gv[mid] = g
        s = run3(data, sd, I, lc, lc_tr, t0m, gv, None)
        out["mid_gain"].append(s[SS:W1][:, mi].sum() / (len(mi) * 0.5))
    for b in BIAS_GRID:
        bv = np.zeros(N)
        bv[mid] = b
        s = run3(data, sd, I, lc, lc_tr, t0m, np.ones(N), bv)
        out["mid_bias"].append(s[SS:W1][:, mi].sum() / (len(mi) * 0.5))
    lcmid = np.r_[lc, mid]
    forced = np.concatenate([lc_tr, ref[:, mid]], 1)
    t0d = tref.copy()
    t0d[dn] = 0.0
    for g in GAIN_GRID:
        gv = np.ones(N)
        gv[dn] = g
        s = run3(data, sd, I, lcmid, forced, t0d, gv, None)
        out["dn_gain"].append(s[SS:W1, d].sum() / 0.5)
    return out


def calibrate(pool, smoke):
    cells = [(lv, s, sd) for lv in LEVELS for s in "LR" for sd in (CAL_SEEDS[:1] if smoke else CAL_SEEDS)]
    res = pool.map(cal_job, cells)
    ref_mid, ref_dn = np.mean([r["ref_mid"] for r in res]), np.mean([r["ref_dn"] for r in res])
    mg = np.mean([r["mid_gain"] for r in res], 0)
    mb = np.mean([r["mid_bias"] for r in res], 0)
    dg = np.mean([r["dn_gain"] for r in res], 0)
    return dict(ref_mid=float(ref_mid), ref_dn=float(ref_dn),
                mid_gain=float(GAIN_GRID[np.argmin(np.abs(mg - ref_mid))]), mid_bias=float(BIAS_GRID[np.argmin(np.abs(mb - ref_mid))]),
                dn_gain=float(GAIN_GRID[np.argmin(np.abs(dg - ref_dn))]),
                curves=dict(gain_grid=GAIN_GRID.tolist(), bias_grid=BIAS_GRID.tolist(), mid_gain=mg.tolist(), mid_bias=mb.tolist(), dn_gain=dg.tolist()))


def part_a_one(data, idx, N, lc, mid, sd, I, side, lc_tr, cond, cal, r):
    if cond == "LCIRC":
        lc_tr = R.manipulate(lc_tr, "CIRC", np.random.default_rng(np.random.SeedSequence([8_446_000, 9, r])))[0]
    tref, gain, bias = a_vectors(cond if cond != "LCIRC" else "REF", N, mid, cal)
    return run3(data, sd, I, lc, lc_tr, tref, gain, bias)


def job_run(job):
    t0 = time.perf_counter()
    data, idx, N, lc, mid, dn = setup()
    W = np.asarray(data.W, float)
    cal = job["cal"]
    S = SETS[job["set"]]
    seeds = S["noise"][:job["n_reps"]]
    src = data if job["family"] == "DATA" else V2.make_block_net("LCxLC", job["k"])[0]
    set_id = list(SETS).index(job["set"])
    src_id = 0 if job["family"] == "DATA" else job["k"] - 8_421_000
    A = np.full((len(A_CONDS), len(LEVELS), 2, len(seeds), 6), np.nan)   # dn rate, mid ipsi count, D_exc, D_inh, mid pair r, lc count
    B = np.full((len(B_DYN), len(B_CELLS), len(LEVELS), 2, len(seeds)), np.nan)
    added = np.zeros((2, len(LEVELS), 2, len(seeds)))
    checks = dict(ref_free_identity=[], dd_bb_identity=[], swap_counts=[], swap_subset=[], swap_isi=[], swap_fallback_spikes=[])
    lcmid = np.r_[lc, mid]
    for li, lv in enumerate(LEVELS):
        for si, side in enumerate("LR"):
            I = R.current(idx, side, lv, N)
            mi, d = idx[f"mid_{side}"], idx[f"DNa02_{side}"][0]
            w = W[d, mid]
            for r, sd in enumerate(seeds):
                free = ALIF(src, P, sd).run(I, T)
                lc_tr = free[:, lc]
                ref = None
                for ci, cond in enumerate(A_CONDS):
                    s = part_a_one(data, idx, N, lc, mid, sd, I, side, lc_tr, cond, cal, r)
                    if cond == "REF":
                        ref = s
                        if job["family"] == "DATA":
                            nonlc = np.setdiff1d(np.arange(N), lc)
                            checks["ref_free_identity"].append(bool(np.array_equal(s[:, nonlc], free[:, nonlc])))
                    n = s[SS:W1][:, mid].sum(0)
                    pr = M.sync_metrics(s[:, mi])[M.SYNC_NAMES.index("paircorr5")]
                    A[ci, li, si, r] = (s[SS:W1, d].sum() / 0.5, s[SS:W1][:, mi].sum(), (np.maximum(w, 0) * n).sum(),
                                        (np.minimum(w, 0) * n).sum(), pr, s[SS:W1][:, lc].sum())
                if job["family"] == "DATA":
                    continue
                # Part B: DATA-source REF intermediate trains for the same (level, side, rep)
                dfree = ALIF(data, P, sd).run(I, T)
                dref = run3(data, sd, I, lc, dfree[:, lc], np.full(N, P.t_ref), np.ones(N), None)
                XD, XB = dref[:, mid], ref[:, mid]
                rng = np.random.default_rng(np.random.SeedSequence([8_446_000, set_id, li, si, r, src_id]))
                DB, nDB, fDB = count_swap(XD, XB, rng)
                BD, nBD, fBD = count_swap(XB, XD, rng)
                checks["swap_fallback_spikes"].append(fDB + fBD)
                added[:, li, si, r] = (nDB / max(XB[W0:W1].sum(), 1), nBD / max(XD[W0:W1].sum(), 1))
                for name, x, tsrc, csrc in (("DB", DB, XD, XB), ("BD", BD, XB, XD)):
                    checks["swap_counts"].append(bool(np.array_equal(x[W0:W1].sum(0), csrc[W0:W1].sum(0))))
                    keep = x[W0:W1] & tsrc[W0:W1]
                    checks["swap_subset"].append(bool(np.array_equal(keep.sum(0), np.minimum(tsrc[W0:W1].sum(0), csrc[W0:W1].sum(0)))))
                    checks["swap_isi"].append(bool(all((np.diff(np.flatnonzero(x[W0:W1, j])) >= 4).all() or not (x[W0:W1, j] & ~tsrc[W0:W1, j]).any()
                                                       for j in range(x.shape[1]))))
                lcsrc = {"D": dfree[:, lc], "B": lc_tr}
                cells = {"DD": (XD, "D"), "DB": (DB, "D"), "BD": (BD, "B"), "BB": (XB, "B")}
                for di, dyn in enumerate(B_DYN):
                    tref, gain = b_vectors(dyn, N, dn, cal)
                    for bi, cname in enumerate(B_CELLS):
                        mtr, lsrc = cells[cname]
                        s = run3(data, sd, I, lcmid, np.concatenate([lcsrc[lsrc], mtr], 1), tref, gain, None)
                        B[di, bi, li, si, r] = s[SS:W1, d].sum() / 0.5
                        if dyn == "REF" and cname in ("DD", "BB"):
                            checks["dd_bb_identity"].append(bool(np.array_equal(s[:, d], (dref if cname == "DD" else ref)[:, d])))
    with open(os.path.join(job["out"], f"{job['name']}.npz"), "xb") as f:
        np.savez_compressed(f, A=A, B=B, added=added, a_conds=np.array(A_CONDS), b_cells=np.array(B_CELLS), b_dyn=np.array(B_DYN),
                            levels=np.array(LEVELS), seeds=np.array(seeds))
    fb = checks.pop("swap_fallback_spikes")
    return dict(name=job["name"], wall_s=round(time.perf_counter() - t0, 1), checks={k: (all(v), len(v)) for k, v in checks.items()},
                swap_fallback_spikes=int(sum(fb)))


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    ap.add_argument("--protocol-sha256", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    import integrity_v5v41 as IG
    if IG.stage1()["ok"] != 28:
        sys.exit("STOP: Stage 1")
    if hashlib.sha256(open(PROTOCOL, "rb").read()).hexdigest() != a.protocol_sha256:
        sys.exit("refused: protocol sha256 mismatch")
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    calp = os.path.join(a.out, "calibration.json")
    with mp.get_context("spawn").Pool(a.workers) as pool:
        if os.path.exists(calp):
            cal = json.load(open(calp))
        else:
            cal = calibrate(pool, a.smoke)
            with open(calp, "x") as f:
                json.dump(cal, f, indent=1)
        print("calibration", {k: cal[k] for k in ("ref_mid", "ref_dn", "mid_gain", "mid_bias", "dn_gain")}, flush=True)
        jobs = []
        for sname, S in SETS.items():
            if a.smoke and sname != "MAIN":
                continue
            srcs = [("DATA", None)] + [("B1", k) for k in S["b1"]]
            if a.smoke:
                srcs = srcs[:2]
            for fam, k in srcs:
                jobs.append(dict(set=sname, family=fam, k=k, cal=cal, out=raw, n_reps=1 if a.smoke else 8,
                                 name=f"{sname}_{fam}" + (f"_{k}" if k else "")))
        jobs = [j for j in jobs if not os.path.exists(os.path.join(raw, j["name"] + ".npz"))]
        with open(os.path.join(a.out, f"config_{time.strftime('%Y%m%dT%H%M%S')}.json"), "x") as f:
            json.dump(dict(protocol_sha256=a.protocol_sha256, smoke=a.smoke, sets=SETS, levels=LEVELS, a_conds=A_CONDS, b_cells=B_CELLS, b_dyn=B_DYN,
                           jobs=[j["name"] for j in jobs], code_sha256={f: IG.sha(os.path.join(HERE, f)) for f in ("v6m3.py", "v6m2.py", "v6m.py", "alif.py")},
                           started=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1)
        for r in pool.imap_unordered(job_run, jobs):
            print(json.dumps(r), flush=True)
    with open(os.path.join(a.out, f"run_done_{time.strftime('%Y%m%dT%H%M%S')}.json"), "x") as f:
        json.dump(dict(stage1_post=IG.stage1(), finished=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1)


if __name__ == "__main__":
    main()
