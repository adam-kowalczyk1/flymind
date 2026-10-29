"""Graded within-projection shuffle (fraction f of CX weights permuted among themselves, per projection and sign),
NO gain compensation; network's own calibrate_ring/steer as in phase 1. Measures cue-driven bump (during cue),
persistence 1 s after cue removal (coherence, EPG rate) and bearing error. Dev network seeds."""
import json, sys, numpy as np
sys.path.insert(0, "/Users/admin/so101_fly_project/bio2")
import test_cx_working_memory_vs_kalman as X
from brain import Brain
wrap = lambda x: float(np.angle(np.exp(1j * x)))

def graded(seed, f):
    b = Brain(seed=seed); rng = np.random.default_rng(10_000 + seed); g = b.groups; W = b.net.W.copy()
    for ga in X.CX_GROUPS:
        for gb in X.CX_GROUPS:
            sub = W[np.ix_(g[gb], g[ga])].copy()
            for sign in (1.0, -1.0):
                idx = np.flatnonzero((sign * sub) > 0)
                pick = idx[rng.random(len(idx)) < f]
                sub.flat[pick] = sub.flat[rng.permutation(pick)]
            W[np.ix_(g[gb], g[ga])] = sub
    b.net.W = W; b.reset(); b.calibrate_ring(); b.calibrate_steer()
    return b

seeds = [int(s) for s in sys.argv[1].split(",")]; fr = [float(x) for x in sys.argv[2].split(",")]; out = sys.argv[3]
rows = []
for s in seeds:
    for f in fr:
        b = graded(s, f) if f > 0 else (lambda bb: (bb.calibrate_ring(), bb.calibrate_steer(), bb)[2])(Brain(seed=s))
        u0 = b.u_for(0.0)
        for a0 in np.radians([-60, -20, 20, 60]):
            b.reset(); cc = []
            for _ in range(30):
                spk = b.step10(cue=a0); cc.append(b.bump(spk))
            cue_ang, cue_coh, cue_rate = np.mean([c[1] for c in cc[-10:]]), None, np.mean([c[2] for c in cc[-10:]])
            cue_err = np.degrees(wrap(cc[-1][0] - a0))
            mem = [b.bump(b.step10(u=u0)) for _ in range(100)]
            rows.append(dict(seed=s, f=f, a0=float(np.degrees(a0)), cue_coh=float(cue_ang), cue_rate=float(cue_rate), cue_err=float(cue_err),
                             mem_coh_1s=float(np.mean([m[1] for m in mem[-10:]])), mem_rate_1s=float(np.mean([m[2] for m in mem[-10:]])),
                             mem_err_1s=float(np.degrees(wrap(mem[-1][0] - a0))), slope_mem=np.asarray(b.steer["slope_mem"]).tolist(),
                             slope=np.asarray(b.steer["slope"]).tolist(), calib_vrange=[float(b.calib[0][0]), float(b.calib[0][-1])]))
        print("seed", s, "f", f, flush=True)
json.dump(rows, open(out, "w"))
