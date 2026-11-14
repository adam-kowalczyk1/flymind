"""RT-H red-team Part A probes (V6m3). Seeds 8 499 001-099 only. Writes only into this directory.
B1 instances 8 499 001-003 (new LCxLC block shuffles); noise reps 8 499 011-018; calibration 8 499 021-024; LCIRC rng 8 499 031.
Run from repo root: .venv/bin/python -I -B flymind/results/v6m3/redteam/RT_H/rth_partA.py
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FM = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, FM)
import v5v42 as V2  # noqa: E402
import v5v43 as R  # noqa: E402
import v6m as M  # noqa: E402
import v6m3 as M3  # noqa: E402
from alif import ALIF  # noqa: E402

T, SS, W1 = M3.T, M3.SS, M3.W1
P = M3.P
B1_K = (8_499_001, 8_499_002, 8_499_003)
NOISE = tuple(range(8_499_011, 8_499_019))
CAL = tuple(range(8_499_021, 8_499_025))
LEVELS = (8.0, 9.0)
GM, BM = 0.725, -7.0                     # V6m3 calibration values
# cond: (tref_mid, gain_mid, bias_mid, b_a_mid, tau_syn_mid, syn_scale_mid, lcirc)
CONDS = {
    "REF": (P.t_ref, 1, 0, P.b_a, 5, 1, 0),
    "MT0": (0, 1, 0, P.b_a, 5, 1, 0),
    "MT1": (1, 1, 0, P.b_a, 5, 1, 0),           # 1 blocked step
    "MT2": (2, 1, 0, P.b_a, 5, 1, 0),           # 2 blocked steps (REF = 3)
    "MT4": (4, 1, 0, P.b_a, 5, 1, 0),           # 4 blocked steps
    "MT0G": (0, GM, 0, P.b_a, 5, 1, 0),
    "MT0B": (0, 1, BM, P.b_a, 5, 1, 0),
    "MT0S": (0, 1, 0, P.b_a, 5, "cal", 0),      # t_ref 0 + synaptic-only gain (noise unscaled), calibrated here
    "RG": (P.t_ref, GM, 0, P.b_a, 5, 1, 0),     # matching manipulation WITHOUT removing the block
    "RB": (P.t_ref, 1, BM, P.b_a, 5, 1, 0),
    "RBP": (P.t_ref, 1, 3.0, P.b_a, 5, 1, 0),   # block intact, rate raised
    "RNA": (P.t_ref, 1, 0, 0.0, 5, 1, 0),       # block intact, no adaptation at mids
    "RTS10": (P.t_ref, 1, 0, P.b_a, 10, 0.5, 0),  # block intact, slower mid synapses, charge-preserving
    "LCIRC": (P.t_ref, 1, 0, P.b_a, 5, 1, 1),
    "MT0_LCIRC": (0, 1, 0, P.b_a, 5, 1, 1),
    "MT0B_LCIRC": (0, 1, BM, P.b_a, 5, 1, 1),
}
_NET = {}


def nets(k):
    if "data" not in _NET:
        _NET["data"] = M3.setup()
    if k not in _NET:
        _NET[k] = _NET["data"][0] if k is None else V2.make_block_net("LCxLC", k)[0]
    return _NET["data"], _NET[k]


def run_rt(data, sd, I, cidx, forced, tref, gain, bias, b_a, tau_syn, syn_scale):
    """step2 (v6m2) generalised: per-neuron tau_syn and synaptic-increment scale. Defaults == M3.run3."""
    net = ALIF(data, P, sd, gain=gain, b_a=b_a)
    p, dt = net.p, net.p.dt
    I = I + bias[None, :]
    out = np.zeros((T, net.N), bool)
    for t in range(T):
        slot = net.t % p.delay_steps
        net.g += syn_scale * (net.W @ net.buf[slot]) - net.g * dt / tau_syn
        In = I[t] + p.noise * net.rng.standard_normal(net.N)
        net.v += dt / p.tau_m * ((p.v_rest - net.v) + net.gain * (net.g + In) - net.a)
        net.v[net.ref > 0] = p.v_reset
        net.ref -= dt
        spk = net.v >= p.v_th
        spk[cidx] = forced[t]
        net.v[spk] = p.v_reset
        net.ref[spk] = tref[spk]
        net.a += -net.a * dt / p.tau_a + net.b_a * spk
        net.buf[slot] = spk
        net.t += 1
        out[t] = spk
    return out


def vectors(c, N, mid, s_cal):
    tr, g, b, ba, ts, sc, circ = CONDS[c]
    v = dict(tref=np.full(N, P.t_ref), gain=np.ones(N), bias=np.zeros(N), b_a=np.full(N, P.b_a), tau_syn=np.full(N, 5.0), syn_scale=np.ones(N))
    v["tref"][mid], v["gain"][mid], v["bias"][mid], v["b_a"][mid], v["tau_syn"][mid] = tr, g, b, ba, ts
    v["syn_scale"][mid] = s_cal if sc == "cal" else sc
    return v, circ


def cal_task(a):
    lv, side, sd, svals = a
    (data, idx, N, lc, mid, dn), _ = nets(None)
    I = R.current(idx, side, lv, N)
    mi = idx[f"mid_{side}"]
    lc_tr = ALIF(data, P, sd).run(I, T)[:, lc]
    out = []
    for s in svals:
        v, _ = vectors("MT0S", N, mid, s)
        x = run_rt(data, sd, I, lc, lc_tr, **v)
        out.append(x[SS:W1][:, mi].sum() / (len(mi) * 0.5))
    v, _ = vectors("REF", N, mid, 1.0)
    ref = run_rt(data, sd, I, lc, lc_tr, **v)
    return ref[SS:W1][:, mi].sum() / (len(mi) * 0.5), out


def isi_stats(x):
    """x [T, n] mid trains; fraction of ISIs (500-1000 ms) <= 4 ms and <= 6 ms; burst fraction."""
    d = []
    for j in range(x.shape[1]):
        t = np.flatnonzero(x[SS:W1, j])
        if len(t) > 1:
            d.append(np.diff(t))
    d = np.concatenate(d) if d else np.zeros(0)
    return (float((d <= 4).mean()) if len(d) else np.nan, float((d <= 6).mean()) if len(d) else np.nan, int(len(d)))


def task(a):
    k, lv, side, r, sd, s_cal = a
    (data, idx, N, lc, mid, dn), src = nets(k)
    W = np.asarray(data.W, float)
    I = R.current(idx, side, lv, N)
    mi, d = idx[f"mid_{side}"], idx[f"DNa02_{side}"][0]
    w = W[d, mid]
    free = ALIF(src, P, sd).run(I, T)
    lc_tr = free[:, lc]
    li, si = LEVELS.index(lv), "LR".index(side)
    circ_tr = R.manipulate(lc_tr, "CIRC", np.random.default_rng(np.random.SeedSequence([8_499_031, li, si, r])))[0]
    res = {}
    for c in CONDS:
        v, circ = vectors(c, N, mid, s_cal)
        s = run_rt(data, sd, I, lc, circ_tr if circ else lc_tr, **v)
        n = s[SS:W1][:, mid].sum(0)
        res[c] = dict(dn=float(s[SS:W1, d].sum() / 0.5), mid_ipsi=int(s[SS:W1][:, mi].sum()), dexc=float((np.maximum(w, 0) * n).sum()),
                      dinh=float((np.minimum(w, 0) * n).sum()), n=n.tolist(),
                      pr=M.sync_metrics(s[:, mi])[M.SYNC_NAMES.index("paircorr5")], isi=isi_stats(s[:, mi]))
        if c == "REF":
            ref3 = M3.run3(data, sd, I, lc, lc_tr, np.full(N, P.t_ref), np.ones(N), None)
            res["_engine_identity"] = bool(np.array_equal(ref3, s))
    return dict(k=k, lv=lv, side=side, r=r, res=res)


def main():
    out = os.path.join(HERE, "rth_partA_raw.json")
    t0 = time.process_time(), time.perf_counter()
    with mp.get_context("spawn").Pool(8) as pool:
        svals = np.round(np.arange(0.55, 0.951, 0.025), 3).tolist()
        cr = pool.map(cal_task, [(lv, s, sd, svals) for lv in LEVELS for s in "LR" for sd in CAL])
        ref_mid = float(np.mean([c[0] for c in cr]))
        curve = np.mean([c[1] for c in cr], 0)
        s_cal = float(svals[int(np.argmin(np.abs(curve - ref_mid)))])
        print("cal MT0S: ref_mid", round(ref_mid, 2), "syn-only gain", s_cal, "curve", dict(zip(svals, np.round(curve, 2))), flush=True)
        tasks = [(k, lv, side, r, sd, s_cal) for k in (None,) + B1_K for lv in LEVELS for side in "LR" for r, sd in enumerate(NOISE)]
        rs = pool.map(task, tasks)
    with open(out, "x") as f:
        json.dump(dict(cal=dict(ref_mid=ref_mid, s_cal=s_cal, svals=svals, curve=curve.tolist()), runs=rs,
                       wall_s=time.perf_counter() - t0[1]), f)
    print("done", round(time.perf_counter() - t0[1], 1), "s wall")


if __name__ == "__main__":
    main()
