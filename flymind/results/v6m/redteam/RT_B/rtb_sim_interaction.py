"""RT-B new simulation (seeds ONLY from 8_498_101-199): interaction of DN t_ref 0 x intermediate circular shift, intermediates clamped.
Noise seeds 8_498_111..118 (replay + source free runs), circ-shift RNG 8_498_151..158. Network instances reused: DATA and B1 8_421_001..010
(fixed model objects; no new network randomness). Writes only results/v6m/redteam/RT_B/sim_interaction.npz.
Conditions (all LC10a clamped to source trains, intermediates clamped): M0 (=REF), MC (circ-shifted intermediates), T0 (M0 + DN t_ref 0),
MCT0 (MC + DN t_ref 0; same shift as MC). Uses v6m.replay / v6m.C / v5v43.manipulate unchanged."""
import os, sys, time, multiprocessing as mp
import numpy as np
HERE = "/Users/admin/so101_fly_project/flymind"
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "results/v6m/redteam/RT_B/sim_interaction.npz")
NOISE = tuple(range(8_498_111, 8_498_119))
CIRC_SEED0 = 8_498_151
CONDS = ("M0", "MC", "T0", "MCT0")


def job(fam_k):
    import v5v41 as V, v5v43 as R, v6m as M
    from alif import ALIF, ALIFParams
    fam, k = fam_k
    data, idx, _, _ = V.make_net("DATA", None)
    src = data if fam == "DATA" else R._b1(k)[0]
    P = ALIFParams(noise=2.0); N = len(data.bodies)
    lc = np.r_[idx["in_L"], idx["in_R"]]; mid = np.r_[idx["mid_L"], idx["mid_R"]]; lcmid = np.r_[lc, mid]
    out = np.zeros((len(CONDS), 3, 2, len(NOISE)))
    chk = []
    for li, lv in enumerate(R.LEVELS):
        for si, side in enumerate("LR"):
            I = R.current(idx, side, lv, N); dn_i, mid_i = idx[f"DNa02_{side}"][0], idx[f"mid_{side}"]
            for r, sd in enumerate(NOISE):
                s = ALIF(src, P, sd).run(I, R.T); tr = s[:, lc]
                ref, *_ = M.replay(data, P, sd, I, lc, tr, M.C(), idx, None, dn_i, mid_i)
                mtr0 = ref[:, mid]
                mtrc, lost = R.manipulate(mtr0, "CIRC", np.random.default_rng(CIRC_SEED0 + r))
                chk.append(bool(np.array_equal(mtrc[R.W0:R.W1].sum(0), mtr0[R.W0:R.W1].sum(0))))
                for ci, (mt, cd) in enumerate(((mtr0, M.C(clamp_mid="M0")), (mtrc, M.C(clamp_mid="MCIRC")),
                                               (mtr0, M.C(clamp_mid="M0", dn_tref=0.0)), (mtrc, M.C(clamp_mid="MCIRC", dn_tref=0.0)))):
                    spk, *_ = M.replay(data, P, sd, I, lcmid, np.concatenate([tr, mt], 1), cd, idx, None, dn_i, mid_i)
                    if ci == 0:
                        chk.append(bool(np.array_equal(spk, ref)))          # identity clamp == REF
                    out[ci, li, si, r] = spk[R.SS:R.W1, dn_i].sum() / 0.5
    return fam, k, out, all(chk)


if __name__ == "__main__":
    t0 = time.time()
    fams = [("DATA", None)] + [("B1", k) for k in range(8_421_001, 8_421_011)]
    with mp.get_context("spawn").Pool(6) as p:
        res = p.map(job, fams)
    D = [r for r in res if r[0] == "DATA"][0]; B = sorted([r for r in res if r[0] == "B1"], key=lambda x: x[1])
    print("checks ok:", all(r[3] for r in res), "wall", round(time.time() - t0, 1), "s")
    with open(OUT, "xb") as f:
        np.savez_compressed(f, data=D[2], b1=np.stack([b[2] for b in B]), conds=np.array(CONDS), noise=np.array(NOISE), circ_seed0=CIRC_SEED0)
