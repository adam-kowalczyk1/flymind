"""Pomiar sygnałów widzenia w scenie (do ustawienia progów vision.py z danych):
 1) piłeczka toczy się w poprzek, ramię stoi, przesłona stała: wykrycia celu i błąd azymutu vs prawda;
 2) baza obraca się (±0,6 rad/s) przy nieruchomej scenie: obszar OFF i fałszywe cele z kopią eferentną i bez;
 3) czarna kula (r 8 cm) leci na kamerę z 0,7 m z 1,5 m/s: obszar OFF w czasie;
 4) piłeczka stacza się z równi do paszczy (scenariusz chwytu): maks. obszar OFF (nie może wyzwolić ucieczki)."""
import mujoco
import numpy as np

import scene2
from vision import Vision, true_bearing


def cam_yaw(d):
    R = d.cam("eye").xmat.reshape(3, 3)
    f = -R[:, 2]
    return np.arctan2(f[1], f[0])


def run(m, d, steps, ctrl_fn=None, eff=True):
    r, opt = scene2.eye_renderer(m)
    v = Vision(scene2.CAM_FOVY, scene2.CAM_W / scene2.CAM_H, efference=eff)
    n_sub = round(scene2.scene.CONTROL_DT / m.opt.timestep)
    out, psi = [], cam_yaw(d)
    for k in range(steps):
        if ctrl_fn:
            ctrl_fn(k, m, d)
        for _ in range(n_sub):
            mujoco.mj_step(m, d)
        r.update_scene(d, camera="eye", scene_option=opt)
        p2 = cam_yaw(d)
        o = v.step(r.render(), dpsi=float(np.angle(np.exp(1j * (p2 - psi)))))
        psi = p2
        out.append(o)
    r.close()          # bez close kolejny renderer dla nowego MjModel w tym samym procesie renderuje błędne klatki
    return out


if __name__ == "__main__":
    # 1) toczenie w poprzek
    m, d = scene2.load()
    scene2.reset_scene(m, d)
    scene2.set_mocap(m, d, "occluder", (scene2.OCC_X, 0.0, 0.05))
    truth, det, vis = [], [], []
    seg = None

    def rec(k, m, d):
        pass
    o1 = run(m, d, 500)
    m, d = scene2.load()
    scene2.reset_scene(m, d)
    scene2.set_mocap(m, d, "occluder", (scene2.OCC_X, 0.0, 0.05))
    r, opt = scene2.eye_renderer(m)
    sr, _ = scene2.eye_renderer(m)
    sr.enable_segmentation_rendering()
    v = Vision(scene2.CAM_FOVY, scene2.CAM_W / scene2.CAM_H)
    errs, hits, false_hidden, visible_n, hidden_n = [], 0, 0, 0, 0
    for k in range(500):
        for _ in range(10):
            mujoco.mj_step(m, d)
        r.update_scene(d, camera="eye", scene_option=opt)
        o = v.step(r.render())
        sr.update_scene(d, camera="eye", scene_option=opt)
        sg = sr.render()
        visible = ((sg[..., 0] == m.geom("ball").id) & (sg[..., 1] == mujoco.mjtObj.mjOBJ_GEOM)).sum() > 20
        if k < 10:
            continue
        if visible:
            visible_n += 1
            if o["target"] is not None:
                hits += 1
                errs.append(np.degrees(o["target"] - true_bearing(d, "ball")))
        else:
            hidden_n += 1
            false_hidden += o["target"] is not None
    e = np.array(errs)
    print(f"1) toczenie: cel wykryty w {hits}/{visible_n} klatek z widoczną piłeczką; błąd azymutu {e.mean():+.1f} ± "
          f"{e.std():.1f}° (|błąd| p90 {np.percentile(abs(e), 90):.1f}°); fałszywe cele gdy zasłonięta: {false_hidden}/{hidden_n}")
    r.close()
    sr.close()

    # 2) obrót bazy przy nieruchomej scenie (piłeczka zaparkowana)
    for eff in (False, True):
        m, d = scene2.load()
        q, _ = scene2.reset_scene(m, d, ball_y0=0.9, ball_vy=0.0)
        scene2.set_mocap(m, d, "occluder", (scene2.OCC_X, 0.0, 0.05))

        def rot(k, m, d):
            d.ctrl[0] = q[0] + 0.35 * np.sin(2 * np.pi * k * 0.01 / 1.2)    # ±0,35 rad, okres 1,2 s → ±1,8 rad/s max
        o = run(m, d, 360, rot, eff)
        areas = np.array([max(x["off_area"]) for x in o[10:]])
        grow = np.array([max(x["grow"]) for x in o[10:]])
        print(f"2) obrót własny, kopia eferentna {'TAK' if eff else 'NIE'}: maks. obszar OFF {areas.max()}, maks. przyrost/50 ms "
              f"{grow.max()} (p99 {np.percentile(grow, 99):.0f}), klatki z loomingiem > 0: {sum(max(x['loom']) > 0 for x in o[10:])}/{len(o) - 10}, "
              f"fałszywe cele: {sum(x['target'] is not None for x in o[10:])}")

    # 3) drapieżnik
    m, d = scene2.load()
    q, _ = scene2.reset_scene(m, d, ball_y0=0.9, ball_vy=0.0)
    cam0 = d.cam("eye").xpos.copy()
    fwd = -d.cam("eye").xmat.reshape(3, 3)[:, 2]

    def pred(k, m, dd):
        dist = max(0.7 - 1.5 * k * 0.01, 0.12)
        scene2.set_mocap(m, dd, "predator", cam0 + fwd * dist)
    o = run(m, d, 45, pred)
    print("3) drapieżnik (odległość → obszar OFF L/P, przyrost/50 ms, looming): " + ", ".join(
        f"{max(0.7 - 1.5 * k * 0.01, 0.12):.2f} m: {o[k]['off_area']} +{max(o[k]['grow'])} {max(o[k]['loom']):.2f}" for k in range(0, 45, 3)))

    # 4) piłeczka z równi do paszczy
    m, d = scene2.load(ramp_deg=12.0)
    q, _ = scene2.scene.ik_catch_pose(m, d, r=0.28)
    mujoco.mj_resetData(m, d)
    d.qpos[:5], d.qpos[5], d.ctrl[:5] = q, 0.93, q
    mujoco.mj_forward(m, d)
    o = run(m, d, 120)
    a = np.array([max(x["off_area"]) for x in o[5:]])
    gr = np.array([max(x["grow"]) for x in o[5:]])
    print(f"4) piłeczka z równi do paszczy: maks. obszar OFF {a.max()}, maks. przyrost/50 ms {gr.max()}, looming > 0: {sum(max(x['loom']) > 0 for x in o)}; "
          f"cel wykryty w {sum(x['target'] is not None for x in o)}/{len(o)} klatek")
