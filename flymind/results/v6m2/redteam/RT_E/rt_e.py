"""RT-E independent replication of V6m2 MAIN core cells. Own clamped replay + own DNa02-only replay (alif.py equations re-typed),
own MASYNC/MCIRC surrogates, own bias calibration. Seeds 8 498 501-599 only; B1 8 421 011-015.
Run from /Users/admin/so101_fly_project: .venv/bin/python -I -B flymind/results/v6m2/redteam/RT_E/rt_e.py"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

FLY = "/Users/admin/so101_fly_project/flymind"
sys.path.insert(0, FLY)
import v5v41 as V  # noqa: E402  (network construction only)
import v5v42 as V2  # noqa: E402
from alif import ALIF, ALIFParams  # noqa: E402  (free source run + self-check only)

OUT = os.path.join(FLY, "results/v6m2/redteam/RT_E")
P = ALIFParams(noise=2.0)            # MAIN arm: J0 0.2, b_a 0.5
T, W0, W1, SS = 1000, 300, 1000, 500
LEVELS = (7.0, 8.0, 9.0)
NOISE = tuple(range(8_498_501, 8_498_505))
CAL = tuple(range(8_498_511, 8_498_515))
MANIP = 8_498_530
B1 = tuple(range(8_421_011, 8_421_016))
INPUTS = ("M0", "MASYNC", "MCIRC", "MASYNC_W")      # MASYNC_W: exact counts kept separately in [300,500) and [500,1000)
DYNS = ("REF", "T0", "T0B")
TREF = dict(REF=2.2, T0=0.0, T0B=0.0)
GRID = np.arange(-60.0, 0.0 + 1e-9, 2.0)


def net(fam, k):
    data, idx, _, _ = V.make_net("DATA", None, 0.2)
    src = data if fam == "DATA" else V2.make_block_net("LCxLC", k, 0.2)[0]
    return data, src, idx


def cur(idx, side, lv, N):
    I = np.zeros((T, N))
    I[:, idx[f"in_{side}"]] = lv
    return I


def clamped(spec, sd, I, cidx, forced):
    """alif equations, spikes of cidx forced. Own code."""
    p = P
    W = np.asarray(spec.W, float)
    N = W.shape[0]
    rng = np.random.default_rng(sd)
    v, g, a, ref = np.full(N, p.v_rest), np.zeros(N), np.zeros(N), np.zeros(N)
    D = int(round(p.delay_ms / p.dt))
    buf = np.zeros((D, N), bool)
    out = np.zeros((T, N), bool)
    for t in range(T):
        s = t % D
        g += W @ buf[s] - g * p.dt / p.tau_syn
        In = I[t] + p.noise * rng.standard_normal(N)
        v += p.dt / p.tau_m * (p.v_rest - v + np.ones(N) * (g + In) - a)
        v[ref > 0] = p.v_reset
        ref -= p.dt
        k = v >= p.v_th
        if len(cidx):
            k[cidx] = forced[t]
        v[k] = p.v_reset
        ref[k] = p.t_ref
        a += -a * p.dt / p.tau_a + p.b_a * k
        buf[s] = k
        out[t] = k
    return out


def dn_only(Wdn, mids, Idn, Z, trefs, biases):
    """DNa02-only replay. Wdn [2, n_mid]; mids [C, T, n_mid] clamped intermediate trains; Idn [T, 2] external current;
    Z [T, 2] standard normals (the DN columns of the replay noise stream); trefs, biases [C]. Returns spikes [C, T, 2]."""
    p = P
    C = len(mids)
    drive = np.einsum("dm,ctm->ctd", Wdn, mids.astype(float))      # drive[c, t] = W @ mid(t); arrives at t + D
    D = int(round(p.delay_ms / p.dt))
    v, g, a, ref = np.full((C, 2), p.v_rest), np.zeros((C, 2)), np.zeros((C, 2)), np.zeros((C, 2))
    tr = np.repeat(np.asarray(trefs, float)[:, None], 2, 1)
    out = np.zeros((C, T, 2), bool)
    Ib = Idn[None] + np.asarray(biases, float)[:, None, None]
    for t in range(T):
        g += (drive[:, t - D] if t >= D else 0.0) - g * p.dt / p.tau_syn
        In = Ib[:, t] + p.noise * Z[t]
        v += p.dt / p.tau_m * (p.v_rest - v + (g + In) - a)
        v[ref > 0] = p.v_reset
        ref -= p.dt
        k = v >= p.v_th
        v[k] = p.v_reset
        ref[k] = tr[k]
        a += -a * p.dt / p.tau_a + p.b_a * k
        out[:, t] = k
    return out


def place(n, L, rng):
    """n spikes uniformly over all subsets of range(L) with ISI >= 4: random arrangement of n spike-blocks among free slots."""
    if n == 0:
        return np.zeros(L, bool)
    free = L - 4 * (n - 1) - 1
    assert free >= 0, (n, L)
    items = np.r_[np.ones(n, int), np.zeros(free, int)]
    rng.shuffle(items)
    x = []
    for it in items:
        if it:
            x += [1, 0, 0, 0]
        else:
            x.append(0)
    x = np.array(x[:L] if len(x) >= L else x + [0] * (L - len(x)), bool)
    assert x.sum() == n and len(x) == L
    return x


def variant(m, var, rng):
    x = m.copy()
    if var == "M0":
        return x
    if var == "MCIRC":
        for j in range(m.shape[1]):
            x[W0:W1, j] = np.roll(m[W0:W1, j], rng.integers(0, W1 - W0))
        return x
    segs = [(W0, W1)] if var == "MASYNC" else [(W0, SS), (SS, W1)]
    for j in range(m.shape[1]):
        for lo, hi in segs:
            x[lo:hi, j] = place(int(m[lo:hi, j].sum()), hi - lo, rng)
    return x


def calib():
    data, src, idx = net("DATA", None)
    N = len(data.bodies)
    lc, mid, dn = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]], np.r_[idx["DNa02_L"], idx["DNa02_R"]]
    Wdn = np.asarray(data.W, float)[np.ix_(dn, mid)]
    ref, curve = [], np.zeros(len(GRID))
    for lv in LEVELS:
        for si, side in enumerate("LR"):
            I = cur(idx, side, lv, N)
            for sd in CAL:
                lct = ALIF(src, P, sd).run(I, T)[:, lc]
                full = clamped(data, sd, I, lc, lct)
                Z = np.random.default_rng(sd).standard_normal((T, N))[:, dn]
                ref.append(full[SS:W1, dn[si]].sum() / 0.5)
                s = dn_only(Wdn, np.repeat(full[None, :, mid], len(GRID), 0), I[:, dn], Z, np.zeros(len(GRID)), GRID)
                curve += s[:, SS:W1, si].sum(1) / 0.5
    curve /= len(LEVELS) * 2 * len(CAL)
    b = float(GRID[np.argmin(np.abs(curve - np.mean(ref)))])
    return dict(bias=b, ref=float(np.mean(ref)), curve=dict(zip(GRID.tolist(), curve.round(2).tolist())))


def job(arg):
    fam, k, bias = arg
    data, src, idx = net(fam, k)
    N = len(data.bodies)
    lc, mid, dn = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]], np.r_[idx["DNa02_L"], idx["DNa02_R"]]
    Wdn = np.asarray(data.W, float)[np.ix_(dn, mid)]
    src_id = 0 if fam == "DATA" else k - 8_421_000
    rate = np.zeros((len(DYNS), len(INPUTS), len(LEVELS), 2, len(NOISE)))
    drv = np.zeros((len(INPUTS), len(LEVELS), 2, len(NOISE), 3))   # ipsi-DN drive in [SS-D, W1-D): exc, inh, n mid spikes
    chk = dict(identity=True, counts=True, isi=True)
    for li, lv in enumerate(LEVELS):
        for si, side in enumerate("LR"):
            I = cur(idx, side, lv, N)
            for r, sd in enumerate(NOISE):
                lct = ALIF(src, P, sd).run(I, T)[:, lc]
                full = clamped(data, sd, I, lc, lct)
                m0 = full[:, mid]
                rng = np.random.default_rng(np.random.SeedSequence([MANIP, src_id, li, si, r]))
                ms = [variant(m0, v, rng) for v in INPUTS]
                for v, m in zip(INPUTS, ms):
                    chk["counts"] &= bool(np.array_equal(m[W0:W1].sum(0), m0[W0:W1].sum(0)) and np.array_equal(m[:W0], m0[:W0]))
                    if v.startswith("MASYNC"):
                        chk["isi"] &= all((np.diff(np.flatnonzero(m[W0:W1, j])) >= 4).all() for j in range(m.shape[1])) if v == "MASYNC" else True
                Z = np.random.default_rng(sd).standard_normal((T, N))[:, dn]
                mids = np.stack([m for m in ms for _ in DYNS])
                trefs = [TREF[d] for _ in INPUTS for d in DYNS]
                biases = [bias if d == "T0B" else 0.0 for _ in INPUTS for d in DYNS]
                s = dn_only(Wdn, mids, I[:, dn], Z, trefs, biases)
                chk["identity"] &= bool(np.array_equal(s[0], full[:, dn]))       # M0 x REF == full clamped replay
                c = 0
                for ii in range(len(INPUTS)):
                    for di in range(len(DYNS)):
                        rate[di, ii, li, si, r] = s[c, SS:W1, si].sum() / 0.5
                        c += 1
                    w = Wdn[si]
                    seg = ms[ii][SS - 2:W1 - 2].sum(0)
                    drv[ii, li, si, r] = (seg @ np.clip(w, 0, None), seg @ np.clip(w, None, 0), seg[w != 0].sum())
    return dict(name=f"{fam}" + (f"_{k}" if k else ""), rate=rate.tolist(), drv=drv.tolist(), chk=chk)


def selfcheck():
    data, src, idx = net("B1", B1[0])
    N = len(data.bodies)
    I = cur(idx, "L", 8.0, N)
    a = ALIF(data, P, 8_498_590).run(I, T)
    b = clamped(data, 8_498_590, I, np.array([], int), None)
    assert np.array_equal(a, b), "own clamped step != alif.ALIF"
    rng = np.random.default_rng(8_498_591)
    # uniformity of place(): n=2, L=9 -> admissible pairs with gap>=4: C(9-3,2)=15 configurations, each p=1/15
    cnt = {}
    for _ in range(30000):
        key = tuple(np.flatnonzero(place(2, 9, rng)))
        cnt[key] = cnt.get(key, 0) + 1
    assert len(cnt) == 15 and min(cnt.values()) > 1700 and max(cnt.values()) < 2300, cnt
    return "selfcheck OK (own clamped == alif.ALIF; place() uniform over 15 configs)"


if __name__ == "__main__":
    t0 = time.time()
    print(selfcheck(), flush=True)
    cal = calib()
    print("calibration", cal["bias"], cal["ref"], flush=True)
    jobs = [("DATA", None, cal["bias"])] + [("B1", k, cal["bias"]) for k in B1]
    with mp.get_context("spawn").Pool(6) as pool:
        res = pool.map(job, jobs)
    with open(os.path.join(OUT, "rt_e_raw.json"), "w") as f:
        json.dump(dict(cal=cal, inputs=INPUTS, dyns=DYNS, levels=LEVELS, noise=NOISE, b1=B1, res=res, wall_s=time.time() - t0), f)
    print("done", round(time.time() - t0, 1), [r["chk"] for r in res])
