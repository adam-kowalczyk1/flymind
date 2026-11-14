"""RT-D test 2: is the E3 MCIRC 'timing' effect carried by the DN->intermediate->DN loop (21 DN-target intermediates) or by the
rest? And replication of the B_t0 M0-vs-MCIRC result on fresh reps. Seeds: noise 8 498 305-308; CIRC offsets 8 498 365-368.
Same engine as rtd_dn_nonlin.step_x. Run: .venv/bin/python -I -B flymind/results/v6m/redteam/RT_D/rtd_fb.py"""
import multiprocessing as mp
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rtd_dn_nonlin as X  # noqa: E402  (adds flymind to path)
import v5v41 as V  # noqa: E402
import v5v43 as R  # noqa: E402
import v6m as M  # noqa: E402
from alif import ALIF, ALIFParams  # noqa: E402

NOISE = tuple(range(8_498_305, 8_498_309))
CIRC_RNG = 8_498_365
KEYS = (("REF", "M0"), ("REF", "MCIRC"), ("REF", "MCIRC_fb"), ("REF", "MCIRC_nonfb"), ("t0", "M0"), ("t0", "MCIRC"))


def job(src_key):
    data, idx, _, _ = V.make_net("DATA", None)
    src = data if src_key == "DATA" else R._b1(src_key)[0]
    P = ALIFParams(noise=2.0)
    N = len(data.bodies)
    W = np.asarray(data.W, float)
    lc = np.r_[idx["in_L"], idx["in_R"]]
    dn, mid = np.r_[idx["DNa02_L"], idx["DNa02_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    fb = (W[np.ix_(mid, dn)] != 0).any(1)
    lcmid = np.r_[lc, mid]
    out = np.full((len(KEYS), len(M.LEVELS), 2, len(NOISE)), np.nan)
    for li, lv in enumerate(M.LEVELS):
        for si, side in enumerate("LR"):
            I = R.current(idx, side, lv, N)
            dn_i = idx[f"DNa02_{side}"][0]
            for r, sd in enumerate(NOISE):
                train = ALIF(src, P, sd).run(I, M.T)[:, lc]
                ref = M.replay(data, P, sd, I, lc, train, M.CONDS_MAIN["REF"], idx, None, dn_i, idx[f"mid_{side}"])[0]
                m0 = ref[:, mid]
                mc = R.manipulate(m0, "CIRC", np.random.default_rng(CIRC_RNG + r))[0]
                mids = {"M0": m0, "MCIRC": mc, "MCIRC_fb": np.where(fb[None, :], mc, m0), "MCIRC_nonfb": np.where(fb[None, :], m0, mc)}
                for ki, (dyn, cl) in enumerate(KEYS):
                    tref = np.full(N, M.TREF0)
                    tref[dn] = 0.0 if dyn == "t0" else M.TREF0
                    net = ALIF(data, P, sd)
                    forced = np.concatenate([train, mids[cl]], 1)
                    cnt = 0
                    for t in range(M.T):
                        s, _ = X.step_x(net, I[t], forced[t], lcmid, tref, None, None, None)
                        cnt += int(s[dn_i]) if t >= M.SS else 0
                    out[ki, li, si, r] = cnt / 0.5
                    if ki == 0:
                        assert cnt == ref[M.SS:, dn_i].sum()
    np.savez(os.path.join(HERE, "raw_fb", f"{src_key}.npz"), out=out, keys=np.array(["|".join(k) for k in KEYS]))
    return src_key


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "raw_fb"), exist_ok=True)
    with mp.get_context("spawn").Pool(4) as pool:
        for r in pool.imap_unordered(job, X.SOURCES):
            print("done", r, flush=True)
    Z = {k: np.load(os.path.join(HERE, "raw_fb", f"{k}.npz"))["out"].mean((1, 2)) for k in X.SOURCES}
    B = [k for k in X.SOURCES if k != "DATA"]
    rng = np.random.default_rng(8_498_398)
    g = lambda i, kk=None, rr=None, dd=None: (np.mean([Z[B[a]][i][rr[j]] for j, a in enumerate(kk)]) - Z["DATA"][i][dd].mean()) if kk is not None else \
        np.mean([Z[b][i].mean() for b in B]) - Z["DATA"][i].mean()
    for i, k in enumerate(KEYS):
        print(f"{'|'.join(k):18s} DATA {Z['DATA'][i].mean():6.1f}  B1 {np.mean([Z[b][i].mean() for b in B]):6.1f}  gap {g(i):+6.1f}")
    bs = []
    for _ in range(5000):
        kk, rr, dd = rng.integers(3, size=3), rng.integers(4, size=(3, 4)), rng.integers(4, size=4)
        G = [g(i, kk, rr, dd) for i in range(len(KEYS))]
        bs.append([G[1] - G[0], G[2] - G[0], G[3] - G[0], G[5] - G[4], (G[1] - G[0]) - (G[5] - G[4])])
    bs = np.array(bs)
    G = [g(i) for i in range(len(KEYS))]
    pts = [G[1] - G[0], G[2] - G[0], G[3] - G[0], G[5] - G[4], (G[1] - G[0]) - (G[5] - G[4])]
    for n, p, col in zip(("REF: MCIRC-M0", "REF: MCIRC_fb-M0", "REF: MCIRC_nonfb-M0", "t0: MCIRC-M0", "interaction REF-t0"), pts, bs.T):
        print(f"  gap change {n:22s} {p:+6.1f} Hz  CI95 [{np.percentile(col, 2.5):+.1f}; {np.percentile(col, 97.5):+.1f}]")
