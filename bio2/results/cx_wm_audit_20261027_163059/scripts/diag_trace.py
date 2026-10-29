"""Diagnostic: run one trial of the UNMODIFIED experiment loop and log per-step traces via monkeypatching
(no change to the loop itself). Usage: diag_trace.py VARIANT SEED [T_OCC] [T_TOTAL] -> prints JSON summary, saves npz."""
import json, os, sys
import numpy as np
BIO2 = "/Users/admin/so101_fly_project/bio2"
sys.path.insert(0, BIO2)
import test_cx_working_memory_vs_kalman as X

LOG = []
_apply = X.apply_base_velocity
def apply_logged(d, m, omega_cmd, dt=X.CFG["dt"]):
    LOG.append(dict(t=float(d.time), omega=float(omega_cmd), q0=float(d.qpos[0]), aim=X.get_aim_azimuth(d),
                    ball=X.get_ball_azimuth(d), ball_xy=d.body("ball").xpos[:2].tolist(), cue=CUE[-1] if CUE else None,
                    ctrl0_before=float(d.ctrl[0])))
    return _apply(d, m, omega_cmd, dt)
X.apply_base_velocity = apply_logged
CUE = []
for cls in (X.LastObsPDController, X.KalmanPDController, X.BioAdaptiveController):
    f = cls.step
    def wrap(self, cue_rel, *a, _f=f, **k):
        CUE.append(None if cue_rel is None else float(cue_rel))
        return _f(self, cue_rel, *a, **k)
    cls.step = wrap

if __name__ == "__main__":
    v, s = sys.argv[1], int(sys.argv[2])
    t_occ = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    t_tot = float(sys.argv[4]) if len(sys.argv) > 4 else 3.5
    res = X.run_closedloop_trial(v, s, t_occ, t_total=t_tot)
    out = os.path.join(os.path.dirname(__file__), "..", "preflight", f"trace_{v}_s{s}_occ{t_occ}.json")
    json.dump(dict(result=res, log=LOG), open(out, "w"))
    a = np.array([[r["t"], np.degrees(X.angle_diff(r["ball"], r["aim"])), r["omega"], np.nan if r["cue"] is None else np.degrees(r["cue"]), np.degrees(r["aim"]), r["q0"]] for r in LOG])
    print(json.dumps(res))
    print(" t     true_rel  omega   cue    aim_az  q0")
    for row in a[::10]:
        print(" ".join(f"{x:7.3f}" for x in row))
