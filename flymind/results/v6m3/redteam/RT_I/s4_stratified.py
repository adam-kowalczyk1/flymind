"""RT-I scratch: count-swap with counts matched separately in 300-500 and 500-1000 ms (stratified), REF + T0G. Seeds as s2 (noise 8 499 101-108),
swap RNG root 8 499 160. Also records DNa02-weighted excitatory drive of each cell in 500-1000 ms.
Run: .venv/bin/python -I -B flymind/results/v6m3/redteam/RT_I/s4_stratified.py"""
import json, multiprocessing as mp, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
import s2_swap_sim as S2  # noqa: E402
import v5v42 as V2, v5v43 as R, v6m3 as M3  # noqa: E401,E402
from alif import ALIF  # noqa: E402
T, W0, W1, SS = M3.T, M3.W0, M3.W1, M3.SS
CELLS = ("DD", "BB", "DB_U", "BD_U", "DB_U2", "BD_U2", "DB_CT2", "BD_CT2", "DDm2", "BBm2")
DYN = ("REF", "T0G")


def strat(fn, x, c, rng, *a):
    """apply fn (S2.swap / S2.thin style on [W0, W1)) separately on [300,500) and [500,1000) by shifting the window."""
    out = x.copy()
    for lo, hi in ((300, 500), (500, 1000)):
        S2.W0, S2.W1 = lo, hi
        out = fn(out, c, rng, *a)
        out = out[0] if isinstance(out, tuple) else out
    S2.W0, S2.W1 = W0, W1
    return out


def job(arg):
    k, li, si = arg
    data, idx, N, lc, mid, dn = M3.setup()
    W = np.asarray(data.W, float)
    src = V2.make_block_net("LCxLC", k)[0]
    side = "LR"[si]
    I = R.current(idx, side, M3.LEVELS[li], N)
    d = idx[f"DNa02_{side}"][0]
    wpos = np.maximum(W[d, mid], 0)
    pos = {n: i for i, n in enumerate(mid)}
    groups = {g: np.array([pos[n] for n in idx[g]]) for g in ("mid_L", "mid_R")}
    Y = np.full((len(DYN), len(CELLS), 8), np.nan)
    DR = np.full((len(CELLS), 8), np.nan)
    for r, sd in enumerate(S2.NOISE):
        t0 = np.full(N, M3.P.t_ref)
        dfree, bfree = ALIF(data, M3.P, sd).run(I, T), ALIF(src, M3.P, sd).run(I, T)
        XD = M3.run3(data, sd, I, lc, dfree[:, lc], t0, np.ones(N), None)[:, mid]
        XB = M3.run3(data, sd, I, lc, bfree[:, lc], t0, np.ones(N), None)[:, mid]
        rng = np.random.default_rng(np.random.SeedSequence([8_499_160, k - 8_421_000, li, si, r]))
        cells = {"DD": (XD, "D"), "BB": (XB, "B"),
                 "DB_U": (S2.swap(XD, XB, rng, "U", groups)[0], "D"), "BD_U": (S2.swap(XB, XD, rng, "U", groups)[0], "B"),
                 "DB_U2": (strat(S2.swap, XD, XB, rng, "U", groups), "D"), "BD_U2": (strat(S2.swap, XB, XD, rng, "U", groups), "B"),
                 "DB_CT2": (strat(S2.swap, XD, XB, rng, "CT", groups), "D"), "BD_CT2": (strat(S2.swap, XB, XD, rng, "CT", groups), "B")}
        for lo, hi in ((300, 500), (500, 1000)):
            for nm in ("DB_U2", "BD_U2", "DB_CT2"):
                csrc = XB if nm.startswith("DB") else XD
                assert np.array_equal(cells[nm][0][lo:hi].sum(0), csrc[lo:hi].sum(0))
        mD, mB = XD.copy(), XB.copy()
        for lo, hi in ((300, 500), (500, 1000)):
            m = np.minimum(XD[lo:hi].sum(0), XB[lo:hi].sum(0))
            S2.W0, S2.W1 = lo, hi
            mD, mB = S2.thin(mD, m, rng), S2.thin(mB, m, rng)
        S2.W0, S2.W1 = W0, W1
        cells["DDm2"], cells["BBm2"] = (mD, "D"), (mB, "B")
        for ci, nm in enumerate(CELLS):
            x = cells[nm][0]
            DR[ci, r] = (wpos * x[SS:W1].sum(0)).sum()
            lctr = dfree[:, lc] if cells[nm][1] == "D" else bfree[:, lc]
            for di, dyn in enumerate(DYN):
                tref, gain = M3.b_vectors(dyn, N, dn, S2.CAL)
                Y[di, ci, r] = M3.run3(data, sd, I, np.r_[lc, mid], np.concatenate([lctr, x], 1), tref, gain, None)[SS:W1, d].sum() / 0.5
    return dict(k=k, li=li, si=si, Y=Y.tolist(), DR=DR.tolist())


if __name__ == "__main__":
    t = time.perf_counter()
    with mp.get_context("spawn").Pool(8) as pool:
        res = pool.map(job, [(k, li, si) for k in S2.INST for li in range(2) for si in range(2)])
    json.dump(dict(res=res, cells=CELLS, dyn=DYN), open(os.path.join(HERE, "stratified.json"), "x"))
    print("wall", round(time.perf_counter() - t, 1))
