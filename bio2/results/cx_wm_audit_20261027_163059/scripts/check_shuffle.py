"""Non-invasive check of make_within_projection_shuffled_brain: per-projection weight multisets, sign,
non-CX weights untouched, ring profile destroyed, and why slope_mem == 0 (EPG activity in memory phase)."""
import sys, numpy as np
sys.path.insert(0, "/Users/admin/so101_fly_project/bio2")
import test_cx_working_memory_vs_kalman as X
from brain import Brain
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 100
b0 = Brain(seed=seed); W0 = b0.net.W.copy()
bs = X.make_within_projection_shuffled_brain(seed); W1 = bs.net.W
g = b0.groups; cx = np.concatenate([g[k] for k in X.CX_GROUPS])
ok_multiset = all(np.allclose(np.sort(W0[np.ix_(g[b], g[a])].ravel()), np.sort(W1[np.ix_(g[b], g[a])].ravel()))
                  for a in X.CX_GROUPS for b in X.CX_GROUPS)
mask = np.ones_like(W0, bool); mask[np.ix_(cx, cx)] = False
print("per-projection multiset preserved:", ok_multiset)
print("non-CX weights identical:", np.array_equal(W0[mask], W1[mask]))
print("sign pattern preserved:", np.array_equal(np.sign(W0), np.sign(W1)))
print("frac CX weights changed:", float((W0[np.ix_(cx, cx)] != W1[np.ix_(cx, cx)]).mean()))
# ring-profile correlation: weight vs cos(phase difference) for EPG->EPG and EPG->PFL3
th = b0.theta
for a, bb in (("EPG", "EPG"), ("EPG", "PFL3_L"), ("PEN_a_L", "EPG"), ("Delta7", "EPG")):
    pre, post = g[a], g[bb]; d = np.cos(th[post][:, None] - th[pre][None, :]).ravel()
    print(f"corr(w, cos dphi) {a}->{bb}: intact {np.corrcoef(W0[np.ix_(post, pre)].ravel(), d)[0,1]:+.3f}  shuffled {np.corrcoef(W1[np.ix_(post, pre)].ravel(), d)[0,1]:+.3f}")
print("steer intact :", {k: np.round(v, 3).tolist() for k, v in Brain(seed=seed).__dict__.items() if False} or "")
b0.calibrate_ring(); b0.calibrate_steer()
for name, b in (("intact", b0), ("shuffled", bs)):
    print(name, "steer:", {k: np.round(v, 3).tolist() for k, v in b.steer.items()})
    print(name, "ring calib v range [rad/s]:", np.round(b.calib[0][[0, -1]], 3).tolist(), "u_for(0)=", round(b.u_for(0.0), 3))
    # memory phase: cue 0.3 s then free bump for 1 s
    b.reset()
    for _ in range(30): b.step10(cue=0.5)
    ep = []; coh = []; ang = []
    for _ in range(100):
        s = b.step10(u=b.u_for(0.0)); a_, c_, r_ = b.bump(s); ep.append(r_); coh.append(c_); ang.append(a_)
    print(f"{name} memory phase: EPG mean rate first/last 100ms {np.mean(ep[:10]):.1f}/{np.mean(ep[-10:]):.1f} Hz; coherence last {np.mean(coh[-10:]):.2f}; bump angle start/end {np.degrees(ang[0]):.1f}/{np.degrees(ang[-1]):.1f} deg (cue was 28.6)")
