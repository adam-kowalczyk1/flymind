"""flymind/v5v43.py — V5 v4.3 LC10a spike-train replay (EXPLORATORY). Protocol: program_v5v41/V5v43_PROTOCOL.md.
LC10a neurons of the DATA network are clamped to recorded (manipulated) trains; intermediates and DNa02 follow the alif.py equations
(re-implemented in `step_clamped` line by line; `test_v5v43.py` checks exact identity with free alif.ALIF runs). No mujoco/bio2.
Run: .venv/bin/python -I -B flymind/v5v43.py --out flymind/results/v5v43 --protocol-sha256 <sha>
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
from alif import ALIF, ALIFParams  # noqa: E402

PROTOCOL = os.path.join(HERE, "program_v5v41", "V5v43_PROTOCOL.md")
B1_SEEDS = tuple(range(8_421_001, 8_421_011))
LEVELS = (7.0, 8.0, 9.0)
VARIANTS = ("V0", "J1", "J2", "J5", "J10", "J20", "CIRC", "POIS")
W0, W1, SS = 300, 1000, 500          # manipulation window [W0, W1) ms, steady window [SS, W1)
T = 1000


def step_clamped(net, I, forced, cidx):
    """alif.ALIF.step with spikes of neurons cidx forced to `forced` (bool)."""
    p, dt = net.p, net.p.dt
    slot = net.t % p.delay_steps
    net.g += net.W @ net.buf[slot] - net.g * dt / p.tau_syn
    In = I + p.noise * net.rng.standard_normal(net.N) if p.noise else I
    net.v += dt / p.tau_m * (p.v_rest - net.v + net.gain * (net.g + In) - net.a)
    net.v[net.ref > 0] = p.v_reset
    net.ref -= dt
    spk = net.v >= p.v_th
    spk[cidx] = forced
    net.v[spk] = p.v_reset
    net.ref[spk] = p.t_ref
    net.a += -net.a * dt / p.tau_a + net.b_a * spk
    net.buf[slot] = spk
    net.t += 1
    return spk


def current(idx, side, level, N):
    I = np.zeros((T, N))
    I[:, idx[f"in_{side}"]] = level
    return I


def manipulate(train, variant, rng):
    """train [T, nLC] bool; manipulation only inside [W0, W1). Returns (new train, spikes lost to collisions)."""
    x = train.copy()
    seg = train[W0:W1]
    L = W1 - W0
    if variant == "V0":
        return x, 0
    if variant.startswith("J"):
        J = int(variant[1:])
        t, n = np.nonzero(seg)
        t2 = t + rng.integers(-J, J + 1, size=len(t))
        t2 = np.where(t2 < 0, -t2, t2)
        t2 = np.where(t2 >= L, 2 * (L - 1) - t2, t2)
        new = np.zeros_like(seg)
        new[t2, n] = True
        x[W0:W1] = new
        return x, int(len(t) - new.sum())
    if variant == "CIRC":
        off = rng.integers(0, L, size=seg.shape[1])
        x[W0:W1] = np.stack([np.roll(seg[:, j], off[j]) for j in range(seg.shape[1])], 1)
        return x, 0
    if variant == "POIS":
        r = seg.mean(0)
        x[W0:W1] = rng.random(seg.shape) < r[None, :]
        return x, int(seg.sum() - x[W0:W1].sum())
    raise ValueError(variant)


def fano_pop(train_ipsi):
    c = train_ipsi[SS:W1].reshape(-1, 10, train_ipsi.shape[1]).sum((1, 2)).astype(float)
    return float(c.var() / c.mean()) if c.mean() > 0 else float("nan")


def source_job(job):
    """Free run of the source network, then replays of its LC10a trains into the DATA network."""
    t0 = time.perf_counter()
    spec_src, idx, _, _ = V.make_net("DATA", None) if job["family"] == "DATA" else _b1(job["k"])
    data, _, _, _ = V.make_net("DATA", None)
    P = ALIFParams(noise=2.0)
    lc = np.r_[idx["in_L"], idx["in_R"]]
    N = len(data.bodies)
    out = np.zeros((len(LEVELS), 2, len(V.NOISE_SEEDS), len(VARIANTS), 5))   # dn_ipsi, mid_ipsi, lc_fano, lost, lc_ipsi_spikes
    free = np.zeros((len(LEVELS), 2, len(V.NOISE_SEEDS), 2))
    for li, lv in enumerate(LEVELS):
        for si, side in enumerate("LR"):
            I = current(idx, side, lv, N)
            dn, mid, ipsi = idx[f"DNa02_{side}"], idx[f"mid_{side}"], idx[f"in_{side}"]
            pos_ipsi = np.searchsorted(lc, ipsi)
            for r, sd in enumerate(V.NOISE_SEEDS):
                s = ALIF(spec_src, P, sd).run(I, T)
                free[li, si, r] = (s[SS:W1, dn].sum(), s[SS:W1][:, mid].sum())
                train = s[:, lc]
                for vi, var in enumerate(VARIANTS):
                    rng = np.random.default_rng(8_430_000 + 100 * vi + r)
                    tr, lost = manipulate(train, var, rng)
                    net = ALIF(data, P, sd)
                    spk = np.zeros((T, N), bool)
                    for t in range(T):
                        spk[t] = step_clamped(net, I[t], tr[t], lc)
                    out[li, si, r, vi] = (spk[SS:W1, dn].sum(), spk[SS:W1][:, mid].sum(), fano_pop(tr[:, pos_ipsi]), lost,
                                          tr[SS:W1, pos_ipsi].sum())
    path = os.path.join(job["out"], f"{job['name']}.npz")
    with open(path, "xb") as f:
        np.savez_compressed(f, replay=out, free=free, levels=np.array(LEVELS), variants=np.array(VARIANTS),
                            n_mid=np.array([len(idx["mid_L"]), len(idx["mid_R"])]))
    return dict(name=job["name"], wall_s=round(time.perf_counter() - t0, 1))


def _b1(k):
    import v5v42 as V2
    spec, idx, gr, _ = V2.make_block_net("LCxLC", k)
    return spec, idx, gr, None


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    ap.add_argument("--protocol-sha256", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    import integrity_v5v41 as IG
    if IG.stage1()["ok"] != 28:
        sys.exit("STOP: Stage 1")
    if hashlib.sha256(open(PROTOCOL, "rb").read()).hexdigest() != a.protocol_sha256:
        sys.exit("refused: protocol sha256 mismatch")
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    jobs = [dict(family="DATA", k=None, name="DATA", out=raw)] + [dict(family="B1", k=k, name=f"B1_{k}", out=raw) for k in B1_SEEDS]
    with open(os.path.join(a.out, "config.json"), "x") as f:
        json.dump(dict(protocol_sha256=a.protocol_sha256, levels=LEVELS, variants=VARIANTS, b1_seeds=B1_SEEDS, noise_seeds=V.NOISE_SEEDS,
                       window=[W0, W1], steady=[SS, W1], started=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1)
    with mp.get_context("spawn").Pool(a.workers) as pool:
        for r in pool.imap_unordered(source_job, jobs):
            print(r, flush=True)
    with open(os.path.join(a.out, "run_done.json"), "x") as f:
        json.dump(dict(stage1_post=IG.stage1(), finished=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1)


if __name__ == "__main__":
    main()
