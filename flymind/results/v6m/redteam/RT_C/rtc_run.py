"""RT-C (red team V6m): parameter dependence of the V6m key results. Reuses v6m.replay/v6m.step, v5v43.manipulate/current,
v5v41.make_net, v5v42.make_block_net unchanged; only ALIFParams / module constants (v6m.BA0) are set in-process. Writes only next to itself.
Seeds (RT-C sub-range 8 498 201–299): noise 8 498 201–204; LCIRC rng 8 498 210+r; MCIRC rng 8 498 220+r.
Run: .venv/bin/python -I -B flymind/results/v6m/redteam/RT_C/rtc_run.py
"""
import multiprocessing as mp
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FM = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, FM)
import v5v41 as V  # noqa: E402
import v5v42 as V2  # noqa: E402
import v5v43 as R  # noqa: E402
import v6m  # noqa: E402
from alif import ALIF, ALIFParams  # noqa: E402

NOISE = (8_498_201, 8_498_202, 8_498_203, 8_498_204)
B1 = (8_421_001, 8_421_002, 8_421_003)
# config: (ALIF overrides, J0, levels). D0 = V6m's own set at 2 of its levels (calibrates this reduced design).
CFG = {"D0": ({}, 0.2, (8.0, 9.0)), "TH8": (dict(v_th=-44.0), 0.2, (9.0, 10.0)),
       "BA1": (dict(b_a=1.0), 0.2, (9.5, 10.5)), "J025": ({}, 0.25, (7.5, 8.0))}
CONDS = ("REF", "LCIRC", "E1_DN_t0", "E1c_DN_t0", "E3_M0", "E3_MCIRC", "E1b_MID_t0", "E2a_DN_b00")
NAMES = v6m.SUM_NAMES


def job(a):
    cfg, fam, k = a
    t0 = time.perf_counter()
    al, J0, levels = CFG[cfg]
    v6m.BA0 = al.get("b_a", 0.5)                      # baseline b_a vector for vectors()/C(); patched in this process only
    conds = {"REF": v6m.C(), "LCIRC": v6m.C(lc="LCIRC"), "E1_DN_t0": v6m.C(dn_tref=0.0), "E1c_DN_t0": v6m.C(clamp_mid="M0", dn_tref=0.0),
             "E3_M0": v6m.C(clamp_mid="M0"), "E3_MCIRC": v6m.C(clamp_mid="MCIRC"), "E1b_MID_t0": v6m.C(mid_tref=0.0),
             "E2a_DN_b00": v6m.C(dn_ba=0.0)}
    P = ALIFParams(**{**ALIFParams(noise=2.0).__dict__, **al})
    data, idx, _, _ = V.make_net("DATA", None, J0)
    src = data if fam == "DATA" else V2.make_block_net("LCxLC", k, J0)[0]
    N = len(data.bodies)
    lc = np.r_[idx["in_L"], idx["in_R"]]
    dn, mid = np.r_[idx["DNa02_L"], idx["DNa02_R"]], np.r_[idx["mid_L"], idx["mid_R"]]
    W_noinh = np.asarray(data.W, float)
    summ = np.full((len(CONDS), len(levels), 2, len(NOISE), len(NAMES)), np.nan)
    midsync = np.full((len(CONDS), len(levels), 2, len(NOISE), len(v6m.SYNC_NAMES)), np.nan)
    lcsync = np.full_like(midsync, np.nan)
    chk = dict(ref_eq_free=[], m0_eq_ref=[], lc_eq=[], vec_ok=[])
    for li, lv in enumerate(levels):
        for si, side in enumerate("LR"):
            I = R.current(idx, side, lv, N)
            dn_i, mid_i, lc_i = idx[f"DNa02_{side}"][0], idx[f"mid_{side}"], idx[f"in_{side}"]
            pos = np.searchsorted(lc, lc_i)
            for r, sd in enumerate(NOISE):
                s = ALIF(src, P, sd).run(I, R.T)
                train = s[:, lc]
                ref_spk = None
                for ci, cn in enumerate(CONDS):
                    cd = conds[cn]
                    tr = train
                    if cd["lc"]:
                        tr, _ = R.manipulate(train, "CIRC", np.random.default_rng(8_498_210 + r))
                    cidx, forced = lc, tr
                    if cd["clamp_mid"]:
                        mtr = ref_spk[:, mid]
                        if cd["clamp_mid"] == "MCIRC":
                            mtr, _ = R.manipulate(mtr, "CIRC", np.random.default_rng(8_498_220 + r))
                        cidx, forced = np.r_[lc, mid], np.concatenate([tr, mtr], 1)
                    spk, a_dn, a_mid, blk, exc, vecs = v6m.replay(data, P, sd, I, cidx, forced, cd, idx, W_noinh, dn_i, mid_i)
                    tref, ba, _ = vecs
                    exp_ba = np.full(N, v6m.BA0)
                    exp_ba[dn], exp_ba[mid] = cd["dn_ba"], cd["mid_ba"]
                    chk["vec_ok"].append(bool(np.array_equal(ba, exp_ba) and np.all(tref[lc] == 2.2)))
                    if cn == "REF":
                        ref_spk = spk
                        if fam == "DATA":
                            nonlc = np.setdiff1d(np.arange(N), lc)
                            chk["ref_eq_free"].append(bool(np.array_equal(spk[:, nonlc], s[:, nonlc])))
                    if cn == "E3_M0":
                        chk["m0_eq_ref"].append(bool(np.array_equal(spk, ref_spk)))
                    if not cd["lc"]:
                        chk["lc_eq"].append(bool(np.array_equal(spk[:, lc], train)))
                    summ[ci, li, si, r] = v6m.summarise(spk, a_dn, a_mid, blk, exc, dn_i, mid_i, lc_i, cd, 0)[0]
                    midsync[ci, li, si, r] = v6m.sync_metrics(spk[:, mid_i])
                    if ci < 2:
                        lcsync[ci, li, si, r] = v6m.sync_metrics(tr[:, pos])
    out = os.path.join(HERE, "raw", f"{cfg}_{fam}{'' if k is None else '_' + str(k)}.npz")
    with open(out, "xb") as f:
        np.savez_compressed(f, summ=summ, midsync=midsync, lcsync=lcsync, conds=np.array(CONDS), sum_names=np.array(NAMES),
                            levels=np.array(levels), seeds=np.array(NOISE), v_th=P.v_th, b_a=v6m.BA0, J0=J0)
    return cfg, fam, k, {c: (all(v), len(v)) for c, v in chk.items()}, round(time.perf_counter() - t0, 1)


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)
    jobs = [(c, "DATA", None) for c in CFG] + [(c, "B1", k) for c in CFG for k in B1]
    t0 = time.perf_counter()
    with mp.get_context("spawn").Pool(8) as pool:
        for res in pool.imap_unordered(job, jobs):
            print(res, flush=True)
    print("wall", round(time.perf_counter() - t0, 1))
