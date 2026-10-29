"""Open-loop feasibility probe of CX-state interventions (no MuJoCo). Dev network seeds only.
Protocol: cue at a0 for 0.3 s -> free (u_for(0)) 0.4 s -> intervention -> free 0.6 s.
Interventions: pulse = EPG Gaussian current (same as visual cue input) centred at bump_now+delta for D ms
(delta=0 is the sham: identical input energy, no displacement); reset = ring inhibition (rest=True) for D ms.
Records bump angle/coherence, EPG/PFL3 mean rate and DNa02 L-R before/after."""
import json, sys, numpy as np
sys.path.insert(0, "/Users/admin/so101_fly_project/bio2")
from brain import Brain
wrap = lambda x: float(np.angle(np.exp(1j * x)))
seeds = [int(s) for s in sys.argv[1].split(",")]
out = sys.argv[2]
rows = []
for s in seeds:
    b = Brain(seed=s); b.calibrate_ring(); b.calibrate_steer(); u0 = b.u_for(0.0); g = b.groups
    def snap(spk):
        a, c, r = b.bump(spk)
        rt = b.rate
        return dict(ang=a, coh=c, epg=r, pfl3=float(rt[np.r_[g["PFL3_L"], g["PFL3_R"]]].mean()),
                    dna02=float(rt[g["DNa02_L"]].mean() - rt[g["DNa02_R"]].mean()))
    for a0 in np.radians([-40.0, 0.0, 40.0]):
        for kind, delta, D in [("pulse", d, D) for d in (-30, 0, 30) for D in (30, 50, 100, 200)] + [("reset", 0, D) for D in (50, 100, 200)]:
            b.reset()
            for _ in range(30): b.step10(cue=a0)
            for _ in range(40): spk = b.step10(u=u0)
            pre = snap(spk)
            pre_ang = [b.bump(spk)[0]]
            for _ in range(D // 10):
                if kind == "pulse":
                    spk = b.step10(cue=pre["ang"] + np.radians(delta), u=u0)
                else:
                    spk = b.step10(u=u0, rest=True)
            during = snap(spk)
            traj = []
            for k in range(60):
                spk = b.step10(u=u0); traj.append(snap(spk))
            post50, post600 = traj[4], traj[-1]
            shift = lambda x: float(np.degrees(wrap(x["ang"] - pre["ang"])))
            rows.append(dict(seed=s, a0=float(np.degrees(a0)), kind=kind, delta=delta, D=D,
                             pre=pre, during=during, post50=post50, post600=post600,
                             shift_during=shift(during), shift_post50=shift(post50), shift_post600=shift(post600)))
    print("seed", s, flush=True)
json.dump(rows, open(out, "w"))
