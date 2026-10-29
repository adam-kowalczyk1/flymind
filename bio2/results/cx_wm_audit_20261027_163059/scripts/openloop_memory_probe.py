"""Open-loop memory probe (no MuJoCo, no vision): does the CX bump hold a cued bearing and integrate imposed
self-rotation, independent of the moving-target confound of the closed-loop task?
Protocol per network seed: cue at a for 0.3 s (as calibrate_steer), then cue removed for 2.0 s while an imposed base
rotation w is fed exactly as BIO-Static does (u_for(-w)); BIO-NoSelf feeds u_for(0). Ideal egocentric bearing:
a - w*t. Shuffled network = make_within_projection_shuffled_brain. Seeds 100-109 (pilot range, never 0-39)."""
import json, sys, numpy as np
sys.path.insert(0, "/Users/admin/so101_fly_project/bio2")
import test_cx_working_memory_vs_kalman as X
from brain import Brain

seeds = range(int(sys.argv[1]), int(sys.argv[2]) + 1)
out = sys.argv[3]
T_CHECK = (0.25, 0.5, 1.0, 2.0)
rows = []
for s in seeds:
    b = Brain(seed=s); b.calibrate_ring(); b.calibrate_steer()
    sh = X.make_within_projection_shuffled_brain(s)
    for net, br, mode in (("intact", b, "static"), ("intact", b, "noself"), ("shuffled", sh, "static")):
        for a_deg in (-30.0, 0.0, 30.0):
            for w in (-0.3, 0.0, 0.3):
                br.reset()
                for _ in range(30):
                    br.step10(cue=np.radians(a_deg))
                u = br.u_for(-w) if mode == "static" else br.u_for(0.0)
                angs, cohs = [], []
                for k in range(200):
                    ang, coh, _ = br.bump(br.step10(u=u)); angs.append(ang); cohs.append(coh)
                angs = np.unwrap(angs)
                for tc in T_CHECK:
                    i = int(round(tc * 100)) - 1
                    ideal = np.radians(a_deg) - w * tc
                    rows.append(dict(seed=s, net=net, mode=mode, a_deg=a_deg, w=w, t=tc,
                                     err_deg=float(np.degrees(X.wrap_angle(angs[i] - ideal))),
                                     coh=float(np.mean(cohs[max(0, i - 9):i + 1]))))
    print("seed", s, "done", flush=True)
json.dump(rows, open(out, "w"))
