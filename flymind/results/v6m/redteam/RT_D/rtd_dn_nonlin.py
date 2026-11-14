"""RT-D (red team, V6m) — DN-only nonlinearity test with LC10a + intermediates clamped to the REF replay of each run.
Asks: does the M0-vs-MCIRC "timing route at DNa02" survive (B) DN t_ref 0, (C) t_ref 0 + subtractive reset + multi-spike per step
(removes the dt = 1 ms one-spike-per-step cap), (D) C + no leak (perfect integrator), (E) no leak alone? Also (bias) whether the
smaller RELATIVE gap at DN t_ref 0 survives when the DATA rate is matched to REF by a DN bias current.
Seeds (RT-D sub-range 8 498 301–399): noise 8 498 301–304; MCIRC offsets 8 498 351–354 (per rep, shared across sources).
Networks reused (not new seeds): DATA, B1 instances 8 421 001–003. Engine = v6m.step plus a leak mask and multi-spike option;
with default options it is checked bit-identical to v6m.replay REF/E1c (DN counts).
Run (from repo root): .venv/bin/python -I -B flymind/results/v6m/redteam/RT_D/rtd_dn_nonlin.py
"""
import multiprocessing as mp
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FM = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, FM)
import v5v41 as V  # noqa: E402
import v5v43 as R  # noqa: E402
import v6m as M  # noqa: E402
from alif import ALIF, ALIFParams  # noqa: E402

NOISE = tuple(range(8_498_301, 8_498_305))
CIRC_RNG = 8_498_351
SOURCES = ("DATA", 8_421_001, 8_421_002, 8_421_003)
# variant: (dn_tref, subtractive, multi-spike, no-leak, dn bias [mV])
VARS = {"A_REF": (2.2, False, False, False, 0.0), "B_t0": (0.0, False, False, False, 0.0),
        "C_t0_sub_multi": (0.0, True, True, False, 0.0), "D_t0_sub_multi_noleak": (0.0, True, True, True, 0.0),
        "E_noleak": (2.2, False, False, True, 0.0),
        "B_t0_bias-10": (0.0, False, False, False, -10.0), "B_t0_bias-20": (0.0, False, False, False, -20.0),
        "B_t0_bias-30": (0.0, False, False, False, -30.0), "A_REF_bias+10": (2.2, False, False, False, 10.0),
        "A_REF_bias-10": (2.2, False, False, False, -10.0)}
CLAMPS_FOR = {k: (("M0", "MCIRC") if "bias" not in k else ("M0",)) for k in VARS}


def step_x(net, I, forced, cidx, tref, sub, multi, keepleak):
    """v6m.step with leak factor (keepleak 1/0 per neuron) and multi-spike counting for `multi` (requires subtractive)."""
    p, dt = net.p, net.p.dt
    slot = net.t % p.delay_steps
    net.g += net.W @ net.buf[slot] - net.g * dt / p.tau_syn
    In = I + p.noise * net.rng.standard_normal(net.N) if p.noise else I
    leak = p.v_rest - net.v if keepleak is None else (p.v_rest - net.v) * keepleak
    net.v += dt / p.tau_m * (leak + net.gain * (net.g + In) - net.a)
    net.v[net.ref > 0] = p.v_reset
    net.ref -= dt
    spk = net.v >= p.v_th
    spk[cidx] = forced
    n = spk.astype(float)
    if multi is not None:
        m = spk & multi
        n[m] = np.floor((net.v[m] - p.v_th) / (p.v_th - p.v_reset)) + 1
    if sub is None:
        net.v[spk] = p.v_reset
    else:
        net.v[spk & ~sub] = p.v_reset
        net.v[spk & sub] -= (p.v_th - p.v_reset) * n[spk & sub]
    net.ref[spk] = tref[spk]
    net.a += -net.a * dt / p.tau_a + net.b_a * n
    net.buf[slot] = spk
    net.t += 1
    return spk, n


def job(src_key):
    data, idx, _, _ = V.make_net("DATA", None)
    src = data if src_key == "DATA" else R._b1(src_key)[0]
    P = ALIFParams(noise=2.0)
    N = len(data.bodies)
    lc = np.r_[idx["in_L"], idx["in_R"]]
    dn, mid = np.r_[idx["DNa02_L"], idx["DNa02_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    lcmid = np.r_[lc, mid]
    keys = [(v, c) for v in VARS for c in CLAMPS_FOR[v]]
    out = np.full((len(keys), len(M.LEVELS), 2, len(NOISE)), np.nan)
    val = []
    for li, lv in enumerate(M.LEVELS):
        for si, side in enumerate("LR"):
            I = R.current(idx, side, lv, N)
            dn_i = idx[f"DNa02_{side}"][0]
            for r, sd in enumerate(NOISE):
                train = ALIF(src, P, sd).run(I, M.T)[:, lc]
                ref = M.replay(data, P, sd, I, lc, train, M.CONDS_MAIN["REF"], idx, None, dn_i, idx[f"mid_{side}"])[0]
                mids = {"M0": ref[:, mid], "MCIRC": R.manipulate(ref[:, mid], "CIRC", np.random.default_rng(CIRC_RNG + r))[0]}
                for ki, (vn, cl) in enumerate(keys):
                    tr_, sub_, mul_, nol_, bias = VARS[vn]
                    tref = np.full(N, M.TREF0)
                    tref[dn] = tr_
                    sub = np.zeros(N, bool)
                    sub[dn] = sub_
                    multi = np.zeros(N, bool)
                    multi[dn] = mul_
                    kl = np.ones(N)
                    kl[dn] = 0.0 if nol_ else 1.0
                    Ib = I.copy()
                    Ib[:, dn] += bias
                    net = ALIF(data, P, sd)
                    forced = np.concatenate([train, mids[cl]], 1)
                    cnt = 0.0
                    for t in range(M.T):
                        s, n = step_x(net, Ib[t], forced[t], lcmid, tref, sub if sub_ else None, multi if mul_ else None,
                                      kl if nol_ else None)
                        if t >= M.SS:
                            cnt += n[dn_i]
                    out[ki, li, si, r] = cnt / 0.5
                    if vn == "A_REF" and cl == "M0":
                        val.append(cnt == ref[M.SS:, dn_i].sum())
    np.savez(os.path.join(HERE, "raw", f"{src_key}.npz"), out=out, keys=np.array([f"{v}|{c}" for v, c in keys]), noise=np.array(NOISE))
    return src_key, all(val), len(val)


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)
    with mp.get_context("spawn").Pool(4) as pool:
        for r in pool.imap_unordered(job, SOURCES):
            print("done", r, flush=True)
