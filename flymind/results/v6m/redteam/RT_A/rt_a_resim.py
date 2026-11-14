"""RT-A independent re-simulation (red team of V6m). Own engine written from alif.py equations (NOT v6m.step); compared with
v6m.replay on the SAME seeds. Seeds used (RT-A sub-range 8 498 001-099 only):
  noise reps 8 498 001, 8 498 002; B1 instance (LCxLC block shuffle) 8 498 010; MCIRC rng 8 498 020+r; LCIRC rng 8 498 030+r;
  synth rng 8 498 040+..; MJ2 rng 8 498 060+r.
Run: .venv/bin/python -I -B flymind/results/v6m/redteam/RT_A/rt_a_resim.py   (from /Users/admin/so101_fly_project)"""
import json
import os
import sys
import time

import numpy as np

FM = "/Users/admin/so101_fly_project/flymind"
sys.path.insert(0, FM)
import v5v41 as V  # noqa: E402
import v5v43 as R  # noqa: E402
import v6m as M  # noqa: E402  (only replay/manipulate/synth for comparison; own engine below)
from alif import ALIF, ALIFParams  # noqa: E402

OUT = os.path.join(FM, "results/v6m/redteam/RT_A")
SEEDS = (8_498_001, 8_498_002)
B1K = 8_498_010
P = ALIFParams(noise=2.0)
T, W0, W1, SS = 1000, 300, 1000, 500


def own(W, I, sd, cidx=None, forced=None, tref=None, ba=None, sub=None):
    """Own ALIF loop (alif.py equations): integer refractory counter, ring buffer list, explicit clamp. Returns spikes, DN-free."""
    N = W.shape[0]
    rng = np.random.default_rng(sd)
    D = int(round(P.delay_ms / P.dt))
    tref = np.full(N, P.t_ref) if tref is None else tref
    nblk = np.ceil(tref / P.dt - 1e-12).astype(int)          # alif: ref>0 test then ref-=dt -> ceil(t_ref/dt) blocked steps
    ba = np.full(N, P.b_a) if ba is None else ba
    v, g, a = np.full(N, P.v_rest), np.zeros(N), np.zeros(N)
    cnt = np.zeros(N, int)
    ring = [np.zeros(N, bool) for _ in range(D)]
    out = np.zeros((T, N), bool)
    for t in range(T):
        k = t % D
        g = g + (W @ ring[k] - g * P.dt / P.tau_syn)
        x = I[t] + P.noise * rng.standard_normal(N)
        v = v + P.dt / P.tau_m * (P.v_rest - v + (g + x) - a)
        blk = cnt > 0
        v[blk] = P.v_reset
        cnt[blk] -= 1
        s = v >= P.v_th
        if cidx is not None:
            s[cidx] = forced[t]
        if sub is None:
            v[s] = P.v_reset
        else:
            v[s & ~sub] = P.v_reset
            v[s & sub] = v[s & sub] - (P.v_th - P.v_reset)
        cnt[s] = nblk[s]
        a = a + (-a * P.dt / P.tau_a + ba * s)
        ring[k] = s
        out[t] = s
    return out


def own_circ(x, seed):
    """Own per-neuron circular shift inside [W0, W1); same rng draw as v5v43.manipulate CIRC."""
    y = x.copy()
    off = np.random.default_rng(seed).integers(0, W1 - W0, size=x.shape[1])
    for j in range(x.shape[1]):
        seg = x[W0:W1, j]
        y[W0:W1, j] = np.r_[seg[len(seg) - off[j]:], seg[:len(seg) - off[j]]]
    return y


def main():
    t0 = time.perf_counter()
    data, idx, _, _ = V.make_net("DATA", None)
    b1 = R._b1(B1K)[0]
    W = np.asarray(data.W, float)
    N = W.shape[0]
    lc = np.r_[idx["in_L"], idx["in_R"]]
    dn, mid = np.r_[idx["DNa02_L"], idx["DNa02_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    lcmid = np.r_[lc, mid]
    Wn = W.copy()
    blk = Wn[np.ix_(dn, mid)]
    blk[blk < 0] = 0
    Wn[np.ix_(dn, mid)] = blk
    res = dict(seeds=dict(noise=SEEDS, b1=B1K, mcirc=[8_498_020 + r for r in range(2)], lcirc=[8_498_030 + r for r in range(2)]),
               rows=[], free_eq_alif=[], latency=[])
    conds = ("REF", "E1c_DN_t0", "E3_MCIRC", "E2a_DN_b00", "E1_DN_t0", "E5a_DN_t0_sub", "E5b_noinh", "E1b_MID_t0", "LCIRC", "E3_M0")
    for src_name, src in (("DATA", data), (f"B1_{B1K}", b1)):
        Wsrc = np.asarray(src.W, float)
        for li, lv in enumerate(R.LEVELS):
            for side in "LR":
                I = R.current(idx, side, lv, N)
                dn_i, mid_i = idx[f"DNa02_{side}"][0], idx[f"mid_{side}"]
                for r, sd in enumerate(SEEDS):
                    s_alif = ALIF(src, P, sd).run(I, T)
                    s_own = own(Wsrc, I, sd)
                    res["free_eq_alif"].append(bool(np.array_equal(s_alif, s_own)))
                    train = s_alif[:, lc]
                    o, m = {}, {}
                    for cn in conds:
                        cd = M.CONDS_MAIN[cn]
                        tref, ba, sub = M.vectors(cd, N, dn, mid)
                        # own path
                        tr_o = own_circ(train, 8_498_030 + r) if cd["lc"] else train
                        tr_m = R.manipulate(train, "CIRC", np.random.default_rng(8_498_030 + r))[0] if cd["lc"] else train
                        if cd["clamp_mid"]:
                            mo, mm = o["REF"][:, mid], m["REF"][:, mid]
                            if cd["clamp_mid"] == "MCIRC":
                                mo = own_circ(mo, 8_498_020 + r)
                                mm = R.manipulate(mm, "CIRC", np.random.default_rng(8_498_020 + r))[0]
                            o[cn] = own(Wn if cd["noinh"] else W, I, sd, lcmid, np.concatenate([tr_o, mo], 1), tref, ba, sub)
                            m[cn] = M.replay(data, P, sd, I, lcmid, np.concatenate([tr_m, mm], 1), cd, idx, Wn, dn_i, mid_i)[0]
                        else:
                            o[cn] = own(Wn if cd["noinh"] else W, I, sd, lc, tr_o, tref, ba, sub)
                            m[cn] = M.replay(data, P, sd, I, lc, tr_m, cd, idx, Wn, dn_i, mid_i)[0]
                        d_o, d_m = int(o[cn][SS:W1, dn_i].sum()), int(m[cn][SS:W1, dn_i].sum())
                        first_div = np.flatnonzero((o[cn] != m[cn]).any(1))
                        pre_ok = None
                        if cn != "REF":    # rasters identical to REF before the intended manipulation reaches DN?
                            dif = np.flatnonzero((m[cn][:, dn_i] != m["REF"][:, dn_i]))
                            pre_ok = int(dif[0]) if len(dif) else None
                        res["rows"].append(dict(src=src_name, level=lv, side=side, seed=sd, cond=cn, dn_own=d_o, dn_v6m=d_m,
                                                raster_equal=bool(len(first_div) == 0), first_dn_diff_vs_REF=pre_ok,
                                                mid_ss_ipsi=int(m[cn][SS:W1][:, mid_i].sum())))
                    # latency + LC divergence between sources (same noise seed)
                    ts = np.flatnonzero(m["REF"][:, dn_i])
                    res["latency"].append(dict(src=src_name, level=lv, side=side, seed=sd, lat0=int(ts[0]) if len(ts) else None,
                                               lc_first_spike=int(np.flatnonzero(train.any(1))[0]),
                                               mid_first_spike=int(np.flatnonzero(m["REF"][:, mid].any(1))[0])))
                    if src_name == "DATA":
                        res.setdefault("_data_lc", {})[f"{lv}{side}{sd}"] = train
                    else:
                        tD = res["_data_lc"][f"{lv}{side}{sd}"]
                        dv = np.flatnonzero((tD != train).any(1))
                        res["latency"][-1]["lc_first_divergence_DATA_vs_B1"] = int(dv[0]) if len(dv) else None
    res.pop("_data_lc")
    res["wall_s"] = round(time.perf_counter() - t0, 1)
    with open(os.path.join(OUT, "rt_a_resim.json"), "x") as f:
        json.dump(res, f, indent=1, default=int)
    ok = all(x["dn_own"] == x["dn_v6m"] and x["raster_equal"] for x in res["rows"])
    print("free own==alif:", all(res["free_eq_alif"]), len(res["free_eq_alif"]), "| replay own==v6m (counts+rasters):", ok, len(res["rows"]))
    for x in res["rows"]:
        if not (x["dn_own"] == x["dn_v6m"] and x["raster_equal"]):
            print("MISMATCH", x)
    print("wall", res["wall_s"])


if __name__ == "__main__":
    main()
