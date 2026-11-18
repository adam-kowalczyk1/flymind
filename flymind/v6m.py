"""flymind/v6m.py — V6m mechanistic dissection (EXPLORATORY computational ablations). Protocol: program_v5v41/V6m_PROTOCOL.md.
Extends the V5 v4.3 clamped replay (`v5v43.step_clamped`): per-neuron t_ref, per-neuron b_a (native alif.ALIF), optional
subtractive reset, clamping of LC10a and/or intermediates, optional removal of intermediate→DNa02 inhibition. With default
vectors `step` is identical to `v5v43.step_clamped` / `alif.ALIF.step` (test_v6m.py T1). No mujoco, no bio2. Writes only --out.
Run: .venv/bin/python -I -B flymind/v6m.py --out flymind/results/v6m --protocol-sha256 <sha> [--smoke]
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
import v5v43 as R  # noqa: E402
from alif import ALIF, ALIFParams  # noqa: E402

PROTOCOL = os.path.join(HERE, "program_v5v41", "V6m_PROTOCOL.md")
T, W0, W1, SS = R.T, R.W0, R.W1, R.SS
LEVELS = R.LEVELS
B1_MAIN, B1_REP = R.B1_SEEDS, tuple(range(8_421_011, 8_421_021))
NOISE_MAIN, NOISE_REP = V.NOISE_SEEDS, tuple(range(8_442_001, 8_442_009))
TREF0, BA0 = 2.2, 0.5
P_SYNC = tuple((10.0, p) for p in (0.0, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9, 1.0)) + tuple((40.0, p) for p in (0.35, 0.7, 1.0))   # (event Hz, p)
MANIP = {"LCIRC": (0, "CIRC"), "MCIRC": (1, "CIRC"), "MJ2": (2, "J2"), "MJ5": (3, "J5"), "MJ20": (4, "J20"), "MPOIS": (5, "POIS")}
SYNC_NAMES = ("fano2", "fano5", "fano10", "fano20", "chi2_5", "paircorr5", "volley2", "volley2_shuf", "cv5")
SUM_NAMES = ("dn", "lat0", "lat300", "dn_a_mean", "dn_a_end", "dn_ref_frac", "dn_excess", "mid", "mid_a_mean", "lc_ss", "lc_win",
             "mid_ss", "dn_n_isi", "dn_isi_floor_frac", "dn_isi_le4_frac", "lost")


def C(**kw):
    """Condition: dynamics overrides relative to REF. Keys: dn_tref, mid_tref, dn_ba, mid_ba, clamp_mid (None|'M0'|MANIP key),
    lc (None|'LCIRC'), sub_dn (bool), noinh (bool)."""
    return dict(dn_tref=TREF0, mid_tref=TREF0, dn_ba=BA0, mid_ba=BA0, clamp_mid=None, lc=None, sub_dn=False, noinh=False) | kw


CONDS_MAIN = {
    "REF": C(), "LCIRC": C(lc="LCIRC"),
    **{f"E1_DN_t{t:g}": C(dn_tref=t) for t in (0.0, 1.0, 2.0, 4.0, 6.0)},
    **{f"E1b_MID_t{t:g}": C(mid_tref=t) for t in (0.0, 4.0)},
    "E1c_DN_t0": C(clamp_mid="M0", dn_tref=0.0), "E1c_DN_t6": C(clamp_mid="M0", dn_tref=6.0),
    **{f"E2a_DN_b{str(b).replace('.', '')}": C(dn_ba=b) for b in (0.0, 0.25, 1.0)},
    **{f"E2b_MID_b{str(b).replace('.', '')}": C(mid_ba=b) for b in (0.0, 0.25, 1.0)},
    "E3_M0": C(clamp_mid="M0"), **{f"E3_{m}": C(clamp_mid=m) for m in ("MCIRC", "MJ2", "MJ5", "MJ20", "MPOIS")},
    "E5a_DN_t0_sub": C(dn_tref=0.0, sub_dn=True), "E5b_noinh": C(noinh=True),
}
CONDS_REP = ("REF", "LCIRC", "E1_DN_t0", "E1_DN_t6", "E1c_DN_t0", "E2a_DN_b00", "E2b_MID_b00", "E3_M0", "E3_MCIRC", "E5a_DN_t0_sub")
CONDS_E4 = {"REF": C(), "DN_t0": C(dn_tref=0.0), "DN_b0": C(dn_ba=0.0), "MID_t0": C(mid_tref=0.0)}


def step(net, I, forced, cidx, tref, sub, probe):
    """alif.ALIF.step with: spikes of cidx forced; per-neuron refractory duration tref; subtractive reset where sub (bool vector or
    None). Returns spikes; stores v of `probe` neurons after integration/refractory clamp (before threshold) in net.vint."""
    p, dt = net.p, net.p.dt
    slot = net.t % p.delay_steps
    net.g += net.W @ net.buf[slot] - net.g * dt / p.tau_syn
    In = I + p.noise * net.rng.standard_normal(net.N) if p.noise else I
    net.v += dt / p.tau_m * (p.v_rest - net.v + net.gain * (net.g + In) - net.a)
    net.v[net.ref > 0] = p.v_reset
    net.ref -= dt
    net.vint = net.v[probe].copy()
    spk = net.v >= p.v_th
    spk[cidx] = forced
    if sub is None:
        net.v[spk] = p.v_reset
    else:
        hard = spk & ~sub
        net.v[hard] = p.v_reset
        net.v[spk & sub] -= p.v_th - p.v_reset
    net.ref[spk] = tref[spk]
    net.a += -net.a * dt / p.tau_a + net.b_a * spk
    net.buf[slot] = spk
    net.t += 1
    return spk


def vectors(cond, N, dn, mid):
    tref = np.full(N, TREF0)
    ba = np.full(N, BA0)
    tref[dn], tref[mid], ba[dn], ba[mid] = cond["dn_tref"], cond["mid_tref"], cond["dn_ba"], cond["mid_ba"]
    sub = None
    if cond["sub_dn"]:
        sub = np.zeros(N, bool)
        sub[dn] = True
    return tref, ba, sub


def check_vectors(name, cond, tref, ba, sub, N, dn, mid):
    """T2: only the intended entries differ from REF."""
    r_t, r_b, _ = vectors(C(), N, dn, mid)
    allowed_t = (dn if cond["dn_tref"] != TREF0 else []) , (mid if cond["mid_tref"] != TREF0 else [])
    allowed_b = (dn if cond["dn_ba"] != BA0 else []), (mid if cond["mid_ba"] != BA0 else [])
    dt_ = set(np.flatnonzero(tref != r_t).tolist())
    db_ = set(np.flatnonzero(ba != r_b).tolist())
    assert dt_ == set(np.r_[allowed_t[0], allowed_t[1]].astype(int).tolist()), f"T2 {name} t_ref"
    assert db_ == set(np.r_[allowed_b[0], allowed_b[1]].astype(int).tolist()), f"T2 {name} b_a"
    assert (sub is not None) == cond["sub_dn"] and (sub is None or set(np.flatnonzero(sub).tolist()) == set(dn.tolist())), f"T2 {name} sub"


def sync_metrics(tr, rng_seed=8_440_999):
    """tr [T, n] bool (one population). Window SS–W1. Returns SYNC_NAMES."""
    x = tr[SS:W1].astype(float)
    if x.sum() == 0:
        return [np.nan] * len(SYNC_NAMES)
    out = []
    for b in (2, 5, 10, 20):
        c = x.reshape(-1, b, x.shape[1]).sum((1, 2))
        out.append(c.var() / c.mean())
    X = x.reshape(-1, 5, x.shape[1]).sum(1)                            # [bins, n]
    out.append(X.mean(1).var() / X.var(0).mean())
    act = X.var(0) > 0
    cc = np.corrcoef(X[:, act].T) if act.sum() > 1 else np.full((1, 1), np.nan)
    out.append(np.nanmean(cc[np.triu_indices_from(cc, 1)]))

    def volley(y):
        c2 = y.reshape(-1, 2, y.shape[1]).sum(1)                       # [bins, n]
        pc = c2.sum(1)
        thr = pc.mean() + 3 * pc.std()
        return c2[pc >= thr].sum() / c2.sum()
    out.append(volley(x))
    rng = np.random.default_rng(rng_seed)
    out.append(volley(np.stack([np.roll(x[:, j], rng.integers(len(x))) for j in range(x.shape[1])], 1)))
    c5 = X.sum(1)
    out.append(c5.std() / c5.mean())
    return [float(v) for v in out]


def synth(train, p, rng, ev_rate=10.0):
    """Shared-event surrogate (protocol Exp 4): per-neuron counts in [W0, W1) kept exactly; 0–W0 unchanged."""
    x = train.copy()
    L = W1 - W0
    seg = np.zeros((L, train.shape[1]), bool)
    n_ev = rng.poisson(ev_rate * L / 1000.0)
    ev = rng.integers(0, L, n_ev)
    for j, n in enumerate(train[W0:W1].sum(0)):
        ts = []
        for _ in range(int(n)):
            t = int(ev[rng.integers(n_ev)] + rng.integers(-1, 2)) if (n_ev and rng.random() < p) else int(rng.integers(0, L))
            tries = 0
            while not (0 <= t < L) or any(abs(t - u) < 4 for u in ts):
                t = int(rng.integers(0, L))
                tries += 1
                if tries > 10_000:
                    raise RuntimeError("synth: cannot place spike")
            ts.append(t)
        seg[ts, j] = True
    x[W0:W1] = seg
    assert np.array_equal(x[W0:W1].sum(0), train[W0:W1].sum(0))
    return x


def replay(spec, P, seed, I, cidx, forced, cond, idx, W_noinh, dn_i, mid_i):
    N = len(spec.bodies)
    dn, mid = np.r_[idx["DNa02_L"], idx["DNa02_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    tref, ba, sub = vectors(cond, N, dn, mid)
    net = ALIF(spec, P, seed, b_a=ba)
    if cond["noinh"]:
        net.W = W_noinh
    spk = np.zeros((T, N), bool)
    a_dn = np.zeros(T)
    a_mid = np.zeros(T)
    blocked = np.zeros(T, bool)
    excess = []
    for t in range(T):
        blocked[t] = net.ref[dn_i] > 0
        spk[t] = step(net, I[t], forced[t], cidx, tref, sub, np.array([dn_i]))
        if spk[t, dn_i]:
            excess.append(net.vint[0] - P.v_th)
        a_dn[t] = net.a[dn_i]
        a_mid[t] = net.a[mid_i].mean()
    return spk, a_dn, a_mid, blocked, excess, (tref, ba, sub)


def summarise(spk, a_dn, a_mid, blocked, excess, dn_i, mid_i, lc_i, cond, lost):
    d = spk[:, dn_i]
    ts = np.flatnonzero(d)
    win = ts[(ts >= SS) & (ts < W1)]
    isi = np.diff(win)
    floor = int(np.ceil(cond["dn_tref"] - 1e-9)) + 1
    hist = np.bincount(np.minimum(isi, 51), minlength=52)[1:]          # ISI 1..50 ms, 51 = > 50
    lat0 = float(ts[0]) if len(ts) else np.nan
    t3 = ts[ts >= W0]
    s = [d[SS:W1].sum() / 0.5, lat0, float(t3[0] - W0) if len(t3) else np.nan, a_dn[SS:W1].mean(), a_dn[-1], blocked[SS:W1].mean(),
         float(np.mean(excess)) if excess else np.nan, spk[SS:W1][:, mid_i].sum() / (len(mid_i) * 0.5), a_mid[SS:W1].mean(),
         spk[SS:W1][:, lc_i].sum(), spk[W0:W1][:, lc_i].sum(), spk[SS:W1][:, mid_i].sum(), len(isi),
         float((isi <= floor).mean()) if len(isi) else np.nan, float((isi <= 4).mean()) if len(isi) else np.nan, lost]
    return np.array(s, float), hist, np.packbits(d)


def job_run(job):
    """job: kind 'main' | 'rep' | 'e4'; family; k; level_idx (e4)."""
    t0 = time.perf_counter()
    data, idx, _, _ = V.make_net("DATA", None)
    if job["family"] == "DATA":
        src = data
    else:
        src = R._b1(job["k"])[0]
    P = ALIFParams(noise=2.0)
    N = len(data.bodies)
    lc = np.r_[idx["in_L"], idx["in_R"]]
    dn, mid = np.r_[idx["DNa02_L"], idx["DNa02_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    lcmid = np.r_[lc, mid]
    W_noinh = np.asarray(data.W, float).copy()
    blk = W_noinh[np.ix_(dn, mid)]
    blk[blk < 0] = 0.0
    W_noinh[np.ix_(dn, mid)] = blk
    assert (W_noinh != np.asarray(data.W, float)).sum() == (np.asarray(data.W)[np.ix_(dn, mid)] < 0).sum()
    seeds = NOISE_REP if job["kind"] == "rep" else NOISE_MAIN
    if job["kind"] == "e4":
        conds = {f"E4_{c}_p{pi}": (cd, pi) for pi in range(len(P_SYNC)) for c, cd in CONDS_E4.items()}
        levels = [job["level_idx"]]
    else:
        names = list(CONDS_MAIN) if job["kind"] == "main" else list(CONDS_REP)
        conds = {n: (CONDS_MAIN[n], None) for n in names}
        levels = list(range(len(LEVELS)))
    if job.get("smoke"):
        seeds = seeds[:1]
    nC, nL, nR = len(conds), len(levels), len(seeds)
    summ = np.full((nC, nL, 2, nR, len(SUM_NAMES)), np.nan)
    isi = np.zeros((nC, nL, 2, nR, 51), np.int32)
    dntr = np.zeros((nC, nL, 2, nR, T // 8), np.uint8)
    lcsync = np.full((nC, nL, 2, nR, len(SYNC_NAMES)), np.nan)
    midsync = np.full((nC, nL, 2, nR, len(SYNC_NAMES)), np.nan)
    valid = dict(ref_eq_free_nonlc=[], m0_eq_ref=[], e1c_t22_note="E3_M0 doubles as E1c t_ref 2.2", lc_counts_equal=[], synth_counts_equal=[])
    free_dn = np.zeros((nL, 2, nR))
    for li_, li in enumerate(levels):
        for si, side in enumerate("LR"):
            I = R.current(idx, side, LEVELS[li], N)
            dn_i, mid_i, lc_i = idx[f"DNa02_{side}"][0], idx[f"mid_{side}"], idx[f"in_{side}"]
            pos_ipsi = np.searchsorted(lc, lc_i)
            for r, sd in enumerate(seeds):
                s = ALIF(src, P, sd).run(I, T)
                free_dn[li_, si, r] = s[SS:W1, dn_i].sum()
                train = s[:, lc]
                ref_spk = None
                for ci, (cn, (cd, pi)) in enumerate(conds.items()):
                    lost = 0
                    if pi is not None:
                        rng = np.random.default_rng(8_441_000 + 300 * li + 150 * si + 10 * pi + r)
                        tr = train.copy()
                        tr[:, pos_ipsi] = synth(train[:, pos_ipsi], P_SYNC[pi][1], rng, P_SYNC[pi][0])
                        valid["synth_counts_equal"].append(bool(np.array_equal(tr[W0:W1].sum(0), train[W0:W1].sum(0))))
                    elif cd["lc"]:
                        vi, var = MANIP[cd["lc"]]
                        tr, lost = R.manipulate(train, var, np.random.default_rng(8_440_000 + 100 * vi + r))
                    else:
                        tr = train
                    if cd["clamp_mid"]:
                        if ref_spk is None:
                            raise RuntimeError("REF must precede clamp conditions")
                        mtr = ref_spk[:, mid]
                        if cd["clamp_mid"] != "M0":
                            vi, var = MANIP[cd["clamp_mid"]]
                            mtr, lost = R.manipulate(mtr, var, np.random.default_rng(8_440_000 + 100 * vi + r))
                        cidx, forced = lcmid, np.concatenate([tr, mtr], 1)
                    else:
                        cidx, forced = lc, tr
                    spk, a_dn, a_mid, blocked, excess, vecs = replay(data, P, sd, I, cidx, forced, cd, idx, W_noinh, dn_i, mid_i)
                    if r == 0 and li_ == 0 and si == 0:
                        check_vectors(cn, cd, *vecs, N, dn, mid)
                    if cn == "REF":
                        ref_spk = spk
                        nonlc = np.setdiff1d(np.arange(N), lc)
                        valid["ref_eq_free_nonlc"].append(bool(np.array_equal(spk[:, nonlc], s[:, nonlc])) if job["family"] == "DATA" else None)
                    if cn == "E3_M0":
                        valid["m0_eq_ref"].append(bool(np.array_equal(spk, ref_spk)))
                    if pi is None and not cd["lc"]:
                        valid["lc_counts_equal"].append(bool(np.array_equal(spk[:, lc], train)))
                    summ[ci, li_, si, r], isi[ci, li_, si, r], dntr[ci, li_, si, r] = summarise(spk, a_dn, a_mid, blocked, excess, dn_i, mid_i, lc_i, cd, lost)
                    if cn == "REF" or cd["lc"] or pi is not None:
                        lcsync[ci, li_, si, r] = sync_metrics(tr[:, pos_ipsi])
                    midsync[ci, li_, si, r] = sync_metrics(spk[:, mid_i])
    path = os.path.join(job["out"], f"{job['name']}.npz")
    with open(path, "xb") as f:
        np.savez_compressed(f, summ=summ, isi=isi, dntrain=dntr, lcsync=lcsync, midsync=midsync, free_dn=free_dn,
                            conds=np.array(list(conds)), levels=np.array([LEVELS[i] for i in levels]), seeds=np.array(seeds),
                            sum_names=np.array(SUM_NAMES), sync_names=np.array(SYNC_NAMES), p_sync=np.array(P_SYNC))
    v = {k: (all(x for x in val if x is not None) if isinstance(val, list) else val) for k, val in valid.items()}
    return dict(name=job["name"], wall_s=round(time.perf_counter() - t0, 1), valid=v, n_checks={k: len(val) for k, val in valid.items() if isinstance(val, list)})


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    ap.add_argument("--protocol-sha256", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    import integrity_v5v41 as IG
    if IG.stage1()["ok"] != 28:
        sys.exit("STOP: Stage 1")
    if hashlib.sha256(open(PROTOCOL, "rb").read()).hexdigest() != a.protocol_sha256:
        sys.exit("refused: protocol sha256 mismatch")
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    jobs = [dict(kind="main", family="DATA", k=None, name="main_DATA")] + [dict(kind="main", family="B1", k=k, name=f"main_B1_{k}") for k in B1_MAIN]
    jobs += [dict(kind="e4", family="DATA", k=None, level_idx=i, name=f"e4_DATA_L{i}") for i in range(len(LEVELS))]
    jobs += [dict(kind="rep", family="DATA", k=None, name="rep_DATA")] + [dict(kind="rep", family="B1", k=k, name=f"rep_B1_{k}") for k in B1_REP]
    if a.smoke:
        jobs = [jobs[0], jobs[1], jobs[11]]
    for j in jobs:
        j.update(out=raw, smoke=a.smoke)
    jobs = [j for j in jobs if not os.path.exists(os.path.join(raw, j["name"] + ".npz"))]
    with open(os.path.join(a.out, f"config_{time.strftime('%Y%m%dT%H%M%S')}.json"), "x") as f:
        json.dump(dict(protocol_sha256=a.protocol_sha256, smoke=a.smoke, jobs=[j["name"] for j in jobs], conds_main=CONDS_MAIN, conds_rep=CONDS_REP,
                       conds_e4=CONDS_E4, p_sync=P_SYNC, levels=LEVELS, noise_main=NOISE_MAIN, noise_rep=NOISE_REP, b1_main=B1_MAIN, b1_rep=B1_REP,
                       code_sha256={f: IG.sha(os.path.join(HERE, f)) for f in ("v6m.py", "v5v43.py", "alif.py", "v5v41.py")},
                       started=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1)
    with mp.get_context("spawn").Pool(a.workers) as pool:
        for r in pool.imap_unordered(job_run, jobs):
            print(json.dumps(r), flush=True)
    with open(os.path.join(a.out, f"run_done_{time.strftime('%Y%m%dT%H%M%S')}.json"), "x") as f:
        json.dump(dict(stage1_post=IG.stage1(), finished=time.strftime("%Y-%m-%dT%H:%M:%S")), f, indent=1)


if __name__ == "__main__":
    main()
