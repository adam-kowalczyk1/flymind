"""flymind/v6m_exp6.py — V6m addendum A1 (POST HOC): rate-weighted intermediate drive to DNa02 under REF / LCIRC / E1b_MID_t0 /
E1_DN_t0. Deterministic re-simulation of V6m main conditions (same seeds). Run:
.venv/bin/python -I -B flymind/v6m_exp6.py --out flymind/results/v6m/exp6"""
import argparse
import multiprocessing as mp
import os
import sys

import numpy as np

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("run with python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v5v41 as V  # noqa: E402
import v5v43 as R  # noqa: E402
import v6m as M  # noqa: E402
from alif import ALIF, ALIFParams  # noqa: E402

CONDS = ("REF", "LCIRC", "E1b_MID_t0", "E1_DN_t0")


def job(j):
    data, idx, _, _ = V.make_net("DATA", None)
    src = data if j["family"] == "DATA" else R._b1(j["k"])[0]
    P = ALIFParams(noise=2.0)
    N = len(data.bodies)
    W = np.asarray(data.W, float)
    lc = np.r_[idx["in_L"], idx["in_R"]]
    mid = np.r_[idx["mid_L"], idx["mid_R"]]
    out = np.zeros((len(CONDS), len(M.LEVELS), 2, len(M.NOISE_MAIN), 5))   # dn count, D_exc, D_inh, n_mid_exc_partners, n_mid_all
    for li, lv in enumerate(M.LEVELS):
        for si, side in enumerate("LR"):
            I = R.current(idx, side, lv, N)
            dn_i = idx[f"DNa02_{side}"][0]
            w = W[dn_i, mid]
            for r, sd in enumerate(M.NOISE_MAIN):
                train = ALIF(src, P, sd).run(I, M.T)[:, lc]
                for ci, cn in enumerate(CONDS):
                    cd = M.CONDS_MAIN[cn]
                    tr = R.manipulate(train, "CIRC", np.random.default_rng(8_440_000 + r))[0] if cd["lc"] else train
                    spk = M.replay(data, P, sd, I, lc, tr, cd, idx, None, dn_i, idx[f"mid_{side}"])[0]
                    n = spk[M.SS:M.W1][:, mid].sum(0)
                    out[ci, li, si, r] = (spk[M.SS:M.W1, dn_i].sum(), (np.maximum(w, 0) * n).sum(), (np.minimum(w, 0) * n).sum(),
                                          n[w > 0].sum(), n.sum())
    with open(os.path.join(j["out"], f"{j['name']}.npz"), "xb") as f:
        np.savez_compressed(f, out=out, conds=np.array(CONDS))
    return j["name"]


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    jobs = [dict(family="DATA", k=None, name="DATA")] + [dict(family="B1", k=k, name=f"B1_{k}") for k in M.B1_MAIN]
    for x in jobs:
        x["out"] = a.out
    with mp.get_context("spawn").Pool(6) as pool:
        for r in pool.imap_unordered(job, jobs):
            print(r, flush=True)


if __name__ == "__main__":
    main()
