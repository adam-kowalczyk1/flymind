"""RT-E falsification probe: is the sign of dt = gap(MASYNC) - gap(M0) set by refractoriness or by the operating regime (bias)?
Grid t_ref {2.2, 1.0, 0} x DNa02 bias {-40..+20 mV}; same sources/seeds/surrogate RNG as rt_e.py (MASYNC draw identical)."""
import json
import multiprocessing as mp
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rt_e as E  # noqa: E402

BIAS = (-40.0, -30.0, -20.0, -10.0, -5.0, 0.0, 5.0, 10.0, 20.0)
TR = (2.2, 1.0, 0.0)


def job(arg):
    fam, k = arg
    data, src, idx = E.net(fam, k)
    N = len(data.bodies)
    lc, mid, dn = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["mid_L"], idx["mid_R"]], np.r_[idx["DNa02_L"], idx["DNa02_R"]]
    Wdn = np.asarray(data.W, float)[np.ix_(dn, mid)]
    src_id = 0 if fam == "DATA" else k - 8_421_000
    out = np.zeros((2, len(TR), len(BIAS), len(E.LEVELS), 2, len(E.NOISE)))
    for li, lv in enumerate(E.LEVELS):
        for si, side in enumerate("LR"):
            I = E.cur(idx, side, lv, N)
            for r, sd in enumerate(E.NOISE):
                lct = E.ALIF(src, E.P, sd).run(I, E.T)[:, lc]
                m0 = E.clamped(data, sd, I, lc, lct)[:, mid]
                rng = np.random.default_rng(np.random.SeedSequence([E.MANIP, src_id, li, si, r]))
                ms = [E.variant(m0, v, rng) for v in E.INPUTS][:2]          # same draw order as rt_e.py -> identical MASYNC
                Z = np.random.default_rng(sd).standard_normal((E.T, N))[:, dn]
                mids = np.stack([m for m in ms for _ in TR for _ in BIAS])
                s = E.dn_only(Wdn, mids, I[:, dn], Z, [t for _ in ms for t in TR for _ in BIAS], [b for _ in ms for _ in TR for b in BIAS])
                out[:, :, :, li, si, r] = (s[:, E.SS:E.W1, si].sum(1) / 0.5).reshape(2, len(TR), len(BIAS))
    return fam + (f"_{k}" if k else ""), out.tolist()


if __name__ == "__main__":
    with mp.get_context("spawn").Pool(6) as pool:
        res = dict(pool.map(job, [("DATA", None)] + [("B1", k) for k in E.B1]))
    json.dump(dict(bias=BIAS, tref=TR, res=res), open(os.path.join(E.OUT, "rt_e_biasgrid_raw.json"), "w"))
    x = {n: np.array(v).mean((3, 4)) for n, v in res.items()}       # [inp, tr, bias, rep]
    D = x["DATA"].mean(-1)
    B = np.mean([x[n].mean(-1) for n in x if n != "DATA"], 0)
    print("t_ref  bias | DATA M0  B1 M0 | DATA MAS  B1 MAS | gap M0  dt(Hz)  dtL")
    for ti, t in enumerate(TR):
        for bi, b in enumerate(BIAS):
            g0, g1 = B[0, ti, bi] - D[0, ti, bi], B[1, ti, bi] - D[1, ti, bi]
            dtl = np.log(B[1, ti, bi] / D[1, ti, bi]) - np.log(B[0, ti, bi] / D[0, ti, bi])
            print(f"{t:4.1f} {b:+6.1f} | {D[0,ti,bi]:7.1f} {B[0,ti,bi]:6.1f} | {D[1,ti,bi]:7.1f} {B[1,ti,bi]:6.1f} | {g0:+6.1f} {g1-g0:+7.1f} {dtl:+6.3f}")
