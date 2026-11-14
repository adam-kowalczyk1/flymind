"""flymind/v6m2.py — V6m2 DNa02-only factorial (EXPLORATORY, pre-registered: program_v5v41/V6m2_PROTOCOL.md).
LC10a and all intermediates clamped; only DNa02 is free. DNa02 dynamics × intermediate-input variants, 3 parameter arms.
`step2` = v6m.step (hard reset) + optional per-neuron leak removal; with default options identical to v6m.step (test_v6m2.py).
Run: .venv/bin/python -I -B flymind/v6m2.py --out flymind/results/v6m2 --protocol-sha256 <sha> [--smoke]
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
from alif import ALIF, ALIFParams  # noqa: E402

PROTOCOL = os.path.join(HERE, "program_v5v41", "V6m2_PROTOCOL.md")
T, W0, W1, SS = M.T, M.W0, M.W1, M.SS
ARMS = {
    "MAIN": dict(J0=0.2, b_a=0.5, levels=(7.0, 8.0, 9.0), b1=tuple(range(8_421_001, 8_421_011)),
                 noise=tuple(range(8_443_001, 8_443_009)), cal=tuple(range(8_443_101, 8_443_105))),
    "BA1": dict(J0=0.2, b_a=1.0, levels=(9.5, 10.5), b1=tuple(range(8_421_001, 8_421_006)),
                noise=tuple(range(8_443_201, 8_443_209)), cal=tuple(range(8_443_301, 8_443_305))),
    "J025": dict(J0=0.25, b_a=0.5, levels=(7.5, 8.0), b1=tuple(range(8_421_001, 8_421_006)),
                 noise=tuple(range(8_443_201, 8_443_209)), cal=tuple(range(8_443_301, 8_443_305))),
}
DYN = {"REF": dict(tref=2.2), "T0": dict(tref=0.0), "T0B": dict(tref=0.0, bias=True), "T1": dict(tref=1.0), "T6": dict(tref=6.0),
       "NOLEAK": dict(tref=2.2, noleak=True)}
INPUTS = ("M0", "MCIRC", "MASYNC")
BIAS_GRID = np.arange(-60.0, 0.0 + 1e-9, 2.0)


def step2(net, I, forced, cidx, tref, keepleak):
    """v6m.step (hard reset) with the membrane leak term multiplied by keepleak (per neuron, 1 = normal, 0 = no leak)."""
    p, dt = net.p, net.p.dt
    slot = net.t % p.delay_steps
    net.g += net.W @ net.buf[slot] - net.g * dt / p.tau_syn
    In = I + p.noise * net.rng.standard_normal(net.N) if p.noise else I
    net.v += dt / p.tau_m * ((p.v_rest - net.v) * keepleak + net.gain * (net.g + In) - net.a)
    net.v[net.ref > 0] = p.v_reset
    net.ref -= dt
    spk = net.v >= p.v_th
    spk[cidx] = forced
    net.v[spk] = p.v_reset
    net.ref[spk] = tref[spk]
    net.a += -net.a * dt / p.tau_a + net.b_a * spk
    net.buf[slot] = spk
    net.t += 1
    return spk


def nets(arm, family, k):
    a = ARMS[arm]
    data, idx, _, _ = V.make_net("DATA", None, a["J0"])
    src = data if family == "DATA" else V2.make_block_net("LCxLC", k, a["J0"])[0]
    return data, src, idx, ALIFParams(noise=2.0, b_a=a["b_a"])


def run(data, P, sd, I, cidx, forced, dn, dyn, bias=0.0):
    N = len(data.bodies)
    tref = np.full(N, P.t_ref)
    tref[dn] = DYN[dyn]["tref"]
    kl = np.ones(N)
    if DYN[dyn].get("noleak"):
        kl[dn] = 0.0
    if DYN[dyn].get("bias"):
        I = I.copy()
        I[:, dn] += bias
    net = ALIF(data, P, sd)
    out = np.zeros((T, N), bool)
    for t in range(T):
        out[t] = step2(net, I[t], forced[t], cidx, tref, kl)
    return out


def mid_variant(mtr, var, ss_seq):
    """mtr [T, n_mid] bool; returns manipulated copy (300–1000 ms only)."""
    if var == "M0":
        return mtr
    rng = np.random.default_rng(ss_seq)
    if var == "MCIRC":
        return R.manipulate(mtr, "CIRC", rng)[0]
    x = mtr.copy()
    L = W1 - W0
    seg = np.zeros((L, mtr.shape[1]), bool)
    for j, n in enumerate(mtr[W0:W1].sum(0)):                # exact sampler: uniform over spike sets with ISI >= 4
        n = int(n)
        if n:
            u = np.sort(rng.choice(L - 3 * (n - 1), n, replace=False))
            seg[u + 3 * np.arange(n), j] = True
    x[W0:W1] = seg
    return x


def calibrate(arm):
    """b* for T0B: DATA source, M0 input, calibration seeds (protocol §1)."""
    a = ARMS[arm]
    data, src, idx, P = nets(arm, "DATA", None)
    N = len(data.bodies)
    lc, mid = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    dn = np.r_[idx["DNa02_L"], idx["DNa02_R"]]
    lcmid = np.r_[lc, mid]
    ref, t0 = [], np.zeros(len(BIAS_GRID))
    n = 0
    for lv in a["levels"]:
        for side in "LR":
            I = R.current(idx, side, lv, N)
            d = idx[f"DNa02_{side}"][0]
            for sd in a["cal"]:
                lc_tr = ALIF(src, P, sd).run(I, T)[:, lc]
                r = run(data, P, sd, I, lc, lc_tr, dn, "REF")
                forced = np.concatenate([lc_tr, r[:, mid]], 1)
                ref.append(r[SS:W1, d].sum() / 0.5)
                for bi, b in enumerate(BIAS_GRID):
                    t0[bi] += run(data, P, sd, I, lcmid, forced, dn, "T0B", b)[SS:W1, d].sum() / 0.5
                n += 1
    t0 /= n
    b = float(BIAS_GRID[np.argmin(np.abs(t0 - np.mean(ref)))])
    return dict(arm=arm, bias=b, ref_dn=float(np.mean(ref)), t0_curve=dict(zip(BIAS_GRID.tolist(), t0.tolist())))


def job_run(job):
    t0_ = time.perf_counter()
    arm, a = job["arm"], ARMS[job["arm"]]
    data, src, idx, P = nets(arm, job["family"], job["k"])
    N = len(data.bodies)
    lc, mid = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    dn = np.r_[idx["DNa02_L"], idx["DNa02_R"]]
    lcmid = np.r_[lc, mid]
    seeds = a["noise"][:job["n_reps"]]
    src_id = 0 if job["family"] == "DATA" else int(job["k"]) - 8_421_000
    arm_id = list(ARMS).index(arm)
    out = np.zeros((len(DYN), len(INPUTS), len(a["levels"]), 2, len(seeds)))
    short = np.full(out.shape, np.nan)
    checks = dict(m0_ref_identity=[], counts_preserved=[], masync_isi=[])
    for li, lv in enumerate(a["levels"]):
        for si, side in enumerate("LR"):
            I = R.current(idx, side, lv, N)
            d = idx[f"DNa02_{side}"][0]
            for r, sd in enumerate(seeds):
                lc_tr = ALIF(src, P, sd).run(I, T)[:, lc]
                ref = run(data, P, sd, I, lc, lc_tr, dn, "REF")
                mtr0 = ref[:, mid]
                for ii, inp in enumerate(INPUTS):
                    mtr = mid_variant(mtr0, inp, np.random.SeedSequence([8_444_000, arm_id, ii, li, si, r, src_id]))
                    if inp != "M0":
                        checks["counts_preserved"].append(bool(np.array_equal(mtr[W0:W1].sum(0), mtr0[W0:W1].sum(0))))
                    if inp == "MASYNC":
                        checks["masync_isi"].append(bool(all((np.diff(np.flatnonzero(mtr[W0:W1, j])) >= 4).all() for j in range(mtr.shape[1]))))
                    forced = np.concatenate([lc_tr, mtr], 1)
                    for di, dyn in enumerate(DYN):
                        s = run(data, P, sd, I, lcmid, forced, dn, dyn, job["bias"])
                        if inp == "M0" and dyn == "REF":
                            checks["m0_ref_identity"].append(bool(np.array_equal(s, ref)))
                        x = np.flatnonzero(s[SS:W1, d])
                        out[di, ii, li, si, r] = len(x) / 0.5
                        if len(x) > 1:
                            short[di, ii, li, si, r] = float((np.diff(x) <= 4).mean())
    with open(os.path.join(job["out"], f"{job['name']}.npz"), "xb") as f:
        np.savez_compressed(f, dn=out, short_isi=short, dyn=np.array(list(DYN)), inputs=np.array(INPUTS), levels=np.array(a["levels"]),
                            seeds=np.array(seeds), bias=job["bias"])
    return dict(name=job["name"], wall_s=round(time.perf_counter() - t0_, 1),
                checks={k: (all(v), len(v)) for k, v in checks.items()})


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
    arms = ["MAIN"] if a.smoke else list(ARMS)
    calp = os.path.join(a.out, "bias_calibration.json")
    with mp.get_context("spawn").Pool(a.workers) as pool:
        if os.path.exists(calp):
            cal = json.load(open(calp))
        else:
            cal = {c["arm"]: c for c in pool.map(calibrate, arms)}
            with open(calp, "x") as f:
                json.dump(cal, f, indent=1)
        print("bias", {k: v["bias"] for k, v in cal.items()}, flush=True)
        jobs = []
        for arm in arms:
            srcs = [("DATA", None)] + [("B1", k) for k in ARMS[arm]["b1"]]
            if a.smoke:
                srcs = srcs[:2]
            for fam, k in srcs:
                jobs.append(dict(arm=arm, family=fam, k=k, bias=cal[arm]["bias"], out=raw, n_reps=1 if a.smoke else 8,
                                 name=f"{arm}_{fam}" + (f"_{k}" if k else "")))
        jobs = [j for j in jobs if not os.path.exists(os.path.join(raw, j["name"] + ".npz"))]
        with open(os.path.join(a.out, f"config_{time.strftime('%Y%m%dT%H%M%S')}.json"), "x") as f:
            json.dump(dict(protocol_sha256=a.protocol_sha256, smoke=a.smoke, arms=ARMS, dyn=DYN, inputs=INPUTS, jobs=[j["name"] for j in jobs],
                           code_sha256={f: IG.sha(os.path.join(HERE, f)) for f in ("v6m2.py", "v6m.py", "v5v43.py", "alif.py")},
                           started=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1)
        for r in pool.imap_unordered(job_run, jobs):
            print(json.dumps(r), flush=True)
    with open(os.path.join(a.out, f"run_done_{time.strftime('%Y%m%dT%H%M%S')}.json"), "x") as f:
        json.dump(dict(stage1_post=IG.stage1(), finished=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1)


if __name__ == "__main__":
    main()
