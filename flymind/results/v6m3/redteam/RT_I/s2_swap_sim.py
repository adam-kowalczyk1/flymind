"""RT-I scratch: alternative count-swaps for V6m3 Part B. Seeds 8 499 101-199 only (noise 8 499 101-108; swap RNG root 8 499 150).
Reuses v6m3 functions unchanged (imported, not modified). Run from /Users/admin/so101_fly_project:
  .venv/bin/python -I -B flymind/results/v6m3/redteam/RT_I/s2_swap_sim.py
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

T, W0, W1, SS = M3.T, M3.W0, M3.W1, M3.SS
NOISE = tuple(range(8_499_101, 8_499_109))
SWAP_ROOT = 8_499_150
INST = (8_421_001, 8_421_004, 8_421_007, 8_421_010)
CAL = json.load(open(os.path.join(FM, "results", "v6m3", "calibration.json")))
DYN = ("REF", "T0", "T0G")
CELLS = ("DD", "BB", "DB_U", "BD_U", "DB_CT", "BD_CT", "DB_CC", "BD_CC", "DDm", "BBm", "BB_pre", "BD_U_pre", "BD_CT_pre")


def swap(timing, counts, rng, mode, groups):
    """Generalised count_swap. Deletion: uniform random subset (as v6m3). Addition: 'U' uniform (v6m3), 'CT' times drawn from the
    timing source's own same-side population PSTH, 'CC' copied from the count source neuron's own spike times. ISI>=4 where possible."""
    out = timing.copy()
    seg = out[W0:W1]
    cseg = counts[W0:W1]
    psth = {g: timing[W0:W1][:, cols].sum(1).astype(float) for g, cols in groups.items()}
    gof = {j: g for g, cols in groups.items() for j in cols}
    added = fb = 0
    for j in range(seg.shape[1]):
        have, want = np.flatnonzero(seg[:, j]), int(cseg[:, j].sum())
        if len(have) > want:
            seg[:, j] = False
            seg[rng.choice(have, want, replace=False), j] = True
            continue
        for _ in range(want - len(have)):
            occ = np.flatnonzero(seg[:, j])
            ok = np.ones(len(seg), bool)
            for d in range(-3, 4):
                p = occ + d
                ok[p[(p >= 0) & (p < len(seg))]] = False
            cand = np.flatnonzero(ok)
            w = None
            if mode == "CT":
                w = (psth[gof[j]] - seg[:, j])[cand].clip(0)
            elif mode == "CC":
                w = cseg[cand, j].astype(float)
            if len(cand) == 0:
                cand, w = np.flatnonzero(~seg[:, j]), None
                fb += 1
            if w is not None and w.sum() > 0:
                pick = rng.choice(cand, p=w / w.sum())
            else:
                pick = rng.choice(cand)
                fb += mode != "U" and w is not None
            seg[pick, j] = True
            added += 1
    return out, added, fb


def thin(x, m, rng):
    out = x.copy()
    seg = out[W0:W1]
    for j in range(seg.shape[1]):
        have = np.flatnonzero(seg[:, j])
        if len(have) > m[j]:
            seg[:, j] = False
            seg[rng.choice(have, m[j], replace=False), j] = True
    return out


def job(arg):
    k, li, si = arg
    t0 = time.perf_counter()
    data, idx, N, lc, mid, dn = M3.setup()
    src = V2.make_block_net("LCxLC", k)[0]
    lv, side = M3.LEVELS[li], "LR"[si]
    I = R.current(idx, side, lv, N)
    d = idx[f"DNa02_{side}"][0]
    pos = {n: i for i, n in enumerate(mid)}
    groups = {g: np.array([pos[n] for n in idx[g]]) for g in ("mid_L", "mid_R")}
    mi_local = groups[f"mid_{side}"]
    lcmid = np.r_[lc, mid]
    Y = np.full((len(DYN), len(CELLS), len(NOISE)), np.nan)
    PR = np.full((len(CELLS), len(NOISE)), np.nan)
    ADD = np.zeros((6, len(NOISE)))       # added frac DB_U BD_U DB_CT BD_CT DB_CC BD_CC (of count source window spikes)
    FB = np.zeros((6, len(NOISE)))
    CNT = np.zeros((len(CELLS), len(NOISE)))   # ipsi-mid spike count 500-1000 (check)
    for r, sd in enumerate(NOISE):
        dfree = ALIF(data, M3.P, sd).run(I, T)
        bfree = ALIF(src, M3.P, sd).run(I, T)
        tref0 = np.full(N, M3.P.t_ref)
        XD = M3.run3(data, sd, I, lc, dfree[:, lc], tref0, np.ones(N), None)[:, mid]
        XB = M3.run3(data, sd, I, lc, bfree[:, lc], tref0, np.ones(N), None)[:, mid]
        cells = {"DD": (XD, "D"), "BB": (XB, "B")}
        for vi, mode in enumerate(("U", "CT", "CC")):
            rng = np.random.default_rng(np.random.SeedSequence([SWAP_ROOT, k - 8_421_000, li, si, r, vi]))
            db, a1, f1 = swap(XD, XB, rng, mode, groups)
            bd, a2, f2 = swap(XB, XD, rng, mode, groups)
            cells[f"DB_{mode}"], cells[f"BD_{mode}"] = (db, "D"), (bd, "B")
            ADD[2 * vi:2 * vi + 2, r] = a1 / max(XB[W0:W1].sum(), 1), a2 / max(XD[W0:W1].sum(), 1)
            FB[2 * vi:2 * vi + 2, r] = f1, f2
            for x, c in ((db, XB), (bd, XD)):
                assert np.array_equal(x[W0:W1].sum(0), c[W0:W1].sum(0)) and np.array_equal(x[:W0], (XD if x is db else XB)[:W0])
        rng = np.random.default_rng(np.random.SeedSequence([SWAP_ROOT, k - 8_421_000, li, si, r, 9]))
        m = np.minimum(XD[W0:W1].sum(0), XB[W0:W1].sum(0))
        cells["DDm"], cells["BBm"] = (thin(XD, m, rng), "D"), (thin(XB, m, rng), "B")
        for nm in ("BB", "BD_U", "BD_CT"):
            x = cells[nm][0].copy()
            x[:W0] = XD[:W0]                       # common (DATA) 0-300 ms preamble; LC10a irrelevant (no LC->DNa02 weights)
            cells[nm + "_pre"] = (x, "B")
        for ci, nm in enumerate(CELLS):
            x = cells[nm][0]
            PR[ci, r] = M.sync_metrics(x[:, mi_local])[M.SYNC_NAMES.index("paircorr5")]
            CNT[ci, r] = x[SS:W1][:, mi_local].sum()
            lctr = dfree[:, lc] if cells[nm][1] == "D" else bfree[:, lc]
            for di, dyn in enumerate(DYN):
                tref, gain = M3.b_vectors(dyn, N, dn, CAL)
                s = M3.run3(data, sd, I, lcmid, np.concatenate([lctr, x], 1), tref, gain, None)
                Y[di, ci, r] = s[SS:W1, d].sum() / 0.5
    return dict(k=k, li=li, si=si, Y=Y.tolist(), PR=PR.tolist(), ADD=ADD.tolist(), FB=FB.tolist(), CNT=CNT.tolist(), wall=time.perf_counter() - t0)


def repro(arg):
    """Exact re-run of one MAIN cell with the ORIGINAL seeds (verification only, no new randomness)."""
    k, li, si, r = arg
    data, idx, N, lc, mid, dn = M3.setup()
    src = V2.make_block_net("LCxLC", k)[0]
    sd = M3.SETS["MAIN"]["noise"][r]
    I = R.current(idx, "LR"[si], M3.LEVELS[li], N)
    d = idx[f"DNa02_{'LR'[si]}"][0]
    bfree, dfree = ALIF(src, M3.P, sd).run(I, T), ALIF(data, M3.P, sd).run(I, T)
    t0 = np.full(N, M3.P.t_ref)
    XB = M3.run3(data, sd, I, lc, bfree[:, lc], t0, np.ones(N), None)[:, mid]
    XD = M3.run3(data, sd, I, lc, dfree[:, lc], t0, np.ones(N), None)[:, mid]
    rng = np.random.default_rng(np.random.SeedSequence([8_446_000, 0, li, si, r, k - 8_421_000]))
    DB, _, _ = M3.count_swap(XD, XB, rng)
    BD, _, _ = M3.count_swap(XB, XD, rng)
    cells = {"DD": (XD, dfree), "DB": (DB, dfree), "BD": (BD, bfree), "BB": (XB, bfree)}
    out = []
    for dyn in M3.B_DYN:
        tref, gain = M3.b_vectors(dyn, N, dn, CAL)
        out.append([M3.run3(data, sd, I, np.r_[lc, mid], np.concatenate([cells[c][1][:, lc], cells[c][0]], 1), tref, gain, None)[SS:W1, d].sum() / 0.5
                    for c in M3.B_CELLS])
    raw = np.load(os.path.join(FM, "results", "v6m3", "raw", f"MAIN_B1_{k}.npz"))["B"][:, :, li, si, r]
    return dict(arg=arg, rerun=out, raw=raw.tolist(), equal=bool(np.array_equal(np.array(out), raw)))


if __name__ == "__main__":
    t0 = time.perf_counter()
    with mp.get_context("spawn").Pool(8) as pool:
        rp = pool.map(repro, [(8_421_001, 0, 0, 0), (8_421_004, 1, 1, 5)])
        res = pool.map(job, [(k, li, si) for k in INST for li in range(2) for si in range(2)])
    json.dump(dict(repro=rp, res=res, cells=CELLS, dyn=DYN, inst=INST, noise=NOISE), open(os.path.join(HERE, "swap_sim.json"), "x"))
    print("repro", [x["equal"] for x in rp], "wall", round(time.perf_counter() - t0, 1), "cpu-sum", round(sum(x["wall"] for x in res), 1))
