"""RT-F (red team, V6m2) — alternative explanations for 'a refractory block of >= 1 step in DNa02 makes synchronous input harmful'.
MAIN arm only (J0 0.2, b_a 0.5), DATA + B1 8 421 001-003 (reused networks), levels 7/8/9 mV, L/R, 4 noise reps 8 498 601-604.
Stage 1 (full network, v6m2.run): source free run -> LC10a trains; REF replay -> intermediate trains (as V6m2).
Stage 2 (DNa02-only, vectorised): every non-DN neuron is clamped, there are no DN->DN synapses (checked), so the ipsi DNa02 is driven by
X[t] = W[d, nonDN] @ S[t-2] + I + noise; it is re-simulated under many DN variants. Identity check: REF x M0 == REF replay raster;
T0B(-38) x M0 == v6m2.run raster (spot check).
Inputs: M0, MASYNC (v6m2.mid_variant, own seeds), MTHIN (DATA and B1 intermediate trains each thinned at random, per neuron, to the
per-neuron minimum of the paired DATA/B1 counts in 300-1000 ms: identical counts, each keeps its own timing).
Seeds: noise 8 498 601-604; MASYNC SeedSequence([8 498 650, li, si, r, src]); MTHIN SeedSequence([8 498 660, li, si, r, k]).
Run (repo root): .venv/bin/python -I -B flymind/results/v6m2/redteam/RT_F/rtf_alt.py
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
import v5v43 as R  # noqa: E402
import v6m2 as M2  # noqa: E402
from alif import ALIF  # noqa: E402

T, W0, W1, SS = M2.T, M2.W0, M2.W1, M2.SS
NOISE = tuple(range(8_498_601, 8_498_605))
SOURCES = ("DATA", 8_421_001, 8_421_002, 8_421_003)
LEVELS = (7.0, 8.0, 9.0)
D0 = dict(tref=2.2, clamp=True, sub=False, multi=False, kl=1.0, bias=0.0, gain=1.0, tau=5.0)
COND = {
    "REF": {}, "T0": dict(tref=0.0), "T1": dict(tref=1.0),
    # (a) reset / charge discarding vs spike block
    "T0_SUB": dict(tref=0.0, sub=True), "T0_SUBM": dict(tref=0.0, sub=True, multi=True),
    "BLK3_INT": dict(clamp=False), "BLK3_INT_SUB": dict(clamp=False, sub=True), "T1_INT": dict(tref=1.0, clamp=False),
    # (c) operating point: additive bias vs multiplicative gain
    **{f"T0_b{b:g}": dict(tref=0.0, bias=b) for b in (-10.0, -20.0, -30.0, -38.0, -50.0)},
    **{f"REF_b{b:+g}": dict(bias=b) for b in (-10.0, 10.0, 20.0)},
    **{f"T0_g{g:.2f}": dict(tref=0.0, gain=g) for g in np.round(np.arange(0.60, 1.001, 0.025), 3)},
    **{f"REF_g{g:.2f}": dict(gain=g) for g in (0.9, 1.1, 1.2, 1.3)},
    # (e) DNa02 synaptic time constant (PSC charge normalised to tau 5: jump x 5/tau)
    **{f"{n}_tau{t:g}": dict(tref=tr, tau=t) for n, tr in (("REF", 2.2), ("T0", 0.0)) for t in (2.0, 10.0)},
}
INPUTS = ("M0", "MASYNC", "MTHIN")


def gen(src_key):
    data, src, idx, P = M2.nets("MAIN", "DATA" if src_key == "DATA" else "B1", None if src_key == "DATA" else src_key)
    N = len(data.bodies)
    lc, mid = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    dn = np.r_[idx["DNa02_L"], idx["DNa02_R"]]
    W = np.asarray(data.W, float)
    assert not W[np.ix_(dn, dn)].any()
    out = dict(lc=[], mid=[], dnref=[], xi=[], I=[], key=[])
    for li, lv in enumerate(LEVELS):
        for si, side in enumerate("LR"):
            I = R.current(idx, side, lv, N)
            d = idx[f"DNa02_{side}"][0]
            for r, sd in enumerate(NOISE):
                lc_tr = ALIF(src, P, sd).run(I, T)[:, lc]
                ref = M2.run(data, P, sd, I, lc, lc_tr, dn, "REF")
                xi = np.random.default_rng(sd).standard_normal((T, N))[:, d]
                out["lc"].append(lc_tr)
                out["mid"].append(ref[:, mid])
                out["dnref"].append(ref[:, d])
                out["xi"].append(xi)
                out["I"].append(I[:, d])
                out["key"].append((li, si, r))
    return src_key, {k: np.array(v) for k, v in out.items()}


def drive(W_d, lc_idx, mid_idx, lc_tr, mid_tr):
    """X[t] = synaptic input arriving at step t (spikes of step t-2; delay_steps 2)."""
    s = np.zeros((T, W_d.shape[0]))
    s[:, lc_idx] = lc_tr
    s[:, mid_idx] = mid_tr
    x = s @ W_d
    out = np.zeros(T)
    out[2:] = x[:-2]
    return out


def sim(X, I, xi, conds, P):
    """X [B, T] synaptic drive, I/xi [T]; conds list of dicts (len B). Returns spike counts n [B, T] (multi-spike counts)."""
    B = X.shape[0]
    c = {k: np.array([cc[k] for cc in conds], float) for k in D0}
    clamp, sub, multi = c["clamp"] > 0, c["sub"] > 0, c["multi"] > 0
    v = np.full(B, P.v_rest)
    g = np.zeros(B)
    a = np.zeros(B)
    ref = np.zeros(B)
    n_out = np.zeros((B, T))
    dec = P.dt / c["tau"]
    scale = 5.0 / c["tau"]
    for t in range(T):
        g += scale * X[:, t] - g * dec
        In = I[t] + c["bias"] + P.noise * xi[t]
        v += P.dt / P.tau_m * ((P.v_rest - v) * c["kl"] + c["gain"] * (g + In) - a)
        blocked = ref > 0
        v[blocked & clamp] = P.v_reset
        ref -= P.dt
        spk = (v >= P.v_th) & ~blocked
        n = spk.astype(float)
        m = spk & multi
        n[m] = np.floor((v[m] - P.v_th) / (P.v_th - P.v_reset)) + 1
        h = spk & ~sub
        v[h] = P.v_reset
        s = spk & sub
        v[s] -= (P.v_th - P.v_reset) * n[s]
        ref[spk] = c["tref"][spk]
        a += -a * P.dt / P.tau_a + P.b_a * n
        n_out[:, t] = n
    return n_out


def thin(tr, target, rng):
    x = tr.copy()
    seg = x[W0:W1]
    for j in range(seg.shape[1]):
        t = np.flatnonzero(seg[:, j])
        if len(t) > target[j]:
            seg[rng.choice(t, len(t) - target[j], replace=False), j] = False
    x[W0:W1] = seg
    return x


def cell_job(args):
    k, li, si, r, G_src, G_data = args
    data, _, idx, P = M2.nets("MAIN", "DATA", None)
    side = "LR"[si]
    d = idx[f"DNa02_{side}"][0]
    lc, mid = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    W_d = np.asarray(data.W, float)[d]
    src_id = 0 if k == "DATA" else k - 8_421_000
    lc_tr, mid0, dnref, xi, I = G_src
    inp = {"M0": mid0,
           "MASYNC": M2.mid_variant(mid0, "MASYNC", np.random.SeedSequence([8_498_650, li, si, r, src_id]))}
    if k != "DATA":                                             # MTHIN pair (B1 k, DATA) at matched per-neuron counts
        md = G_data[1]
        tgt = np.minimum(mid0[W0:W1].sum(0), md[W0:W1].sum(0))
        rng = np.random.default_rng(np.random.SeedSequence([8_498_660, li, si, r, src_id]))
        inp["MTHIN"] = thin(mid0, tgt, rng)
        inp["MTHIN_DATA"] = thin(md, tgt, rng)
        assert np.array_equal(inp["MTHIN"][W0:W1].sum(0), inp["MTHIN_DATA"][W0:W1].sum(0))
    names = list(COND)
    conds = [D0 | COND[n] for n in names]
    res = {}
    for nm, mtr in inp.items():
        lct = lc_tr if nm != "MTHIN_DATA" else G_data[0]
        X = drive(W_d, lc, mid, lct, mtr)
        Ii, xii = (I, xi) if nm != "MTHIN_DATA" else (G_data[4], G_data[3])
        n = sim(np.tile(X, (len(conds), 1)), Ii, xii, conds, P)
        res[nm] = n[:, SS:W1].sum(1) / 0.5
        if nm == "M0":
            assert np.array_equal(n[names.index("REF")] > 0, dnref), "identity REF x M0 failed"
            isi = {}
            for cn in ("REF", "T0", "T1", "T0_b-38", "T0_SUB", "BLK3_INT"):
                x = np.flatnonzero(n[names.index(cn), SS:W1])
                h = np.bincount(np.diff(x), minlength=12)[:12] if len(x) > 1 else np.zeros(12)
                isi[cn] = h.tolist()
            res["isi"] = isi
    cnt = dict(src=mid0[W0:W1].sum(0).tolist())
    return (str(k), li, si, r), res, cnt


def main():
    t0 = time.perf_counter()
    with mp.get_context("spawn").Pool(4) as pool:
        G = dict(pool.map(gen, SOURCES))
    print("stage1", round(time.perf_counter() - t0, 1), "s", flush=True)
    # spot check: T0B(-38) DN-only == v6m2.run, one cell
    data, _, idx, P = M2.nets("MAIN", "DATA", None)
    N = len(data.bodies)
    lc, mid = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    dn = np.r_[idx["DNa02_L"], idx["DNa02_R"]]
    g = G[8_421_002]
    i = 3
    li, si, r = g["key"][i]
    forced = np.concatenate([g["lc"][i], g["mid"][i]], 1)
    full = M2.run(data, P, NOISE[r], R.current(idx, "LR"[si], LEVELS[li], N), np.r_[lc, mid], forced, dn, "T0B", -38.0)
    d = idx[f"DNa02_{'LR'[si]}"][0]
    X = drive(np.asarray(data.W, float)[d], lc, mid, g["lc"][i], g["mid"][i])
    mine = sim(X[None], g["I"][i], g["xi"][i], [D0 | dict(tref=0.0, bias=-38.0)], P)[0] > 0
    assert np.array_equal(mine, full[:, d]), "spot check T0B failed"
    print("identity checks OK", flush=True)
    jobs = []
    for k in SOURCES:
        for i, (li, si, r) in enumerate(G[k]["key"]):
            gs = tuple(G[k][f][i] for f in ("lc", "mid", "dnref", "xi", "I"))
            gd = tuple(G["DATA"][f][i] for f in ("lc", "mid", "dnref", "xi", "I"))
            jobs.append((k, li, si, r, gs, gd))
    with mp.get_context("spawn").Pool(8) as pool:
        out = pool.map(cell_job, jobs)
    names = list(COND)
    arr = {}                                                   # [src, cond, input, li, si, r]
    ns = len(SOURCES)
    A = np.full((ns, len(names), 4, 3, 2, len(NOISE)), np.nan)
    inames = ("M0", "MASYNC", "MTHIN", "MTHIN_DATA")
    isi = {}
    cnts = {}
    for (k, li, si, r), res, cnt in out:
        s = [str(x) for x in SOURCES].index(k)
        for ii, nm in enumerate(inames):
            if nm in res:
                A[s, :, ii, li, si, r] = res[nm]
        for cn, h in res["isi"].items():
            isi.setdefault(k, {}).setdefault(cn, np.zeros(12))
            isi[k][cn] += np.array(h)
        cnts[f"{k}|{li}|{si}|{r}"] = cnt["src"]
    np.savez_compressed(os.path.join(HERE, "rtf_raw.npz"), A=A, conds=np.array(names), inputs=np.array(inames),
                        sources=np.array([str(x) for x in SOURCES]))
    with open(os.path.join(HERE, "rtf_aux.json"), "w") as f:
        json.dump(dict(isi={k: {c: v.tolist() for c, v in d.items()} for k, d in isi.items()}, counts=cnts), f)
    print("done", round(time.perf_counter() - t0, 1), "s", flush=True)


if __name__ == "__main__":
    main()
