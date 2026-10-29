"""Scene feasibility probe (MuJoCo + vision, no SNN): detectability of stationary / slow / mirrored balls, effect of
stopping the ball, and how fast a P tracker (omega = 2.5*cue) converges. Uses phase-1 helpers unchanged."""
import json, sys, numpy as np, mujoco
sys.path.insert(0, "/Users/admin/so101_fly_project/bio2")
import scene2
import test_cx_working_memory_vs_kalman as X
from vision import Vision

def run(y0, vy, t_stop=None, T=3.0, K=2.5):
    m, d = scene2.load(); scene2.reset_scene(m, d, ball_y0=y0, ball_vy=vy)
    scene2.set_mocap(m, d, "occluder", scene2.PARK); mujoco.mj_forward(m, d)
    r, opt = scene2.eye_renderer(m); vis = Vision(scene2.CAM_FOVY, scene2.CAM_W / scene2.CAM_H, efference=True)
    bv = m.joint("ball").dofadr[0]; qp = None; log = []
    try:
        for k in range(int(T * 100)):
            t = d.time
            if t_stop is not None and t >= t_stop:
                d.qvel[bv:bv + 6] = 0.0
            q = float(d.qpos[0]); dpsi = 0.0 if qp is None else -(q - qp); qp = q
            r.update_scene(d, camera="eye", scene_option=opt); vo = vis.step(r.render(), dpsi=dpsi)
            R = d.cam("eye").xmat.reshape(3, 3); c0 = d.cam("eye").xpos; aim = X.get_aim_azimuth(d)
            cue = None
            for c in vo.get("cands", []):
                rw = R @ c["ray"]
                if rw[2] < -1e-3:
                    p = c0 + (scene2.scene.BALL_R - c0[2]) / rw[2] * rw
                    cue = X.angle_diff(float(np.arctan2(p[1], p[0])), aim); break
            true = X.angle_diff(X.get_ball_azimuth(d), aim)
            om = 0.0 if cue is None else float(np.clip(K * cue, -0.6, 0.6))
            X.apply_base_velocity(d, m, om)
            log.append((t, np.degrees(true), np.nan if cue is None else np.degrees(cue), om, -float(d.qvel[0])))
            for _ in range(10): mujoco.mj_step(m, d)
    finally:
        r.close()
    return np.array(log)

cases = {"stationary_y+0.14": (0.14, 0.0, None), "stationary_y-0.14": (-0.14, 0.0, None),
         "std_y+0.14_vy-0.10": (0.14, -0.10, None), "mirror_y-0.14_vy+0.10": (-0.14, 0.10, None),
         "slow_y+0.10_vy-0.05": (0.10, -0.05, None), "slow_mirror_y-0.10_vy+0.05": (-0.10, 0.05, None),
         "std_stop_at_1.2s": (0.14, -0.10, 1.2), "mirror_stop_at_1.2s": (-0.14, 0.10, 1.2)}
res = {}
for name, (y0, vy, ts) in cases.items():
    L = run(y0, vy, ts)
    det = ~np.isnan(L[:, 2])
    seg = lambda a, b: float(det[(L[:, 0] >= a) & (L[:, 0] < b)].mean())
    res[name] = dict(det_0_0p5=seg(0, 0.5), det_0p5_1p2=seg(0.5, 1.2), det_1p2_2=seg(1.2, 2.0), det_2_3=seg(2.0, 3.0),
                     true_err_at=[float(L[int(t * 100), 1]) for t in (0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.9)],
                     cue_minus_true_mean=float(np.nanmean(L[:, 2] - L[:, 1])), w_base_at_1p2=float(L[120, 4]))
    print(name, json.dumps(res[name]), flush=True)
json.dump(res, open(sys.argv[1], "w"), indent=1)
